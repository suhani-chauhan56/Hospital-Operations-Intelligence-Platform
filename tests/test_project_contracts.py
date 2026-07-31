from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
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


def test_operational_intelligence_marts_are_consistent():
    command = pd.read_csv(ROOT / "reports" / "command_center_kpis.csv")
    scores = pd.read_csv(
        ROOT / "reports" / "hospital_efficiency_scores.csv"
    )
    emergency = pd.read_csv(
        ROOT / "reports" / "emergency_forecast.csv",
        parse_dates=["forecast_date"],
    )
    outlook = pd.read_csv(
        ROOT / "reports" / "operational_forecast_summary.csv"
    )
    recommendations = pd.read_csv(
        ROOT / "reports" / "operational_recommendations.csv"
    )

    assert len(command) == 1
    assert len(emergency) == 7
    assert command["hospital_efficiency_score"].between(0, 100).all()
    assert scores["efficiency_score"].between(0, 100).all()
    hospital_score = scores.loc[
        scores["scope_type"] == "hospital",
        "efficiency_score",
    ].iloc[0]
    assert abs(
        hospital_score - command.loc[0, "hospital_efficiency_score"]
    ) < 1e-6
    assert emergency["forecast_date"].is_monotonic_increasing
    assert (
        outlook.loc[0, "peak_hour_status"]
        == "unavailable_no_arrival_timestamps"
    )
    assert recommendations[
        ["owner", "timeframe", "success_measure", "reliability"]
    ].notna().all().all()

    procedures_sql = (ROOT / "sql" / "procedures.sql").read_text(
        encoding="utf-8"
    )
    assert "USE hospital_ops;" in procedures_sql
    assert "DELIMITER $$" in procedures_sql
    assert (
        "DROP PROCEDURE IF EXISTS sp_command_center_report;"
        in procedures_sql
    )
    assert (
        "DROP TRIGGER IF EXISTS trg_billing_gap_before_insert;"
        in procedures_sql
    )


def test_readmission_probability_decomposition_is_exact():
    model = joblib.load(ROOT / "models" / "readmission.pkl")
    columns = list(model.named_steps["prep"].feature_names_in_)
    features = pd.read_csv(
        ROOT / "datasets" / "processed" / "model_features.csv",
        nrows=64,
    )
    transformed = model.named_steps["prep"].transform(features[columns])
    estimator = model.named_steps["model"]
    logits = (
        np.asarray(transformed @ estimator.coef_[0]).ravel()
        + float(estimator.intercept_[0])
    )
    reconstructed = 1 / (1 + np.exp(-logits))
    predicted = model.predict_proba(features[columns])[:, 1]
    assert np.allclose(reconstructed, predicted, atol=1e-12)
