-- Healthcare Operations Analytics — PostgreSQL reference schema
-- PostgreSQL 14+
-- Star-schema style: admissions is the central fact table, joined out to
-- patients / doctors / departments (dimensions) and billing / treatments /
-- satisfaction_surveys (secondary facts). The local SQLite database is loaded from
-- data/cleaned/admissions_cleaned.csv for admissions and raw supporting tables.
-- SQLite tables are materialized by scripts/load_db.py; relationship integrity is
-- verified by scripts/validate_project.py rather than claiming this PostgreSQL DDL
-- is executed verbatim in SQLite.

CREATE SCHEMA IF NOT EXISTS analytics;
SET search_path TO analytics;

CREATE TABLE departments (
    department_id   SMALLINT PRIMARY KEY,
    department      TEXT NOT NULL,
    staffed_beds    SMALLINT NOT NULL CHECK (staffed_beds > 0)
);

CREATE TABLE doctors (
    doctor_id           INTEGER PRIMARY KEY,
    doctor_name         TEXT NOT NULL,
    department_id       SMALLINT REFERENCES departments(department_id),
    employment_status   TEXT CHECK (employment_status IN ('Full-Time','Part-Time','Contract')),
    years_experience    SMALLINT CHECK (years_experience >= 0)
);

CREATE TABLE patients (
    patient_id      INTEGER PRIMARY KEY,
    patient_name    TEXT NOT NULL,
    date_of_birth   DATE,
    gender          TEXT,
    state           TEXT,             -- ~2% NULL in source: intake gap
    insurance_type  TEXT              -- ~4% NULL in source: intake gap
);

CREATE TABLE admissions (
    admission_id            INTEGER PRIMARY KEY,
    patient_id               INTEGER REFERENCES patients(patient_id),
    doctor_id                 INTEGER REFERENCES doctors(doctor_id),
    department_id             SMALLINT REFERENCES departments(department_id),
    admission_date             TIMESTAMP NOT NULL,
    discharge_date              TIMESTAMP,
    admission_type              TEXT CHECK (admission_type IN
                                  ('Emergency','Urgent','Elective','Newborn','Trauma')),
    severity_score               NUMERIC(3,1) CHECK (severity_score BETWEEN 1 AND 10),
    length_of_stay_days           NUMERIC(4,1),
    wait_minutes                   INTEGER,      -- cleaned: negative clock-sync values corrected pre-load
    discharge_efficiency            NUMERIC(4,1), -- 0-100, lower = rushed discharge
    readmitted_30d                   SMALLINT CHECK (readmitted_30d IN (0,1)),
    department_raw_text_original      TEXT       -- kept for audit trail; NOT used in joins
);

CREATE TABLE billing (
    billing_id              INTEGER PRIMARY KEY,
    admission_id             INTEGER REFERENCES admissions(admission_id),
    gross_charge               NUMERIC(12,2),
    insurance_payment           NUMERIC(12,2),
    patient_out_of_pocket        NUMERIC(12,2),
    direct_operating_cost         NUMERIC(12,2)
);

CREATE TABLE satisfaction_surveys (
    survey_id                      INTEGER PRIMARY KEY,
    admission_id                    INTEGER REFERENCES admissions(admission_id),
    satisfaction_score               NUMERIC(4,1) CHECK (satisfaction_score BETWEEN 0 AND 100),
    response_days_after_discharge     SMALLINT
);

CREATE TABLE treatments (
    treatment_id      INTEGER PRIMARY KEY,
    admission_id       INTEGER REFERENCES admissions(admission_id),
    procedure           TEXT NOT NULL,
    treatment_cost        NUMERIC(10,2)
);

CREATE INDEX idx_admissions_date ON admissions(admission_date);
CREATE INDEX idx_admissions_dept ON admissions(department_id);
CREATE INDEX idx_admissions_patient ON admissions(patient_id);
CREATE INDEX idx_billing_admission ON billing(admission_id);
CREATE INDEX idx_treatments_admission ON treatments(admission_id);
