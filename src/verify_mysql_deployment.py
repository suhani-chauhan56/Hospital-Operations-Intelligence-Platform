from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
STATUS_PATH = REPORTS / "mysql_deployment_status.json"
COUNTS_PATH = REPORTS / "mysql_table_counts.csv"
EVIDENCE_PATH = REPORTS / "mysql_query_evidence.csv"
EXPECTED_TABLES = [
    "patients",
    "doctors",
    "departments",
    "admissions",
    "diagnoses",
    "procedures",
    "medicines",
    "labs",
    "insurance",
    "billing",
    "claims",
    "appointments",
    "model_features",
    "command_center_kpis",
    "hospital_efficiency_scores",
    "emergency_forecast",
    "operational_forecast_summary",
    "operational_recommendations",
]
EXPECTED_VIEWS = [
    "vw_executive_kpis",
    "vw_command_center",
    "vw_department_kpis",
    "vw_doctor_utilization",
    "vw_monthly_revenue",
    "vw_bed_occupancy",
    "vw_efficiency_ranking",
    "vw_operational_action_queue",
    "vw_patient_360",
    "billing_claims",
]


def write_status(status: dict) -> None:
    REPORTS.mkdir(exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a populated MySQL warehouse and save query evidence."
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Return a failure code unless the complete warehouse is verified.",
    )
    args = parser.parse_args()
    generated = datetime.now(timezone.utc).isoformat()
    url = os.getenv("HOSPITAL_DB_URL")
    if not url:
        status = {
            "status": "credentials_required",
            "verified_at_utc": generated,
            "reason": "HOSPITAL_DB_URL is not configured.",
            "next_step": (
                "Set HOSPITAL_DB_URL, run schema/load/views/procedures, then "
                "python src/verify_mysql_deployment.py --require-ready."
            ),
            "evidence_generated": False,
        }
        write_status(status)
        print(status["reason"])
        if args.require_ready:
            raise SystemExit(2)
        return

    try:
        engine = create_engine(url, pool_pre_ping=True)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        views = set(inspector.get_view_names())
        missing_tables = sorted(set(EXPECTED_TABLES) - tables)
        missing_views = sorted(set(EXPECTED_VIEWS) - views)
        counts = []
        with engine.connect() as connection:
            version = str(connection.execute(text("SELECT VERSION()")).scalar_one())
            database = str(connection.execute(text("SELECT DATABASE()")).scalar_one())
            for table in EXPECTED_TABLES:
                if table in tables:
                    row_count = int(
                        connection.execute(
                            text(f"SELECT COUNT(*) FROM `{table}`")
                        ).scalar_one()
                    )
                    counts.append({"table": table, "rows": row_count})

            evidence_queries = {
                "Admissions": "SELECT COUNT(*) FROM admissions",
                "Patients": "SELECT COUNT(*) FROM patients",
                "Readmission rate": "SELECT AVG(readmitted_30d) FROM admissions",
                "Average LOS": "SELECT AVG(los_days) FROM admissions",
                "Paid revenue": "SELECT SUM(paid_amount) FROM billing",
                "Claim approval ratio": "SELECT AVG(claim_approved) FROM claims",
                "Hospital efficiency score": (
                    "SELECT hospital_efficiency_score "
                    "FROM command_center_kpis LIMIT 1"
                ),
                "Next-week emergency patients": (
                    "SELECT emergency_patients "
                    "FROM operational_forecast_summary LIMIT 1"
                ),
            }
            evidence = [
                {
                    "metric": metric,
                    "value": float(connection.execute(text(query)).scalar() or 0),
                    "query": query,
                }
                for metric, query in evidence_queries.items()
            ]

        pd.DataFrame(counts).to_csv(COUNTS_PATH, index=False)
        pd.DataFrame(evidence).to_csv(EVIDENCE_PATH, index=False)
        ready = not missing_tables and not missing_views and all(
            row["rows"] > 0 for row in counts
        )
        status = {
            "status": "verified" if ready else "incomplete",
            "verified_at_utc": generated,
            "database": database,
            "mysql_version": version,
            "tables_verified": len(counts),
            "views_verified": len(set(EXPECTED_VIEWS) & views),
            "missing_tables": missing_tables,
            "missing_views": missing_views,
            "evidence_generated": True,
            "table_counts_report": str(COUNTS_PATH.relative_to(ROOT)),
            "query_evidence_report": str(EVIDENCE_PATH.relative_to(ROOT)),
        }
        write_status(status)
        print(
            f"MySQL deployment status: {status['status']} "
            f"({len(counts)} tables, {status['views_verified']} views)."
        )
        if args.require_ready and not ready:
            raise SystemExit(2)
    except Exception as exc:
        status = {
            "status": "connection_failed",
            "verified_at_utc": generated,
            "reason": f"{type(exc).__name__}: {exc}",
            "evidence_generated": False,
        }
        write_status(status)
        if args.require_ready:
            raise
        print(status["reason"])


if __name__ == "__main__":
    main()
