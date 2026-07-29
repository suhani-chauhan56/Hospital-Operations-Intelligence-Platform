from __future__ import annotations

import gzip
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"

DEPLOYMENT_TABLES = (
    "model_features",
    "billing",
    "claims",
    "labs",
    "medicines",
)

REQUIRED_ARTIFACTS = (
    MODELS / "readmission.pkl",
    MODELS / "waiting.pkl",
    MODELS / "revenue.pkl",
    MODELS / "manifest.json",
    REPORTS / "occupancy_forecast_daily.csv",
    REPORTS / "business_insights.csv",
    REPORTS / "readmission_shap_importance.csv",
    REPORTS / "revenue_shap_importance.csv",
    REPORTS / "patient_readmission_explanations.csv",
    REPORTS / "executive_report.pdf",
)


def compress_csv(source: Path, target: Path) -> None:
    temporary = target.with_suffix(target.suffix + ".tmp")
    with source.open("rb") as source_handle, temporary.open("wb") as raw_target:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_target,
            compresslevel=9,
            mtime=0,
        ) as compressed_target:
            shutil.copyfileobj(
                source_handle,
                compressed_target,
                length=1024 * 1024,
            )
    os.replace(temporary, target)


def main() -> None:
    missing = [
        PROCESSED / f"{name}.csv"
        for name in DEPLOYMENT_TABLES
        if not (PROCESSED / f"{name}.csv").exists()
    ]
    missing.extend(path for path in REQUIRED_ARTIFACTS if not path.exists())
    if missing:
        rendered = "\n".join(f"- {path.relative_to(ROOT)}" for path in missing)
        raise FileNotFoundError(
            f"Cannot build Streamlit deployment bundle. Missing:\n{rendered}"
        )

    total_bytes = 0
    for name in DEPLOYMENT_TABLES:
        source = PROCESSED / f"{name}.csv"
        target = PROCESSED / f"{name}.csv.gz"
        compress_csv(source, target)
        total_bytes += target.stat().st_size
        print(
            f"Packaged {target.relative_to(ROOT)} "
            f"({target.stat().st_size / 1024 / 1024:.2f} MB)"
        )

    print(
        "Streamlit deployment bundle ready "
        f"({total_bytes / 1024 / 1024:.2f} MB compressed data)."
    )


if __name__ == "__main__":
    main()
