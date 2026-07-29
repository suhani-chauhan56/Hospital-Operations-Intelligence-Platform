from __future__ import annotations

from pathlib import Path
import json
import hashlib

import joblib
import numpy as np
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


def transformed_values(values) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim == 3:
        return array[:, :, -1]
    return array


def explain_pipeline(
    df: pd.DataFrame,
    model_name: str,
    output_name: str,
    classification: bool = False,
) -> None:
    import shap

    pipeline = joblib.load(MODELS / model_name)
    prep = pipeline.named_steps["prep"]
    estimator = pipeline.named_steps["model"]
    columns = prep.feature_names_in_
    sample = df[list(columns)].sample(n=min(250, len(df)), random_state=42)
    transformed = prep.transform(sample)
    names = prep.get_feature_names_out()

    if classification and hasattr(estimator, "estimators_"):
        estimator = estimator.estimators_[0]

    try:
        explainer = shap.Explainer(estimator, transformed[:50])
        explanation = explainer(transformed)
        values = transformed_values(explanation.values)
    except Exception:
        predict = estimator.predict_proba if classification else estimator.predict
        explainer = shap.Explainer(predict, transformed[:50])
        explanation = explainer(transformed[:100])
        values = transformed_values(explanation.values)

    importance = pd.DataFrame(
        {"feature": names, "mean_abs_shap": np.abs(values).mean(axis=0)}
    ).sort_values("mean_abs_shap", ascending=False)
    importance.head(50).to_csv(REPORTS / output_name, index=False)

    if classification:
        positive = np.where(values > 0, values, -np.inf)
        top_index = positive.argmax(axis=1)
        patient_rows = df.loc[sample.index[: len(values)], ["patient_id"]].copy()
        patient_rows["top_risk_factor"] = names[top_index]
        patient_rows["factor_contribution"] = values[
            np.arange(len(values)), top_index
        ]
        patient_rows.to_csv(
            REPORTS / "patient_readmission_explanations.csv", index=False
        )


def main() -> None:
    df = pd.read_csv(PROCESSED / "model_features.csv")
    manifest_path = MODELS / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ["readmission", "revenue_scenario"]:
        artifact = manifest["artifacts"][key]
        model_path = MODELS / artifact["artifact"]
        if sha256_file(model_path) != artifact["sha256"]:
            raise RuntimeError(f"Model hash mismatch before SHAP generation: {key}")
    explain_pipeline(
        df,
        "readmission.pkl",
        "readmission_shap_importance.csv",
        classification=True,
    )
    explain_pipeline(df, "revenue.pkl", "revenue_shap_importance.csv")
    manifest["explanations"] = {
        "readmission": {
            "model_sha256": manifest["artifacts"]["readmission"]["sha256"],
            "report": "readmission_shap_importance.csv",
            "report_sha256": sha256_file(
                REPORTS / "readmission_shap_importance.csv"
            ),
        },
        "revenue_scenario": {
            "model_sha256": manifest["artifacts"]["revenue_scenario"]["sha256"],
            "report": "revenue_shap_importance.csv",
            "report_sha256": sha256_file(
                REPORTS / "revenue_shap_importance.csv"
            ),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Readmission, patient-risk, and revenue SHAP reports saved.")


if __name__ == "__main__":
    main()
