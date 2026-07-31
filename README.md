# 🏥 Hospital Operations Intelligence Platform

> A production-style healthcare analytics portfolio that turns fragmented
> hospital data into governed operational decisions.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_App-FF4B4B?logo=streamlit&logoColor=white)](https://hospital-operations-intelligence-platform-hvnncsycljark8qxv7b8.streamlit.app/)
[![SQL](https://img.shields.io/badge/SQL-65_Analyses-146C6E)](sql/analytics.sql)
[![Tests](https://img.shields.io/badge/Tests-11_Passing-28A745)](#-quality-and-governance)
[![License](https://img.shields.io/badge/License-MIT-0F4C81)](LICENSE)

[![Open Live Dashboard](https://img.shields.io/badge/Open_Live_Dashboard-Launch-0F4C81?style=for-the-badge&logo=streamlit&logoColor=white)](https://hospital-operations-intelligence-platform-hvnncsycljark8qxv7b8.streamlit.app/)
[![Executive PDF](https://img.shields.io/badge/Executive_PDF-View_Report-D7644A?style=for-the-badge)](reports/executive_report.pdf)

## ⚡ 30-Second Overview

| Scale | Intelligence layer | Delivery |
|---|---|---|
| **120,000 admissions** | **4 ML workflows** | **12-page Streamlit app** |
| **64,873 patients** | **5 governed marts** | **5-page executive PDF** |
| **70,000 claims** | **65 SQL analyses** | **Power BI implementation assets** |
| **12 core SQL tables** | **SHAP explanations** | **33 contracts + 11 tests** |

**What makes this more than a dashboard:** raw data is validated, transformed
into relational and ML-ready datasets, scored through registered pipelines,
converted into governed decision marts, and reused consistently by MySQL,
Streamlit, Power BI, and executive reporting.

## 📖 The Project Story

### The problem

Hospital leaders often receive separate admissions, claims, billing, and
clinical extracts. The result is delayed reporting, inconsistent KPI
definitions, limited visibility into patient risk, and reactive capacity
planning.

I designed one reproducible flow from raw files to management decisions:

```mermaid
flowchart LR
    A[Raw CSV] --> B[Excel Validation]
    B --> C[Python ETL]
    C --> D[Warehouse Tables]
    C --> E[ML Feature Store]
    E --> F[ML + SHAP]
    D --> G[Operational Marts]
    F --> G
    D --> H[(MySQL)]
    G --> H
    H --> I[SQL Analytics]
    G --> J[Streamlit / Power BI / PDF]
    I --> J
```

Production entry point: [`run_pipeline.ps1`](run_pipeline.ps1). The eight notebooks preserve R&D and experimentation; deployment uses the production modules under `src/`.

### The outcome

The platform gives administrators one place to monitor patient flow,
readmissions, occupied-bed demand, collections, claims, doctor workload, and
department performance, then move from KPI to forecast, explanation, and
accountable action.

## ⭐ Features That Interest Recruiters

- ✅ **End-to-end ownership:** validation, ETL, modeling, SQL, UI, reporting,
  testing, and deployment packaging
- ✅ **Governed KPI layer:** five reusable marts prevent different dashboards
  from calculating the same metric differently
- ✅ **Patient ID risk workflow:** scores a selected patient through the
  registered readmission pipeline
- ✅ **Explainable predictions:** local model contributions and SHAP outputs
  explain model behavior
- ✅ **Operational forecasting:** chronological occupied-bed evaluation and a
  seven-day emergency baseline
- ✅ **Hospital efficiency score:** transparent outcome, collection, capacity,
  and patient-flow components
- ✅ **Actionable recommendations:** every action includes priority, owner,
  timeframe, evidence, and success measure
- ✅ **Advanced SQL:** keys, constraints, indexes, views, CTEs, window
  functions, procedures, triggers, and 65 analyses
- ✅ **Model governance:** patient-grouped splits, zero patient overlap, SHA256
  artifact registration, and provenance labels
- ✅ **Honest analytics:** observed, derived, simulated, surrogate, forecast,
  and assumed fields are explicitly distinguished

## 💡 Verified Decision Outcomes

| Finding | Management response |
|---|---|
| ICU readmission is **23.8%**, versus **11.8%** hospital-wide. | Strengthen ICU discharge review and follow-up. |
| High-complexity encounters record **21.3%** readmission. | Prioritize this cohort for risk screening. |
| Collections are **64.5%** of billed value despite **91.4%** claim approval. | Separate claim approval from collection recovery. |
| ICU average LOS is **12.0 days**, versus **4.5 days** in General wards. | Review transfer and discharge constraints. |

The latest command-center mart reports:

| Date | Patients | Occupied beds | Occupancy | Critical cohort | Efficiency | 7-day emergency forecast |
|---|---:|---:|---:|---:|---:|---:|
| `2024-12-30` | **36** | **263** | **52.6%**<sup>*</sup> | **14**<sup>*</sup> | **76/100**<sup>*</sup> | **127** |

<sup>*</sup> Capacity uses a configurable 500-bed assumption; critical cohort
and efficiency are transparent derived portfolio measures.

## 🖥️ Product Walkthrough

![Hospital Command Center](reports/screenshots/home-redesign-desktop.png)

| Executive Operations | Patient Risk Prediction |
|---|---|
| ![Executive dashboard](reports/screenshots/executive-dashboard.png) | ![AI prediction center](reports/screenshots/ai-predictions.png) |

| Patient Intelligence | Explainable AI |
|---|---|
| ![Patient analytics](reports/screenshots/patient-analytics.png) | ![Explainable AI](reports/screenshots/explainable-ai.png) |

<details>
<summary><strong>View more current application screens</strong></summary>
<br>

| Bed Management | Revenue Analytics |
|---|---|
| ![Bed management](reports/screenshots/bed-occupancy.png) | ![Revenue analytics](reports/screenshots/revenue-analytics.png) |

| Healthcare Assistant | Report Center |
|---|---|
| ![Healthcare assistant](reports/screenshots/assistant-redesign.png) | ![Report center](reports/screenshots/reports-assistant.png) |

</details>

## 🤖 Machine Learning Evidence

| Tier | Decision task | Registered model | Held-out result |
|---|---|---|---|
| Core | 30-day readmission | Logistic Regression | ROC-AUC `0.736`, recall `0.673` |
| Core | Occupied-bed forecast | XGBoost | MAE `6.38 beds`, R² `0.689` |
| Sandbox | Waiting-time workflow | Random Forest | RMSE `0.074 minutes` |
| Sandbox | Revenue scenario | CatBoost | RMSE `$2,890.79`, R² `0.144` |

Core models use observed targets. Waiting time is simulated because arrival,
triage, and service timestamps were not supplied. Admission-level revenue uses
a surrogate claim link. Sandbox metrics demonstrate engineering workflow and
are not presented as validated hospital performance.

## 🗃️ MySQL and Analytics Layer

**12 normalized core tables**

```text
patients      doctors       departments    admissions
diagnoses     procedures    medicines      labs
insurance     billing       claims         appointments
```

**5 governed analytical marts**

```text
command_center_kpis       hospital_efficiency_scores
emergency_forecast        operational_forecast_summary
operational_recommendations
```

The database layer includes primary and foreign keys, validation constraints,
indexes, KPI views, rerunnable procedures and triggers, an FK-ordered loader,
and a deployment verifier.

## ⚙️ Run the Complete Project

```powershell
git clone https://github.com/suhani-chauhan56/Hospital-Operations-Intelligence-Platform.git
cd Hospital-Operations-Intelligence-Platform
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\run_pipeline.ps1
python -m pytest -q
python -m streamlit run streamlit\app.py
```

Open `http://localhost:8501`.

Pipeline order:

```text
Data validation -> ETL -> feature engineering -> model training -> SHAP
-> operational marts -> executive PDF -> contracts -> deployment bundle
```

### Optional MySQL deployment

1. Run `sql/schema.sql` **once** in MySQL Workbench.
2. Set the connection and load the warehouse:

```powershell
$env:HOSPITAL_DB_URL = "mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/hospital_ops"
python src\load_mysql.py --truncate
```

3. Run `sql/views.sql`, then `sql/procedures.sql` in Workbench.
4. Run `sql/analytics.sql` for the analytical query portfolio.
5. Verify with `python src\verify_mysql_deployment.py --require-ready`.

Detailed execution and troubleshooting are in the [runbook](docs/RUNBOOK.md).

## ✅ Quality and Governance

- **33 project contracts** validate tables, keys, dates, provenance, models, reports, forecasts, and cross-mart consistency
- **11 automated tests** cover artifacts, SHAP lineage, probability decomposition, Streamlit routes, predictions, assistant behavior, and PDF regeneration
- **Zero patient overlap** between readmission train and test cohorts
- **Current screenshots:** nine routes captured with zero Streamlit exceptions and zero browser console errors

```powershell
python src\validate_project.py
python -m pytest -q
```

Expected: `33 table and model contracts` and `11 passed`.

## ⚠️ Responsible Use

- Portfolio analytics system, not a medical device
- Doctor, department, demographics, medicine, and appointment dimensions are
  deterministic portfolio constructs
- Waiting time is simulated and revenue attribution is surrogate-linked
- Occupancy uses a configurable capacity assumption
- Peak-hour forecasting is withheld because arrival timestamps are unavailable
- Clinical, staffing, and financial decisions require local validation

## 📚 Evidence and Documentation

[Architecture](docs/ARCHITECTURE.md) ·
[Execution Runbook](docs/RUNBOOK.md) ·
[Data Governance](docs/DATA_GOVERNANCE.md) ·
[Recruiter Guide](docs/RECRUITER_GUIDE.md) ·
[Power BI Guide](powerbi/README.md) ·
[Executive Action Plan](reports/executive_action_plan.csv)

## 🙋‍♀️ Author

**Suhani Chauhan**  
B.Tech CSE (Data Science) | Aspiring Data Analyst / ML Engineer

[LinkedIn](https://www.linkedin.com/in/suhani-chauhan-39055832a) ·
[GitHub](https://github.com/suhani-chauhan56)

⭐ Built to demonstrate how reliable analytics engineering can turn hospital
data into transparent, testable, and decision-ready intelligence.
