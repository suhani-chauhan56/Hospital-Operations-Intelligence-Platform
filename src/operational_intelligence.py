from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from project_config import config_value


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
REPORTS = ROOT / "reports"


def read_processed_table(name: str, **kwargs) -> pd.DataFrame:
    candidates = [
        PROCESSED / f"{name}.csv.gz",
        PROCESSED / f"{name}.csv",
    ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path, **kwargs)
    expected = " or ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Required operational source is missing: {expected}")


def historical_occupancy(
    features: pd.DataFrame,
    capacity: int,
) -> pd.DataFrame:
    start = features["admit_date"].dropna().min()
    end = features["admit_date"].dropna().max()
    dates = pd.date_range(start, end, freq="D")
    admissions = features.groupby("admit_date").size()
    discharges = features.groupby("discharge_date").size()
    delta = pd.Series(0, index=dates, dtype=float)
    delta = delta.add(admissions, fill_value=0)
    discharge_delta = discharges.copy()
    discharge_delta.index = discharge_delta.index + pd.Timedelta(days=1)
    delta = delta.sub(discharge_delta, fill_value=0).reindex(dates, fill_value=0)
    census = delta.cumsum().clip(lower=0)
    return pd.DataFrame(
        {
            "date": dates,
            "occupied_beds": census.values,
            "occupancy_pct": np.clip(census.values / capacity * 100, 0, 100),
        }
    )


def latest_snapshot(
    features: pd.DataFrame,
    capacity: int,
) -> dict[str, float | int | pd.Timestamp]:
    latest_date = features["admit_date"].max()
    latest = features[features["admit_date"] == latest_date]
    current = historical_occupancy(features, capacity).iloc[-1]
    emergency = latest[latest["admit_type"] == "Emergency"]
    if emergency.empty:
        emergency = features[
            (features["admit_type"] == "Emergency")
            & (features["admit_date"] >= latest_date - pd.Timedelta(days=29))
        ]

    complexity_threshold = features["patient_complexity_index"].quantile(0.75)
    critical = latest[
        (latest["ward_type"] == "ICU")
        | (latest["patient_complexity_index"] >= complexity_threshold)
    ]
    daily_doctor_load = (
        features.groupby(["admit_date", "doctor_id"])
        .size()
        .rename("admissions")
    )
    reference_load = max(float(daily_doctor_load.quantile(0.9)), 1.0)
    latest_doctor_load = latest.groupby("doctor_id").size()
    doctor_utilization = (
        min(float(latest_doctor_load.mean()) / reference_load, 1.0)
        if not latest_doctor_load.empty
        else 0.0
    )
    return {
        "as_of_date": latest_date,
        "patients_today": int(latest["patient_id"].nunique()),
        "occupancy_pct": float(current["occupancy_pct"]),
        "occupied_beds": int(current["occupied_beds"]),
        "emergency_wait_minutes": float(
            emergency["waiting_time_minutes"].mean()
        ),
        "critical_patients": int(critical["patient_id"].nunique()),
        "doctor_utilization_pct": doctor_utilization * 100,
    }


def department_summary(features: pd.DataFrame) -> pd.DataFrame:
    summary = features.groupby("department", as_index=False).agg(
        patients=("patient_id", "nunique"),
        admissions=("admission_id", "count"),
        average_wait=("waiting_time_minutes", "mean"),
        readmission_rate=("readmitted_30d", "mean"),
        bed_utilization=("bed_utilization_score", "mean"),
    )
    return summary


