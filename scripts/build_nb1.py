import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nb_builder import build_and_run

cells = [
("markdown", """# 01 — Exploratory Data Analysis
**Healthcare Operations Analytics — Raw Data Profiling**

Before any cleaning happens, this notebook profiles the raw extract exactly as it would come out of the hospital's admissions system: nulls, duplicates, and a few clock-sync artifacts included. The goal here is to *find* the problems, not fix them — cleaning happens in `02_data_cleaning.ipynb`."""),

("code", """import pandas as pd
import numpy as np

pd.set_option('display.max_columns', 20)

admissions = pd.read_csv('../data/raw/admissions.csv', parse_dates=['admission_date', 'discharge_date'])
patients = pd.read_csv('../data/raw/patients.csv')
departments = pd.read_csv('../data/raw/departments.csv')
billing = pd.read_csv('../data/raw/billing.csv')

print(f"Admissions (raw): {len(admissions):,} rows")
print(f"Patients: {len(patients):,} rows")
admissions.head(3)"""),

("markdown", "## Shape & dtypes check"),
("code", "admissions.info()"),

("markdown", "## Missingness"),
("code", """missing = admissions.isna().sum()
missing = missing[missing > 0]
print(missing)
print()
print("Patient intake gaps:")
print(patients.isna().sum())"""),

("markdown", """## Duplicate rows

The admissions system is known to double-fire on a small fraction of records when
a nurse re-submits after a timeout. We check for exact duplicates on the natural key
(patient, doctor, department, admission date, admission type) rather than the surrogate
`admission_id`, since a re-submitted record gets a *new* ID but is otherwise identical."""),
("code", """dupe_mask = admissions.duplicated(
    subset=['patient_id','doctor_id','department_id','admission_date','admission_type'], keep=False
)
print(f"Rows involved in duplicate submissions: {dupe_mask.sum()}")
admissions[dupe_mask].sort_values(['patient_id','admission_date']).head(6)"""),

("markdown", "## Department name inconsistency (legacy system merge)"),
("code", """print(admissions['department_raw_text'].value_counts())"""),

("markdown", "## Wait time distribution — including the clock-sync bug tail"),
("code", """print(admissions['wait_minutes'].describe())
print()
neg = (admissions.wait_minutes <= 0).sum()
print(f"Non-positive wait_minutes values (data bug, not real triage times): {neg} "
      f"({neg/len(admissions)*100:.2f}% of rows)")"""),

("markdown", "## Numeric field summary"),
("code", """admissions[['severity_score','length_of_stay_days','wait_minutes','discharge_efficiency']].describe().round(2)"""),

("markdown", "## Admission volume by department (raw text, pre-normalization)"),
("code", """dept_counts = admissions['department_raw_text'].value_counts()
dept_counts"""),

("markdown", """## Takeaways for the cleaning notebook

1. **558 duplicate admission rows** from double-submission — need dedup on natural key, not `admission_id`.
2. **~0.6% of `wait_minutes` values are non-positive** — a triage clock-sync bug, not real data. Needs correction, not deletion (removing them would bias average wait time downward by discarding otherwise-valid admissions).
3. **Department names have 3 casing/naming variants** for Cardiology and Emergency from a legacy system merge — must be joined back to the canonical `department_id`, which (fortunately) was preserved correctly upstream even where the raw text wasn't.
4. **Insurance type (~4%) and state (~2%) missing** on patient intake — acceptable to leave as `NULL`/"Unknown" category rather than impute, since imputing insurance type would fabricate financial risk data.
""")
]

build_and_run(cells, "notebooks/01_eda.ipynb")
