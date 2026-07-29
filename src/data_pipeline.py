from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "datasets" / "raw"
INTERIM = ROOT / "datasets" / "interim"
PROCESSED = ROOT / "datasets" / "processed"
REPORTS = ROOT / "reports"
EXCEL = ROOT / "excel"


DEPARTMENTS = [
    "Cardiology",
    "Emergency",
    "Orthopedics",
    "Neurology",
    "General Medicine",
    "Pediatrics",
    "Oncology",
    "Surgery",
]
MEDICINES = ["MET", "AML", "ATO", "PAN", "CEF", "INS", "PCM", "LOS"]


class DuplicateRemover(BaseEstimator, TransformerMixin):
    def __init__(self, key: str):
        self.key = key

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop_duplicates(subset=[self.key]).copy()


class FunctionTransformerDF(BaseEstimator, TransformerMixin):
    def __init__(self, function):
        self.function = function

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return self.function(X.copy())


def stable_int(value: str, modulo: int) -> int:
    digest = hashlib.md5(str(value).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def ensure_dirs() -> None:
    for path in [INTERIM, PROCESSED, REPORTS, EXCEL]:
        path.mkdir(parents=True, exist_ok=True)


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    admissions = pd.read_csv(RAW / "admissions.csv")
    billing = pd.read_csv(RAW / "claims_and_billing.csv")
    return admissions, billing


def validate_raw(admissions: pd.DataFrame, billing: pd.DataFrame) -> None:
    checks = []
    for name, df, keys in [
        ("admissions", admissions, ["admission_id"]),
        ("billing", billing, ["billing_id", "claim_id"]),
    ]:
        checks.append(
            {
                "dataset": name,
                "rows": len(df),
                "columns": df.shape[1],
                "duplicate_rows": int(df.duplicated().sum()),
                "duplicate_keys": int(df.duplicated(subset=keys).sum()),
                "missing_cells": int(df.isna().sum().sum()),
            }
        )

    rule_rows = [
        {
            "rule": "Admissions: discharge_date >= admit_date",
            "failed_rows": int(
                (
                    pd.to_datetime(admissions["discharge_date"], errors="coerce")
                    < pd.to_datetime(admissions["admit_date"], errors="coerce")
                ).sum()
            ),
        },
        {
            "rule": "Admissions: los_days between 0 and 90",
            "failed_rows": int(
                (~pd.to_numeric(admissions["los_days"], errors="coerce").between(0, 90)).sum()
            ),
        },
        {
            "rule": "Billing: billed_amount >= paid_amount",
            "failed_rows": int(
                (
                    pd.to_numeric(billing["paid_amount"], errors="coerce")
                    > pd.to_numeric(billing["billed_amount"], errors="coerce")
                ).sum()
            ),
        },
        {
            "rule": "Billing: valid claim status",
            "failed_rows": int(
                (~billing["claim_status"].isin(["Paid", "Denied", "Pending"])).sum()
            ),
        },
    ]

    with pd.ExcelWriter(EXCEL / "raw_validation_report.xlsx", engine="openpyxl") as writer:
        pd.DataFrame(checks).to_excel(writer, index=False, sheet_name="Dataset Checks")
        pd.DataFrame(rule_rows).to_excel(writer, index=False, sheet_name="Business Rules")
        admissions.isna().sum().rename("missing_count").to_frame().to_excel(
            writer, sheet_name="Admissions Missing"
        )
        billing.isna().sum().rename("missing_count").to_frame().to_excel(
            writer, sheet_name="Billing Missing"
        )


def _clean_admission_values(df: pd.DataFrame) -> pd.DataFrame:
    df["admit_date"] = pd.to_datetime(df["admit_date"], errors="coerce")
    df["discharge_date"] = pd.to_datetime(df["discharge_date"], errors="coerce")
    numeric_cols = [
        "los_days",
        "num_procedures",
        "charlson_index",
        "hba1c",
        "creatinine",
        "haemoglobin",
        "systolic_bp",
        "readmitted_30d",
        "readmitted_7d",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    for col in ["admit_type", "ward_type", "discharge_type", "hospital_id"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    # IQR winsorization limits extreme values while preserving all patient rows.
    for col in numeric_cols:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr > 0:
            df[col] = df[col].clip(q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    df["los_days"] = df["los_days"].clip(lower=0)
    df["num_procedures"] = df["num_procedures"].clip(lower=0)
    df["charlson_index"] = df["charlson_index"].clip(lower=0)
    return df


def _clean_billing_values(df: pd.DataFrame) -> pd.DataFrame:
    df["claim_billing_date"] = pd.to_datetime(
        df["claim_billing_date"], errors="coerce", dayfirst=True
    )
    for col in ["billed_amount", "paid_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median()).clip(lower=0)
    for col in ["insurance_provider", "payment_method", "claim_status"]:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()
    df["claim_status"] = df["claim_status"].replace({"Rejected": "Denied"})
    df["claim_gap"] = df["billed_amount"] - df["paid_amount"]
    df["claim_approved"] = (df["claim_status"] == "Paid").astype(int)
    return df


def clean_admissions(df: pd.DataFrame) -> pd.DataFrame:
    pipeline = Pipeline(
        [
            ("duplicates", DuplicateRemover("admission_id")),
            ("missing_dates_outliers", FunctionTransformerDF(_clean_admission_values)),
        ]
    )
    return pipeline.fit_transform(df)


def clean_billing(df: pd.DataFrame) -> pd.DataFrame:
    pipeline = Pipeline(
        [
            ("duplicates", DuplicateRemover("billing_id")),
            ("missing_dates_outliers", FunctionTransformerDF(_clean_billing_values)),
        ]
    )
    return pipeline.fit_transform(df)


def link_billing_to_admissions(
    billing: pd.DataFrame, admissions: pd.DataFrame
) -> pd.DataFrame:
    """Create a reproducible surrogate link because source identifiers do not overlap."""
    linked = billing.reset_index(drop=True).copy()
    admission_keys = admissions[
        ["admission_id", "patient_id", "admit_date", "discharge_date"]
    ].reset_index(drop=True)
    positions = np.arange(len(linked)) % len(admission_keys)
    matched = admission_keys.iloc[positions].reset_index(drop=True)
    linked["source_patient_id"] = linked["patient_id"]
    linked["source_encounter_id"] = linked["encounter_id"]
    linked["admission_id"] = matched["admission_id"]
    linked["patient_id"] = matched["patient_id"]
    linked["claim_billing_date"] = linked["claim_billing_date"].fillna(
        matched["discharge_date"]
    )
    linked["linkage_method"] = "deterministic_surrogate_no_shared_source_key"
    return linked


def engineer_features(adm: pd.DataFrame, bill: pd.DataFrame) -> pd.DataFrame:
    adm = adm.copy()
    adm["department"] = adm.apply(
        lambda r: DEPARTMENTS[
            (stable_int(r["hospital_id"], len(DEPARTMENTS)) + stable_int(r["ward_type"], 3))
            % len(DEPARTMENTS)
        ],
        axis=1,
    )
    department_number = {name: index for index, name in enumerate(DEPARTMENTS)}
    adm["doctor_id"] = adm.apply(
        lambda row: (
            f"DOC{department_number[row['department']] * 5 + stable_int(row['admission_id'], 5) + 1:03d}"
        ),
        axis=1,
    )
    adm["age"] = adm["patient_id"].apply(lambda x: 18 + stable_int(x, 72))
    adm["gender"] = adm["patient_id"].apply(lambda x: ["Female", "Male", "Other"][stable_int(x, 3)])
    adm["medicine_code"] = adm["admission_id"].apply(lambda x: MEDICINES[stable_int(x, len(MEDICINES))])
    adm["medicine_count"] = 1 + adm["num_procedures"] + (adm["charlson_index"] > 2).astype(int)
    adm["admit_month"] = adm["admit_date"].dt.month
    adm["admit_dayofweek"] = adm["admit_date"].dt.dayofweek
    adm["is_weekend_admission"] = adm["admit_dayofweek"].isin([5, 6]).astype(int)
    adm["age_group"] = pd.cut(
        adm["age"],
        bins=[0, 18, 35, 50, 65, 120],
        labels=["0-18", "19-35", "36-50", "51-65", "66+"],
        include_lowest=True,
    ).astype(str)
    adm["season"] = adm["admit_month"].map(
        {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
         6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
    )
    adm = adm.sort_values(["patient_id", "admit_date", "admission_id"])
    adm["previous_admissions"] = adm.groupby("patient_id").cumcount()
    adm["readmission_history"] = adm.groupby("patient_id")["readmitted_30d"].transform(
        lambda values: values.shift(fill_value=0).cumsum()
    )

    dept_daily = (
        adm.groupby(["department", "admit_date"])
        .size()
        .rename("department_daily_admissions")
        .reset_index()
    )
    adm = adm.merge(dept_daily, on=["department", "admit_date"], how="left")
    adm["department_load"] = adm["department_daily_admissions"] / adm["department_daily_admissions"].max()
    adm["disease_severity_score"] = (
        adm["charlson_index"] * 2
        + (adm["hba1c"] > 7).astype(int)
        + (adm["creatinine"] > 1.3).astype(int)
        + (adm["haemoglobin"] < 11).astype(int)
        + (adm["systolic_bp"] > 140).astype(int)
    )
    adm["lab_abnormality_score"] = (
        (adm["hba1c"] > 7).astype(int)
        + (adm["creatinine"] > 1.3).astype(int)
        + (adm["haemoglobin"] < 11).astype(int)
        + (adm["systolic_bp"] > 140).astype(int)
    )
    adm["doctor_experience"] = adm["doctor_id"].apply(lambda x: 2 + stable_int(x, 28))
    adm["bed_utilization_score"] = np.minimum(1, (adm["los_days"] * adm["department_load"]) / 8)
    adm["patient_complexity_index"] = (
        adm["disease_severity_score"] + adm["previous_admissions"] + adm["num_procedures"]
    )
    adm["risk_score"] = (
        0.30 * adm["patient_complexity_index"]
        + 0.25 * adm["los_days"]
        + 0.20 * adm["readmission_history"]
        + 0.15 * adm["lab_abnormality_score"]
        + 0.10 * adm["department_load"]
    )
    adm["waiting_time_minutes"] = (
        18
        + adm["department_daily_admissions"] * 1.7
        + adm["admit_type"].map({"Emergency": 18, "OPD": 28, "Elective": 8}).fillna(12)
        + adm["is_weekend_admission"] * 9
        + adm["charlson_index"] * 2
    ).round(0)
    adm["waiting_time_origin"] = "simulated_formula"
    adm["average_waiting_time"] = adm.groupby("department")[
        "waiting_time_minutes"
    ].transform("mean")
    adm["total_procedures"] = adm["num_procedures"]

    billing_summary = bill.groupby("admission_id", as_index=False).agg(
        billed_amount=("billed_amount", "sum"),
        paid_amount=("paid_amount", "sum"),
        claim_approval_ratio=("claim_approved", "mean"),
        claim_count=("billing_id", "nunique"),
    )
    adm = adm.merge(billing_summary, on="admission_id", how="left")
    adm["billed_amount"] = adm["billed_amount"].fillna(
        900 + adm["los_days"] * 650 + adm["num_procedures"] * 1200 + adm["charlson_index"] * 300
    )
    adm["paid_amount"] = adm["paid_amount"].fillna(adm["billed_amount"] * 0.72)
    adm["claim_approval_ratio"] = adm["claim_approval_ratio"].fillna(0.72)
    adm["claim_count"] = adm["claim_count"].fillna(0)
    adm["revenue_per_patient"] = adm["paid_amount"]
    adm["revenue_origin"] = np.where(
        adm["claim_count"] > 0,
        "surrogate_linked_claim",
        "simulated_cost_formula",
    )
    adm["billing_category"] = pd.qcut(
        adm["billed_amount"].rank(method="first"),
        q=4,
        labels=["Low", "Medium", "High", "Very High"],
    ).astype(str)
    adm["insurance_category"] = np.where(adm["claim_count"] > 0, "Insurance", "Self Pay")
    adm["average_medicine_cost"] = (adm["billed_amount"] * 0.12 / adm["medicine_count"]).round(2)
    adm["department_origin"] = "deterministic_derived_dimension"
    adm["doctor_origin"] = "deterministic_derived_dimension"
    adm["demographics_origin"] = "deterministic_derived_dimension"
    adm["medicine_origin"] = "deterministic_derived_dimension"
    return adm


def build_warehouse_tables(features: pd.DataFrame, billing: pd.DataFrame) -> dict[str, pd.DataFrame]:
    patients = features[["patient_id", "age", "gender", "age_group"]].drop_duplicates("patient_id")
    departments = pd.DataFrame({"department_id": range(1, len(DEPARTMENTS) + 1), "department": DEPARTMENTS})
    doctors = (
        features[["doctor_id", "department", "doctor_experience"]]
        .drop_duplicates("doctor_id")
        .merge(departments, on="department", how="left")
    )
    admissions = features.merge(departments, on="department", how="left")[
        [
            "admission_id",
            "patient_id",
            "doctor_id",
            "department_id",
            "hospital_id",
            "admit_date",
            "discharge_date",
            "los_days",
            "admit_type",
            "ward_type",
            "discharge_type",
            "readmitted_30d",
            "readmitted_7d",
            "waiting_time_minutes",
        ]
    ]
    diagnoses = features[["admission_id", "charlson_index", "disease_severity_score"]].copy()
    procedures = features[["admission_id", "num_procedures"]].copy()
    medicines = features[["admission_id", "medicine_code", "medicine_count", "average_medicine_cost"]].copy()
    labs = features[
        ["admission_id", "hba1c", "creatinine", "haemoglobin", "systolic_bp", "lab_abnormality_score"]
    ].copy()
    insurance = (
        billing[["insurance_provider"]]
        .drop_duplicates()
        .sort_values("insurance_provider")
        .reset_index(drop=True)
    )
    insurance.insert(0, "insurance_id", np.arange(1, len(insurance) + 1))
    billing_with_insurance = billing.merge(
        insurance, on="insurance_provider", how="left", validate="many_to_one"
    )
    billing_table = billing_with_insurance[
        [
            "billing_id",
            "admission_id",
            "patient_id",
            "insurance_id",
            "payment_method",
            "claim_billing_date",
            "billed_amount",
            "paid_amount",
            "claim_gap",
        ]
    ].copy()
    claims = billing_with_insurance[
        [
            "claim_id",
            "billing_id",
            "insurance_id",
            "claim_status",
            "claim_approved",
            "source_patient_id",
            "source_encounter_id",
            "linkage_method",
        ]
    ].copy()
    claims.insert(0, "claim_line_id", "CLINE-" + claims["billing_id"].astype(str))
    claims["claim_id"] = claims["claim_id"].fillna(
        "NOCLAIM-" + claims["billing_id"].astype(str)
    )
    appointments = admissions[
        ["admission_id", "patient_id", "doctor_id", "department_id", "admit_date"]
    ].copy()
    appointments.insert(
        0, "appointment_id", "APT-" + appointments["admission_id"].astype(str)
    )
    appointments["appointment_status"] = "Completed"
    appointments["scheduled_time"] = "09:00:00"
    return {
        "patients": patients,
        "departments": departments,
        "doctors": doctors,
        "admissions": admissions,
        "diagnoses": diagnoses,
        "procedures": procedures,
        "medicines": medicines,
        "labs": labs,
        "insurance": insurance,
        "billing": billing_table,
        "claims": claims,
        "appointments": appointments,
        "model_features": features,
    }


def save_outputs(tables: dict[str, pd.DataFrame], admissions: pd.DataFrame, billing: pd.DataFrame) -> None:
    admissions.to_csv(INTERIM / "admissions_clean.csv", index=False)
    billing.to_csv(INTERIM / "claims_clean.csv", index=False)
    for name, df in tables.items():
        df.to_csv(PROCESSED / f"{name}.csv", index=False)
    kpi = pd.DataFrame(
        [
            {"metric": "Admissions", "value": len(tables["admissions"])},
            {"metric": "Patients", "value": tables["patients"]["patient_id"].nunique()},
            {"metric": "Readmission Rate", "value": tables["admissions"]["readmitted_30d"].mean()},
            {"metric": "Average LOS", "value": tables["admissions"]["los_days"].mean()},
            {"metric": "Average Waiting Time", "value": tables["admissions"]["waiting_time_minutes"].mean()},
            {"metric": "Paid Revenue", "value": billing["paid_amount"].sum()},
            {"metric": "Claim Approval Ratio", "value": billing["claim_approved"].mean()},
        ]
    )
    kpi.to_csv(REPORTS / "executive_kpis.csv", index=False)
    quality = pd.DataFrame(
        [
            {
                "table": name,
                "rows": len(table),
                "columns": table.shape[1],
                "duplicate_rows": int(table.duplicated().sum()),
                "missing_cells": int(table.isna().sum().sum()),
            }
            for name, table in tables.items()
        ]
    )
    quality.to_csv(REPORTS / "data_quality_report.csv", index=False)

    features = tables["model_features"]
    ward = features.groupby("ward_type", as_index=False).agg(
        admissions=("admission_id", "count"),
        readmission_rate=("readmitted_30d", "mean"),
        average_los=("los_days", "mean"),
    )
    hospital = features.groupby("hospital_id", as_index=False).agg(
        admissions=("admission_id", "count"),
        readmission_rate=("readmitted_30d", "mean"),
    )
    payer = billing.groupby("insurance_provider", as_index=False).agg(
        approval_rate=("claim_approved", "mean"),
        paid_amount=("paid_amount", "sum"),
        claim_gap=("claim_gap", "sum"),
    )
    simulated_wait = features.groupby("ward_type")["waiting_time_minutes"].mean()
    insights = [
        {
            "area": "Patient outcomes",
            "reliability": "Observed",
            "decision_use": "Prioritize ward-level discharge review.",
            "insight": (
                f"{ward.loc[ward.readmission_rate.idxmax(), 'ward_type']} has "
                f"the highest observed ward readmission rate at "
                f"{ward.readmission_rate.max():.1%}."
            ),
        },
        {
            "area": "Hospital flow",
            "reliability": "Observed",
            "decision_use": "Use for site-level capacity and staffing review.",
            "insight": (
                f"{hospital.loc[hospital.admissions.idxmax(), 'hospital_id']} records "
                f"the highest admission volume with {hospital.admissions.max():,.0f} encounters."
            ),
        },
        {
            "area": "Claims",
            "reliability": "Observed",
            "decision_use": "Focus denial management on payer-specific gaps.",
            "insight": (
                f"{payer.loc[payer.claim_gap.idxmax(), 'insurance_provider']} has the "
                f"largest observed billed-to-paid gap at "
                f"{payer.claim_gap.max():,.0f}."
            ),
        },
        {
            "area": "Waiting scenario",
            "reliability": "Simulated",
            "decision_use": "Demonstrates queue-model workflow only; replace with timestamp data.",
            "insight": (
                f"{simulated_wait.idxmax()} has the highest simulated average wait at "
                f"{simulated_wait.max():.1f} minutes."
            ),
        },
        {
            "area": "Risk",
            "reliability": "Derived from observed clinical fields",
            "decision_use": "Use as a screening segment, not a causal conclusion.",
            "insight": (
                "Patients in the top complexity quartile have a "
                f"{features.loc[features.patient_complexity_index >= features.patient_complexity_index.quantile(.75), 'readmitted_30d'].mean():.1%} "
                "readmission rate."
            ),
        },
    ]
    pd.DataFrame(insights).to_csv(REPORTS / "business_insights.csv", index=False)
    provenance = pd.DataFrame(
        [
            ("readmitted_30d", "Observed", "Admissions source"),
            ("los_days", "Observed", "Admissions source"),
            ("clinical_labs", "Observed", "Admissions source"),
            ("hospital_id", "Observed", "Admissions source"),
            ("ward_type", "Observed", "Admissions source"),
            ("claim_financials", "Observed", "Claims source only"),
            ("department", "Derived", "Deterministic portfolio dimension"),
            ("doctor_id", "Derived", "Deterministic portfolio dimension"),
            ("age_gender", "Derived", "Deterministic portfolio dimension"),
            ("medicine", "Derived", "Deterministic portfolio dimension"),
            ("waiting_time_minutes", "Simulated", "Formula-generated target"),
            ("revenue_per_patient", "Mixed", "Surrogate-linked or formula-generated"),
            ("admission_claim_link", "Derived", "No shared source identifier"),
            ("bed_capacity", "Assumption", "Configured portfolio capacity"),
        ],
        columns=["feature", "provenance", "method"],
    )
    provenance.to_csv(REPORTS / "feature_provenance.csv", index=False)


def main() -> None:
    ensure_dirs()
    admissions_raw, billing_raw = load_raw()
    validate_raw(admissions_raw, billing_raw)
    admissions = clean_admissions(admissions_raw)
    billing = clean_billing(billing_raw)
    billing = link_billing_to_admissions(billing, admissions)
    features = engineer_features(admissions, billing)
    tables = build_warehouse_tables(features, billing)
    save_outputs(tables, admissions, billing)
    print("Pipeline complete. Clean data, feature tables, validation workbook, and KPI reports saved.")


if __name__ == "__main__":
    main()
