# Recruiter Walkthrough

## Five-Minute Story

### 1. Business problem

Hospital leaders need reliable evidence on admissions, readmissions, patient
flow, claims collection, and bed demand. The supplied files are disconnected
and do not share an encounter key.

### 2. Data quality and ETL

`src/data_pipeline.py` validates, cleans, and normalizes 120,000 admissions and
70,000 claims records. `reports/data_quality_report.csv` and the Excel workbook
show the controls. `src/validate_project.py` enforces keys, foreign keys, dates,
lineage, and model contracts.

### 3. SQL and warehouse

The MySQL design contains 12 normalized business tables, keys, indexes, views,
procedures, triggers, 60 analytical queries, CTEs, and window functions.
`src/load_mysql.py` performs FK-ordered loads; `src/verify_mysql_deployment.py`
produces auditable database evidence.

### 4. Decision insights

Lead with observed evidence:

- ICU 30-day readmission: 23.8%, compared with 11.8% hospital-wide.
- High-complexity cohort: 21.3% readmission.
- Claims collection: 64.5% of billed value despite 91.4% approval.
- Observed patient census feeds occupied-bed forecasting; capacity is an
  explicitly labelled assumption.

The accountable action plan is in `reports/executive_action_plan.csv`.

### 5. Delivery

The Streamlit application exposes operational analysis, governed patient-record
summaries, forecasts, model explanations, reports, and downloads. The executive
PDF is a four-page decision pack with periods, trends, thresholds, owners, and
timeframes. Power BI assets provide the model, measures, page plan, and theme.

## Evidence Map

| Recruiter question | Evidence |
|---|---|
| Can the candidate clean real data? | `src/data_pipeline.py`, Excel validation, quality CSV |
| Can the candidate model relational data? | `sql/schema.sql`, `sql/views.sql` |
| Can the candidate write advanced SQL? | `sql/analytics.sql`, `sql/procedures.sql` |
| Can the candidate communicate findings? | `reports/executive_report.pdf` |
| Can the candidate build a usable product? | `streamlit/app.py`, UI smoke tests |
| Can the candidate validate work? | `src/validate_project.py`, `tests/` |
| Can the candidate manage ML risk? | `models/manifest.json`, grouped splits, SHAP lineage |
| Can the candidate discuss limitations? | `docs/DATA_GOVERNANCE.md`, provenance CSV |

## Scope Discipline

The core Data Analyst narrative ends after governed KPIs, SQL analysis,
dashboarding, and recommendations. Readmission and occupancy are optional
predictive extensions. Waiting-time and revenue models are sandbox engineering
demonstrations and should not lead an interview presentation.

## Honest Limitations

Doctor, department, demographic, medicine, appointment, waiting-time, and
admission-claim dimensions are derived because the source does not contain
their master keys or timestamps. They demonstrate product workflows. Executive
conclusions lead with observed hospital, ward, date, clinical, readmission,
payer, and aggregate claims fields.

## Suggested Demo Order

1. Open the executive PDF.
2. Show observed ward outcomes in Streamlit.
3. Open the SQL schema and one CTE/window-function query.
4. Show the data-quality and validation reports.
5. Show readmission model lineage and one SHAP explanation.
6. Close with the action plan and deployment gates.
