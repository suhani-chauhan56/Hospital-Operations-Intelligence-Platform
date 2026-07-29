USE hospital_ops;

SELECT DATABASE();

-- 01 Executive KPIs
SELECT * FROM vw_executive_kpis;

-- 02 Department ranking by admissions
SELECT department, admissions
FROM vw_department_kpis
ORDER BY admissions DESC;

-- 03 Department ranking by revenue
SELECT department, revenue
FROM vw_department_kpis
ORDER BY revenue DESC;

-- 04 Department readmission rate
SELECT department, readmission_rate
FROM vw_department_kpis
ORDER BY readmission_rate DESC;

-- 05 Average waiting time by department
SELECT department, average_wait
FROM vw_department_kpis
ORDER BY average_wait DESC;

-- 06 Average length of stay by department
SELECT department, average_los
FROM vw_department_kpis
ORDER BY average_los DESC;

-- 07 Doctor utilization ranking
SELECT * FROM vw_doctor_utilization ORDER BY admissions DESC;

-- 08 High readmission doctors
SELECT
    doctor_id,
    department,
    admissions,
    readmission_rate
FROM vw_doctor_utilization
WHERE
    admissions >= 100
ORDER BY readmission_rate DESC;

-- 09 Monthly admissions
SELECT DATE_FORMAT(admit_date, '%Y-%m-01') AS month_start, COUNT(*) AS admissions
FROM admissions
GROUP BY
    DATE_FORMAT(admit_date, '%Y-%m-01')
ORDER BY month_start;

-- 10 Quarterly admissions growth
WITH
    q AS (
        SELECT YEAR(admit_date) AS yr, QUARTER(admit_date) AS qtr, COUNT(*) AS admissions
        FROM admissions
        GROUP BY
            YEAR(admit_date),
            QUARTER(admit_date)
    )
SELECT
    yr,
    qtr,
    admissions,
    admissions - LAG(admissions) OVER (
        ORDER BY yr, qtr
    ) AS admissions_growth
FROM q;

-- 11 Monthly revenue
SELECT month_start, SUM(paid_revenue) AS paid_revenue
FROM vw_monthly_revenue
GROUP BY
    month_start
ORDER BY month_start;

-- 12 Quarterly revenue growth
WITH
    q AS (
        SELECT YEAR(claim_billing_date) AS yr, QUARTER(claim_billing_date) AS qtr, SUM(paid_amount) AS revenue
        FROM billing_claims
        GROUP BY
            YEAR(claim_billing_date),
            QUARTER(claim_billing_date)
    )
SELECT
    yr,
    qtr,
    revenue,
    revenue - LAG(revenue) OVER (
        ORDER BY yr, qtr
    ) AS revenue_growth
FROM q;

-- 13 Insurance claim success by provider
SELECT
    insurance_provider,
    AVG(claim_approved) AS approval_ratio,
    COUNT(*) AS claims
FROM billing_claims
GROUP BY
    insurance_provider
ORDER BY approval_ratio DESC;

-- 14 Denied claim value
SELECT
    insurance_provider,
    SUM(billed_amount) AS denied_value
FROM billing_claims
WHERE
    claim_status = 'Denied'
GROUP BY
    insurance_provider
ORDER BY denied_value DESC;

-- 15 Payment method mix
SELECT
    payment_method,
    COUNT(*) AS claims,
    SUM(paid_amount) AS paid_amount
FROM billing_claims
GROUP BY
    payment_method
ORDER BY paid_amount DESC;

-- 16 Average claim gap
SELECT insurance_provider, AVG(claim_gap) AS avg_gap
FROM billing_claims
GROUP BY
    insurance_provider
ORDER BY avg_gap DESC;

-- 17 Patient revisit frequency
SELECT patient_id, COUNT(*) AS visits
FROM admissions
GROUP BY
    patient_id
HAVING
    COUNT(*) > 1
ORDER BY visits DESC;

-- 18 Readmission by admit type
SELECT
    admit_type,
    AVG(readmitted_30d) AS readmission_rate,
    COUNT(*) admissions
FROM admissions
GROUP BY
    admit_type;

