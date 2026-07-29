CREATE DATABASE IF NOT EXISTS hospital_ops;
USE hospital_ops;

CREATE TABLE patients (
    patient_id VARCHAR(64) PRIMARY KEY,
    age INT NOT NULL,
    gender VARCHAR(16) NOT NULL,
    age_group VARCHAR(16) NOT NULL,
    CHECK (age BETWEEN 0 AND 120)
);

CREATE TABLE departments (
    department_id INT PRIMARY KEY,
    department VARCHAR(80) UNIQUE NOT NULL
);

CREATE TABLE doctors (
    doctor_id VARCHAR(32) PRIMARY KEY,
    department VARCHAR(80) NOT NULL,
    doctor_experience INT NOT NULL,
    department_id INT NOT NULL,
    CONSTRAINT fk_doctor_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE admissions (
    admission_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    doctor_id VARCHAR(32) NOT NULL,
    department_id INT NOT NULL,
    hospital_id VARCHAR(64) NOT NULL,
    admit_date DATE NOT NULL,
    discharge_date DATE,
    los_days INT,
    admit_type VARCHAR(32),
    ward_type VARCHAR(32),
    discharge_type VARCHAR(32),
    readmitted_30d TINYINT NOT NULL DEFAULT 0,
    readmitted_7d TINYINT NOT NULL DEFAULT 0,
    waiting_time_minutes DECIMAL(8,2),
    CONSTRAINT fk_admission_patient
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    CONSTRAINT fk_admission_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    CONSTRAINT fk_admission_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id),
    CHECK (discharge_date IS NULL OR discharge_date >= admit_date)
);

