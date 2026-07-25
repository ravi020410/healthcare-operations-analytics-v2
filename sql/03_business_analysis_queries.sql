-- Advanced Business Analysis Queries
-- PostgreSQL 14+. Executed against the cleaned `analytics` schema.
-- Every result referenced in reports/executive_report.md was produced by
-- running these queries against the actual dataset (see scripts/run_queries.py).

-- =====================================================================
-- Q1. Core Executive KPI Scorecard
-- =====================================================================
SELECT
    COUNT(*)                                                   AS total_admissions,
    ROUND(AVG(length_of_stay_days), 2)                          AS avg_los_days,
    ROUND(100.0 * SUM(readmitted_30d) / COUNT(*), 2)             AS readmission_rate_pct,
    ROUND(AVG(wait_minutes), 1)                                   AS avg_wait_minutes,
    ROUND(AVG(discharge_efficiency), 1)                            AS avg_discharge_efficiency
FROM admissions;

-- =====================================================================
-- Q2. 3-Month Moving Average of Monthly Admissions (CTE + window LAG)
-- =====================================================================
WITH monthly_counts AS (
    SELECT DATE_TRUNC('month', admission_date)::DATE AS admission_month,
           COUNT(admission_id) AS admissions_count
    FROM admissions
    GROUP BY 1
)
SELECT
    admission_month,
    admissions_count,
    admissions_count - LAG(admissions_count) OVER (ORDER BY admission_month) AS mom_change,
    ROUND(AVG(admissions_count) OVER (
        ORDER BY admission_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 1) AS moving_avg_3m
FROM monthly_counts
ORDER BY admission_month;

-- =====================================================================
-- Q3. Statistical Triage Wait-Time Outliers (Z-score > 3, per department)
-- =====================================================================
WITH wait_stats AS (
    SELECT department_id, AVG(wait_minutes) AS avg_wait, STDDEV(wait_minutes) AS std_wait
    FROM admissions
    GROUP BY 1
)
SELECT a.admission_id, d.department, a.wait_minutes,
       ROUND((a.wait_minutes - ws.avg_wait) / NULLIF(ws.std_wait, 0), 2) AS z_score
FROM admissions a
JOIN departments d ON a.department_id = d.department_id
JOIN wait_stats ws ON a.department_id = ws.department_id
WHERE a.wait_minutes > (ws.avg_wait + 3 * ws.std_wait)
ORDER BY z_score DESC;

-- =====================================================================
-- Q4. Bed Utilization Rate by Department (concurrent occupancy proxy)
-- =====================================================================
SELECT
    d.department,
    d.staffed_beds,
    ROUND(SUM(a.length_of_stay_days) / (d.staffed_beds * 1096.0) * 100, 1) AS occupancy_rate_pct
    -- 1096 = days across the 3-year (2023-2025) observation window
FROM admissions a
JOIN departments d ON a.department_id = d.department_id
GROUP BY d.department, d.staffed_beds
ORDER BY occupancy_rate_pct DESC;

-- =====================================================================
-- Q5. Readmission Rate vs. Discharge Efficiency Bucket
-- (Directly supports the "rushed discharge → readmission" finding)
-- =====================================================================
SELECT
    WIDTH_BUCKET(discharge_efficiency, 0, 100, 5) AS efficiency_bucket,
    COUNT(*)                                       AS admissions,
    ROUND(100.0 * SUM(readmitted_30d) / COUNT(*), 2) AS readmission_rate_pct
FROM admissions
GROUP BY 1
ORDER BY 1;

-- =====================================================================
-- Q6. Weekend vs. Weekday Wait Time Comparison
-- =====================================================================
SELECT
    CASE WHEN EXTRACT(DOW FROM admission_date) IN (0,6) THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    ROUND(AVG(wait_minutes), 1) AS avg_wait_minutes,
    COUNT(*) AS admissions
FROM admissions
GROUP BY 1;

-- =====================================================================
-- Q7. Financial Leakage: Gross Charge vs. Direct Operating Cost by Department
-- =====================================================================
SELECT
    d.department,
    ROUND(SUM(b.gross_charge), 0)          AS gross_billings,
    ROUND(SUM(b.direct_operating_cost), 0)  AS operating_cost,
    ROUND(SUM(b.gross_charge - b.direct_operating_cost), 0) AS gross_margin,
    ROUND(100.0 * SUM(b.gross_charge - b.direct_operating_cost) / NULLIF(SUM(b.gross_charge),0), 1) AS margin_pct
FROM billing b
JOIN admissions a ON b.admission_id = a.admission_id
JOIN departments d ON a.department_id = d.department_id
GROUP BY d.department
ORDER BY gross_margin DESC;

-- =====================================================================
-- Q8. Top Cost Drivers: Highest Average Treatment Cost by Procedure
-- =====================================================================
SELECT procedure, COUNT(*) AS times_performed, ROUND(AVG(treatment_cost), 2) AS avg_cost
FROM treatments
GROUP BY procedure
ORDER BY avg_cost DESC;

-- =====================================================================
-- Q9. Patient Satisfaction vs. Wait Time Correlation Bands
-- =====================================================================
SELECT
    CASE
        WHEN a.wait_minutes < 15 THEN '<15 min'
        WHEN a.wait_minutes < 30 THEN '15-30 min'
        WHEN a.wait_minutes < 60 THEN '30-60 min'
        ELSE '60+ min'
    END AS wait_band,
    ROUND(AVG(s.satisfaction_score), 1) AS avg_satisfaction,
    COUNT(*) AS responses
FROM satisfaction_surveys s
JOIN admissions a ON s.admission_id = a.admission_id
GROUP BY 1
ORDER BY MIN(a.wait_minutes);

-- =====================================================================
-- Q10. Physician Panel Load: Admissions per Doctor, Full-Time vs Contract
-- =====================================================================
SELECT
    doc.employment_status,
    COUNT(DISTINCT doc.doctor_id) AS doctor_count,
    COUNT(a.admission_id) AS total_admissions,
    ROUND(1.0 * COUNT(a.admission_id) / COUNT(DISTINCT doc.doctor_id), 1) AS admissions_per_doctor
FROM doctors doc
JOIN admissions a ON doc.doctor_id = a.doctor_id
GROUP BY doc.employment_status
ORDER BY admissions_per_doctor DESC;