def efficiency_outputs(
    features: pd.DataFrame,
    billing: pd.DataFrame,
    snapshot: dict[str, float | int | pd.Timestamp],
) -> tuple[float, pd.DataFrame, dict[str, float]]:
    readmission = float(features["readmitted_30d"].mean())
    collection = float(
        billing["paid_amount"].sum() / max(billing["billed_amount"].sum(), 1)
    )
    average_wait = float(features["waiting_time_minutes"].mean())
    outcome_score = float(
        np.clip((0.25 - readmission) / (0.25 - 0.10) * 100, 0, 100)
    )
    collection_score = float(np.clip(collection / 0.70 * 100, 0, 100))
    capacity_score = float(
        np.clip(
            100 - abs(float(snapshot["occupancy_pct"]) - 80) * 2,
            0,
            100,
        )
    )
    flow_score = float(np.clip(100 - average_wait / 90 * 100, 0, 100))
    components = {
        "patient_outcome_score": outcome_score,
        "collection_score": collection_score,
        "capacity_balance_score": capacity_score,
        "patient_flow_score": flow_score,
    }
    overall = (
        outcome_score * 0.40
        + collection_score * 0.30
        + capacity_score * 0.20
        + flow_score * 0.10
    )

    department = department_summary(features)
    max_pressure = max(float(department["bed_utilization"].max()), 0.01)
    department["patient_outcome_score"] = (
        1 - department["readmission_rate"]
    ) * 100
    department["patient_flow_score"] = np.clip(
        100 - department["average_wait"] / 90 * 100,
        0,
        100,
    )
    department["capacity_balance_score"] = np.clip(
        department["bed_utilization"] / max_pressure * 100,
        0,
        100,
    )
    department["collection_score"] = np.nan
    department["efficiency_score"] = (
        department["patient_outcome_score"] * 0.50
        + department["patient_flow_score"] * 0.25
        + department["capacity_balance_score"] * 0.25
    )
    department_scores = department[
        [
            "department",
            "efficiency_score",
            "patient_outcome_score",
            "collection_score",
            "capacity_balance_score",
            "patient_flow_score",
        ]
    ].rename(columns={"department": "scope_name"})
    department_scores.insert(0, "scope_type", "department")
    department_scores["provenance"] = "derived_portfolio_dimension"

    hospital_row = pd.DataFrame(
        [
            {
                "scope_type": "hospital",
                "scope_name": "Hospital portfolio",
                "efficiency_score": overall,
                **components,
                "provenance": "mixed_observed_derived_simulated_assumed",
            }
        ]
    )
    scores = pd.concat([hospital_row, department_scores], ignore_index=True)
    return overall, scores, components


def emergency_forecast(
    features: pd.DataFrame,
) -> pd.DataFrame:
    end_date = features["admit_date"].max()
    daily = (
        features[features["admit_type"] == "Emergency"]
        .groupby("admit_date")
        .size()
        .reindex(
            pd.date_range(features["admit_date"].min(), end_date, freq="D"),
            fill_value=0,
        )
    )
    recent = daily.tail(56)
    weekday_average = recent.groupby(recent.index.dayofweek).mean()
    future_dates = pd.date_range(end_date + pd.Timedelta(days=1), periods=7)
    forecast_values = [
        float(weekday_average.get(date.dayofweek, recent.mean()))
        for date in future_dates
    ]
    return pd.DataFrame(
        {
            "forecast_date": future_dates,
            "forecast_emergency_patients": forecast_values,
            "method": "eight_week_weekday_seasonal_baseline",
            "provenance": "forecast_from_observed_daily_emergency_admissions",
        }
    )


def forecast_summary(
    features: pd.DataFrame,
    occupancy_forecast: pd.DataFrame,
    emergency: pd.DataFrame,
    capacity: int,
) -> pd.DataFrame:
    daily = (
        features[features["admit_type"] == "Emergency"]
        .groupby("admit_date")
        .size()
    )
    prior_week = float(daily.tail(7).sum())
    next_week = float(emergency["forecast_emergency_patients"].sum())
    current_occupied = int(
        historical_occupancy(features, capacity).iloc[-1]["occupied_beds"]
    )
    next_week_peak = (
        int(np.ceil(occupancy_forecast.head(7)["forecast_occupied_beds"].max()))
        if not occupancy_forecast.empty
        else current_occupied
    )
    peak = emergency.loc[emergency["forecast_emergency_patients"].idxmax()]
    return pd.DataFrame(
        [
            {
                "forecast_start_date": emergency["forecast_date"].min(),
                "forecast_end_date": emergency["forecast_date"].max(),
                "emergency_patients": int(round(next_week)),
                "emergency_growth_pct": (
                    (next_week / prior_week - 1) * 100
                    if prior_week
                    else 0.0
                ),
                "additional_beds": max(next_week_peak - current_occupied, 0),
                "peak_day": pd.Timestamp(peak["forecast_date"]).strftime(
                    "%A"
                ),
                "peak_day_volume": int(
                    round(peak["forecast_emergency_patients"])
                ),
                "method": (
                    "weekday_seasonal_emergency_baseline_plus_registered_"
                    "occupied_bed_forecast"
                ),
                "peak_hour_status": "unavailable_no_arrival_timestamps",
            }
        ]
    )