CREATE TABLE diagnoses (
    admission_id VARCHAR(64) PRIMARY KEY,
    charlson_index DECIMAL(6,2),
    disease_severity_score DECIMAL(8,2),
    CONSTRAINT fk_diagnosis_admission
        FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE procedures (
    admission_id VARCHAR(64) PRIMARY KEY,
    num_procedures INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_procedure_admission
        FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE medicines (
    admission_id VARCHAR(64),
    medicine_code VARCHAR(16),
    medicine_count INT NOT NULL DEFAULT 0,
    average_medicine_cost DECIMAL(12,2),
    PRIMARY KEY (admission_id, medicine_code),
    CONSTRAINT fk_medicine_admission
        FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE labs (
    admission_id VARCHAR(64) PRIMARY KEY,
    hba1c DECIMAL(8,2),
    creatinine DECIMAL(8,2),
    haemoglobin DECIMAL(8,2),
    systolic_bp DECIMAL(8,2),
    lab_abnormality_score DECIMAL(8,2),
    CONSTRAINT fk_lab_admission
        FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

CREATE TABLE insurance (
    insurance_id INT PRIMARY KEY,
    insurance_provider VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE billing (
    billing_id VARCHAR(32) PRIMARY KEY,
    admission_id VARCHAR(64) NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    insurance_id INT,
    payment_method VARCHAR(32),
    claim_billing_date DATETIME,
    billed_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    paid_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
    claim_gap DECIMAL(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_billing_admission
        FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
    CONSTRAINT fk_billing_patient
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    CONSTRAINT fk_billing_insurance
        FOREIGN KEY (insurance_id) REFERENCES insurance(insurance_id)
);

CREATE TABLE claims (
    claim_line_id VARCHAR(48) PRIMARY KEY,
    claim_id VARCHAR(48) NOT NULL,
    billing_id VARCHAR(32) NOT NULL,
    insurance_id INT,
    claim_status VARCHAR(32) NOT NULL,
    claim_approved TINYINT NOT NULL DEFAULT 0,
    source_patient_id VARCHAR(64),
    source_encounter_id VARCHAR(64),
    linkage_method VARCHAR(80),
    CONSTRAINT fk_claim_billing
        FOREIGN KEY (billing_id) REFERENCES billing(billing_id),
    CONSTRAINT fk_claim_insurance
        FOREIGN KEY (insurance_id) REFERENCES insurance(insurance_id)
);

CREATE TABLE appointments (
    appointment_id VARCHAR(80) PRIMARY KEY,
    admission_id VARCHAR(64),
    patient_id VARCHAR(64) NOT NULL,
    doctor_id VARCHAR(32) NOT NULL,
    department_id INT NOT NULL,
    admit_date DATE NOT NULL,
    appointment_status VARCHAR(24) NOT NULL,
    scheduled_time TIME,
    CONSTRAINT fk_appointment_admission
        FOREIGN KEY (admission_id) REFERENCES admissions(admission_id),
    CONSTRAINT fk_appointment_patient
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    CONSTRAINT fk_appointment_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    CONSTRAINT fk_appointment_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE command_center_kpis (
    as_of_date DATE PRIMARY KEY,
    patients_today INT NOT NULL,
    occupancy_pct DECIMAL(8,3) NOT NULL,
    occupied_beds INT NOT NULL,
    emergency_wait_minutes DECIMAL(8,3),
    critical_patients INT NOT NULL,
    doctor_utilization_pct DECIMAL(8,3),
    hospital_efficiency_score DECIMAL(8,3) NOT NULL,
    capacity_assumption INT NOT NULL,
    snapshot_provenance VARCHAR(120) NOT NULL
);

CREATE TABLE hospital_efficiency_scores (
    scope_type VARCHAR(24) NOT NULL,
    scope_name VARCHAR(80) NOT NULL,
    efficiency_score DECIMAL(8,3) NOT NULL,
    patient_outcome_score DECIMAL(8,3),
    collection_score DECIMAL(8,3),
    capacity_balance_score DECIMAL(8,3),
    patient_flow_score DECIMAL(8,3),
    provenance VARCHAR(120) NOT NULL,
    PRIMARY KEY (scope_type, scope_name)
);

CREATE TABLE emergency_forecast (
    forecast_date DATE PRIMARY KEY,
    forecast_emergency_patients DECIMAL(10,3) NOT NULL,
    method VARCHAR(120) NOT NULL,
    provenance VARCHAR(120) NOT NULL
);

CREATE TABLE operational_forecast_summary (
    forecast_start_date DATE PRIMARY KEY,
    forecast_end_date DATE NOT NULL,
    emergency_patients INT NOT NULL,
    emergency_growth_pct DECIMAL(10,3),
    additional_beds INT NOT NULL,
    peak_day VARCHAR(16) NOT NULL,
    peak_day_volume INT NOT NULL,
    method VARCHAR(160) NOT NULL,
    peak_hour_status VARCHAR(80) NOT NULL
);

CREATE TABLE operational_recommendations (
    priority VARCHAR(8) NOT NULL,
    title VARCHAR(80) PRIMARY KEY,
    signal VARCHAR(160) NOT NULL,
    action VARCHAR(320) NOT NULL,
    owner VARCHAR(80) NOT NULL,
    timeframe VARCHAR(32) NOT NULL,
    success_measure VARCHAR(240) NOT NULL,
    reliability VARCHAR(80) NOT NULL
);

CREATE INDEX idx_admissions_patient_date ON admissions(patient_id, admit_date);
CREATE INDEX idx_admissions_department_date ON admissions(department_id, admit_date);
CREATE INDEX idx_admissions_doctor ON admissions(doctor_id);
CREATE INDEX idx_admissions_hospital_date ON admissions(hospital_id, admit_date);
CREATE INDEX idx_billing_patient_date ON billing(patient_id, claim_billing_date);
CREATE INDEX idx_billing_admission ON billing(admission_id);
CREATE INDEX idx_claim_status ON claims(claim_status);
CREATE INDEX idx_claim_insurance ON claims(insurance_id);
CREATE INDEX idx_appointments_doctor_date ON appointments(doctor_id, admit_date);
CREATE INDEX idx_efficiency_scope_score
    ON hospital_efficiency_scores(scope_type, efficiency_score);
CREATE INDEX idx_recommendations_priority
    ON operational_recommendations(priority);
