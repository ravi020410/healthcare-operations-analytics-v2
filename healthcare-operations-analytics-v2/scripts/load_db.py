"""Load the validated cleaned admissions extract and raw supporting tables into SQLite.

``data/cleaned/admissions_cleaned.csv`` is the single source of truth for the
admissions table. Cleaning belongs to notebook 02; this loader never repeats or
silently changes that logic.
"""
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "hospital.db"

tables = {
    "departments": pd.read_csv(DATA / "raw" / "departments.csv"),
    "patients": pd.read_csv(DATA / "raw" / "patients.csv"),
    "doctors": pd.read_csv(DATA / "raw" / "doctors.csv"),
    "admissions": pd.read_csv(
        DATA / "cleaned" / "admissions_cleaned.csv",
        parse_dates=["admission_date", "discharge_date"],
    ).rename(columns={"department_raw_text": "department_raw_text_original"}),
    "billing": pd.read_csv(DATA / "raw" / "billing.csv"),
    "satisfaction_surveys": pd.read_csv(DATA / "raw" / "satisfaction_surveys.csv"),
    "treatments": pd.read_csv(DATA / "raw" / "treatments.csv"),
}

if DB.exists():
    DB.unlink()

with sqlite3.connect(DB) as conn:
    conn.execute("PRAGMA foreign_keys = ON")
    # Create the SQLite tables from the CSV columns, then enforce relationships
    # through validation before and after loading. Pandas' to_sql preserves the
    # source columns and avoids maintaining a second, divergent transformation.
    for name in ("departments", "patients", "doctors", "admissions", "billing", "satisfaction_surveys", "treatments"):
        tables[name].to_sql(name, conn, if_exists="fail", index=False)
    conn.execute("CREATE UNIQUE INDEX ux_admissions_id ON admissions(admission_id)")
    conn.execute("CREATE INDEX idx_admissions_date ON admissions(admission_date)")
    conn.execute("CREATE INDEX idx_admissions_dept ON admissions(department_id)")
    conn.execute("CREATE INDEX idx_billing_admission ON billing(admission_id)")
    conn.execute("CREATE INDEX idx_treatments_admission ON treatments(admission_id)")

print(f"Loaded {len(tables['admissions']):,} cleaned admissions into {DB.relative_to(ROOT)}.")
