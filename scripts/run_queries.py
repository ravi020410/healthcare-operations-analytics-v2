"""
Runs SQLite-equivalent versions of sql/03_business_analysis_queries.sql
against the real generated dataset, so every number that ends up in the
README / executive report is genuinely computed, not typed in by hand.

(SQLite lacks DATE_TRUNC/STDDEV/WIDTH_BUCKET/EXTRACT(DOW) — the shipped
.sql files use real PostgreSQL syntax; this script translates the same
logic so results are locally reproducible without a Postgres server.)
"""
import sqlite3
import pandas as pd
import statistics
import json

conn = sqlite3.connect("data/hospital.db")

results = {}

# Q1 Executive KPIs
q1 = pd.read_sql("""
SELECT
  COUNT(*) AS total_admissions,
  ROUND(AVG(length_of_stay_days),2) AS avg_los_days,
  ROUND(100.0*SUM(readmitted_30d)/COUNT(*),2) AS readmission_rate_pct,
  ROUND(AVG(wait_minutes),1) AS avg_wait_minutes,
  ROUND(AVG(discharge_efficiency),1) AS avg_discharge_efficiency
FROM admissions
""", conn)
results["Q1_executive_kpis"] = q1.to_dict("records")[0]

# Satisfaction (join)
q1b = pd.read_sql("SELECT ROUND(AVG(satisfaction_score),1) AS avg_satisfaction FROM satisfaction_surveys", conn)
results["Q1_executive_kpis"]["avg_satisfaction"] = q1b.iloc[0,0]

# Billing totals
q1c = pd.read_sql("SELECT ROUND(SUM(gross_charge),0) AS gross_billings FROM billing", conn)
results["Q1_executive_kpis"]["gross_billings"] = q1c.iloc[0,0]

# Q2 Monthly trend + 3mo moving avg
q2 = pd.read_sql("""
SELECT strftime('%Y-%m', admission_date) AS admission_month, COUNT(*) AS admissions_count
FROM admissions GROUP BY 1 ORDER BY 1
""", conn)
q2["mom_change"] = q2["admissions_count"].diff()
q2["moving_avg_3m"] = q2["admissions_count"].rolling(3).mean().round(1)
results["Q2_monthly_trend"] = q2.tail(6).to_dict("records")

# Q3 Wait time outliers (z-score by department, computed in pandas since SQLite lacks STDDEV)
adm = pd.read_sql("SELECT admission_id, department_id, wait_minutes FROM admissions", conn)
dept = pd.read_sql("SELECT department_id, department FROM departments", conn)
adm = adm.merge(dept, on="department_id")
stats = adm.groupby("department")["wait_minutes"].agg(["mean", "std"]).reset_index()
adm = adm.merge(stats, on="department")
adm["z"] = (adm.wait_minutes - adm["mean"]) / adm["std"]
outliers = adm[adm.z > 3].sort_values("z", ascending=False)
results["Q3_wait_outliers_count"] = int(len(outliers))
results["Q3_top_outlier_department"] = outliers.department.mode().iloc[0] if len(outliers) else None

# Q4 Bed utilization
q4 = pd.read_sql("""
SELECT d.department, d.staffed_beds, SUM(a.length_of_stay_days) AS total_bed_days
FROM admissions a JOIN departments d ON a.department_id=d.department_id
GROUP BY d.department, d.staffed_beds
""", conn)
q4["occupancy_rate_pct"] = (q4.total_bed_days / (q4.staffed_beds * 1096) * 100).round(1)
results["Q4_bed_utilization"] = q4.sort_values("occupancy_rate_pct", ascending=False).to_dict("records")

# Q5 Readmission vs discharge efficiency bucket
adm2 = pd.read_sql("SELECT discharge_efficiency, readmitted_30d FROM admissions", conn)
adm2["bucket"] = pd.cut(adm2.discharge_efficiency, bins=[0,20,40,60,80,100],
                          labels=["0-20","20-40","40-60","60-80","80-100"])
q5 = adm2.groupby("bucket", observed=True).agg(
    admissions=("readmitted_30d","count"),
    readmission_rate_pct=("readmitted_30d", lambda x: round(100*x.mean(),2))
).reset_index()
results["Q5_readmission_by_efficiency"] = q5.to_dict("records")

# Q6 Weekend vs weekday wait
adm3 = pd.read_sql("SELECT admission_date, wait_minutes FROM admissions", conn, parse_dates=["admission_date"])
adm3["day_type"] = adm3.admission_date.dt.dayofweek.apply(lambda d: "Weekend" if d>=5 else "Weekday")
q6 = adm3.groupby("day_type").agg(avg_wait_minutes=("wait_minutes","mean"), admissions=("wait_minutes","count")).round(1).reset_index()
results["Q6_weekend_vs_weekday_wait"] = q6.to_dict("records")

# Q7 Financial margin by department
q7 = pd.read_sql("""
SELECT d.department,
  ROUND(SUM(b.gross_charge),0) AS gross_billings,
  ROUND(SUM(b.direct_operating_cost),0) AS operating_cost,
  ROUND(SUM(b.gross_charge - b.direct_operating_cost),0) AS gross_margin,
  ROUND(100.0*SUM(b.gross_charge - b.direct_operating_cost)/SUM(b.gross_charge),1) AS margin_pct
FROM billing b JOIN admissions a ON b.admission_id=a.admission_id
JOIN departments d ON a.department_id=d.department_id
GROUP BY d.department ORDER BY gross_margin DESC
""", conn)
results["Q7_financial_margin_by_dept"] = q7.to_dict("records")

# Q8 Treatment cost drivers
q8 = pd.read_sql("""
SELECT "procedure", COUNT(*) AS times_performed, ROUND(AVG(treatment_cost),2) AS avg_cost
FROM treatments GROUP BY "procedure" ORDER BY avg_cost DESC
""", conn)
results["Q8_treatment_cost_drivers"] = q8.to_dict("records")

# Q9 Satisfaction vs wait band
sat = pd.read_sql("""
SELECT s.satisfaction_score, a.wait_minutes
FROM satisfaction_surveys s JOIN admissions a ON s.admission_id = a.admission_id
""", conn)
sat["wait_band"] = pd.cut(sat.wait_minutes, bins=[-1,15,30,60,10000], labels=["<15 min","15-30 min","30-60 min","60+ min"])
q9 = sat.groupby("wait_band", observed=True).agg(avg_satisfaction=("satisfaction_score","mean"), responses=("satisfaction_score","count")).round(1).reset_index()
results["Q9_satisfaction_by_wait_band"] = q9.to_dict("records")

# Q10 Physician panel load
q10 = pd.read_sql("""
SELECT doc.employment_status,
  COUNT(DISTINCT doc.doctor_id) AS doctor_count,
  COUNT(a.admission_id) AS total_admissions
FROM doctors doc JOIN admissions a ON doc.doctor_id = a.doctor_id
GROUP BY doc.employment_status
""", conn)
q10["admissions_per_doctor"] = (q10.total_admissions / q10.doctor_count).round(1)
results["Q10_physician_panel_load"] = q10.to_dict("records")

with open("reports/query_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(json.dumps(results["Q1_executive_kpis"], indent=2))
print("\nFull results written to reports/query_results.json")
conn.close()
