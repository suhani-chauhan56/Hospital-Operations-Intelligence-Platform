# Power BI Implementation Specification

Connect to the MySQL views for production-style reporting or load the matching
files from `datasets/processed/` for a portable portfolio demonstration.

Before publishing, import `reports/feature_provenance.csv` and expose the
reliability label beside management callouts. Waiting-time visuals are
simulations; department/doctor dimensions are deterministic derivations;
admission-level finance uses a surrogate claims link. Observed hospital and
ward views should lead executive decision pages.

For a recruiter presentation, lead with Executive, observed ward outcomes,
claims performance, and data quality. Treat readmission and occupied-bed
forecasting as optional predictive extensions. Keep simulated waiting and
surrogate revenue predictions on a clearly labelled Sandbox page rather than
mixing them into core KPI pages.

## Data Model

Use `admissions` as the operational fact table. Relate patients, doctors, and
departments one-to-many to admissions. Relate diagnoses, procedures, medicines,
labs, appointments, and billing through `admission_id`. Relate claims to billing
through `billing_id` and insurance to billing/claims through `insurance_id`.
Create a calendar table and mark it as the date table.

## Report Pages

1. **Executive:** admissions, patients, readmission, LOS, occupancy, claims,
   revenue, monthly trends, and management alerts.
2. **Department:** ranking, patients, revenue, success rate, LOS, waiting time,
   and readmission.
3. **Doctor:** patient count, consultations, workload percentile, revenue,
   utilization, and readmission.
4. **Patient:** timeline, history, medicines, labs, billing, claims, and risk.
5. **Finance:** billed and paid revenue, claim gaps, approval, insurer,
   expenses/proxy costs, and profit/proxy margin.
6. **Operations:** wait, occupancy, admissions, discharge, patient flow,
   weekends, and 7/30/90-day forecasts.

## Core DAX

```DAX
Admissions = DISTINCTCOUNT(admissions[admission_id])
Patients = DISTINCTCOUNT(admissions[patient_id])
Readmission Rate = AVERAGE(admissions[readmitted_30d])
Average LOS = AVERAGE(admissions[los_days])
Average Wait = AVERAGE(admissions[waiting_time_minutes])
Paid Revenue = SUM(billing[paid_amount])
Billed Revenue = SUM(billing[billed_amount])
Revenue Leakage = SUM(billing[claim_gap])
Claim Approval Ratio = AVERAGE(claims[claim_approved])
Revenue Per Patient = DIVIDE([Paid Revenue], [Patients])
Prior Month Revenue =
    CALCULATE([Paid Revenue], DATEADD('Calendar'[Date], -1, MONTH))
Monthly Revenue Growth =
    DIVIDE([Paid Revenue] - [Prior Month Revenue], [Prior Month Revenue])
```

## Visual and Filter Plan

Use KPI cards only for the top executive measures. Prefer line charts for time,
ranked bars for departments/doctors, matrices for detailed comparisons,
scatterplots for workload versus outcome, and decomposition trees for revenue
and readmission drivers. Add slicers for date, department, doctor, admission
type, ward, insurer, payment method, and claim status.

Use `reports/occupancy_forecast_daily.csv` for the forecast visual,
`reports/business_insights.csv` for management callouts, and the SHAP CSV files
for feature-importance charts.