-- 19 Readmission by ward
SELECT
    ward_type,
    AVG(readmitted_30d) AS readmission_rate,
    COUNT(*) admissions
FROM admissions
GROUP BY
    ward_type;

-- 20 Seven-day readmission rate
SELECT AVG(readmitted_7d) AS readmitted_7d_rate FROM admissions;

-- 21 Bed occupancy trend
SELECT * FROM vw_daily_occupancy ORDER BY admit_date;

-- 22 Weekend occupancy
SELECT DAYNAME(admit_date) AS day_name, AVG(occupancy_pct) AS avg_occupancy
FROM vw_daily_occupancy
GROUP BY
    DAYNAME(admit_date),
    DAYOFWEEK(admit_date)
ORDER BY DAYOFWEEK(admit_date);

-- 23 Peak waiting day
SELECT admit_date, AVG(waiting_time_minutes) AS avg_wait
FROM admissions
GROUP BY
    admit_date
ORDER BY avg_wait DESC
LIMIT 20;

-- 24 Emergency waiting time
SELECT department_id, AVG(waiting_time_minutes) AS emergency_wait
FROM admissions
WHERE
    admit_type = 'Emergency'
GROUP BY
    department_id
ORDER BY emergency_wait DESC;

-- 25 LOS distribution by admit type
SELECT
    admit_type,
    AVG(los_days) avg_los,
    MIN(los_days) min_los,
    MAX(los_days) max_los
FROM admissions
GROUP BY
    admit_type;

-- 26 High LOS patients
SELECT
    patient_id,
    admission_id,
    los_days
FROM admissions
ORDER BY los_days DESC
LIMIT 50;

-- 27 Comorbidity severity by department
SELECT
    d.department,
    AVG(di.charlson_index) AS avg_charlson,
    AVG(di.disease_severity_score) AS avg_severity
FROM
    diagnoses di
    JOIN admissions a ON di.admission_id = a.admission_id
    JOIN departments d ON a.department_id = d.department_id
GROUP BY
    d.department
ORDER BY avg_severity DESC;

-- 28 Lab abnormality by readmission
SELECT a.readmitted_30d, AVG(l.lab_abnormality_score) AS avg_lab_abnormality
FROM admissions a
    JOIN labs l ON a.admission_id = l.admission_id
GROUP BY
    a.readmitted_30d;

-- 29 Medicine usage
SELECT
    medicine_code,
    SUM(medicine_count) AS total_usage,
    AVG(average_medicine_cost) AS avg_cost
FROM medicines
GROUP BY
    medicine_code
ORDER BY total_usage DESC;

-- 30 Procedure volume by department
SELECT d.department, SUM(p.num_procedures) AS procedures
FROM
    procedures p
    JOIN admissions a ON p.admission_id = a.admission_id
    JOIN departments d ON a.department_id = d.department_id
GROUP BY
    d.department
ORDER BY procedures DESC;

-- 31 Revenue per patient
SELECT patient_id, SUM(paid_amount) AS revenue
FROM billing_claims
GROUP BY
    patient_id
ORDER BY revenue DESC
LIMIT 50;

-- 32 Revenue per admission proxy by department
SELECT
    department,
    revenue / NULLIF(admissions, 0) AS revenue_per_admission
FROM vw_department_kpis
ORDER BY revenue_per_admission DESC;

-- 33 Top hospitals by admissions
SELECT department_id, COUNT(*) admissions
FROM admissions
GROUP BY
    department_id
ORDER BY admissions DESC;

-- 34 Discharge outcomes
SELECT
    discharge_type,
    COUNT(*) AS admissions,
    AVG(readmitted_30d) AS readmission_rate
FROM admissions
GROUP BY
    discharge_type;

-- 35 Claims by status
SELECT
    claim_status,
    COUNT(*) claims,
    SUM(billed_amount) billed,
    SUM(paid_amount) paid
FROM billing_claims
GROUP BY
    claim_status;

-- 36 Claim aging
SELECT DATE(claim_billing_date) claim_date, COUNT(*) claims, SUM(paid_amount) paid
FROM billing_claims
GROUP BY
    DATE(claim_billing_date);

