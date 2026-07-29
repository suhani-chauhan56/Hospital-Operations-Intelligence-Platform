from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
    StackingRegressor,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from project_config import config_value

try:
    from xgboost import XGBClassifier, XGBRegressor
except Exception:
    XGBClassifier = None
    XGBRegressor = None

try:
    from lightgbm import LGBMClassifier, LGBMRegressor
except Exception:
    LGBMClassifier = None
    LGBMRegressor = None

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
except Exception:
    CatBoostClassifier = None
    CatBoostRegressor = None


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
RANDOM_STATE = int(config_value("random_state"))
MAX_TRAIN_ROWS = int(config_value("model_sample_rows"))
BED_CAPACITY = int(config_value("bed_capacity"))

READMISSION_FEATURES = [
    "los_days",
    "num_procedures",
    "charlson_index",
    "hba1c",
    "creatinine",
    "haemoglobin",
    "systolic_bp",
    "previous_admissions",
    "readmission_history",
    "disease_severity_score",
    "lab_abnormality_score",
    "patient_complexity_index",
    "admit_type",
    "ward_type",
    "season",
]

# The source has no observed wait timestamps. This model is retained as an
# explicitly labeled simulation and uses only variables available in its formula.
WAITING_FEATURES = [
    "charlson_index",
    "previous_admissions",
    "department_load",
    "is_weekend_admission",
    "admit_type",
    "ward_type",
    "season",
]

# Excludes billed amount, billing category, claim approval, and paid amount to
# prevent direct financial target leakage.
REVENUE_FEATURES = [
    "los_days",
    "num_procedures",
    "charlson_index",
    "hba1c",
    "creatinine",
    "haemoglobin",
    "systolic_bp",
    "previous_admissions",
    "disease_severity_score",
    "lab_abnormality_score",
    "medicine_count",
    "patient_complexity_index",
    "admit_type",
    "ward_type",
    "season",
]

FEATURES = sorted(
    set(READMISSION_FEATURES + WAITING_FEATURES + REVENUE_FEATURES)
)
CATEGORICAL_FEATURES = ["admit_type", "ward_type", "season", "hospital_id"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preprocessor(df: pd.DataFrame) -> ColumnTransformer:
    categorical = [
        column for column in CATEGORICAL_FEATURES if column in df.columns
    ]
    numeric = [column for column in df.columns if column not in categorical]
    return ColumnTransformer(
        [
            ("numeric", StandardScaler(), numeric),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical,
            ),
        ]
    )


def group_split(
    X: pd.DataFrame, y: pd.Series, groups: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, dict]:
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=0.20, random_state=RANDOM_STATE
    )
    train_index, test_index = next(splitter.split(X, y, groups))
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    train_groups = set(groups.iloc[train_index])
    test_groups = set(groups.iloc[test_index])
    audit = {
        "split_strategy": "GroupShuffleSplit(patient_id)",
        "train_rows": len(train_index),
        "test_rows": len(test_index),
        "train_patients": len(train_groups),
        "test_patients": len(test_groups),
        "patient_overlap": len(train_groups & test_groups),
    }
    return X_train, X_test, y_train, y_test, audit


def regression_metrics(y_true, prediction) -> dict[str, float]:
    truth = np.asarray(y_true, dtype=float)
    estimate = np.asarray(prediction, dtype=float)
    denominator = np.maximum(np.abs(truth), 1.0)
    return {
        "RMSE": float(np.sqrt(mean_squared_error(truth, estimate))),
        "MAE": float(mean_absolute_error(truth, estimate)),
        "MAPE": float(np.mean(np.abs(truth - estimate) / denominator)),
        "R2": float(r2_score(truth, estimate)),
    }


def readmission_estimators() -> list[tuple[str, object]]:
    estimators: list[tuple[str, object]] = [
        (
            "logistic",
            LogisticRegression(max_iter=1000, class_weight="balanced"),
        ),
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=90,
                max_depth=10,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
    ]
    if XGBClassifier:
        estimators.append(
            (
                "xgboost",
                XGBClassifier(
                    n_estimators=100,
                    max_depth=3,
                    learning_rate=0.08,
                    subsample=0.9,
                    eval_metric="logloss",
                    random_state=RANDOM_STATE,
                ),
            )
        )
    if LGBMClassifier:
        estimators.append(
            (
                "lightgbm",
                LGBMClassifier(
                    n_estimators=100,
                    learning_rate=0.08,
                    random_state=RANDOM_STATE,
                    verbose=-1,
                ),
            )
        )
    if CatBoostClassifier:
        estimators.append(
            (
                "catboost",
                CatBoostClassifier(
                    iterations=100,
                    depth=5,
                    learning_rate=0.08,
                    verbose=False,
                    random_seed=RANDOM_STATE,
                ),
            )
        )
    return estimators


