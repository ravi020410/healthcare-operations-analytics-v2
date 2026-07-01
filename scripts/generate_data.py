"""
Synthetic Hospital Operations Data Generator
---------------------------------------------
Generates a realistic 3-year (2023-2025) multi-department hospital dataset.
Data is intentionally messy in ways real operational extracts are messy:
- Missing insurance/contact fields
- Duplicate admission records (system double-entry, a known real-world issue)
- A handful of negative/zero wait times from clock-sync bugs
- Inconsistent department name casing from legacy system merges
- Seasonal admission volume (flu season spikes, holiday dips)
- Outlier billing amounts for a small number of complex cases

Author: Ravikant Yadav
"""
import numpy as np
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

N_PATIENTS = 18000
N_DOCTORS = 140
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

DEPARTMENTS = [
    ("Cardiology", 42), ("Emergency", 60), ("Orthopedics", 35),
    ("Oncology", 28), ("Pediatrics", 40), ("General Surgery", 38),
    ("Neurology", 24), ("Primary Care", 30), ("Obstetrics", 26),
    ("ICU", 20),
]
# Legacy-system casing inconsistency injected on purpose
DEPT_CASING_VARIANTS = {
    "Cardiology": ["Cardiology", "CARDIOLOGY", "cardiology"],
    "Emergency": ["Emergency", "ER", "Emergency Dept"],
}

INSURANCE_TYPES = ["Private HMO", "Private PPO", "Medicare", "Medicaid", "Self-Pay", "Uninsured"]
ADMISSION_TYPES = ["Emergency", "Urgent", "Elective", "Newborn", "Trauma"]

# ---------- Departments & Beds ----------
departments = pd.DataFrame({
    "department_id": range(1, len(DEPARTMENTS) + 1),
    "department": [d[0] for d in DEPARTMENTS],
    "staffed_beds": [d[1] for d in DEPARTMENTS],
})

# ---------- Doctors ----------
doctors = pd.DataFrame({
    "doctor_id": range(1, N_DOCTORS + 1),
    "doctor_name": [fake.name() for _ in range(N_DOCTORS)],
    "department_id": np.random.choice(departments.department_id, N_DOCTORS,
                                       p=np.array([d[1] for d in DEPARTMENTS]) / sum(d[1] for d in DEPARTMENTS)),
    "employment_status": np.random.choice(["Full-Time", "Part-Time", "Contract"], N_DOCTORS, p=[0.72, 0.18, 0.10]),
    "years_experience": np.random.randint(1, 35, N_DOCTORS),
})

# ---------- Patients ----------
patients = pd.DataFrame({
    "patient_id": range(1, N_PATIENTS + 1),
    "patient_name": [fake.name() for _ in range(N_PATIENTS)],
    "date_of_birth": [fake.date_of_birth(minimum_age=0, maximum_age=95) for _ in range(N_PATIENTS)],
    "gender": np.random.choice(["Female", "Male", "Other/Unspecified"], N_PATIENTS, p=[0.51, 0.47, 0.02]),
    "state": [fake.state_abbr() for _ in range(N_PATIENTS)],
    "insurance_type": np.random.choice(INSURANCE_TYPES, N_PATIENTS, p=[0.28, 0.22, 0.20, 0.14, 0.10, 0.06]),
})
# Inject missingness: ~4% missing insurance (common intake gap), ~2% missing state
patients.loc[patients.sample(frac=0.04, random_state=1).index, "insurance_type"] = np.nan
patients.loc[patients.sample(frac=0.02, random_state=2).index, "state"] = np.nan

# ---------- Admissions (seasonal + weekday effects) ----------
def seasonal_weight(day_offset):
    day = START_DATE + timedelta(days=day_offset)
    # flu-season bump Dec-Feb, summer dip Jul-Aug
    month_factor = {12: 1.35, 1: 1.4, 2: 1.25, 7: 0.85, 8: 0.85}.get(day.month, 1.0)
    weekday_factor = 1.15 if day.weekday() >= 5 else 1.0  # weekends busier in ER-heavy mix
    return month_factor * weekday_factor