-- 37 CTE high risk departments
WITH
    dept AS (
        SELECT d.department, AVG(a.readmitted_30d) readmit, AVG(a.waiting_time_minutes) wait_time
        FROM admissions a
            JOIN departments d ON a.department_id = d.department_id
        GROUP BY
            d.department
    )
SELECT *
FROM dept
WHERE
    readmit > (
        SELECT AVG(readmitted_30d)
        FROM admissions
    )
ORDER BY wait_time DESC;

-- 38 Window rank doctors
SELECT
    doctor_id,
    department,
    admissions,
    RANK() OVER (
        PARTITION BY
            department
        ORDER BY admissions DESC
    ) AS department_rank
FROM vw_doctor_utilization;

-- 39 Running admissions
SELECT
    admit_date,
    COUNT(*) admissions,
    SUM(COUNT(*)) OVER (
        ORDER BY admit_date
    ) AS running_admissions
FROM admissions
GROUP BY
    admit_date
ORDER BY admit_date;

-- 40 Running revenue
SELECT
    DATE(claim_billing_date) billing_date,
    SUM(paid_amount) paid,
    SUM(SUM(paid_amount)) OVER (
        ORDER BY DATE(claim_billing_date)
    ) AS running_revenue
FROM billing_claims
GROUP BY
    DATE(claim_billing_date);

-- 41 Department percentile wait
SELECT d.department, a.admission_id, a.waiting_time_minutes, CUME_DIST() OVER (
        PARTITION BY
            d.department
        ORDER BY a.waiting_time_minutes
    ) AS wait_percentile
FROM admissions a
    JOIN departments d ON a.department_id = d.department_id;

-- 42 Patients with multiple high-risk signals
SELECT a.patient_id, COUNT(*) visits, AVG(di.disease_severity_score) severity, AVG(a.readmitted_30d) readmit
FROM admissions a
    JOIN diagnoses di ON a.admission_id = di.admission_id
GROUP BY
    a.patient_id
HAVING
    visits > 1
    AND severity >= 4
ORDER BY readmit DESC;

-- 43 Claims approval by month
SELECT DATE_FORMAT(
        claim_billing_date, '%Y-%m-01'
    ) month_start, AVG(claim_approved) approval_ratio
FROM billing_claims
GROUP BY
    DATE_FORMAT(
        claim_billing_date,
        '%Y-%m-01'
    )
ORDER BY month_start;

-- 44 Average paid amount by provider
SELECT
    insurance_provider,
    AVG(paid_amount) avg_paid,
    SUM(paid_amount) total_paid
FROM billing_claims
GROUP BY
    insurance_provider;

-- 45 High waiting admissions
SELECT
    admission_id,
    patient_id,
    waiting_time_minutes
FROM admissions
ORDER BY waiting_time_minutes DESC
LIMIT 100;

-- 46 Same patient readmission gap
WITH
    visits AS (
        SELECT
            patient_id,
            admit_date,
            LAG(discharge_date) OVER (
                PARTITION BY
                    patient_id
                ORDER BY admit_date
            ) prev_discharge
        FROM admissions
    )
SELECT
    patient_id,
    admit_date,
    prev_discharge,
    DATEDIFF(admit_date, prev_discharge) AS gap_days
FROM visits
WHERE
    prev_discharge IS NOT NULL
ORDER BY gap_days;

-- 47 Revenue leakage
SELECT insurance_provider, SUM(billed_amount - paid_amount) AS leakage
FROM billing_claims
GROUP BY
    insurance_provider
ORDER BY leakage DESC;

-- 48 Department contribution to revenue
SELECT
    department,
    revenue,
    revenue / SUM(revenue) OVER () AS revenue_share
FROM vw_department_kpis
ORDER BY revenue_share DESC;

-- 49 Admission mix
SELECT
    admit_type,
    COUNT(*) admissions,
    COUNT(*) / SUM(COUNT(*)) OVER () AS admission_share
FROM admissions
GROUP BY
    admit_type;

-- 50 Ward mix
SELECT
    ward_type,
    COUNT(*) admissions,
    COUNT(*) / SUM(COUNT(*)) OVER () AS ward_share
FROM admissions
GROUP BY
    ward_type;