def train_readmission(df: pd.DataFrame) -> dict:
    X = df[READMISSION_FEATURES]
    y = df["readmitted_30d"].astype(int)
    X_train, X_test, y_train, y_test, audit = group_split(
        X, y, df["patient_id"]
    )
    rows = []
    fitted: list[tuple[str, Pipeline]] = []
    for name, estimator in readmission_estimators():
        pipeline = Pipeline(
            [("prep", preprocessor(X_train)), ("model", estimator)]
        )
        pipeline.fit(X_train, y_train)
        prediction = pipeline.predict(X_test)
        probability = pipeline.predict_proba(X_test)[:, 1]
        rows.append(
            {
                "model": name,
                "accuracy": accuracy_score(y_test, prediction),
                "precision": precision_score(
                    y_test, prediction, zero_division=0
                ),
                "recall": recall_score(y_test, prediction, zero_division=0),
                "f1": f1_score(y_test, prediction, zero_division=0),
                "roc_auc": roc_auc_score(y_test, probability),
                "confusion_matrix": confusion_matrix(
                    y_test, prediction
                ).tolist(),
                **audit,
                "target_origin": "observed",
            }
        )
        fitted.append((name, pipeline))

    if len(fitted) >= 3:
        voting = Pipeline(
            [
                ("prep", preprocessor(X_train)),
                (
                    "model",
                    VotingClassifier(
                        estimators=[
                            (name, pipeline.named_steps["model"])
                            for name, pipeline in fitted[:3]
                        ],
                        voting="soft",
                    ),
                ),
            ]
        )
        voting.fit(X_train, y_train)
        prediction = voting.predict(X_test)
        probability = voting.predict_proba(X_test)[:, 1]
        rows.append(
            {
                "model": "voting_classifier",
                "accuracy": accuracy_score(y_test, prediction),
                "precision": precision_score(
                    y_test, prediction, zero_division=0
                ),
                "recall": recall_score(y_test, prediction, zero_division=0),
                "f1": f1_score(y_test, prediction, zero_division=0),
                "roc_auc": roc_auc_score(y_test, probability),
                "confusion_matrix": confusion_matrix(
                    y_test, prediction
                ).tolist(),
                **audit,
                "target_origin": "observed",
            }
        )
        fitted.append(("voting_classifier", voting))

    metrics = pd.DataFrame(rows).sort_values("roc_auc", ascending=False)
    best_name = str(metrics.iloc[0]["model"])
    best_pipeline = next(
        pipeline for name, pipeline in fitted if name == best_name
    )
    deployment_model = clone(best_pipeline).fit(X, y)
    model_path = MODELS / "readmission.pkl"
    joblib.dump(deployment_model, model_path)
    metrics.to_csv(REPORTS / "readmission_model_metrics.csv", index=False)
    return {
        "artifact": model_path.name,
        "sha256": sha256_file(model_path),
        "selected_model": best_name,
        "primary_metric": "roc_auc",
        "primary_metric_value": float(metrics.iloc[0]["roc_auc"]),
        "features": READMISSION_FEATURES,
        **audit,
        "target_origin": "observed",
        "portfolio_tier": "core_analytical",
        "decision_use": "screening_research_only",
    }


