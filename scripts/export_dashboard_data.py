import sqlite3
import pandas as pd
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
conn = sqlite3.connect(ROOT / "data" / "hospital.db")

out = {}

kpi = pd.read_sql("""
SELECT COUNT(*) AS total_admissions,
       ROUND(AVG(length_of_stay_days),2) AS avg_los_days,
       ROUND(100.0*SUM(readmitted_30d)/COUNT(*),2) AS readmission_rate_pct,
       ROUND(AVG(wait_minutes),1) AS avg_wait_minutes,
       ROUND(AVG(discharge_efficiency),1) AS avg_discharge_efficiency
FROM admissions""", conn).to_dict("records")[0]
kpi["avg_satisfaction"] = round(pd.read_sql("SELECT AVG(satisfaction_score) s FROM satisfaction_surveys", conn).iloc[0,0], 1)
kpi["gross_billings"] = round(pd.read_sql("SELECT SUM(gross_charge) s FROM billing", conn).iloc[0,0], 0)
out["kpi"] = kpi

monthly = pd.read_sql("""
SELECT strftime('%Y-%m', admission_date) AS month, COUNT(*) AS admissions
FROM admissions GROUP BY 1 ORDER BY 1""", conn)
out["monthly_trend"] = monthly.to_dict("records")

dept = pd.read_sql("""
SELECT d.department, COUNT(*) AS admissions, ROUND(AVG(a.length_of_stay_days),2) AS avg_los,
       ROUND(100.0*SUM(a.readmitted_30d)/COUNT(*),2) AS readmission_rate_pct
FROM admissions a JOIN departments d ON a.department_id=d.department_id
GROUP BY d.department ORDER BY admissions DESC""", conn)
out["by_department"] = dept.to_dict("records")

fin = pd.read_sql("""
SELECT d.department,
  ROUND(SUM(b.gross_charge),0) AS gross_billings,
  ROUND(SUM(b.gross_charge-b.direct_operating_cost),0) AS gross_margin
FROM billing b JOIN admissions a ON b.admission_id=a.admission_id
JOIN departments d ON a.department_id=d.department_id
GROUP BY d.department ORDER BY gross_margin DESC""", conn)
out["financials_by_department"] = fin.to_dict("records")

admtype = pd.read_sql("""
SELECT admission_type, COUNT(*) AS admissions
FROM admissions GROUP BY admission_type ORDER BY admissions DESC""", conn)
out["by_admission_type"] = admtype.to_dict("records")

insurance = pd.read_sql("""
SELECT COALESCE(insurance_type,'Unknown') AS insurance_type, COUNT(*) AS patients
FROM patients GROUP BY 1 ORDER BY patients DESC""", conn)
out["by_insurance"] = insurance.to_dict("records")

with (ROOT / "dashboards" / "dashboard_data.json").open("w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, default=str)

# The standalone dashboard intentionally embeds its data so it can open without a
# server. Keep that embedded payload synchronized with the JSON export.
html_path = ROOT / "dashboards" / "dashboard.html"
html = html_path.read_text(encoding="utf-8")
payload = json.dumps(out, default=str)
updated, replacements = re.subn(r"const DATA = .*?;\r?\n", f"const DATA = {payload};\n", html, count=1)
if replacements != 1:
    raise RuntimeError("Could not locate the embedded dashboard DATA payload")
html_path.write_text(updated, encoding="utf-8")

print("KPIs:", out["kpi"])
print(f"Monthly points: {len(out['monthly_trend'])}, Departments: {len(out['by_department'])}")
conn.close()
