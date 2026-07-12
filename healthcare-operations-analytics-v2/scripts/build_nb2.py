import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nb_builder import build_and_run

cells = [
("markdown", """# 02 — Data Cleaning
**Healthcare Operations Analytics**

Fixes the three issues found in `01_eda.ipynb`: duplicate submissions, the triage
clock-sync bug, and legacy department-name casing. Each fix is applied with a
documented rationale — nothing is silently dropped."""),

("code", """import pandas as pd
import numpy as np

admissions = pd.read_csv('../data/raw/admissions.csv', parse_dates=['admission_date','discharge_date'])
departments = pd.read_csv('../data/raw/departments.csv')
print(f"Starting rows: {len(admissions):,}")"""),

("markdown", """## 1. De-duplicate on natural key

We keep the **first** occurrence of each (patient, doctor, department, admission_date,
admission_type) combination. Using `admission_id` for dedup would miss these entirely,
since the resubmitted record gets a new surrogate key."""),
("code", """natural_key = ['patient_id','doctor_id','department_id','admission_date','admission_type']
before = len(admissions)
admissions = admissions.drop_duplicates(subset=natural_key, keep='first')
after = len(admissions)
print(f"Removed {before - after} duplicate admission records ({(before-after)/before*100:.2f}% of raw rows).")"""),

("markdown", """## 2. Correct the triage clock-sync bug

Non-positive `wait_minutes` values are a known artifact of a triage kiosk clock
occasionally resetting to system boot time. These are **not real zero-wait
admissions** — deleting the rows would also delete otherwise-valid severity,
LOS, and billing data for those patients, so we impute using the **department-level
median wait time** instead (median chosen over mean to stay robust to the
right-skewed wait time distribution)."""),
("code", """bad_wait = admissions.wait_minutes <= 0
print(f"Correcting {bad_wait.sum()} non-positive wait_minutes values ({bad_wait.mean()*100:.2f}%).")

dept_medians = admissions.groupby('department_id')['wait_minutes'].transform(
    lambda s: s[s > 0].median()
)
admissions.loc[bad_wait, 'wait_minutes'] = dept_medians[bad_wait]
print(f"Remaining non-positive values: {(admissions.wait_minutes <= 0).sum()}")"""),

("markdown", """## 3. Normalize department naming

`department_id` was preserved correctly throughout (it's the true foreign key), so
this step doesn't require a fuzzy-matching lookup — we simply confirm every
`department_id` maps to exactly one canonical name in `departments.csv` and drop
the noisy raw text column from the analytical table, keeping it only in an audit CSV."""),
("code", """dept_map = departments.set_index('department_id')['department'].to_dict()
admissions['department'] = admissions['department_id'].map(dept_map)

# Audit trail: preserve the messy raw text mapping separately, don't ship it in the analytical table
audit = admissions[['admission_id','department_id','department','department_raw_text']].copy()
audit.to_csv('../data/cleaned/department_naming_audit.csv', index=False)
admissions = admissions.drop(columns=['department_raw_text'])
print("Canonical department names applied. Audit trail saved separately.")
admissions['department'].value_counts()"""),

("markdown", "## 4. Outlier clipping on billing-relevant numeric fields (IQR method, 3x multiplier)"),
("code", """def iqr_bounds(s, k=3):
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - k*iqr, q3 + k*iqr

for col in ['length_of_stay_days', 'severity_score']:
    lo, hi = iqr_bounds(admissions[col])
    n_clipped = ((admissions[col] < lo) | (admissions[col] > hi)).sum()
    admissions[col] = admissions[col].clip(lo, hi)
    print(f"{col}: clipped {n_clipped} extreme values to [{lo:.1f}, {hi:.1f}]")"""),

("markdown", "## 5. Final integrity checks before saving"),
("code", """assert admissions['admission_id'].is_unique, "admission_id must be unique after cleaning"
assert admissions['wait_minutes'].min() > 0, "wait_minutes must be positive after cleaning"
assert admissions['department'].isna().sum() == 0, "every admission must map to a department"

print(f"Final cleaned row count: {len(admissions):,}")
admissions.to_csv('../data/cleaned/admissions_cleaned.csv', index=False)
print("Saved data/cleaned/admissions_cleaned.csv")"""),

("markdown", """## Summary

| Issue | Rows affected | Resolution |
|---|---|---|
| Duplicate submissions | 558 (1.19%) | Dropped, kept first occurrence on natural key |
| Clock-sync wait time bug | 279 (0.6%) | Imputed with department-level median |
| Department casing inconsistency | 3 variants across 2 departments | Mapped to canonical name via `department_id`, raw text preserved in audit file |
| LOS / severity extreme outliers | Clipped via 3× IQR | Retained (not dropped) to avoid losing otherwise-valid admissions |
""")
]

build_and_run(cells, "notebooks/02_data_cleaning.ipynb")
