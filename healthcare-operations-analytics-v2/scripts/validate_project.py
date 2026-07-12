"""Validate cleaned data, SQLite contents, and generated dashboard/report KPIs.

Run after ``load_db.py``. The script exits non-zero on any integrity or
reconciliation failure, making it suitable for local checks or CI.
"""
from pathlib import Path
import json
import re
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
CLEAN = DATA / "cleaned"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS  {message}")


admissions = pd.read_csv(CLEAN / "admissions_cleaned.csv", parse_dates=["admission_date", "discharge_date"])
patients = pd.read_csv(RAW / "patients.csv")
doctors = pd.read_csv(RAW / "doctors.csv")
departments = pd.read_csv(RAW / "departments.csv")
billing = pd.read_csv(RAW / "billing.csv")
surveys = pd.read_csv(RAW / "satisfaction_surveys.csv")
treatments = pd.read_csv(RAW / "treatments.csv")

natural_key = ["patient_id", "doctor_id", "department_id", "admission_date", "admission_type"]
require(admissions["admission_id"].is_unique, "cleaned admission_id values are unique")
require(not admissions.duplicated(natural_key).any(), "cleaned admissions have no duplicate natural keys")
require((admissions["wait_minutes"] > 0).all(), "all cleaned wait times are positive")
require((admissions["discharge_date"] >= admissions["admission_date"]).all(), "admission chronology is valid")
require(set(admissions["readmitted_30d"].dropna().unique()).issubset({0, 1}), "readmission target contains only 0/1")

checks = [
    (admissions.patient_id, patients.patient_id, "admissions.patient_id -> patients.patient_id"),
    (admissions.doctor_id, doctors.doctor_id, "admissions.doctor_id -> doctors.doctor_id"),
    (admissions.department_id, departments.department_id, "admissions.department_id -> departments.department_id"),
    (doctors.department_id, departments.department_id, "doctors.department_id -> departments.department_id"),
    (billing.admission_id, admissions.admission_id, "billing.admission_id -> admissions.admission_id"),
    (surveys.admission_id, admissions.admission_id, "satisfaction_surveys.admission_id -> admissions.admission_id"),
    (treatments.admission_id, admissions.admission_id, "treatments.admission_id -> admissions.admission_id"),
]
for child, parent, label in checks:
    require(child.isin(parent).all(), f"foreign key relationship is valid: {label}")

with sqlite3.connect(DATA / "hospital.db") as conn:
    db_count = conn.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]
    db_ids = pd.read_sql("SELECT admission_id FROM admissions ORDER BY admission_id", conn)["admission_id"]
require(db_count == len(admissions), "SQLite admission count matches cleaned CSV")
require(db_ids.equals(admissions.admission_id.sort_values().reset_index(drop=True)), "SQLite admission keys match cleaned CSV")

with (ROOT / "reports" / "query_results.json").open(encoding="utf-8") as f:
    report = json.load(f)["Q1_executive_kpis"]
with (ROOT / "dashboards" / "dashboard_data.json").open(encoding="utf-8") as f:
    dashboard = json.load(f)["kpi"]
html = (ROOT / "dashboards" / "dashboard.html").read_text(encoding="utf-8")
match = re.search(r"const DATA = (.*?);\r?\n", html)
require(match is not None, "dashboard contains an embedded data payload")
embedded_dashboard = json.loads(match.group(1))["kpi"]
for metric in ("total_admissions", "avg_los_days", "readmission_rate_pct", "avg_wait_minutes", "avg_discharge_efficiency", "avg_satisfaction", "gross_billings"):
    require(report[metric] == dashboard[metric], f"report and dashboard agree on {metric}")
    require(dashboard[metric] == embedded_dashboard[metric], f"dashboard JSON and embedded data agree on {metric}")

print("\nProject validation passed.")