day_weights = np.array([seasonal_weight(i) for i in range(TOTAL_DAYS)])
day_weights = day_weights / day_weights.sum()

N_ADMISSIONS = 46500  # will dedupe down close to the ~45K reported KPI
admission_days = np.random.choice(TOTAL_DAYS, N_ADMISSIONS, p=day_weights)
admission_dates = [START_DATE + timedelta(days=int(d)) for d in admission_days]

dept_ids = np.random.choice(departments.department_id, N_ADMISSIONS,
                             p=np.array([d[1] for d in DEPARTMENTS]) / sum(d[1] for d in DEPARTMENTS))

admissions = pd.DataFrame({
    "admission_id": range(1, N_ADMISSIONS + 1),
    "patient_id": np.random.choice(patients.patient_id, N_ADMISSIONS),
    "doctor_id": np.random.choice(doctors.doctor_id, N_ADMISSIONS),
    "department_id": dept_ids,
    "admission_date": admission_dates,
    "admission_type": np.random.choice(ADMISSION_TYPES, N_ADMISSIONS, p=[0.34, 0.22, 0.28, 0.06, 0.10]),
    "severity_score": np.clip(np.random.normal(5.2, 1.8, N_ADMISSIONS), 1, 10).round(1),
})

# Length of stay correlated with severity + department type (ICU/Oncology longer)
long_stay_depts = departments[departments.department.isin(["ICU", "Oncology"])].department_id.tolist()
base_los = np.random.gamma(shape=2.0, scale=1.6, size=N_ADMISSIONS)
los_bonus = np.where(admissions.department_id.isin(long_stay_depts), 3.5, 0)
admissions["length_of_stay_days"] = np.clip((base_los + los_bonus + admissions.severity_score * 0.3), 0.5, 45).round(1)

admissions["discharge_date"] = admissions.apply(
    lambda r: r["admission_date"] + timedelta(days=float(r["length_of_stay_days"])), axis=1
)

# Wait time: triage minutes, with a small clock-sync-bug tail of negatives (real-world data quality issue)
admissions["wait_minutes"] = np.clip(np.random.gamma(shape=2.2, scale=11, size=N_ADMISSIONS), 1, 240).round(0)
bug_idx = admissions.sample(frac=0.006, random_state=3).index
admissions.loc[bug_idx, "wait_minutes"] = np.random.choice([-5, -12, 0], size=len(bug_idx))

# Discharge efficiency score (used later as a readmission driver) - lower = rushed discharge
admissions["discharge_efficiency"] = np.clip(np.random.normal(72, 15, N_ADMISSIONS), 10, 100).round(1)
# Rushed discharges more likely on weekends / high-severity / short LOS
weekend_mask = pd.to_datetime(admissions.admission_date).dt.weekday >= 5
admissions.loc[weekend_mask, "discharge_efficiency"] -= np.random.uniform(5, 15, weekend_mask.sum())
admissions["discharge_efficiency"] = admissions["discharge_efficiency"].clip(10, 100).round(1)

# 30-day readmission target - driven by discharge_efficiency, severity, age proxy, and department
readmit_logit = (
    -3.85
    + (100 - admissions.discharge_efficiency) * 0.028
    + admissions.severity_score * 0.18
    + np.where(admissions.department_id.isin(long_stay_depts), 0.35, 0)
)
readmit_prob = 1 / (1 + np.exp(-readmit_logit))
admissions["readmitted_30d"] = (np.random.rand(N_ADMISSIONS) < readmit_prob).astype(int)