def recommendations(
    features: pd.DataFrame,
    billing: pd.DataFrame,
    snapshot: dict[str, float | int | pd.Timestamp],
) -> pd.DataFrame:
    rows = []
    readmission = float(features["readmitted_30d"].mean())
    if readmission > 0.10:
        rows.append(
            {
                "priority": "P1",
                "title": "Readmission control",
                "signal": f"{readmission:.1%} hospital-wide readmission",
                "action": (
                    "Prioritize ICU discharge review and post-discharge "
                    "follow-up."
                ),
                "owner": "Clinical Quality Lead",
                "timeframe": "30 days",
                "success_measure": (
                    "Root-cause review completed and approved ward target set"
                ),
                "reliability": "observed",
            }
        )
    collection = float(
        billing["paid_amount"].sum() / max(billing["billed_amount"].sum(), 1)
    )
    if collection < 0.70:
        rows.append(
            {
                "priority": "P1",
                "title": "Collection recovery",
                "signal": f"{collection:.1%} of billed value collected",
                "action": (
                    "Review payer-specific billed-to-paid gaps and aged claims."
                ),
                "owner": "Revenue Cycle Manager",
                "timeframe": "30 days",
                "success_measure": (
                    "Collection rate monitored against illustrative 70% threshold"
                ),
                "reliability": "observed",
            }
        )
    rows.append(
        {
            "priority": "P2",
            "title": "Queue-data readiness",
            "signal": (
                f"{float(snapshot['emergency_wait_minutes']):.0f} minute "
                "simulated emergency wait"
            ),
            "action": (
                "Capture arrival, triage, and service-start timestamps before "
                "staffing optimization."
            ),
            "owner": "Operations Data Owner",
            "timeframe": "60 days",
            "success_measure": (
                "Observed queue timestamps pass completeness checks"
            ),
            "reliability": "simulated_workflow_measure",
        }
    )
    return pd.DataFrame(rows)


def build_outputs(
    features: pd.DataFrame,
    billing: pd.DataFrame,
    occupancy_forecast: pd.DataFrame,
    capacity: int,
) -> dict[str, pd.DataFrame]:
    snapshot = latest_snapshot(features, capacity)
    overall, scores, _ = efficiency_outputs(features, billing, snapshot)
    command_center = pd.DataFrame(
        [
            {
                **snapshot,
                "hospital_efficiency_score": overall,
                "capacity_assumption": capacity,
                "snapshot_provenance": (
                    "observed_latest_date_with_derived_and_simulated_metrics"
                ),
            }
        ]
    )
    emergency = emergency_forecast(features)
    summary = forecast_summary(
        features,
        occupancy_forecast,
        emergency,
        capacity,
    )
    recommendation_table = recommendations(features, billing, snapshot)
    return {
        "command_center_kpis": command_center,
        "hospital_efficiency_scores": scores,
        "emergency_forecast": emergency,
        "operational_forecast_summary": summary,
        "operational_recommendations": recommendation_table,
    }


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    features = read_processed_table(
        "model_features",
        parse_dates=["admit_date", "discharge_date"],
    )
    billing = read_processed_table(
        "billing",
        parse_dates=["claim_billing_date"],
    )
    occupancy_forecast = pd.read_csv(
        REPORTS / "occupancy_forecast_daily.csv",
        parse_dates=["forecast_date"],
    )
    outputs = build_outputs(
        features,
        billing,
        occupancy_forecast,
        int(config_value("bed_capacity")),
    )
    for name, frame in outputs.items():
        path = REPORTS / f"{name}.csv"
        frame.to_csv(path, index=False)
        print(f"Operational mart saved: {path.relative_to(ROOT)} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
