import sys
sys.path.insert(0, "scripts")
from nb_builder import build_and_run

cells = [
("markdown", """# 03 — Feature Engineering
**Healthcare Operations Analytics**

Builds the feature set used later for the readmission model in `05_business_insights.ipynb`,
plus a few operational fields used across the SQL/dashboard layer."""),

("code", """import pandas as pd
import numpy as np

admissions = pd.read_csv('../data/cleaned/admissions_cleaned.csv', parse_dates=['admission_date','discharge_date'])
patients = pd.read_csv('../data/raw/patients.csv')
billing = pd.read_csv('../data/raw/billing.csv')
treatments = pd.read_csv('../data/raw/treatments.csv')
satisfaction = pd.read_csv('../data/raw/satisfaction_surveys.csv')

print(admissions.shape)"""),

("markdown", "## Patient age at admission"),
("code", """patients['date_of_birth'] = pd.to_datetime(patients['date_of_birth'])
admissions = admissions.merge(patients[['patient_id','date_of_birth']], on='patient_id', how='left')
admissions['patient_age'] = ((admissions['admission_date'] - admissions['date_of_birth']).dt.days / 365.25).round(1)
admissions['age_group'] = pd.cut(admissions.patient_age, bins=[0,18,35,50,65,120],
                                   labels=['0-18','19-35','36-50','51-65','66+'])
admissions[['patient_age','age_group']].describe(include='all')"""),

("markdown", "## Calendar features (weekend flag, month, is flu-season)"),
("code", """admissions['is_weekend_admission'] = admissions.admission_date.dt.dayofweek >= 5
admissions['admission_month'] = admissions.admission_date.dt.month
admissions['is_flu_season'] = admissions.admission_month.isin([12,1,2])
admissions[['is_weekend_admission','admission_month','is_flu_season']].head()"""),

("markdown", "## Treatment intensity per admission"),
("code", """tx_agg = treatments.groupby('admission_id').agg(
    treatment_count=('treatment_id','count'),
    total_treatment_cost=('treatment_cost','sum')
).reset_index()
admissions = admissions.merge(tx_agg, on='admission_id', how='left')
admissions[['treatment_count','total_treatment_cost']] = admissions[['treatment_count','total_treatment_cost']].fillna(0)
admissions[['treatment_count','total_treatment_cost']].describe()"""),

("markdown", "## Financial features"),
("code", """billing_slim = billing[['admission_id','gross_charge','direct_operating_cost']].copy()
billing_slim['margin'] = billing_slim.gross_charge - billing_slim.direct_operating_cost
admissions = admissions.merge(billing_slim, on='admission_id', how='left')
admissions['cost_per_stay_day'] = (admissions.gross_charge / admissions.length_of_stay_days.replace(0, np.nan)).round(2)
admissions[['gross_charge','margin','cost_per_stay_day']].describe()"""),

("markdown", "## Satisfaction join (only ~58% of admissions have a response — kept as NaN, not imputed)"),
("code", """sat_slim = satisfaction[['admission_id','satisfaction_score']]
admissions = admissions.merge(sat_slim, on='admission_id', how='left')
print(f"Satisfaction response rate: {admissions.satisfaction_score.notna().mean()*100:.1f}%")"""),

("markdown", """## Discharge efficiency bucket

Used directly in the readmission model as a categorical signal, since the earlier
EDA suggested the relationship with readmission isn't perfectly linear."""),
("code", """admissions['discharge_efficiency_bucket'] = pd.cut(
    admissions.discharge_efficiency, bins=[0,40,60,80,100],
    labels=['Rushed (0-40)','Below Avg (40-60)','Good (60-80)','Excellent (80-100)']
)
admissions['discharge_efficiency_bucket'].value_counts()"""),

("markdown", "## Save the feature table"),
("code", """feature_cols = [
    'admission_id','patient_id','department_id','department','admission_type',
    'severity_score','length_of_stay_days','wait_minutes','discharge_efficiency',
    'discharge_efficiency_bucket','readmitted_30d','patient_age','age_group',
    'is_weekend_admission','admission_month','is_flu_season',
    'treatment_count','total_treatment_cost','gross_charge','margin',
    'cost_per_stay_day','satisfaction_score'
]
features = admissions[feature_cols]
features.to_csv('../data/cleaned/admissions_features.csv', index=False)
print(f"Saved feature table: {features.shape[0]:,} rows x {features.shape[1]} columns")
features.head(3)""")
]

build_and_run(cells, "notebooks/03_feature_engineering.ipynb")
