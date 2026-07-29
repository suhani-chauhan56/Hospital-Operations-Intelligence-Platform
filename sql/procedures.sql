USE hospital_ops;

DELIMITER /
/

CREATE PROCEDURE sp_monthly_operations_report(IN report_year INT, IN report_month INT)
BEGIN
    SELECT
        d.department,
        COUNT(DISTINCT a.admission_id) AS admissions,
        AVG(a.los_days) AS avg_los,
        AVG(a.waiting_time_minutes) AS avg_wait,
        AVG(a.readmitted_30d) AS readmission_rate,
        SUM(COALESCE(b.paid_amount, 0)) AS revenue
    FROM admissions a
    JOIN departments d ON a.department_id = d.department_id
    LEFT JOIN billing b ON a.admission_id = b.admission_id
    WHERE YEAR(a.admit_date) = report_year
      AND MONTH(a.admit_date) = report_month
    GROUP BY d.department
    ORDER BY revenue DESC;
END
/
/

CREATE PROCEDURE sp_patient_360(IN p_patient_id VARCHAR(64))
BEGIN
    SELECT *
    FROM vw_patient_360
    WHERE patient_id = p_patient_id
    ORDER BY admit_date DESC;
END
/
/

USE hospital_ops;

SELECT DATABASE();

CREATE TRIGGER trg_billing_gap_before_insert
BEFORE INSERT ON billing
FOR EACH ROW
BEGIN
    SET NEW.claim_gap = GREATEST(NEW.billed_amount - NEW.paid_amount, 0);
END
/
/

CREATE TRIGGER trg_billing_gap_before_update
BEFORE UPDATE ON billing
FOR EACH ROW
BEGIN
    SET NEW.claim_gap = GREATEST(NEW.billed_amount - NEW.paid_amount, 0);
END
/
/

CREATE TRIGGER trg_claim_approval_before_insert
BEFORE INSERT ON claims
FOR EACH ROW
BEGIN
    SET NEW.claim_approved = CASE WHEN NEW.claim_status = 'Paid' THEN 1 ELSE 0 END;
END
/
/

DELIMITER;