from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
TABLE_ORDER = [
    "departments",
    "patients",
    "doctors",
    "admissions",
    "diagnoses",
    "procedures",
    "medicines",
    "labs",
    "insurance",
    "billing",
    "claims",
    "appointments",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load validated warehouse CSVs into MySQL."
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Delete existing warehouse rows before loading.",
    )
    args = parser.parse_args()
    url = os.getenv("HOSPITAL_DB_URL")
    if not url:
        raise RuntimeError("Set HOSPITAL_DB_URL before loading MySQL.")

    engine = create_engine(url, pool_pre_ping=True)
    existing = set(inspect(engine).get_table_names())
    missing_schema = [table for table in TABLE_ORDER if table not in existing]
    if missing_schema:
        raise RuntimeError(
            "Run sql/schema.sql first. Missing tables: "
            + ", ".join(missing_schema)
        )

    if args.truncate:
        with engine.begin() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            for table in reversed(TABLE_ORDER):
                connection.execute(text(f"DELETE FROM `{table}`"))
            connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    for table in TABLE_ORDER:
        frame = pd.read_csv(PROCESSED / f"{table}.csv")
        frame.to_sql(
            table,
            engine,
            if_exists="append",
            index=False,
            chunksize=5000,
            method="multi",
        )
        with engine.connect() as connection:
            database_rows = connection.execute(
                text(f"SELECT COUNT(*) FROM `{table}`")
            ).scalar_one()
        if database_rows != len(frame):
            raise RuntimeError(
                f"Row-count mismatch for {table}: CSV={len(frame)}, "
                f"MySQL={database_rows}"
            )
        print(f"Loaded {table}: {database_rows:,} rows")

    features = pd.read_csv(PROCESSED / "model_features.csv")
    features.to_sql(
        "model_features",
        engine,
        if_exists="replace",
        index=False,
        chunksize=3000,
        method="multi",
    )
    print(f"Loaded model_features: {len(features):,} rows")


if __name__ == "__main__":
    main()