# Apply legacy casing inconsistency to a subset of rows (join key stays department_id; a raw text col carries the mess)
dept_map = departments.set_index("department_id").department.to_dict()
admissions["department_raw_text"] = admissions.department_id.map(dept_map)
for dept_name, variants in DEPT_CASING_VARIANTS.items():
    d_id = departments[departments.department == dept_name].department_id.values[0]
    mask = admissions.department_id == d_id
    admissions.loc[mask, "department_raw_text"] = np.random.choice(variants, mask.sum())

# Inject ~1.2% exact-duplicate admission rows (double-entry bug) BEFORE saving to raw
dupes = admissions.sample(frac=0.012, random_state=4)
admissions_raw = pd.concat([admissions, dupes], ignore_index=True)
admissions_raw = admissions_raw.sample(frac=1, random_state=5).reset_index(drop=True)  # shuffle

# ---------- Billing ----------
base_charge = np.random.gamma(shape=2.4, scale=3200, size=len(admissions))
severity_mult = 1 + (admissions.severity_score - 5) * 0.08
los_mult = 1 + admissions.length_of_stay_days * 0.06
charges = base_charge * severity_mult * los_mult
# small number of very high-cost complex cases (real long tail)
outlier_idx = admissions.sample(frac=0.008, random_state=6).index
charges[outlier_idx] *= np.random.uniform(4, 9, len(outlier_idx))

billing = pd.DataFrame({
    "billing_id": range(1, len(admissions) + 1),
    "admission_id": admissions.admission_id,
    "gross_charge": charges.round(2),
})
billing["insurance_payment_pct"] = np.random.uniform(0.35, 0.85, len(billing))
billing["insurance_payment"] = (billing.gross_charge * billing.insurance_payment_pct).round(2)
billing["patient_out_of_pocket"] = (billing.gross_charge - billing.insurance_payment).round(2)
billing["direct_operating_cost"] = (billing.gross_charge * np.random.uniform(0.45, 0.65, len(billing))).round(2)
billing.drop(columns=["insurance_payment_pct"], inplace=True)

# ---------- Satisfaction surveys (not every patient responds - realistic ~58% response rate) ----------
responded = admissions.sample(frac=0.58, random_state=7)
satisfaction = pd.DataFrame({
    "survey_id": range(1, len(responded) + 1),
    "admission_id": responded.admission_id.values,
    "satisfaction_score": np.clip(np.random.normal(79, 14, len(responded)) -
                                   (100 - responded.discharge_efficiency.values) * 0.15, 0, 100).round(0),
    "response_days_after_discharge": np.random.randint(1, 21, len(responded)),
})

# ---------- Treatments ----------
PROCEDURES = ["Bloodwork Panel", "X-Ray", "MRI Scan", "CT Scan", "Physical Therapy",
              "Minor Surgery", "Major Surgery", "Medication Administration", "Consultation"]
n_treatments = int(len(admissions) * 1.7)  # multiple treatments per admission on average
treatments = pd.DataFrame({
    "treatment_id": range(1, n_treatments + 1),
    "admission_id": np.random.choice(admissions.admission_id, n_treatments),
    "procedure": np.random.choice(PROCEDURES, n_treatments),
    "treatment_cost": np.round(np.random.gamma(2.0, 480, n_treatments), 2),
})

# ---------- Save raw (messy) ----------
patients.to_csv("data/raw/patients.csv", index=False)
doctors.to_csv("data/raw/doctors.csv", index=False)
departments.to_csv("data/raw/departments.csv", index=False)
admissions_raw.to_csv("data/raw/admissions.csv", index=False)
billing.to_csv("data/raw/billing.csv", index=False)
satisfaction.to_csv("data/raw/satisfaction_surveys.csv", index=False)
treatments.to_csv("data/raw/treatments.csv", index=False)

print(f"Generated {len(patients)} patients, {len(doctors)} doctors, {len(admissions_raw)} raw admission rows "
      f"({len(dupes)} intentional duplicates), {len(billing)} billing records, "
      f"{len(satisfaction)} survey responses, {len(treatments)} treatment records.")
