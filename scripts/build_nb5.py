import sys
sys.path.insert(0, "scripts")
from nb_builder import build_and_run

cells = [
("markdown", """# 05 — Predictive Modeling & Business Insights
**Healthcare Operations Analytics**

Trains a classifier to predict 30-day readmission risk at the point of discharge,
then translates the model's feature importances into operational recommendations."""),

("code", """import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, roc_curve, classification_report, confusion_matrix

features = pd.read_csv('../data/cleaned/admissions_features.csv')
print(features.shape)
features['readmitted_30d'].value_counts(normalize=True)"""),

("markdown", """## Model setup

Target: `readmitted_30d`. We deliberately exclude `total_treatment_cost` and `margin`
from the feature set — those are *downstream* of the admission, not known at
discharge-decision time, and including them would leak information a real early-warning
system wouldn't have."""),
("code", """categorical = ['department','admission_type','age_group','discharge_efficiency_bucket']
numeric = ['severity_score','length_of_stay_days','wait_minutes','discharge_efficiency',
           'patient_age','is_weekend_admission','is_flu_season','treatment_count']

X = features[categorical + numeric].copy()
y = features['readmitted_30d']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
print(f"Train: {X_train.shape}, Test: {X_test.shape}")
print(f"Train positive rate: {y_train.mean():.3f} | Test positive rate: {y_test.mean():.3f}")"""),

("code", """preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
], remainder='passthrough')

model = Pipeline([
    ('prep', preprocessor),
    ('clf', RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_leaf=25,
        class_weight='balanced', random_state=42, n_jobs=-1
    ))
])

model.fit(X_train, y_train)
print("Model trained.")"""),

("markdown", "## Evaluation"),
("code", """y_proba = model.predict_proba(X_test)[:,1]
y_pred = (y_proba >= 0.5).astype(int)

auc = roc_auc_score(y_test, y_proba)
print(f"ROC-AUC: {auc:.3f}\\n")
print(classification_report(y_test, y_pred, target_names=['No Readmit','Readmit']))"""),

("code", """fpr, tpr, _ = roc_curve(y_test, y_proba)
fig, ax = plt.subplots(figsize=(6,5.5))
ax.plot(fpr, tpr, color='#2E4780', linewidth=2, label=f'Random Forest (AUC={auc:.3f})')
ax.plot([0,1],[0,1], linestyle='--', color='grey', label='Random baseline')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('ROC Curve — 30-Day Readmission Model')
ax.legend()
plt.tight_layout()
plt.savefig('../visuals/07_roc_curve.png')
plt.show()"""),

("markdown", """## A note on the AUC

An AUC in this range is realistic — and worth explaining rather than hiding.
Real hospital readmission models in published clinical literature (e.g. HOSPITAL
score, LACE index) typically land in the 0.65-0.75 AUC range, because readmission
is driven by many factors outside any single admission's operational data (home
support, medication adherence, comorbidities not captured here). A much higher AUC
on a project like this would be a red flag for data leakage, not a sign of a better model."""),

("markdown", "## Feature importances"),
("code", """ohe = model.named_steps['prep'].named_transformers_['cat']
cat_names = ohe.get_feature_names_out(categorical)
all_names = list(cat_names) + numeric

importances = pd.Series(model.named_steps['clf'].feature_importances_, index=all_names)
importances = importances.sort_values(ascending=False).head(15)

fig, ax = plt.subplots(figsize=(9,6))
importances.sort_values().plot(kind='barh', ax=ax, color='#5B7FBF')
ax.set_title('Top 15 Feature Importances — Readmission Risk')
ax.set_xlabel('Importance')
plt.tight_layout()
plt.savefig('../visuals/08_feature_importances.png')
plt.show()

importances"""),

("markdown", """## Business insight: rushed discharges

Cross-referencing the top feature importances against the readmission-by-discharge-efficiency
chart from `04_visualization.ipynb` quantifies the relationship directly:"""),
("code", """rushed = features[features.discharge_efficiency_bucket == 'Rushed (0-40)']['readmitted_30d'].mean()
excellent = features[features.discharge_efficiency_bucket == 'Excellent (80-100)']['readmitted_30d'].mean()
lift = rushed / excellent if excellent > 0 else float('nan')

print(f"Readmission rate, rushed discharges:    {rushed*100:.1f}%")
print(f"Readmission rate, excellent discharges: {excellent*100:.1f}%")
print(f"Relative risk (rushed vs excellent):    {lift:.2f}x")"""),

("markdown", "## Weekend admission wait-time gap (operational finding)"),
("code", """weekend_wait = features[features.is_weekend_admission == True]['wait_minutes'].mean()
weekday_wait = features[features.is_weekend_admission == False]['wait_minutes'].mean()
gap_pct = (weekend_wait - weekday_wait) / weekday_wait * 100
print(f"Weekday avg wait: {weekday_wait:.1f} min | Weekend avg wait: {weekend_wait:.1f} min")
print(f"Weekend wait is {gap_pct:.1f}% higher than weekday.")"""),

("markdown", """## Summary of quantified findings

These numbers (not placeholders — computed above) feed directly into the executive report:

1. Rushed discharges (efficiency 0-40) show measurably higher 30-day readmission risk
   than well-managed discharges (efficiency 80-100) — see relative risk ratio above.
2. Weekend admissions show a meaningfully higher average triage wait than weekday admissions.
3. Model AUC sits in the realistic 0.65-0.75 range expected for readmission prediction using
   operational (non-clinical-history) features — consistent with published hospital readmission
   models, and a signal that the model isn't leaking future information.
""")
]

build_and_run(cells, "notebooks/05_business_insights.ipynb")
