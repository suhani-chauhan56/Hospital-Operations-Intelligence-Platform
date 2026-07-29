# 🏥 Hospital Operations Intelligence Platform

> A production-style healthcare analytics portfolio connecting governed ETL, MySQL, machine learning, SHAP, executive reporting, Power BI assets, and a deployed Streamlit command center.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_App-FF4B4B?logo=streamlit&logoColor=white)](https://hospital-operations-intelligence-platform-hvnncsycljark8qxv7b8.streamlit.app/)
[![Tests](https://img.shields.io/badge/Tests-10_Passing-28A745)](#-quality-and-governance)
[![License](https://img.shields.io/badge/License-MIT-0F4C81)](LICENSE)

## 🚀 Live Demo

[![Launch Hospital Intelligence Platform](https://img.shields.io/badge/Launch_Hospital_Intelligence_Platform-Open_Live_Dashboard-0F4C81?style=for-the-badge&logo=streamlit&logoColor=white)](https://hospital-operations-intelligence-platform-hvnncsycljark8qxv7b8.streamlit.app/)

[View source code](https://github.com/suhani-chauhan56/Hospital-Operations-Intelligence-Platform) · [Download executive report](reports/executive_report.pdf)

## 📌 Business Problem

Hospital leaders often work with disconnected admissions, billing, claims, and operational data. This makes it difficult to identify readmission burden, capacity constraints, revenue leakage, and high-risk patient cohorts.

This project converts fragmented data into a governed platform combining **ETL, MySQL, advanced SQL, machine learning, SHAP, executive reporting, and interactive dashboards**.

## 🎯 At a Glance

| Admissions | Unique patients | Claims | SQL analyses | Governed marts | Quality checks |
|---:|---:|---:|---:|---:|---:|
| **120,000** | **64,873** | **70,000** | **65** | **5** | **33 contracts + 10 tests** |

### What is implemented

- Hospital Command Center with latest-day KPIs, efficiency scoring, forecasts, and owned actions
- Patient 360 search and Patient ID readmission scoring with local model drivers
- Four modeling workflows plus a healthcare assistant grounded in loaded analytics
- Five-page PDF, downloadable outputs, and Power BI implementation assets
- MySQL warehouse with normalized tables, analytical marts, views, procedures, triggers, and a deployment verifier

## 🧱 End-to-End Architecture

```mermaid
flowchart LR
    A[Raw CSV] --> B[Excel Validation]
    B --> C[Python ETL]
    C --> D[Processed Warehouse Tables]
    C --> E[ML Feature Store]
    E --> F[ML Models + SHAP]
    D --> G[Governed Operational Marts]
    F --> G
    D --> H[(MySQL Warehouse)]
    G --> H
    H --> I[SQL Analytics]
    G --> J[Streamlit / Power BI / PDF]
    I --> J
```

Production entry point: [`run_pipeline.ps1`](run_pipeline.ps1). Notebooks are documented experimentation stages and are not required by the deployed app.

## 💡 Verified Business Insights

| Finding | Management action |
|---|---|
| ICU readmission is **23.8%**, versus **11.8%** hospital-wide. | Strengthen ICU discharge planning and follow-up. |
| High-complexity encounters record **21.3%** readmission. | Prioritize this cohort for risk screening. |
| Collections are **64.5%** of billed value despite **91.4%** claim approval. | Separate approval controls from collection recovery. |
| ICU average LOS is **12.0 days**, versus **4.5 days** in General wards. | Review transfer and discharge constraints. |

Recommendations, owners, thresholds, and timeframes are available in the [executive action plan](reports/executive_action_plan.csv).

### Latest command-center output

| Observed date | Patients | Occupied beds | Occupancy | Critical cohort | Efficiency | Next-week emergency forecast |
|---|---:|---:|---:|---:|---:|---:|
| `2024-12-30` | **36** | **263** | **52.6%**<sup>*</sup> | **14**<sup>*</sup> | **76/100**<sup>*</sup> | **127 patients** |

`*` Occupancy uses the configured 500-bed assumption; critical cohort and efficiency are transparent portfolio-derived measures.

## 🖥️ Application Experience

![Hospital intelligence platform home](reports/screenshots/home-redesign-desktop.png)

| Executive Dashboard | AI Prediction Center |
|---|---|
| ![Executive dashboard](reports/screenshots/executive-dashboard.png) | ![AI predictions](reports/screenshots/ai-predictions.png) |

The Command Center reads the same five governed marts used by MySQL, Power BI, and the PDF. Patient risk is scored from the registered model pipeline, and positive drivers explain model behavior without presenting them as diagnoses.

<details>
<summary><strong>View additional application screens</strong></summary>
<br>

| Patient Intelligence | Bed Management |
|---|---|
| ![Patient intelligence](reports/screenshots/patient-analytics.png) | ![Bed management](reports/screenshots/bed-occupancy.png) |

| Revenue Analytics | Explainable AI |
|---|---|
| ![Revenue analytics](reports/screenshots/revenue-analytics.png) | ![Explainable AI](reports/screenshots/explainable-ai.png) |

| Healthcare Assistant | Report Center |
|---|---|
| ![Healthcare assistant](reports/screenshots/assistant-redesign.png) | ![Report center](reports/screenshots/reports-assistant.png) |

</details>

## 🤖 Machine Learning

| Tier | Task | Selected model | Held-out result |
|---|---|---|---|
| Core | 30-day readmission | Logistic Regression | ROC-AUC `0.736`, recall `0.673` |
| Core | Occupied-bed forecast | XGBoost | MAE `6.38 beds`, R² `0.689` |
| Sandbox | Waiting-time workflow | Random Forest | RMSE `0.074 minutes` |
| Sandbox | Revenue scenario | CatBoost | RMSE `$2,890.79`, R² `0.144` |

Core models use observed targets. Waiting time is simulated, while admission-level revenue uses a surrogate claim link. Sandbox results demonstrate engineering workflow and are not presented as validated operational performance.

## 🗃️ MySQL and SQL Analytics

The warehouse contains **12 normalized core tables** plus **5 governed operational marts**:

```text
patients      doctors       departments    admissions
diagnoses     procedures    medicines      labs
insurance     billing       claims         appointments

command_center_kpis       hospital_efficiency_scores
emergency_forecast        operational_forecast_summary
operational_recommendations
```

Implementation includes **primary and foreign keys, constraints, indexes, KPI views, rerunnable stored procedures and triggers, CTEs, window functions, 65 analytical queries, an FK-ordered loader, and a deployment verifier**.

See [`schema.sql`](sql/schema.sql), [`views.sql`](sql/views.sql), and [`analytics.sql`](sql/analytics.sql).

## 🧰 Technology Stack

| Layer | Tools |
|---|---|
| Validation and processing | Excel, Python, Pandas, NumPy |
| Database and analytics | MySQL, SQLAlchemy, advanced SQL |
| Machine learning | Scikit-learn, XGBoost, LightGBM, CatBoost |
| Explainability | SHAP |
| Visualization | Plotly, Streamlit, Power BI assets |
| Quality | Pytest, data contracts, SHA256 model registry |

## 📁 Repository Structure

```text
config/       Operational assumptions and thresholds
datasets/     Raw, interim, processed, and deployment data
docs/         Architecture, governance, recruiter guide, runbook
models/       Registered pipelines and artifact manifest
notebooks/    Cleaning through SHAP experimentation
powerbi/      DAX measures, theme, and implementation guide
reports/      Metrics, forecasts, screenshots, action plan, PDFs
sql/          Schema, views, procedures, and 65 analyses
src/          Production ETL, ML, reporting, and validation
streamlit/    Interactive application
tests/        Data, model, assistant, report, and UI tests
```

## ⚙️ Run Locally

### 1. Clone and enter the project

```powershell
git clone https://github.com/suhani-chauhan56/Hospital-Operations-Intelligence-Platform.git
cd Hospital-Operations-Intelligence-Platform
```

### 2. Create the environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Run the complete pipeline

```powershell
.\run_pipeline.ps1
```

Execution flow:

```text
Data validation -> ETL -> Feature engineering -> Model training
-> SHAP -> Operational marts -> Executive report
-> Contract validation -> Deployment bundle
```

### 4. Launch Streamlit

```powershell
python -m streamlit run streamlit\app.py
```

Open `http://localhost:8501`.

### Optional: deploy MySQL

1. Run `sql/schema.sql` in Workbench and confirm with `USE hospital_ops;`.
2. Load the governed core tables and marts:

```powershell
$env:HOSPITAL_DB_URL = "mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/hospital_ops"
python src\load_mysql.py --truncate
```

3. Run `sql/views.sql` and `sql/procedures.sql` in Workbench.
4. Verify with `python src\verify_mysql_deployment.py --require-ready`.

Notebook order, Power BI instructions, and troubleshooting are in the [execution runbook](docs/RUNBOOK.md).

## ✅ Quality and Governance

- Patient-grouped model splits have **zero train/test patient overlap**
- Model and dataset hashes are registered in [`models/manifest.json`](models/manifest.json)
- SHAP reports are tied to the registered model artifacts
- Keys, foreign keys, dates, provenance, reports, and models are contract-tested
- Fields are labelled as **observed, derived, simulated, surrogate, or assumed**

```powershell
python src\validate_project.py
python -m pytest -q
```

Expected result: **33 project contracts and 10 tests passing**.

## ⚠️ Responsible Use and Limitations

- Portfolio analytics platform, not a medical device
- Doctor, department, demographic, medicine, and appointment dimensions are derived
- Waiting time is simulated because queue timestamps were not supplied
- Revenue attribution is surrogate-linked because the source files lack a shared encounter key
- Occupancy percentages use a configurable 500-bed assumption
- Clinical, staffing, and financial decisions require local validation and human review

## 📚 Documentation

[Execution Runbook](docs/RUNBOOK.md) · [Architecture](docs/ARCHITECTURE.md) · [Data Governance](docs/DATA_GOVERNANCE.md) · [Recruiter Guide](docs/RECRUITER_GUIDE.md) · [Power BI Guide](powerbi/README.md)

## 🙋‍♀️ Author

**Suhani Chauhan**  
B.Tech CSE (Data Science) | Aspiring Data Analyst / ML Engineer

[LinkedIn](https://www.linkedin.com/in/suhani-chauhan-39055832a) · [GitHub](https://github.com/suhani-chauhan56)

⭐ If this project is useful, consider starring the repository.
