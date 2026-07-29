# 🏥 Hospital Operations Intelligence Platform

> AI-powered healthcare analytics and decision support for patient flow, readmissions, occupied-bed demand, claims, and executive operations.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live_App-FF4B4B?logo=streamlit&logoColor=white)](https://hospital-operations-intelligence-platform-hvnncsycljark8qxv7b8.streamlit.app/)
[![Tests](https://img.shields.io/badge/Tests-9_Passing-28A745)](#-quality-and-governance)
[![License](https://img.shields.io/badge/License-MIT-0F4C81)](LICENSE)

## 🚀 Live Demo

[![Launch Hospital Intelligence Platform](https://img.shields.io/badge/Launch_Hospital_Intelligence_Platform-Open_Live_Dashboard-0F4C81?style=for-the-badge&logo=streamlit&logoColor=white)](https://hospital-operations-intelligence-platform-hvnncsycljark8qxv7b8.streamlit.app/)

[View source code](https://github.com/suhani-chauhan56/Hospital-Operations-Intelligence-Platform) · [Download executive report](reports/executive_report.pdf)

## 📌 Business Problem

Hospital leaders often work with disconnected admissions, billing, claims, and operational data. This makes it difficult to identify readmission burden, capacity constraints, revenue leakage, and high-risk patient cohorts.

This project converts fragmented data into a governed platform combining **ETL, MySQL, advanced SQL, machine learning, SHAP, executive reporting, and interactive dashboards**.

## 🎯 At a Glance

| Admissions | Unique patients | Claims | SQL analyses | Notebooks | Quality checks |
|---:|---:|---:|---:|---:|---:|
| **120,000** | **64,873** | **70,000** | **60** | **8** | **28 contracts + 9 tests** |

## 🧱 End-to-End Architecture

```mermaid
flowchart LR
    A[Raw CSV] --> B[Excel Validation]
    B --> C[Python ETL]
    C --> D[(MySQL Warehouse)]
    C --> E[Feature Store]
    D --> F[SQL Analytics]
    E --> G[ML + SHAP]
    F --> H[Streamlit / Power BI]
    G --> H
    H --> I[Executive PDF]
```

## 💡 Verified Business Insights

| Finding | Management action |
|---|---|
| ICU readmission is **23.8%**, versus **11.8%** hospital-wide. | Strengthen ICU discharge planning and follow-up. |
| High-complexity encounters record **21.3%** readmission. | Prioritize this cohort for risk screening. |
| Collections are **64.5%** of billed value despite **91.4%** claim approval. | Separate approval controls from collection recovery. |
| ICU average LOS is **12.0 days**, versus **4.5 days** in General wards. | Review transfer and discharge constraints. |

Recommendations, owners, thresholds, and timeframes are available in the [executive action plan](reports/executive_action_plan.csv).

## 🖥️ Application Experience

![Hospital intelligence platform home](reports/screenshots/home-redesign-desktop.png)

| Executive Dashboard | AI Prediction Center |
|---|---|
| ![Executive dashboard](reports/screenshots/executive-dashboard.png) | ![AI predictions](reports/screenshots/ai-predictions.png) |

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

The warehouse contains **12 normalized tables**:

```text
patients      doctors       departments    admissions
diagnoses     procedures    medicines      labs
insurance     billing       claims         appointments
```

Implementation includes **primary and foreign keys, constraints, indexes, KPI views, stored procedures, billing triggers, CTEs, window functions, 60 analytical queries, an FK-ordered loader, and a deployment verifier**.

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
sql/          Schema, views, procedures, and 60 analyses
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
-> SHAP -> Executive report -> Contract validation -> Deployment bundle
```

### 4. Launch Streamlit

```powershell
python -m streamlit run streamlit\app.py
```

Open `http://localhost:8501`.

For MySQL deployment, notebook order, Power BI, and troubleshooting, follow the [complete execution runbook](docs/RUNBOOK.md).

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

Expected result: **28 project contracts and 9 tests passing**.

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
