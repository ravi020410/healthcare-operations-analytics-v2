# Executive Report — Hospital Network Operations & Financial Review
**Period:** Jan 2023 – Dec 2025 (3-year window) · **Prepared by:** Ravikant Yadav
**Data:** 46,500 cleaned admission records (558 duplicate submissions and 279 clock-sync
wait-time errors corrected during cleaning — see `notebooks/02_data_cleaning.ipynb`)

---

## 1. Headline Numbers

| Metric | Value |
|---|---:|
| Total Admissions | 46,500 |
| Average Length of Stay | 5.26 days |
| 30-Day Readmission Rate | 13.25% |
| Average Triage Wait | 24.2 minutes |
| Average Discharge Efficiency Score | 68.6 / 100 |
| Average Patient Satisfaction | 74.1 / 100 |
| Gross Billings (3-yr) | $499.3M |

All figures computed directly by `scripts/run_queries.py` against the cleaned dataset —
re-run it yourself and the numbers will match exactly.

---

## 2. The Central Finding: Discharge Efficiency Drives Readmission Risk

This is the most actionable result in the project. Bucketing admissions by discharge
efficiency score and measuring 30-day readmission rate per bucket:

| Discharge Efficiency Bucket | Readmission Rate |
|---|---:|
| Rushed (0–40) | 27.7% |
| Below Avg (40–60) | ~18% |
| Good (60–80) | ~11% |
| Excellent (80–100) | 7.7% |

**Rushed discharges carry a 3.58x relative readmission risk compared to well-managed
discharges.** This held up as the top feature by importance in the Random Forest
classifier (`notebooks/05_business_insights.ipynb`), ahead of severity score and
department. It's the one lever operations leadership can act on directly — severity
and admission type aren't controllable, discharge process is.

**Recommendation:** Mandate a structured pre-discharge checklist for any admission
where the real-time discharge-efficiency proxy (staffing ratio at time of discharge,
time-of-day, day-of-week) predicts a "rushed" outcome, rather than applying it uniformly.

---

## 3. Capacity: Two Departments Are Structurally Over Capacity

Bed occupancy (patient bed-days ÷ licensed bed-days over the 3-year window):

| Department | Staffed Beds | Occupancy Rate |
|---|---:|---:|
| Oncology | 28 | **101.0%** |
| ICU | 20 | **99.1%** |
| Cardiology | 42 | 60.5% |
| Obstetrics | 26 | 59.6% |

Oncology running above 100% licensed occupancy means the department is regularly
relying on overflow capacity (hallway beds, borrowed space) — a real and common
hospital operations problem, not a data error. Meanwhile Cardiology and Obstetrics
sit well under 65%.

**Recommendation:** Model a 4–6 bed reallocation from Cardiology to Oncology/ICU and
re-forecast occupancy; a full reallocation isn't warranted since Cardiology's own
utilization still needs headroom for its own admission volatility, but a partial shift
is worth costing out.

---

## 4. Weekend Wait Time — A Negative Result Worth Reporting

The original hypothesis (weekend admissions face longer triage waits) was tested
directly and **did not hold**: 24.3 min weekend vs. 24.1 min weekday, a 0.9%
difference that isn't operationally meaningful. Reporting this as "no effect found"
rather than searching for a hypothesis that confirms the assumption is intentional —
a real analyst distinguishes between "we tested it and there's nothing there" and
"we didn't look."

---

## 5. Financial Note & Known Model Limitation

Gross margin sits at a nearly uniform ~45% across all ten departments ($44.8–$45.1M
range). This is a byproduct of how the underlying synthetic dataset assigns operating
cost (a single random ratio applied uniformly, not department-specific cost structures).
**This is flagged here deliberately as a modeling limitation, not presented as a real
finding** — a genuinely department-differentiated cost model (e.g., ICU/Oncology having
structurally higher staff-to-patient cost ratios) would be the next iteration of the
data generator if this dataset were extended.

---

## 6. Readmission Model Performance

Random Forest classifier, 80/20 train/test split, stratified on target:

- **ROC-AUC: 0.637**
- Precision/Recall favor the majority class as expected on an imbalanced target (13.2%
  positive rate); `class_weight='balanced'` was used to keep recall on the readmit class
  usable (0.55) rather than letting the model default to predicting "no readmit" for
  everyone.

An AUC of 0.637 is consistent with published clinical readmission risk models (HOSPITAL
score, LACE index typically report 0.65–0.75 AUC) — readmission is driven substantially
by factors outside operational data (home support, medication adherence, comorbidities)
that this dataset doesn't capture. Reported as-is rather than tuned into an
implausibly high number.

---

## 7. Recommendations Summary

1. **Structured discharge checklist**, targeted at predicted-rushed discharges — highest
   expected impact on readmission rate.
2. **Model a partial bed reallocation** from Cardiology/Obstetrics toward Oncology/ICU.
3. **Re-run the financial margin analysis once department-specific operating cost data
   is available** — the current ~45% flat margin is a data limitation, not a finding.
4. **Do not over-invest in weekend staffing** on the wait-time assumption alone; the
   data doesn't support it. (Volume is still seasonal — see `visuals/01_monthly_admissions.png`
   — which is a separate, valid staffing consideration.)

---

*Methodology: synthetic dataset generated via `scripts/generate_data.py` (seeded,
reproducible), cleaned via `notebooks/02_data_cleaning.ipynb`, queried via
`sql/03_business_analysis_queries.sql`, modeled via `notebooks/05_business_insights.ipynb`.
Real hospital EHR data is not used or referenced anywhere in this project, in compliance
with HIPAA — see README for the reasoning behind that choice.*
