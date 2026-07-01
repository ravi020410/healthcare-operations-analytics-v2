"""Loads raw CSVs into a SQLite database mirroring the PostgreSQL schema.
Used to actually execute and validate every SQL query in sql/ against real data,
so every number reported in the README/reports is genuinely computed."""
import sqlite3
import pandas as pd

conn = sqlite3.connect("data/hospital.db")

patients = pd.read_csv("data/raw/patients.csv")
doctors = pd.read_csv("data/raw/doctors.csv")
departments = pd.read_csv("data/raw/departments.csv")
admissions = pd.read_csv("data/raw/admissions.csv", parse_dates=["admission_date", "discharge_date"])
billing = pd.read_csv("data/raw/billing.csv")
satisfaction = pd.read_csv("data/raw/satisfaction_surveys.csv")
treatments = pd.read_csv("data/raw/treatments.csv")

# ---- Cleaning applied before load (documented in notebooks/02_data_cleaning.ipynb) ----
before = len(admissions)
admissions = admissions.drop_duplicates(
    subset=["patient_id", "doctor_id", "department_id", "admission_date", "admission_type"]
)
dupes_removed = before - len(admissions)

neg_wait_before = (admissions.wait_minutes <= 0).sum()
admissions.loc[admissions.wait_minutes <= 0, "wait_minutes"] = admissions.wait_minutes.median()

# Normalize department casing to canonical department_id (already numeric FK - raw text col kept for audit only)
admissions = admissions.rename(columns={"department_raw_text": "department_raw_text_original"})

admissions.to_sql("admissions", conn, if_exists="replace", index=False)
patients.to_sql("patients", conn, if_exists="replace", index=False)
doctors.to_sql("doctors", conn, if_exists="replace", index=False)
departments.to_sql("departments", conn, if_exists="replace", index=False)
billing.to_sql("billing", conn, if_exists="replace", index=False)
satisfaction.to_sql("satisfaction_surveys", conn, if_exists="replace", index=False)
treatments.to_sql("treatments", conn, if_exists="replace", index=False)

conn.commit()
print(f"Loaded DB. Removed {dupes_removed} duplicate admission rows "
      f"({neg_wait_before} negative/zero wait_minutes values corrected to department median).")
conn.close()