-- 51 High occupancy alert days
SELECT admit_date, occupancy_pct
FROM vw_daily_occupancy
WHERE
    occupancy_pct >= 90
ORDER BY admit_date;

-- 52 Average daily discharge volume
SELECT discharge_date, COUNT(*) discharges
FROM admissions
GROUP BY
    discharge_date
ORDER BY discharge_date;

-- 53 Doctor revenue rank
SELECT
    doctor_id,
    department,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) revenue_rank
FROM vw_doctor_utilization;

-- 54 Department wait versus hospital average
SELECT
    department,
    average_wait,
    average_wait - (
        SELECT AVG(waiting_time_minutes)
        FROM admissions
    ) AS wait_gap
FROM vw_department_kpis
ORDER BY wait_gap DESC;

-- 55 Readmission by age group
SELECT
    p.age_group,
    AVG(a.readmitted_30d) readmission_rate,
    COUNT(*) admissions
FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
GROUP BY
    p.age_group
ORDER BY readmission_rate DESC;

-- 56 Gender utilization
SELECT
    p.gender,
    COUNT(*) admissions,
    AVG(a.los_days) avg_los,
    AVG(a.readmitted_30d) readmit
FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
GROUP BY
    p.gender;

-- 57 Claims without payment
SELECT *
FROM billing_claims
WHERE
    paid_amount = 0
ORDER BY billed_amount DESC
LIMIT 100;

-- 58 Procedure intensity and readmission
SELECT
    p.num_procedures,
    AVG(a.readmitted_30d) readmission_rate,
    COUNT(*) admissions
FROM procedures p
    JOIN admissions a ON p.admission_id = a.admission_id
GROUP BY
    p.num_procedures
ORDER BY p.num_procedures;

-- 59 LOS and billing bucket
SELECT
    CASE
        WHEN a.los_days <= 2 THEN 'Short'
        WHEN a.los_days <= 7 THEN 'Medium'
        ELSE 'Long'
    END AS los_bucket,
    AVG(b.paid_amount) avg_paid,
    COUNT(*) rows_count
FROM
    admissions a
    LEFT JOIN billing_claims b ON a.admission_id = b.encounter_id
GROUP BY
    los_bucket;

-- 60 Daily patient flow
SELECT x.flow_date, SUM(x.admits) admits, SUM(x.discharges) discharges
FROM (
        SELECT
            admit_date AS flow_date, COUNT(*) admits, 0 discharges
        FROM admissions
        GROUP BY
            admit_date
        UNION ALL
        SELECT
            discharge_date AS flow_date, 0 admits, COUNT(*) discharges
        FROM admissions
        GROUP BY
            discharge_date
    ) x
GROUP BY
    x.flow_date
ORDER BY x.flow_date;

-- 61 Hospital command center snapshot
SELECT *
FROM vw_command_center;

-- 62 Department efficiency ranking
SELECT
    scope_name AS department,
    efficiency_score,
    patient_outcome_score,
    capacity_balance_score,
    patient_flow_score,
    efficiency_rank
FROM vw_efficiency_ranking
WHERE scope_type = 'department'
ORDER BY efficiency_rank;

-- 63 Next-week emergency forecast
SELECT
    forecast_date,
    forecast_emergency_patients,
    method,
    provenance
FROM emergency_forecast
ORDER BY forecast_date;

-- 64 Accountable operational recommendation queue
SELECT
    priority,
    title,
    signal,
    action,
    owner,
    timeframe,
    success_measure,
    reliability
FROM vw_operational_action_queue
ORDER BY priority_order, title;

-- 65 Efficiency components below 70
SELECT
    scope_type,
    scope_name,
    component,
    score
FROM (
    SELECT
        scope_type,
        scope_name,
        'Patient outcomes' AS component,
        patient_outcome_score AS score
    FROM hospital_efficiency_scores
    UNION ALL
    SELECT
        scope_type,
        scope_name,
        'Capacity balance',
        capacity_balance_score
    FROM hospital_efficiency_scores
    UNION ALL
    SELECT
        scope_type,
        scope_name,
        'Patient flow',
        patient_flow_score
    FROM hospital_efficiency_scores
) components
WHERE score < 70
ORDER BY score;
