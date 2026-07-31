# Complete Execution Runbook

## 1. Prerequisites

- Python 3.14
- MySQL Server 8.0 and MySQL Workbench
- Power BI Desktop, optional

## 2. Environment Setup

```powershell
cd "C:\Users\HP\Desktop\Hospital OP Inteligent sys"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

Confirm these inputs exist:

```text
datasets/raw/admissions.csv
datasets/raw/claims_and_billing.csv
```

## 3. Production Pipeline

```powershell
.\run_pipeline.ps1
```

Execution order:

```text
data_pipeline.py
-> train_models.py
-> shap_explainability.py
-> operational_intelligence.py
-> generate_executive_report.py
-> validate_project.py
```

Launch in CSV mode:

```powershell
$env:HOSPITAL_DATA_SOURCE = "csv"
python -m streamlit run streamlit\app.py
```

Pipeline and application shortcut:

```powershell
.\run_pipeline.ps1 -LaunchDashboard
```

## 4. MySQL Deployment

In MySQL Workbench, execute:

```text
sql/schema.sql
```

Confirm the database:

```sql
USE hospital_ops;
SELECT DATABASE();
SHOW TABLES;
```

Configure the connection in PowerShell:

```powershell
$env:HOSPITAL_DB_URL = "mysql+mysqlconnector://root:YOUR_PASSWORD@localhost/hospital_ops"
```

Load processed data:

```powershell
python src\load_mysql.py --truncate
```

Execute complete files in MySQL Workbench:

```text
sql/views.sql
sql/procedures.sql
sql/analytics.sql
```

Verify the deployment:

```powershell
python src\verify_mysql_deployment.py --require-ready
```

Launch with MySQL:

```powershell
$env:HOSPITAL_DATA_SOURCE = "mysql"
python -m streamlit run streamlit\app.py
```

Do not run `sql/insert.sql`; bulk loading is handled by `src/load_mysql.py`.

## 5. Validation and Tests

```powershell
python src\validate_project.py
python -m pytest -q
```

Expected:

```text
Project validation passed: 33 table and model contracts.
11 passed
```

## 6. Notebook Workflow

Notebooks are optional R&D files and are not required by Streamlit.

```powershell
python -m jupyter lab
```

Run in numerical order:

```text
01_DataCleaning.ipynb
02_EDA.ipynb
03_FeatureEngineering.ipynb
04_ReadmissionPrediction.ipynb
05_WaitTimePrediction.ipynb
06_BedOccupancyForecast.ipynb
07_RevenuePrediction.ipynb
08_SHAPExplainability.ipynb
```

Experiment outputs are isolated under `models/experiments/` and `reports/experiments/`.

## 7. Power BI

Connect Power BI Desktop to either:

- MySQL database `hospital_ops`
- CSV tables under `datasets/processed/`

Use:

```text
powerbi/README.md
powerbi/measures.dax
powerbi/hospital_operations_theme.json
```

## 8. Streamlit Community Cloud

Build the deployment bundle:

```powershell
python src\package_streamlit_deployment.py
```

Commit the generated `.csv.gz` tables, registered models, manifest, and required
reports allowed by `.gitignore`. In Streamlit Community Cloud, select:

```text
Main file path: streamlit/app.py
Data source: CSV (default)
```

After pushing a refreshed bundle, reboot the app from **Manage app**. The cloud
application uses the same processed data, registered models, model hashes, and
reports as the validated local application.

## 9. Main Outputs

```text
excel/raw_validation_report.xlsx
models/manifest.json
reports/executive_report.pdf
reports/executive_action_plan.csv
reports/*_model_metrics.csv
reports/*_shap_importance.csv
reports/occupancy_forecast_daily.csv
reports/validation_summary.json
```

## 10. Common Issues

### PowerShell activation blocked

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Wrong MySQL database

```sql
USE hospital_ops;
SELECT DATABASE();
```

### CatBoost unavailable in a notebook

```python
%pip install catboost==1.2.10
```

Restart the notebook kernel afterward.

### Port 8501 already in use

```powershell
python -m streamlit run streamlit\app.py --server.port 8502
```
