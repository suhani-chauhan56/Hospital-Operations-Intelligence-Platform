USE hospital_ops;

CREATE OR REPLACE VIEW vw_executive_kpis AS
SELECT
    COUNT(DISTINCT a.admission_id) AS admissions,
    COUNT(DISTINCT a.patient_id) AS patients,
    AVG(a.readmitted_30d) AS readmission_rate,
    AVG(a.los_days) AS average_los,
    AVG(a.waiting_time_minutes) AS average_waiting_time,
    COALESCE(SUM(b.paid_amount), 0) AS paid_revenue,
    AVG(c.claim_approved) AS claim_approval_ratio
FROM admissions a
LEFT JOIN billing b ON a.admission_id = b.admission_id
LEFT JOIN claims c ON b.billing_id = c.billing_id;

CREATE OR REPLACE VIEW vw_command_center AS
SELECT
    c.as_of_date,
    c.patients_today,
    c.occupancy_pct,
    c.occupied_beds,
    c.emergency_wait_minutes,
    c.critical_patients,
    c.doctor_utilization_pct,
    c.hospital_efficiency_score,
    c.capacity_assumption,
    f.forecast_start_date,
    f.forecast_end_date,
    f.emergency_patients AS next_week_emergency_patients,
    f.emergency_growth_pct,
    f.additional_beds,
    f.peak_day,
    f.peak_day_volume,
    f.peak_hour_status
FROM command_center_kpis c
CROSS JOIN operational_forecast_summary f;

CREATE OR REPLACE VIEW vw_efficiency_ranking AS
SELECT
    scope_type,
    scope_name,
    efficiency_score,
    patient_outcome_score,
    collection_score,
    capacity_balance_score,
    patient_flow_score,
    provenance,
    DENSE_RANK() OVER (
        PARTITION BY scope_type
        ORDER BY efficiency_score DESC
    ) AS efficiency_rank
FROM hospital_efficiency_scores;

CREATE OR REPLACE VIEW vw_operational_action_queue AS
SELECT
    priority,
    title,
    signal,
    action,
    owner,
    timeframe,
    success_measure,
    reliability,
    CASE priority
        WHEN 'P1' THEN 1
        WHEN 'P2' THEN 2
        ELSE 3
    END AS priority_order
FROM operational_recommendations;

CREATE OR REPLACE VIEW vw_department_kpis AS
SELECT
    d.department,
    COUNT(DISTINCT a.admission_id) AS admissions,
    COUNT(DISTINCT a.patient_id) AS patients,
    AVG(a.readmitted_30d) AS readmission_rate,
    AVG(a.los_days) AS average_los,
    AVG(a.waiting_time_minutes) AS average_wait,
    COALESCE(SUM(b.paid_amount), 0) AS revenue,
    DENSE_RANK() OVER (ORDER BY COALESCE(SUM(b.paid_amount), 0) DESC) AS revenue_rank
FROM departments d
LEFT JOIN admissions a ON d.department_id = a.department_id
LEFT JOIN billing b ON a.admission_id = b.admission_id
GROUP BY d.department;

CREATE OR REPLACE VIEW vw_doctor_utilization AS
SELECT
    doc.doctor_id,
    doc.department,
    COUNT(DISTINCT a.admission_id) AS admissions,
    COUNT(DISTINCT a.patient_id) AS patients,
    AVG(a.waiting_time_minutes) AS avg_wait,
    AVG(a.readmitted_30d) AS readmission_rate,
    COALESCE(SUM(b.paid_amount), 0) AS revenue,
    PERCENT_RANK() OVER (
        PARTITION BY doc.department
        ORDER BY COUNT(DISTINCT a.admission_id)
    ) AS workload_percentile
FROM doctors doc
LEFT JOIN admissions a ON doc.doctor_id = a.doctor_id
LEFT JOIN billing b ON a.admission_id = b.admission_id
GROUP BY doc.doctor_id, doc.department;

CREATE OR REPLACE VIEW vw_monthly_revenue AS
SELECT
    DATE_FORMAT(b.claim_billing_date, '%Y-%m-01') AS month_start,
    i.insurance_provider,
    SUM(b.billed_amount) AS billed_revenue,
    SUM(b.paid_amount) AS paid_revenue,
    AVG(c.claim_approved) AS claim_approval_ratio,
    SUM(b.paid_amount) - LAG(SUM(b.paid_amount)) OVER (
        PARTITION BY i.insurance_provider
        ORDER BY DATE_FORMAT(b.claim_billing_date, '%Y-%m-01')
    ) AS month_over_month_change
FROM billing b
LEFT JOIN insurance i ON b.insurance_id = i.insurance_id
LEFT JOIN claims c ON b.billing_id = c.billing_id
GROUP BY DATE_FORMAT(b.claim_billing_date, '%Y-%m-01'), i.insurance_provider;

CREATE OR REPLACE VIEW vw_daily_occupancy AS
WITH calendar AS (
    SELECT DISTINCT admit_date AS census_date
    FROM admissions
),
census AS (
    SELECT
        c.census_date,
        (
            SELECT COUNT(*)
            FROM admissions a
            WHERE a.admit_date = c.census_date
        ) AS admissions,
        (
            SELECT COUNT(*)
            FROM admissions a
            WHERE a.admit_date <= c.census_date
              AND COALESCE(a.discharge_date, c.census_date) >= c.census_date
        ) AS occupied_beds
    FROM calendar c
)
SELECT
    census_date AS admit_date,
    admissions,
    occupied_beds,
    LEAST(100, occupied_beds / 500 * 100) AS occupancy_pct,
    AVG(occupied_beds) OVER (
        ORDER BY census_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS occupied_beds_7d_avg
FROM census;

CREATE OR REPLACE VIEW vw_bed_occupancy AS
SELECT *
FROM vw_daily_occupancy;

CREATE OR REPLACE VIEW vw_patient_360 AS
SELECT
    p.patient_id,
    p.age,
    p.gender,
    a.admission_id,
    a.admit_date,
    a.discharge_date,
    d.department,
    doc.doctor_id,
    dg.disease_severity_score,
    l.lab_abnormality_score,
    m.medicine_code,
    m.medicine_count,
    b.billed_amount,
    b.paid_amount,
    c.claim_status
FROM patients p
LEFT JOIN admissions a ON p.patient_id = a.patient_id
LEFT JOIN departments d ON a.department_id = d.department_id
LEFT JOIN doctors doc ON a.doctor_id = doc.doctor_id
LEFT JOIN diagnoses dg ON a.admission_id = dg.admission_id
LEFT JOIN labs l ON a.admission_id = l.admission_id
LEFT JOIN medicines m ON a.admission_id = m.admission_id
LEFT JOIN billing b ON a.admission_id = b.admission_id
LEFT JOIN claims c ON b.billing_id = c.billing_id;

-- Compatibility view for flat-file analytics and simple Power BI imports.
CREATE OR REPLACE VIEW billing_claims AS
SELECT
    b.billing_id,
    b.patient_id,
    b.admission_id AS encounter_id,
    i.insurance_provider,
    b.payment_method,
    c.claim_id,
    b.claim_billing_date,
    b.billed_amount,
    b.paid_amount,
    c.claim_status,
    b.claim_gap,
    c.claim_approved
FROM billing b
LEFT JOIN insurance i ON b.insurance_id = i.insurance_id
LEFT JOIN claims c ON b.billing_id = c.billing_id;
