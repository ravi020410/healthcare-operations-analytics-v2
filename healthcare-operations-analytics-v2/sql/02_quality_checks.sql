-- Data Quality Checks
-- Run against the raw load before the cleaning step, to document exactly
-- what was wrong with the source extract and how it was resolved.

-- 1. Duplicate admission rows (system double-entry bug)
SELECT patient_id, doctor_id, department_id, admission_date, admission_type, COUNT(*) AS occurrences
FROM admissions_raw
GROUP BY patient_id, doctor_id, department_id, admission_date, admission_type
HAVING COUNT(*) > 1;

-- 2. Negative or zero wait times (triage clock-sync bug)
SELECT admission_id, wait_minutes
FROM admissions_raw
WHERE wait_minutes <= 0;

-- 3. Department name casing inconsistency from legacy system merge
SELECT DISTINCT department_raw_text_original
FROM admissions_raw
ORDER BY 1;

-- 4. Missing patient intake fields
SELECT
    SUM(CASE WHEN insurance_type IS NULL THEN 1 ELSE 0 END) AS missing_insurance,
    SUM(CASE WHEN state IS NULL THEN 1 ELSE 0 END) AS missing_state,
    COUNT(*) AS total_patients
FROM patients;

-- 5. Orphan billing records (billing row with no matching admission — referential check)
SELECT b.billing_id
FROM billing b
LEFT JOIN admissions a ON b.admission_id = a.admission_id
WHERE a.admission_id IS NULL;