def regression_estimators(include_stacking: bool) -> list[tuple[str, object]]:
    estimators: list[tuple[str, object]] = [
        (
            "random_forest",
            RandomForestRegressor(
                n_estimators=80,
                max_depth=12,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
        ("gradient_boosting", GradientBoostingRegressor(random_state=RANDOM_STATE)),
    ]
    if XGBRegressor:
        estimators.append(
            (
                "xgboost",
                XGBRegressor(
                    n_estimators=100,
                    max_depth=3,
                    learning_rate=0.08,
                    random_state=RANDOM_STATE,
                ),
            )
        )
    if LGBMRegressor:
        estimators.append(
            (
                "lightgbm",
                LGBMRegressor(
                    n_estimators=100,
                    learning_rate=0.08,
                    random_state=RANDOM_STATE,
                    verbose=-1,
                ),
            )
        )
    if CatBoostRegressor:
        estimators.append(
            (
                "catboost",
                CatBoostRegressor(
                    iterations=100,
                    depth=5,
                    learning_rate=0.08,
                    verbose=False,
                    random_seed=RANDOM_STATE,
                ),
            )
        )
    if include_stacking:
        estimators.append(
            (
                "stacking_regressor",
                StackingRegressor(
                    estimators=[
                        (
                            "rf",
                            RandomForestRegressor(
                                n_estimators=50,
                                max_depth=10,
                                random_state=RANDOM_STATE,
                                n_jobs=-1,
                            ),
                        ),
                        (
                            "gbr",
                            GradientBoostingRegressor(
                                random_state=RANDOM_STATE
                            ),
                        ),
                    ],
                    final_estimator=GradientBoostingRegressor(
                        n_estimators=50, random_state=RANDOM_STATE
                    ),
                    n_jobs=-1,
                ),
            )
        )
    return estimators


def train_regression(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    filename: str,
    metrics_file: str,
    target_origin: str,
    portfolio_tier: str,
    decision_use: str,
    include_stacking: bool = False,
) -> dict:
    X = df[features]
    y = df[target].astype(float)
    X_train, X_test, y_train, y_test, audit = group_split(
        X, y, df["patient_id"]
    )
    rows = []
    fitted: list[tuple[str, Pipeline]] = []
    predictions: dict[str, np.ndarray] = {}
    for name, estimator in regression_estimators(include_stacking):
        pipeline = Pipeline(
            [("prep", preprocessor(X_train)), ("model", estimator)]
        )
        pipeline.fit(X_train, y_train)
        prediction = pipeline.predict(X_test)
        rows.append(
            {
                "model": name,
                **regression_metrics(y_test, prediction),
                **audit,
                "target_origin": target_origin,
            }
        )
        fitted.append((name, pipeline))
        predictions[name] = prediction

    metrics = pd.DataFrame(rows).sort_values("RMSE")
    best_name = str(metrics.iloc[0]["model"])
    best_pipeline = next(
        pipeline for name, pipeline in fitted if name == best_name
    )
    deployment_model = clone(best_pipeline).fit(X, y)
    model_path = MODELS / filename
    joblib.dump(deployment_model, model_path)
    metrics.to_csv(REPORTS / metrics_file, index=False)

    evaluation = X_test[["ward_type"]].copy()
    evaluation["actual"] = y_test
    evaluation["predicted"] = predictions[best_name]
    evaluation.groupby("ward_type", as_index=False)[
        ["actual", "predicted"]
    ].sum().to_csv(
        REPORTS / f"{target}_ward_predictions.csv", index=False
    )
    return {
        "artifact": model_path.name,
        "sha256": sha256_file(model_path),
        "selected_model": best_name,
        "primary_metric": "RMSE",
        "primary_metric_value": float(metrics.iloc[0]["RMSE"]),
        "features": features,
        **audit,
        "target_origin": target_origin,
        "portfolio_tier": portfolio_tier,
        "decision_use": decision_use,
    }


def train_occupancy_forecast(df: pd.DataFrame) -> dict:
    dates = df[["admit_date", "discharge_date"]].copy()
    dates["admit_date"] = pd.to_datetime(dates["admit_date"])
    dates["discharge_date"] = pd.to_datetime(dates["discharge_date"])
    calendar = pd.date_range(
        dates["admit_date"].min(), dates["admit_date"].max(), freq="D"
    )
    admissions = dates.groupby("admit_date").size().reindex(calendar, fill_value=0)
    discharges = (
        dates.groupby(dates["discharge_date"] + pd.Timedelta(days=1))
        .size()
        .reindex(calendar, fill_value=0)
    )
    occupied = (admissions - discharges).cumsum().clip(lower=0)
    daily = pd.DataFrame({"date": calendar, "occupied_beds": occupied.values})
    daily["dayofweek"] = daily["date"].dt.dayofweek
    daily["month"] = daily["date"].dt.month
    daily["is_weekend"] = (daily["dayofweek"] >= 5).astype(int)
    daily["lag_1_beds"] = daily["occupied_beds"].shift(1)
    daily["lag_7_beds"] = daily["occupied_beds"].shift(7)
    daily["rolling_7_beds"] = (
        daily["occupied_beds"].shift(1).rolling(7).mean()
    )
    feature_columns = [
        "dayofweek",
        "month",
        "is_weekend",
        "lag_1_beds",
        "lag_7_beds",
        "rolling_7_beds",
    ]
    model_data = daily.dropna().copy()
    split = int(len(model_data) * 0.80)
    X_train = model_data.iloc[:split][feature_columns]
    X_test = model_data.iloc[split:][feature_columns]
    y_train = model_data.iloc[:split]["occupied_beds"]
    y_test = model_data.iloc[split:]["occupied_beds"]
    model = (
        XGBRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.08,
            random_state=RANDOM_STATE,
        )
        if XGBRegressor
        else RandomForestRegressor(
            n_estimators=100, random_state=RANDOM_STATE
        )
    )
    model.fit(X_train, y_train)
    prediction = model.predict(X_test)
    metrics = {
        "model": type(model).__name__,
        **regression_metrics(y_test, prediction),
        "split_strategy": "chronological_80_20",
        "target_origin": "observed_active_census",
        "capacity_assumption": BED_CAPACITY,
    }
    pd.DataFrame([metrics]).to_csv(
        REPORTS / "occupancy_model_metrics.csv", index=False
    )

    model.fit(model_data[feature_columns], model_data["occupied_beds"])
    model_path = MODELS / "occupancy.pkl"
    joblib.dump(
        {
            "model": model,
            "features": feature_columns,
            "target": "occupied_beds",
            "last_date": daily["date"].max(),
        },
        model_path,
    )

    history = daily.set_index("date")["occupied_beds"].to_dict()
    forecast_rows = []
    last_date = daily["date"].max()
    for step in range(1, 91):
        forecast_date = last_date + pd.Timedelta(days=step)
        prior = [
            history[forecast_date - pd.Timedelta(days=offset)]
            for offset in range(1, 8)
        ]
        row = pd.DataFrame(
            [
                {
                    "dayofweek": forecast_date.dayofweek,
                    "month": forecast_date.month,
                    "is_weekend": int(forecast_date.dayofweek >= 5),
                    "lag_1_beds": prior[0],
                    "lag_7_beds": prior[6],
                    "rolling_7_beds": float(np.mean(prior)),
                }
            ]
        )
        beds = float(max(model.predict(row[feature_columns])[0], 0))
        history[forecast_date] = beds
        forecast_rows.append(
            {
                "forecast_date": forecast_date.date(),
                "forecast_occupied_beds": beds,
                "forecast_occupancy_pct": min(
                    beds / BED_CAPACITY * 100, 100
                ),
            }
        )
    forecast = pd.DataFrame(forecast_rows)
    forecast.to_csv(REPORTS / "occupancy_forecast_daily.csv", index=False)
    pd.DataFrame(
        [
            {
                "horizon_days": horizon,
                "forecast_occupied_beds": forecast.head(horizon)[
                    "forecast_occupied_beds"
                ].mean(),
                "forecast_occupancy_pct": forecast.head(horizon)[
                    "forecast_occupancy_pct"
                ].mean(),
            }
            for horizon in [7, 30, 90]
        ]
    ).to_csv(REPORTS / "occupancy_forecast.csv", index=False)
    return {
        "artifact": model_path.name,
        "sha256": sha256_file(model_path),
        "selected_model": type(model).__name__,
        "primary_metric": "MAE_beds",
        "primary_metric_value": float(metrics["MAE"]),
        "features": feature_columns,
        "split_strategy": "chronological_80_20",
        "target_origin": "observed_active_census",
        "portfolio_tier": "core_analytical",
        "decision_use": "capacity_scenario",
    }


def main() -> None:
    MODELS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    source_path = PROCESSED / "model_features.csv"
    full_df = pd.read_csv(source_path)
    patient_df = full_df
    if len(patient_df) > MAX_TRAIN_ROWS:
        patient_df = patient_df.sample(
            MAX_TRAIN_ROWS, random_state=RANDOM_STATE
        )

    artifacts = {
        "readmission": train_readmission(patient_df),
        "waiting_simulation": train_regression(
            patient_df,
            "waiting_time_minutes",
            WAITING_FEATURES,
            "waiting.pkl",
            "waiting_model_metrics.csv",
            "simulated_formula",
            "sandbox",
            "pipeline_demonstration",
        ),
        "revenue_scenario": train_regression(
            patient_df,
            "revenue_per_patient",
            REVENUE_FEATURES,
            "revenue.pkl",
            "revenue_model_metrics.csv",
            "mixed_surrogate_and_simulated",
            "sandbox",
            "scenario_demonstration",
            include_stacking=True,
        ),
        "occupancy": train_occupancy_forecast(full_df),
    }
    manifest = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "path": str(source_path.relative_to(ROOT)),
            "sha256": sha256_file(source_path),
            "rows": len(full_df),
        },
        "random_state": RANDOM_STATE,
        "artifacts": artifacts,
    }
    (MODELS / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print("Training complete. Canonical models, metrics, forecasts, and manifest saved.")


if __name__ == "__main__":
    main()
