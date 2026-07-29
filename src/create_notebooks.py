from __future__ import annotations

import json
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def code(source: str) -> dict:
    normalized = source.strip()
    return {
        "cell_type": "code",
        "id": hashlib.sha1(f"code:{normalized}".encode("utf-8")).hexdigest()[:12],
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": normalized.splitlines(keepends=True),
    }


def markdown(source: str) -> dict:
    normalized = source.strip()
    return {
        "cell_type": "markdown",
        "id": hashlib.sha1(f"markdown:{normalized}".encode("utf-8")).hexdigest()[:12],
        "metadata": {},
        "source": normalized.splitlines(keepends=True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.14",
                "mimetype": "text/x-python",
                "codemirror_mode": {"name": "ipython", "version": 3},
                "pygments_lexer": "ipython3",
                "nbconvert_exporter": "python",
                "file_extension": ".py",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


SETUP = """
from pathlib import Path
import sys

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

RAW = ROOT / "datasets" / "raw"
INTERIM = ROOT / "datasets" / "interim"
PROCESSED = ROOT / "datasets" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "reports"
EXPERIMENT_MODELS = MODELS / "experiments"
EXPERIMENT_REPORTS = REPORTS / "experiments"
for folder in [INTERIM, PROCESSED, MODELS, REPORTS, EXPERIMENT_MODELS, EXPERIMENT_REPORTS]:
    folder.mkdir(parents=True, exist_ok=True)

print(f"Project root: {ROOT}")
"""


NOTEBOOKS_CONTENT: dict[str, list[dict]] = {
    "01_DataCleaning.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 01: Data Cleaning Pipeline

### Business objective

Hospital data arrives from multiple operational systems and cannot be trusted
until quality rules are applied consistently. This notebook converts the raw
admissions and claims extracts into clean, analysis-ready datasets.

### Pipeline

1. Load and profile raw files
2. Validate keys, dates, categories, and billing rules
3. Treat missing values
4. Remove duplicate keys
5. Correct data types
6. Winsorize numerical outliers
7. Preserve a documented surrogate claim linkage
8. Save clean datasets and quality reports
"""
        ),
        markdown("## 1. Imports and project paths"),
        code(
            SETUP
            + """
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from data_pipeline import (
    clean_admissions,
    clean_billing,
    link_billing_to_admissions,
    validate_raw,
)

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 80)
"""
        ),
        markdown("## 2. Load raw data"),
        code(
            """
admissions_raw = pd.read_csv(RAW / "admissions.csv")
claims_raw = pd.read_csv(RAW / "claims_and_billing.csv")

print("Admissions:", admissions_raw.shape)
print("Claims and billing:", claims_raw.shape)
display(admissions_raw.head())
display(claims_raw.head())
"""
        ),
        markdown("## 3. Data overview and validation"),
        code(
            """
overview = pd.DataFrame(
    {
        "dataset": ["admissions", "claims"],
        "rows": [len(admissions_raw), len(claims_raw)],
        "columns": [admissions_raw.shape[1], claims_raw.shape[1]],
        "duplicate_rows": [
            admissions_raw.duplicated().sum(),
            claims_raw.duplicated().sum(),
        ],
        "missing_cells": [
            admissions_raw.isna().sum().sum(),
            claims_raw.isna().sum().sum(),
        ],
    }
)
display(overview)
display(admissions_raw.describe(include="all").T)
display(claims_raw.describe(include="all").T)
"""
        ),
        code(
            """
validation_rules = pd.DataFrame(
    {
        "rule": [
            "Unique admission_id",
            "Unique billing_id",
            "Discharge date is not before admission",
            "Paid amount does not exceed billed amount",
            "Known claim status",
        ],
        "failures": [
            admissions_raw.duplicated("admission_id").sum(),
            claims_raw.duplicated("billing_id").sum(),
            (
                pd.to_datetime(admissions_raw["discharge_date"], errors="coerce")
                < pd.to_datetime(admissions_raw["admit_date"], errors="coerce")
            ).sum(),
            (
                pd.to_numeric(claims_raw["paid_amount"], errors="coerce")
                > pd.to_numeric(claims_raw["billed_amount"], errors="coerce")
            ).sum(),
            (~claims_raw["claim_status"].isin(["Paid", "Denied", "Pending"])).sum(),
        ],
    }
)
display(validation_rules)
validate_raw(admissions_raw, claims_raw)
print("Excel validation workbook refreshed.")
"""
        ),
        markdown(
            """
### Missing-value strategy

- Numeric clinical values: median imputation
- Operational categories: `Unknown`
- Invalid dates: coercion to missing, then governed review
- Duplicate business keys: retain the first valid record
- Extreme numeric values: IQR winsorization, preserving patient rows
"""
        ),
        code(
            """
missing = pd.concat(
    [
        admissions_raw.isna().sum().rename("admissions"),
        claims_raw.isna().sum().rename("claims"),
    ],
    axis=1,
).fillna(0)

ax = missing.plot(kind="bar", figsize=(14, 5), color=["#146C6E", "#D7644A"])
ax.set_title("Missing values before cleaning")
ax.set_ylabel("Missing cells")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 4. Clean, type-correct, and link data"),
        code(
            """
admissions_clean = clean_admissions(admissions_raw)
claims_clean = clean_billing(claims_raw)
claims_clean = link_billing_to_admissions(claims_clean, admissions_clean)

quality_comparison = pd.DataFrame(
    {
        "dataset": ["admissions", "claims"],
        "raw_rows": [len(admissions_raw), len(claims_raw)],
        "clean_rows": [len(admissions_clean), len(claims_clean)],
        "raw_missing": [
            admissions_raw.isna().sum().sum(),
            claims_raw.isna().sum().sum(),
        ],
        "clean_missing": [
            admissions_clean.isna().sum().sum(),
            claims_clean.isna().sum().sum(),
        ],
        "duplicate_keys_after": [
            admissions_clean.duplicated("admission_id").sum(),
            claims_clean.duplicated("billing_id").sum(),
        ],
    }
)
display(quality_comparison)
display(admissions_clean.dtypes.to_frame("dtype"))
"""
        ),
        markdown(
            """
The source files have no overlapping patient or encounter identifiers.
`link_billing_to_admissions` therefore creates a reproducible surrogate link,
retains both original identifiers, and records the linkage method. The derived
join is suitable for demonstrating architecture, not clinical attribution.
"""
        ),
        markdown("## 5. Outlier assessment"),
        code(
            """
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for axis, column in zip(
    axes, ["los_days", "charlson_index", "systolic_bp"]
):
    sns.boxplot(data=admissions_clean, x=column, ax=axis, color="#70B7A3")
    axis.set_title(column.replace("_", " ").title())
plt.suptitle("Clinical and operational values after IQR treatment")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 6. Save clean outputs"),
        code(
            """
admissions_clean.to_csv(INTERIM / "admissions_clean.csv", index=False)
claims_clean.to_csv(INTERIM / "claims_clean.csv", index=False)

quality_comparison.to_csv(
    EXPERIMENT_REPORTS / "cleaning_quality_summary.csv", index=False
)
print("Saved:")
print("-", INTERIM / "admissions_clean.csv")
print("-", INTERIM / "claims_clean.csv")
print("-", EXPERIMENT_REPORTS / "cleaning_quality_summary.csv")
"""
        ),
        markdown(
            """
## Business conclusions

- Business keys are unique after cleaning.
- Dates and numeric fields use consistent analytical types.
- Missing values are handled with documented domain rules.
- Outliers are controlled without deleting patient encounters.
- Claims remain traceable to their original source identifiers.

The outputs are ready for exploratory analysis, but all surrogate relationships
must be replaced by governed source-system keys before real hospital use.
"""
        ),
    ],
    "02_EDA.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 02: Exploratory Data Analysis

### Business objective

Discover patient-flow, capacity, waiting-time, readmission, and financial
patterns that hospital administrators can turn into operational action.

### Business questions

1. Which service lines handle the highest volume?
2. When do admissions peak?
3. Which departments experience long waiting time?
4. Where are readmissions concentrated?
5. Which departments and payers contribute the most revenue?
"""
        ),
        markdown("## 1. Imports and analytical dataset"),
        code(
            SETUP
            + """
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages

from data_pipeline import (
    clean_admissions,
    clean_billing,
    engineer_features,
    link_billing_to_admissions,
)

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 80)
"""
        ),
        code(
            """
admissions = pd.read_csv(
    INTERIM / "admissions_clean.csv",
    parse_dates=["admit_date", "discharge_date"],
)
claims = pd.read_csv(
    INTERIM / "claims_clean.csv",
    parse_dates=["claim_billing_date"],
)
data = engineer_features(admissions, claims)

billing = pd.read_csv(
    INTERIM / "claims_clean.csv",
    parse_dates=["claim_billing_date"],
)
print("Analytical records:", data.shape)
display(data.head())
"""
        ),
        markdown("## 2. Patient demographics and segmentation"),
        code(
            """
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
sns.histplot(data=data, x="age", bins=18, ax=axes[0], color="#146C6E")
axes[0].set_title("Age distribution")
sns.countplot(data=data, x="gender", ax=axes[1], color="#70B7A3")
axes[1].set_title("Gender distribution")
sns.countplot(
    data=data,
    x="age_group",
    order=["0-18", "19-35", "36-50", "51-65", "66+"],
    ax=axes[2],
    color="#3D6E8F",
)
axes[2].set_title("Age segments")
axes[2].tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 3. Admission and patient-flow analysis"),
        code(
            """
monthly = (
    data.set_index("admit_date")
    .resample("MS")
    .agg(admissions=("admission_id", "count"), patients=("patient_id", "nunique"))
    .reset_index()
)
weekday = (
    data.assign(weekday=data["admit_date"].dt.day_name())
    .groupby("weekday")
    .size()
    .reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
)

fig, axes = plt.subplots(1, 2, figsize=(16, 5))
axes[0].plot(monthly["admit_date"], monthly["admissions"], color="#146C6E")
axes[0].set_title("Monthly admissions trend")
axes[0].set_ylabel("Admissions")
weekday.plot(kind="bar", ax=axes[1], color="#D4A72C")
axes[1].set_title("Admissions by weekday")
axes[1].tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.show()
"""
        ),
        code(
            """
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
sns.countplot(data=data, x="admit_type", ax=axes[0], color="#D7644A")
axes[0].set_title("Emergency, OPD, and elective mix")
sns.countplot(data=data, x="ward_type", ax=axes[1], color="#3D6E8F")
axes[1].set_title("Ward workload")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 4. Department performance"),
        code(
            """
department = data.groupby("department", as_index=False).agg(
    admissions=("admission_id", "count"),
    patients=("patient_id", "nunique"),
    average_wait=("waiting_time_minutes", "mean"),
    average_los=("los_days", "mean"),
    readmission_rate=("readmitted_30d", "mean"),
    revenue=("revenue_per_patient", "sum"),
)
display(department.sort_values("admissions", ascending=False))

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
sns.barplot(
    data=department.sort_values("admissions", ascending=False),
    y="department", x="admissions", ax=axes[0], color="#146C6E"
)
axes[0].set_title("Department workload")
sns.barplot(
    data=department.sort_values("average_wait", ascending=False),
    y="department", x="average_wait", ax=axes[1], color="#D4A72C"
)
axes[1].set_title("Average waiting time")
sns.barplot(
    data=department.sort_values("readmission_rate", ascending=False),
    y="department", x="readmission_rate", ax=axes[2], color="#D7644A"
)
axes[2].set_title("Readmission concentration")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 5. Financial and insurance analysis"),
        code(
            """
monthly_revenue = (
    billing.set_index("claim_billing_date")
    .resample("MS")
    .agg(billed=("billed_amount", "sum"), paid=("paid_amount", "sum"))
    .reset_index()
)
payer = billing.groupby("insurance_provider", as_index=False).agg(
    billed=("billed_amount", "sum"),
    paid=("paid_amount", "sum"),
    approval=("claim_approved", "mean"),
)

fig, axes = plt.subplots(1, 2, figsize=(16, 5))
axes[0].plot(monthly_revenue["claim_billing_date"], monthly_revenue["paid"], color="#269A78")
axes[0].set_title("Collected revenue trend")
sns.barplot(
    data=payer.sort_values("paid", ascending=False),
    y="insurance_provider", x="paid", ax=axes[1], color="#3D6E8F"
)
axes[1].set_title("Insurance contribution")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 6. Readmission risk relationships"),
        code(
            """
risk_comparison = data.groupby("readmitted_30d")[
    [
        "los_days",
        "charlson_index",
        "previous_admissions",
        "lab_abnormality_score",
        "patient_complexity_index",
    ]
].mean().T
display(risk_comparison)

plt.figure(figsize=(10, 6))
sns.heatmap(
    data[
        [
            "readmitted_30d",
            "los_days",
            "charlson_index",
            "previous_admissions",
            "lab_abnormality_score",
            "patient_complexity_index",
            "waiting_time_minutes",
            "revenue_per_patient",
        ]
    ].corr(),
    cmap="RdYlGn_r",
    center=0,
    annot=True,
    fmt=".2f",
)
plt.title("Operational feature correlation")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 7. Save EDA report and analytical summary"),
        code(
            """
with PdfPages(EXPERIMENT_REPORTS / "EDA_Report.pdf") as pdf:
    fig, axes = plt.subplots(2, 2, figsize=(11.7, 8.3))
    axes[0, 0].plot(monthly["admit_date"], monthly["admissions"], color="#146C6E")
    axes[0, 0].set_title("Monthly admissions")
    department.sort_values("admissions").plot.barh(
        x="department", y="admissions", ax=axes[0, 1], legend=False, color="#3D6E8F"
    )
    axes[0, 1].set_title("Department workload")
    department.sort_values("average_wait").plot.barh(
        x="department", y="average_wait", ax=axes[1, 0], legend=False, color="#D4A72C"
    )
    axes[1, 0].set_title("Average waiting time")
    department.sort_values("readmission_rate").plot.barh(
        x="department", y="readmission_rate", ax=axes[1, 1], legend=False, color="#D7644A"
    )
    axes[1, 1].set_title("Readmission rate")
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

department.to_csv(
    EXPERIMENT_REPORTS / "eda_department_summary.csv", index=False
)
print("Saved EDA_Report.pdf and department summary.")
"""
        ),
        markdown(
            """
## Business conclusions

- Orthopedics currently has the highest observed readmission rate.
- Surgery has the longest modeled average waiting time.
- General Medicine leads modeled average revenue per admission.
- High complexity and multiple prior admissions identify a concentrated risk segment.
- Department staffing and discharge follow-up should be reviewed together because
  throughput, waiting time, LOS, and readmission interact.

These are analytical findings from provided and derived portfolio data, not
clinical recommendations.
"""
        ),
    ],
    "03_FeatureEngineering.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 03: Feature Engineering

### Business objective

Transform cleaned operational records into reproducible, leakage-aware features
that machine learning models can use for readmission, waiting time, occupancy,
and revenue prediction.

### Feature groups

- Patient: age group, prior admissions, readmission history, complexity
- Clinical: severity and abnormal-lab scores
- Admission: LOS, weekend, season, emergency type
- Workforce: doctor experience and department load
- Financial: billing category, insurance, claim approval, revenue
- Capacity: medicine count, waiting time, and bed-utilization score
"""
        ),
        markdown("## 1. Imports and clean inputs"),
        code(
            SETUP
            + """
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from data_pipeline import engineer_features, link_billing_to_admissions
from train_models import CATEGORICAL_FEATURES, FEATURES

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 100)
"""
        ),
        code(
            """
admissions = pd.read_csv(
    INTERIM / "admissions_clean.csv",
    parse_dates=["admit_date", "discharge_date"],
)
claims = pd.read_csv(
    INTERIM / "claims_clean.csv",
    parse_dates=["claim_billing_date"],
)
if "admission_id" not in claims:
    claims = link_billing_to_admissions(claims, admissions)

print("Clean admissions:", admissions.shape)
print("Clean claims:", claims.shape)
"""
        ),
        markdown("## 2. Build operational features"),
        code(
            """
final_dataset = engineer_features(admissions, claims)

feature_groups = {
    "patient": [
        "age", "age_group", "previous_admissions", "readmission_history",
        "patient_complexity_index", "risk_score",
    ],
    "admission": [
        "los_days", "is_weekend_admission", "admit_month", "season",
        "admit_type", "ward_type",
    ],
    "clinical": [
        "disease_severity_score", "lab_abnormality_score",
        "charlson_index", "hba1c", "creatinine", "haemoglobin",
    ],
    "workforce": ["doctor_id", "doctor_experience", "department_load"],
    "financial": [
        "insurance_category", "billing_category", "claim_approval_ratio",
        "revenue_per_patient", "average_medicine_cost",
    ],
    "capacity": [
        "medicine_count", "total_procedures", "average_waiting_time",
        "waiting_time_minutes", "bed_utilization_score",
    ],
}
for group, columns in feature_groups.items():
    print(group, "->", [column for column in columns if column in final_dataset])

display(final_dataset.head())
"""
        ),
        markdown("## 3. Validate engineered features"),
        code(
            """
validation = pd.DataFrame(
    {
        "check": [
            "One row per admission",
            "No missing model features",
            "No first-visit history leakage",
            "Readmission target is binary",
            "Waiting time is non-negative",
            "Revenue is non-negative",
        ],
        "failures": [
            final_dataset.duplicated("admission_id").sum(),
            final_dataset[FEATURES].isna().sum().sum(),
            (
                (final_dataset["previous_admissions"] == 0)
                & (final_dataset["readmission_history"] != 0)
            ).sum(),
            (~final_dataset["readmitted_30d"].isin([0, 1])).sum(),
            (final_dataset["waiting_time_minutes"] < 0).sum(),
            (final_dataset["revenue_per_patient"] < 0).sum(),
        ],
    }
)
display(validation)
assert validation["failures"].sum() == 0
"""
        ),
        markdown("## 4. Encoding and scaling experiment"),
        code(
            """
categorical = [column for column in CATEGORICAL_FEATURES if column in FEATURES]
numeric = [column for column in FEATURES if column not in categorical]

preprocessor = ColumnTransformer(
    [
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
    ]
)
sample = final_dataset[FEATURES].sample(min(5000, len(final_dataset)), random_state=42)
transformed = preprocessor.fit_transform(sample)

print("Raw model features:", sample.shape)
print("Encoded and scaled matrix:", transformed.shape)
print("Categorical levels are handled with unknown-category protection.")
"""
        ),
        markdown("## 5. Feature visualizations"),
        code(
            """
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
sns.histplot(final_dataset["risk_score"], bins=30, ax=axes[0], color="#D7644A")
axes[0].set_title("Risk score")
sns.histplot(
    final_dataset["patient_complexity_index"],
    bins=30,
    ax=axes[1],
    color="#3D6E8F",
)
axes[1].set_title("Patient complexity")
sns.boxplot(
    data=final_dataset,
    x="readmitted_30d",
    y="disease_severity_score",
    ax=axes[2],
    color="#70B7A3",
)
axes[2].set_title("Severity by readmission outcome")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 6. Save ML-ready data"),
        code(
            """
final_dataset.to_csv(INTERIM / "notebook_model_features.csv", index=False)

feature_dictionary = pd.DataFrame(
    [
        {"feature_group": group, "feature": feature}
        for group, columns in feature_groups.items()
        for feature in columns
        if feature in final_dataset
    ]
)
feature_dictionary.to_csv(
    EXPERIMENT_REPORTS / "feature_dictionary.csv", index=False
)

print("Saved:", INTERIM / "notebook_model_features.csv")
print("Saved:", EXPERIMENT_REPORTS / "feature_dictionary.csv")
"""
        ),
        markdown(
            """
## Business conclusions

- Historical variables are calculated within patient groups to prevent cross-patient leakage.
- Encoders tolerate unseen categories in future Streamlit predictions.
- Scaling is fitted only inside model pipelines after the train/test split.
- Derived claim and demographic features remain explicitly documented because
  the raw files do not contain a governed natural relationship.

The ML-ready dataset is the input to Notebooks 04-07.
"""
        ),
    ],
    "04_ReadmissionPrediction.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 04: Readmission Prediction

### Business objective

Predict 30-day readmission risk early enough for administrators and care teams
to prioritize discharge review and follow-up capacity.

### Target

`readmitted_30d` (binary classification)

### Experiments

Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost, and
GridSearchCV tuning. Evaluation emphasizes ROC AUC, recall, precision, and F1
rather than accuracy alone because readmission is imbalanced.
"""
        ),
        markdown("## 1. Imports and ML dataset"),
        code(
            SETUP
            + """
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, ConfusionMatrixDisplay,
    f1_score, precision_score, recall_score, RocCurveDisplay, roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline

from train_models import READMISSION_FEATURES, group_split, preprocessor

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
"""
        ),
        code(
            """
data_path = INTERIM / "notebook_model_features.csv"
data = pd.read_csv(data_path)
experiment = data.sample(min(30000, len(data)), random_state=42)
X = experiment[READMISSION_FEATURES]
y = experiment["readmitted_30d"].astype(int)
X_train, X_test, y_train, y_test, split_audit = group_split(
    X, y, experiment["patient_id"]
)
print("Train:", X_train.shape, "Test:", X_test.shape)
print("Readmission prevalence:", f"{y.mean():.2%}")
print("Patient overlap:", split_audit["patient_overlap"])
"""
        ),
        markdown("## 2. Build candidate models"),
        code(
            """
models = {
    "logistic_regression": LogisticRegression(
        max_iter=1000, class_weight="balanced"
    ),
    "random_forest": RandomForestClassifier(
        n_estimators=100, max_depth=10, class_weight="balanced",
        random_state=42, n_jobs=-1,
    ),
}

try:
    from xgboost import XGBClassifier
    models["xgboost"] = XGBClassifier(
        n_estimators=100, max_depth=3, learning_rate=0.08,
        subsample=0.9, eval_metric="logloss", random_state=42,
    )
except ImportError:
    print("XGBoost is not installed.")

try:
    from lightgbm import LGBMClassifier
    models["lightgbm"] = LGBMClassifier(
        n_estimators=100, learning_rate=0.08, random_state=42, verbose=-1
    )
except ImportError:
    print("LightGBM is not installed.")

try:
    from catboost import CatBoostClassifier
    models["catboost"] = CatBoostClassifier(
        iterations=100, depth=5, learning_rate=0.08,
        verbose=False, random_seed=42,
    )
except ImportError:
    print("CatBoost is unavailable. Install the pinned project requirements.")
"""
        ),
        markdown("## 3. Train and evaluate"),
        code(
            """
results = []
fitted_models = {}
for name, estimator in models.items():
    pipeline = Pipeline(
        [("prep", preprocessor(X_train)), ("model", estimator)]
    )
    pipeline.fit(X_train, y_train)
    prediction = pipeline.predict(X_test)
    probability = pipeline.predict_proba(X_test)[:, 1]
    results.append(
        {
            "model": name,
            "accuracy": accuracy_score(y_test, prediction),
            "precision": precision_score(y_test, prediction, zero_division=0),
            "recall": recall_score(y_test, prediction, zero_division=0),
            "f1": f1_score(y_test, prediction, zero_division=0),
            "roc_auc": roc_auc_score(y_test, probability),
        }
    )
    fitted_models[name] = pipeline

results = pd.DataFrame(results).sort_values("roc_auc", ascending=False)
display(results)
"""
        ),
        markdown("## 4. Hyperparameter tuning"),
        code(
            """
tuning_pipeline = Pipeline(
    [
        ("prep", preprocessor(X_train)),
        (
            "model",
            RandomForestClassifier(
                class_weight="balanced", random_state=42, n_jobs=-1
            ),
        ),
    ]
)
parameter_grid = {
    "model__n_estimators": [80, 120],
    "model__max_depth": [8, 12],
    "model__min_samples_leaf": [1, 3],
}
grid = GridSearchCV(
    tuning_pipeline,
    parameter_grid,
    scoring="roc_auc",
    cv=GroupKFold(n_splits=3),
    n_jobs=-1,
    verbose=1,
)
grid.fit(
    X_train,
    y_train,
    groups=experiment.loc[X_train.index, "patient_id"],
)
tuned_model = grid.best_estimator_
print("Best parameters:", grid.best_params_)
print("Cross-validated ROC AUC:", round(grid.best_score_, 4))
"""
        ),
        markdown("## 5. Diagnostic visualizations"),
        code(
            """
best_name = results.iloc[0]["model"]
best_model = fitted_models[best_name]
best_prediction = best_model.predict(X_test)
best_probability = best_model.predict_proba(X_test)[:, 1]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ConfusionMatrixDisplay.from_predictions(
    y_test, best_prediction, cmap="Blues", ax=axes[0]
)
axes[0].set_title(f"Confusion matrix: {best_name}")
RocCurveDisplay.from_predictions(
    y_test, best_probability, ax=axes[1], color="#146C6E"
)
axes[1].plot([0, 1], [0, 1], "--", color="gray")
axes[1].set_title(f"ROC curve: {best_name}")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 6. Save model and metrics"),
        code(
            """
tuned_probability = tuned_model.predict_proba(X_test)[:, 1]
tuned_auc = roc_auc_score(y_test, tuned_probability)
if tuned_auc >= results.iloc[0]["roc_auc"]:
    selected_model = tuned_model
    selected_name = "tuned_random_forest"
else:
    selected_model = best_model
    selected_name = best_name

joblib.dump(selected_model, EXPERIMENT_MODELS / "readmission_notebook.pkl")
results.to_csv(EXPERIMENT_REPORTS / "readmission_metrics.csv", index=False)
print("Selected:", selected_name)
print("Saved:", EXPERIMENT_MODELS / "readmission_notebook.pkl")
"""
        ),
        markdown(
            """
## Business conclusions

- ROC AUC is the primary ranking metric; recall should be tuned to available
  follow-up capacity.
- A high-risk flag is a prioritization aid, not a diagnosis.
- LOS, comorbidity, laboratory abnormality, prior admissions, and complexity
  require explainability review before intervention.
- Threshold calibration and external hospital validation are required before deployment.
"""
        ),
    ],
    "05_WaitTimePrediction.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 05: Waiting-Time Prediction

### Business objective

Estimate patient waiting time so hospital managers can anticipate queue pressure,
adjust doctor coverage, and communicate realistic service expectations.

### Target

`waiting_time_minutes` (regression)

### Models and metrics

Linear Regression, Random Forest, Gradient Boosting, XGBoost, LightGBM, and
CatBoost. Evaluation uses MAE, RMSE, guarded MAPE, and R2.
"""
        ),
        markdown("## 1. Imports, loading, and validation"),
        code(
            SETUP
            + """
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from train_models import WAITING_FEATURES, group_split, preprocessor

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
"""
        ),
        code(
            """
data_path = INTERIM / "notebook_model_features.csv"
data = pd.read_csv(data_path)
assert data["waiting_time_minutes"].notna().all()
assert (data["waiting_time_minutes"] >= 0).all()
experiment = data.sample(min(30000, len(data)), random_state=42)
X = experiment[WAITING_FEATURES]
y = experiment["waiting_time_minutes"].astype(float)
X_train, X_test, y_train, y_test, split_audit = group_split(
    X, y, experiment["patient_id"]
)
display(y.describe())
print("Patient overlap:", split_audit["patient_overlap"])
"""
        ),
        markdown("## 2. Build and compare models"),
        code(
            """
models = {
    "linear_regression": LinearRegression(),
    "random_forest": RandomForestRegressor(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
    ),
    "gradient_boosting": GradientBoostingRegressor(random_state=42),
}
try:
    from xgboost import XGBRegressor
    models["xgboost"] = XGBRegressor(
        n_estimators=100, max_depth=3, learning_rate=0.08, random_state=42
    )
except ImportError:
    pass
try:
    from lightgbm import LGBMRegressor
    models["lightgbm"] = LGBMRegressor(
        n_estimators=100, learning_rate=0.08, random_state=42, verbose=-1
    )
except ImportError:
    pass
try:
    from catboost import CatBoostRegressor
    models["catboost"] = CatBoostRegressor(
        iterations=100, depth=5, learning_rate=0.08,
        verbose=False, random_seed=42,
    )
except ImportError:
    print("CatBoost is unavailable. Install the pinned project requirements.")
"""
        ),
        code(
            """
results = []
fitted_models = {}
predictions = {}
for name, estimator in models.items():
    pipeline = Pipeline(
        [("prep", preprocessor(X_train)), ("model", estimator)]
    )
    pipeline.fit(X_train, y_train)
    prediction = pipeline.predict(X_test)
    denominator = np.maximum(np.abs(y_test.to_numpy()), 1)
    results.append(
        {
            "model": name,
            "MAE": mean_absolute_error(y_test, prediction),
            "RMSE": np.sqrt(mean_squared_error(y_test, prediction)),
            "MAPE": np.mean(np.abs(y_test.to_numpy() - prediction) / denominator),
            "R2": r2_score(y_test, prediction),
        }
    )
    fitted_models[name] = pipeline
    predictions[name] = prediction

results = pd.DataFrame(results).sort_values("RMSE")
display(results)
"""
        ),
        markdown("## 3. Evaluation visualizations"),
        code(
            """
best_name = results.iloc[0]["model"]
best_model = fitted_models[best_name]
best_prediction = predictions[best_name]
residuals = y_test.to_numpy() - best_prediction

fig, axes = plt.subplots(1, 3, figsize=(17, 4))
axes[0].scatter(y_test, best_prediction, alpha=0.2, color="#146C6E")
axes[0].plot([y.min(), y.max()], [y.min(), y.max()], "--", color="gray")
axes[0].set_title("Actual vs predicted")
axes[0].set_xlabel("Actual minutes")
axes[0].set_ylabel("Predicted minutes")
sns.histplot(residuals, bins=30, ax=axes[1], color="#3D6E8F")
axes[1].set_title("Residual distribution")
sns.boxplot(
    data=data, x="department", y="waiting_time_minutes",
    ax=axes[2], color="#D4A72C"
)
axes[2].tick_params(axis="x", rotation=70)
axes[2].set_title("Wait by department")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 4. Save model and conclusions"),
        code(
            """
joblib.dump(best_model, EXPERIMENT_MODELS / "waiting_notebook.pkl")
results.to_csv(EXPERIMENT_REPORTS / "waiting_metrics.csv", index=False)
print("Selected:", best_name)
print("Saved:", EXPERIMENT_MODELS / "waiting_notebook.pkl")
"""
        ),
        markdown(
            """
## Business conclusions

- RMSE describes operational variability while MAE is easier for managers to interpret.
- Department load, patient type, ward, complexity, and weekend admission are
  useful queue-planning signals.
- Predictions should trigger staffing review, not promise an exact patient wait.
- Arrival-hour and real roster data would materially improve this model.
"""
        ),
    ],
    "06_BedOccupancyForecast.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 06: Bed Occupancy Forecast

### Business objective

Forecast occupied-bed demand so administrators can plan staffing, discharge
coordination, elective scheduling, and surge capacity.

### Problem

Time-series regression using a daily active-patient census. A 500-bed staffed
capacity is an explicit portfolio assumption and can be changed before training.

### Models

Seven-day moving-average baseline, XGBoost time-series regressor, and optional
Prophet benchmark. Output is a dated 30-day forecast.
"""
        ),
        markdown("## 1. Imports and daily census construction"),
        code(
            SETUP
            + """
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")
BED_CAPACITY = 500
"""
        ),
        code(
            """
data_path = INTERIM / "notebook_model_features.csv"
data = pd.read_csv(data_path, parse_dates=["admit_date", "discharge_date"])
calendar = pd.date_range(data["admit_date"].min(), data["admit_date"].max(), freq="D")
admissions = data.groupby("admit_date").size().reindex(calendar, fill_value=0)
discharges = (
    data.groupby(data["discharge_date"] + pd.Timedelta(days=1))
    .size()
    .reindex(calendar, fill_value=0)
)
occupied = (admissions - discharges).cumsum().clip(lower=0)
daily = pd.DataFrame(
    {
        "date": calendar,
        "admissions": admissions.values,
        "discharges": discharges.values,
        "occupied_beds": occupied.values,
    }
)
daily["available_beds"] = (BED_CAPACITY - daily["occupied_beds"]).clip(lower=0)
daily["occupancy_pct"] = (daily["occupied_beds"] / BED_CAPACITY * 100).clip(0, 100)
display(daily.tail())
"""
        ),
        markdown("## 2. Validation and time-series features"),
        code(
            """
assert daily["date"].is_monotonic_increasing
assert daily["date"].duplicated().sum() == 0
assert (daily["occupied_beds"] >= 0).all()

daily["dayofweek"] = daily["date"].dt.dayofweek
daily["month"] = daily["date"].dt.month
daily["is_weekend"] = (daily["dayofweek"] >= 5).astype(int)
daily["lag_1"] = daily["occupancy_pct"].shift(1)
daily["lag_7"] = daily["occupancy_pct"].shift(7)
daily["rolling_7"] = daily["occupancy_pct"].shift(1).rolling(7).mean()
daily["moving_average_7"] = daily["occupancy_pct"].shift(1).rolling(7).mean()
model_data = daily.dropna().copy()

plt.figure(figsize=(14, 5))
plt.plot(daily["date"], daily["occupancy_pct"], color="#146C6E", linewidth=1)
plt.axhline(85, linestyle="--", color="#D7644A", label="85% alert")
plt.title("Historical daily occupancy")
plt.ylabel("Occupancy %")
plt.legend()
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 3. Moving-average and ML evaluation"),
        code(
            """
features = ["dayofweek", "month", "is_weekend", "lag_1", "lag_7", "rolling_7"]
split = int(len(model_data) * 0.80)
train = model_data.iloc[:split]
test = model_data.iloc[split:]
X_train, y_train = train[features], train["occupancy_pct"]
X_test, y_test = test[features], test["occupancy_pct"]

try:
    from xgboost import XGBRegressor
    model = XGBRegressor(
        n_estimators=120, max_depth=3, learning_rate=0.06, random_state=42
    )
except ImportError:
    model = RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=-1)

model.fit(X_train, y_train)
ml_prediction = model.predict(X_test)
baseline_prediction = test["moving_average_7"].to_numpy()

metrics = pd.DataFrame(
    [
        {
            "model": "moving_average_7",
            "MAE": mean_absolute_error(y_test, baseline_prediction),
            "RMSE": np.sqrt(mean_squared_error(y_test, baseline_prediction)),
            "R2": r2_score(y_test, baseline_prediction),
        },
        {
            "model": type(model).__name__,
            "MAE": mean_absolute_error(y_test, ml_prediction),
            "RMSE": np.sqrt(mean_squared_error(y_test, ml_prediction)),
            "R2": r2_score(y_test, ml_prediction),
        },
    ]
).sort_values("RMSE")
display(metrics)
"""
        ),
        markdown("## 4. Optional Prophet benchmark"),
        code(
            """
try:
    from prophet import Prophet
    prophet_data = daily[["date", "occupancy_pct"]].rename(
        columns={"date": "ds", "occupancy_pct": "y"}
    )
    prophet_model = Prophet(
        weekly_seasonality=True, yearly_seasonality=True, daily_seasonality=False
    )
    prophet_model.fit(prophet_data)
    prophet_future = prophet_model.make_future_dataframe(periods=30)
    prophet_forecast = prophet_model.predict(prophet_future).tail(30)
    print("Prophet benchmark completed.")
except ImportError:
    prophet_forecast = None
    print("Prophet is optional and not installed.")
"""
        ),
        markdown("## 5. Recursive 30-day forecast"),
        code(
            """
history = daily.set_index("date")["occupancy_pct"].to_dict()
forecast_rows = []
last_date = daily["date"].max()
for step in range(1, 31):
    forecast_date = last_date + pd.Timedelta(days=step)
    prior = [history[forecast_date - pd.Timedelta(days=i)] for i in range(1, 8)]
    row = pd.DataFrame(
        [
            {
                "dayofweek": forecast_date.dayofweek,
                "month": forecast_date.month,
                "is_weekend": int(forecast_date.dayofweek >= 5),
                "lag_1": prior[0],
                "lag_7": prior[6],
                "rolling_7": np.mean(prior),
            }
        ]
    )
    occupancy = float(np.clip(model.predict(row[features])[0], 0, 100))
    history[forecast_date] = occupancy
    forecast_rows.append(
        {
            "date": forecast_date,
            "forecast_occupancy_pct": occupancy,
            "forecast_occupied_beds": int(np.ceil(occupancy / 100 * BED_CAPACITY)),
            "forecast_available_beds": int(
                max(BED_CAPACITY - np.ceil(occupancy / 100 * BED_CAPACITY), 0)
            ),
        }
    )
forecast = pd.DataFrame(forecast_rows)

plt.figure(figsize=(14, 5))
plt.plot(
    daily.tail(120)["date"], daily.tail(120)["occupancy_pct"],
    label="Actual", color="#146C6E"
)
plt.plot(
    forecast["date"], forecast["forecast_occupancy_pct"],
    label="30-day forecast", color="#D7644A"
)
plt.axhline(85, linestyle="--", color="#D4A72C", label="85% alert")
plt.legend()
plt.title("Bed occupancy forecast")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 6. Save model, forecast, and conclusions"),
        code(
            """
artifact = {
    "model": model,
    "features": features,
    "bed_capacity": BED_CAPACITY,
    "last_date": last_date,
}
joblib.dump(artifact, EXPERIMENT_MODELS / "occupancy_notebook.pkl")
forecast.to_csv(EXPERIMENT_REPORTS / "occupancy_30_day_forecast.csv", index=False)
metrics.to_csv(EXPERIMENT_REPORTS / "occupancy_metrics.csv", index=False)
print("Saved:", EXPERIMENT_MODELS / "occupancy_notebook.pkl")
"""
        ),
        markdown(
            """
## Business conclusions

- Daily active census is more meaningful than admission count alone.
- Lagged occupancy provides strong short-term signal but uncertainty grows recursively.
- The forecast supports staffing and capacity scenarios; it does not prove that
  a physical bed is staffed, clean, or appropriate for a specific clinical need.
- Department-level bed inventory and scheduled procedures would improve the forecast.
"""
        ),
    ],
    "07_RevenuePrediction.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 07: Revenue Prediction

### Business objective

Estimate admission revenue and aggregate it into department and planning
scenarios for payer management, budgeting, and resource allocation.

### Target

`revenue_per_patient`

### Models

Random Forest, Gradient Boosting, XGBoost, LightGBM, and CatBoost.
Evaluation uses RMSE, MAE, guarded MAPE, and R2.
"""
        ),
        markdown("## 1. Imports, loading, and target validation"),
        code(
            SETUP
            + """
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

from train_models import REVENUE_FEATURES, group_split, preprocessor

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
"""
        ),
        code(
            """
data_path = INTERIM / "notebook_model_features.csv"
data = pd.read_csv(data_path, parse_dates=["admit_date"])
assert data["revenue_per_patient"].notna().all()
assert (data["revenue_per_patient"] >= 0).all()
experiment = data.sample(min(30000, len(data)), random_state=42)
X = experiment[REVENUE_FEATURES]
y = experiment["revenue_per_patient"].astype(float)
X_train, X_test, y_train, y_test, split_audit = group_split(
    X, y, experiment["patient_id"]
)
display(y.describe())
print("Patient overlap:", split_audit["patient_overlap"])
"""
        ),
        markdown("## 2. Build and compare models"),
        code(
            """
models = {
    "random_forest": RandomForestRegressor(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
    ),
    "gradient_boosting": GradientBoostingRegressor(random_state=42),
}
try:
    from xgboost import XGBRegressor
    models["xgboost"] = XGBRegressor(
        n_estimators=100, max_depth=3, learning_rate=0.08, random_state=42
    )
except ImportError:
    pass
try:
    from lightgbm import LGBMRegressor
    models["lightgbm"] = LGBMRegressor(
        n_estimators=100, learning_rate=0.08, random_state=42, verbose=-1
    )
except ImportError:
    pass
try:
    from catboost import CatBoostRegressor
    models["catboost"] = CatBoostRegressor(
        iterations=100, depth=5, learning_rate=0.08,
        verbose=False, random_seed=42,
    )
except ImportError:
    print("CatBoost is unavailable. Install the pinned project requirements.")

results = []
fitted_models = {}
prediction_map = {}
for name, estimator in models.items():
    pipeline = Pipeline(
        [("prep", preprocessor(X_train)), ("model", estimator)]
    )
    pipeline.fit(X_train, y_train)
    prediction = pipeline.predict(X_test)
    denominator = np.maximum(np.abs(y_test.to_numpy()), 1)
    results.append(
        {
            "model": name,
            "MAE": mean_absolute_error(y_test, prediction),
            "RMSE": np.sqrt(mean_squared_error(y_test, prediction)),
            "MAPE": np.mean(np.abs(y_test.to_numpy() - prediction) / denominator),
            "R2": r2_score(y_test, prediction),
        }
    )
    fitted_models[name] = pipeline
    prediction_map[name] = prediction

results = pd.DataFrame(results).sort_values("RMSE")
display(results)
"""
        ),
        markdown("## 3. Evaluation and business aggregation"),
        code(
            """
best_name = results.iloc[0]["model"]
best_model = fitted_models[best_name]
prediction = prediction_map[best_name]
evaluation = experiment.loc[X_test.index, ["department"]].copy()
evaluation["actual_revenue"] = y_test
evaluation["predicted_revenue"] = prediction

department_forecast = evaluation.groupby("department", as_index=False)[
    ["actual_revenue", "predicted_revenue"]
].sum()
display(department_forecast.sort_values("predicted_revenue", ascending=False))

fig, axes = plt.subplots(1, 2, figsize=(15, 5))
axes[0].scatter(y_test, prediction, alpha=0.2, color="#146C6E")
axes[0].plot([y.min(), y.max()], [y.min(), y.max()], "--", color="gray")
axes[0].set_title("Actual vs predicted admission revenue")
axes[0].set_xlabel("Actual")
axes[0].set_ylabel("Predicted")
department_forecast.sort_values("predicted_revenue").plot.barh(
    x="department", y="predicted_revenue", ax=axes[1],
    legend=False, color="#269A78"
)
axes[1].set_title("Predicted department revenue")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 4. Daily and monthly planning views"),
        code(
            """
all_predictions = best_model.predict(data[REVENUE_FEATURES])
planning = data[["admit_date", "department"]].copy()
planning["predicted_revenue"] = np.maximum(all_predictions, 0)
daily_revenue = planning.groupby("admit_date", as_index=False)["predicted_revenue"].sum()
monthly_revenue = (
    daily_revenue.set_index("admit_date")
    .resample("MS")["predicted_revenue"]
    .sum()
    .reset_index()
)

plt.figure(figsize=(14, 5))
plt.plot(monthly_revenue["admit_date"], monthly_revenue["predicted_revenue"], color="#269A78")
plt.title("Monthly predicted revenue")
plt.ylabel("Revenue")
plt.tight_layout()
plt.show()
"""
        ),
        markdown("## 5. Save model, forecasts, and conclusions"),
        code(
            """
joblib.dump(best_model, EXPERIMENT_MODELS / "revenue_notebook.pkl")
results.to_csv(EXPERIMENT_REPORTS / "revenue_metrics.csv", index=False)
department_forecast.to_csv(EXPERIMENT_REPORTS / "department_revenue_forecast.csv", index=False)
daily_revenue.to_csv(EXPERIMENT_REPORTS / "daily_revenue_forecast.csv", index=False)
monthly_revenue.to_csv(EXPERIMENT_REPORTS / "monthly_revenue_forecast.csv", index=False)
print("Selected:", best_name)
print("Saved:", EXPERIMENT_MODELS / "revenue_notebook.pkl")
"""
        ),
        markdown(
            """
## Business conclusions

- Revenue predictions are most useful when aggregated into department and time views.
- Claim approval, billing category, LOS, and procedure intensity drive financial output.
- Zero paid revenue for denied claims requires guarded percentage metrics.
- Cost data is absent, so revenue must not be presented as profit.
- The surrogate admissions-claims link prevents real financial attribution until
  governed source keys are available.
"""
        ),
    ],
    "08_SHAPExplainability.ipynb": [
        markdown(
            """
# Hospital Operations Intelligence Platform

## Notebook 08: SHAP Explainability

### Business objective

Black-box risk predictions are not acceptable in healthcare operations.
This notebook explains global model behavior and individual patient predictions,
then saves auditable visual reports.

### Outputs

- Global readmission feature importance
- SHAP summary plot
- Individual patient waterfall plot
- Patient-level top risk factors
- `reports/SHAP_Report.pdf`
"""
        ),
        markdown("## 1. Imports, model, and explanation sample"),
        code(
            SETUP
            + """
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from matplotlib.backends.backend_pdf import PdfPages

warnings.filterwarnings("ignore")
SHAP_DIR = EXPERIMENT_REPORTS / "shap"
SHAP_DIR.mkdir(parents=True, exist_ok=True)
"""
        ),
        code(
            """
data_path = INTERIM / "notebook_model_features.csv"
model_path = EXPERIMENT_MODELS / "readmission_notebook.pkl"
data = pd.read_csv(data_path)
pipeline = joblib.load(model_path)
preprocessor = pipeline.named_steps["prep"]
estimator = pipeline.named_steps["model"]
sample = data.sample(min(250, len(data)), random_state=42)
X = sample[list(preprocessor.feature_names_in_)]
X_transformed = preprocessor.transform(X)
feature_names = preprocessor.get_feature_names_out()

if hasattr(estimator, "estimators_"):
    estimator_for_shap = estimator.estimators_[0]
else:
    estimator_for_shap = estimator

print("Model:", type(estimator).__name__)
print("Explanation sample:", X.shape)
"""
        ),
        markdown("## 2. Generate SHAP values"),
        code(
            """
try:
    explainer = shap.Explainer(estimator_for_shap, X_transformed[:50])
    explanation = explainer(X_transformed)
except Exception:
    prediction_function = (
        estimator_for_shap.predict_proba
        if hasattr(estimator_for_shap, "predict_proba")
        else estimator_for_shap.predict
    )
    explainer = shap.Explainer(prediction_function, X_transformed[:50])
    explanation = explainer(X_transformed[:100])

values = np.asarray(explanation.values)
if values.ndim == 3:
    values = values[:, :, -1]
    explanation.values = values
print("SHAP matrix:", values.shape)
"""
        ),
        markdown("## 3. Global feature importance and summary plot"),
        code(
            """
importance = pd.DataFrame(
    {
        "feature": feature_names,
        "mean_abs_shap": np.abs(values).mean(axis=0),
    }
).sort_values("mean_abs_shap", ascending=False)
display(importance.head(20))

plt.figure()
shap.summary_plot(
    values,
    X_transformed[: len(values)],
    feature_names=feature_names,
    show=False,
    max_display=20,
)
plt.tight_layout()
plt.savefig(SHAP_DIR / "readmission_summary.png", dpi=180, bbox_inches="tight")
plt.show()
"""
        ),
        markdown("## 4. Individual prediction explanation"),
        code(
            """
patient_position = 0
patient_id = sample.iloc[patient_position]["patient_id"]
patient_probability = pipeline.predict_proba(
    X.iloc[[patient_position]]
)[0, 1]
print("Patient:", patient_id)
print("Readmission probability:", f"{patient_probability:.1%}")

patient_explanation = shap.Explanation(
    values=values[patient_position],
    base_values=np.asarray(explanation.base_values)[patient_position],
    data=(
        X_transformed[patient_position].toarray().ravel()
        if hasattr(X_transformed[patient_position], "toarray")
        else np.asarray(X_transformed[patient_position]).ravel()
    ),
    feature_names=list(feature_names),
)
shap.plots.waterfall(patient_explanation, max_display=15, show=False)
plt.tight_layout()
plt.savefig(SHAP_DIR / "patient_waterfall.png", dpi=180, bbox_inches="tight")
plt.show()
"""
        ),
        markdown("## 5. Patient-level risk factors"),
        code(
            """
positive = np.where(values > 0, values, -np.inf)
top_index = positive.argmax(axis=1)
patient_factors = pd.DataFrame(
    {
        "patient_id": sample.iloc[: len(values)]["patient_id"].to_numpy(),
        "top_risk_factor": feature_names[top_index],
        "factor_contribution": values[np.arange(len(values)), top_index],
    }
)
display(patient_factors.head(20))
"""
        ),
        markdown("## 6. Save explainability outputs and PDF"),
        code(
            """
importance.to_csv(EXPERIMENT_REPORTS / "readmission_shap_importance.csv", index=False)
patient_factors.to_csv(EXPERIMENT_REPORTS / "patient_shap_explanations.csv", index=False)

with PdfPages(EXPERIMENT_REPORTS / "SHAP_Report.pdf") as pdf:
    for image_path, title in [
        (SHAP_DIR / "readmission_summary.png", "Global readmission drivers"),
        (SHAP_DIR / "patient_waterfall.png", "Individual patient explanation"),
    ]:
        image = plt.imread(image_path)
        fig, axis = plt.subplots(figsize=(11.7, 8.3))
        axis.imshow(image)
        axis.axis("off")
        axis.set_title(title, fontsize=16)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

print("Saved:", EXPERIMENT_REPORTS / "SHAP_Report.pdf")
"""
        ),
        markdown(
            """
## Business conclusions

- Length of stay, comorbidity, haemoglobin, severity, and patient complexity are
  leading global readmission drivers in the current model.
- A global SHAP chart does not explain every individual patient; use the
  patient-level waterfall for case review.
- SHAP explains model behavior, not medical causality.
- Explanations and predictions must be audited for drift, bias, and data quality
  before any operational deployment.

These notebook findings feed the Explainable AI page in Streamlit.
"""
        ),
    ],
}


def main() -> None:
    NOTEBOOKS.mkdir(exist_ok=True)
    for filename, cells in NOTEBOOKS_CONTENT.items():
        output = NOTEBOOKS / filename
        output.write_text(
            json.dumps(notebook(cells), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        print(f"Created {output.name}: {len(cells)} cells")
    print("Production R&D notebooks created.")


if __name__ == "__main__":
    main()
