from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_model_manifest_matches_artifacts():
    manifest = json.loads(
        (ROOT / "models" / "manifest.json").read_text(encoding="utf-8")
    )
    dataset = ROOT / manifest["dataset"]["path"]
    assert sha256_file(dataset) == manifest["dataset"]["sha256"]
    for artifact in manifest["artifacts"].values():
        model = ROOT / "models" / artifact["artifact"]
        assert model.exists()
        assert sha256_file(model) == artifact["sha256"]
        assert artifact.get("patient_overlap", 0) == 0


def test_shap_reports_match_registered_models():
    manifest = json.loads(
        (ROOT / "models" / "manifest.json").read_text(encoding="utf-8")
    )
    for name, explanation in manifest["explanations"].items():
        report = ROOT / "reports" / explanation["report"]
        assert sha256_file(report) == explanation["report_sha256"]
        assert (
            explanation["model_sha256"]
            == manifest["artifacts"][name]["sha256"]
        )


def test_insights_have_reliability_labels():
    insights = pd.read_csv(ROOT / "reports" / "business_insights.csv")
    assert {"reliability", "decision_use", "insight"}.issubset(insights.columns)
    assert {"Observed", "Simulated"}.issubset(set(insights["reliability"]))


def test_warehouse_primary_keys_are_unique():
    contracts = {
        "patients": "patient_id",
        "doctors": "doctor_id",
        "departments": "department_id",
        "admissions": "admission_id",
        "billing": "billing_id",
        "claims": "claim_line_id",
        "appointments": "appointment_id",
    }
    for table, key in contracts.items():
        frame = pd.read_csv(
            ROOT / "datasets" / "processed" / f"{table}.csv",
            usecols=[key],
            dtype=str,
        )
        assert frame[key].notna().all()
        assert frame[key].is_unique


def test_executive_actions_are_accountable():
    actions = pd.read_csv(ROOT / "reports" / "executive_action_plan.csv")
    assert {
        "priority",
        "action",
        "owner",
        "timeframe",
        "success_measure",
        "evidence",
    }.issubset(actions.columns)
    assert actions["owner"].notna().all()
    assert actions["timeframe"].notna().all()
