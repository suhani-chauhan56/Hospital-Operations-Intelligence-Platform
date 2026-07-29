from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    checks: list[dict] = []
    tables: dict[str, pd.DataFrame] = {}

    required_tables = {
        "patients": ["patient_id"],
        "doctors": ["doctor_id"],
        "departments": ["department_id"],
        "admissions": ["admission_id"],
        "insurance": ["insurance_id"],
        "billing": ["billing_id"],
        "claims": ["claim_line_id"],
        "appointments": ["appointment_id"],
        "model_features": ["admission_id"],
    }
    for table, key in required_tables.items():
        path = PROCESSED / f"{table}.csv"
        require(path.exists(), f"Missing processed table: {path}")
        frame = pd.read_csv(path, dtype=str)
        tables[table] = frame
        require(not frame.duplicated(key).any(), f"Duplicate key in {table}")
        require(
            not frame[key].isna().any().any(), f"Missing key value in {table}"
        )
        checks.append(
            {"check": f"table:{table}", "status": "passed", "rows": len(frame)}
        )

    foreign_keys = [
        ("admissions", "patient_id", "patients", "patient_id"),
        ("admissions", "doctor_id", "doctors", "doctor_id"),
        ("admissions", "department_id", "departments", "department_id"),
        ("billing", "admission_id", "admissions", "admission_id"),
        ("billing", "patient_id", "patients", "patient_id"),
        ("billing", "insurance_id", "insurance", "insurance_id"),
        ("claims", "billing_id", "billing", "billing_id"),
        ("claims", "insurance_id", "insurance", "insurance_id"),
        ("appointments", "admission_id", "admissions", "admission_id"),
        ("appointments", "patient_id", "patients", "patient_id"),
        ("appointments", "doctor_id", "doctors", "doctor_id"),
        ("appointments", "department_id", "departments", "department_id"),
        ("model_features", "admission_id", "admissions", "admission_id"),
    ]
    for child, child_key, parent, parent_key in foreign_keys:
        orphaned = ~tables[child][child_key].isin(tables[parent][parent_key])
        require(
            not orphaned.any(),
            f"Orphaned foreign keys: {child}.{child_key} -> {parent}.{parent_key}",
        )
        checks.append(
            {
                "check": f"foreign_key:{child}.{child_key}",
                "status": "passed",
                "rows": int(len(tables[child])),
            }
        )

    admission_dates = pd.read_csv(
        PROCESSED / "admissions.csv",
        usecols=["admit_date", "discharge_date"],
        parse_dates=["admit_date", "discharge_date"],
    )
    require(
        not admission_dates.isna().any().any(),
        "Admissions contain invalid or missing dates",
    )
    require(
        (admission_dates["discharge_date"] >= admission_dates["admit_date"]).all(),
        "Admissions contain discharge dates before admission dates",
    )
    checks.append(
        {
            "check": "business_rule:admission_date_order",
            "status": "passed",
            "rows": len(admission_dates),
        }
    )

    manifest_path = MODELS / "manifest.json"
    require(manifest_path.exists(), "Missing model manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_path = ROOT / manifest["dataset"]["path"]
    require(
        sha256_file(dataset_path) == manifest["dataset"]["sha256"],
        "Training dataset hash does not match manifest",
    )
    for name, artifact in manifest["artifacts"].items():
        path = MODELS / artifact["artifact"]
        require(path.exists(), f"Missing model artifact: {path}")
        require(
            sha256_file(path) == artifact["sha256"],
            f"Model hash mismatch: {name}",
        )
        if "patient_overlap" in artifact:
            require(
                artifact["patient_overlap"] == 0,
                f"Patient leakage detected: {name}",
            )
        require(
            artifact["target_origin"]
            in {
                "observed",
                "simulated_formula",
                "mixed_surrogate_and_simulated",
                "observed_active_census",
            },
            f"Unrecognized target provenance: {name}",
        )
        require(
            artifact.get("portfolio_tier")
            in {"core_analytical", "sandbox"},
            f"Missing or invalid portfolio tier: {name}",
        )
        require(
            bool(artifact.get("decision_use")),
            f"Missing decision-use restriction: {name}",
        )
        checks.append(
            {"check": f"model:{name}", "status": "passed", "rows": None}
        )

    explanations = manifest.get("explanations", {})
    require(
        {"readmission", "revenue_scenario"}.issubset(explanations),
        "SHAP lineage is missing from manifest",
    )
    for name, explanation in explanations.items():
        report_path = REPORTS / explanation["report"]
        require(report_path.exists(), f"Missing SHAP report: {name}")
        require(
            sha256_file(report_path) == explanation["report_sha256"],
            f"SHAP report hash mismatch: {name}",
        )
        expected_model = manifest["artifacts"][name]["sha256"]
        require(
            explanation["model_sha256"] == expected_model,
            f"SHAP model lineage mismatch: {name}",
        )

    provenance = pd.read_csv(REPORTS / "feature_provenance.csv")
    require(
        {"Observed", "Derived", "Simulated", "Mixed", "Assumption"}.issubset(
            set(provenance["provenance"])
        ),
        "Feature provenance categories are incomplete",
    )
    insights = pd.read_csv(REPORTS / "business_insights.csv")
    require(
        {"reliability", "decision_use", "insight"}.issubset(insights.columns),
        "Business insights lack governance labels",
    )
    action_plan = pd.read_csv(REPORTS / "executive_action_plan.csv")
    require(
        {
            "priority",
            "action",
            "owner",
            "timeframe",
            "success_measure",
            "evidence",
        }.issubset(action_plan.columns),
        "Executive action plan lacks accountable delivery fields",
    )
    require(
        action_plan["owner"].notna().all()
        and action_plan["timeframe"].notna().all(),
        "Executive actions require owners and timeframes",
    )
    checks.append(
        {
            "check": "report:accountable_action_plan",
            "status": "passed",
            "rows": len(action_plan),
        }
    )

    summary = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "checks": checks,
        "model_manifest_sha256": sha256_file(manifest_path),
    }
    (REPORTS / "validation_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        f"Project validation passed: {len(checks)} table and model contracts."
    )


if __name__ == "__main__":
    main()
