# Hospital Network Operations Analytics

Analysis of a 3-year (2023–2025), 10-department hospital network dataset
46,500 admissions after cleaning  covering patient flow, discharge quality, capacity
utilization, and financial performance, with a Random Forest model predicting 30-day
readmission risk at discharge.

**[→ View the live dashboard](dashboards/dashboard.html)** (open directly in a browser,
no server needed) · **[→ Read the executive report](reports/executive_report.md)**

---

## Why synthetic data, not a Kaggle dataset

Real hospital admissions data is protected under HIPAA and isn't available for public
portfolio use in any meaningful form. Rather than use one of the generic pre-made
"healthcare" datasets circulating on Kaggle (most of which are themselves synthetic,
just less deliberately constructed), I built a generator
(`scripts/generate_data.py`, seeded and reproducible) that produces a dataset with the
specific data-quality problems real hospital operational extracts actually have:

- **558 duplicate admission records** (a known double-submission bug in admissions systems)
- **279 negative/zero triage wait times** (a triage kiosk clock-sync artifact)
- **Inconsistent department naming** (`Cardiology` / `CARDIOLOGY` / `cardiology`) from a
  simulated legacy-system merge
- **~4% missing insurance type, ~2% missing state** on patient intake
- Seasonal admission volume (flu-season winter bump, summer dip) and a genuinely
  imbalanced 30-day readmission target (13.25% positive rate)

Every one of those problems is found in `notebooks/01_eda.ipynb` and fixed with a
documented rationale in `notebooks/02_data_cleaning.ipynb` nothing is hidden or
pre-cleaned before the analysis starts.

## What's actually in here (and what isn't)

Every number in this README, the executive report, and the dashboard was computed by
running the code in this repo against the generated dataset re-run
`scripts/run_queries.py` yourself and you'll get the same numbers. There is one
deliberate limitation, stated plainly rather than hidden: department-level operating
cost is generated with a single random ratio rather than department-specific cost
structures, which flattens the financial-margin comparison across departments to a
near-uniform ~45%. That's flagged in `reports/executive_report.md` §5 as a modeling
limitation, not presented as a real finding.

## Headline result

**Admissions with a low discharge-efficiency score (0–40) have a 3.58x higher observed
30-day readmission rate than those scoring 80-100 (27.7% vs 7.7%).** This is an
association in synthetic operational data, not evidence that discharge efficiency causes
readmission. It is a useful signal for prioritizing a real-world process review, where
clinical validation would be required before acting on it.

A tested-but-negative result is also reported honestly: the hypothesis that weekend
admissions face longer triage waits did **not** hold (24.3 min weekend vs 24.1 min
weekday) see `reports/executive_report.md` §4.

## Project structure

```text
├── architecture/
│   └── schema_diagram.md          # PostgreSQL Star-Schema ER diagram (Mermaid)
├── dashboards/
│   ├── dashboard.html             # Interactive HTML/Chart.js operations dashboard
│   ├── dashboard_data.json        # Pre-calculated KPI & trend aggregates
│   └── powerbi/                   # DAX measures & step-by-step .pbix build guide
├── data/
│   ├── raw/                       # 7 raw hospital operational extracts (CSV)
│   └── cleaned/                   # Cleaned datasets & engineered ML feature tables
├── notebooks/                     # End-to-end analytical workflow (fully executed)
│   ├── 01_eda.ipynb               # Data profiling & raw anomaly identification
│   ├── 02_data_cleaning.ipynb     # Natural key deduplication & median imputation
│   ├── 03_feature_engineering.ipynb # Clinical, operational & financial feature creation
│   ├── 04_visualization.ipynb     # High-resolution exploratory visualizations
│   └── 05_business_insights.ipynb # 30-day readmission predictive model (Random Forest)
├── reports/
│   ├── executive_report.md        # Comprehensive business findings & recommendations
│   └── query_results.json         # Raw benchmark query outputs
├── sql/                           # Pure PostgreSQL 14+ queries
│   ├── 01_schema.sql              # Star schema DDL with constraints & indexes
│   ├── 02_quality_checks.sql      # Diagnostic data quality validation queries
│   └── 03_business_analysis_queries.sql # Window functions, CTEs, Z-scores & capacity KPIs
└── visuals/                       # Analytical chart PNG exports


## Tech stack

Python (pandas, NumPy, scikit-learn, matplotlib, seaborn) · Database & SQL: PostgreSQL 14+ (Star schema design, CTEs, Window Functions LAG/Moving Avg, Z-score Outlier Detection) · Chart.js for the HTML dashboard · Power BI (DAX measures +
build guide included, `.pbix` built locally see `dashboards/powerbi/BUILD_GUIDE.md`)

## What I'd do with more time

- Department-specific operating cost model, to make the financial margin comparison
  a real finding instead of a flat number (see the limitation noted above)
- A proper time-series model (e.g. SARIMA) for the seasonal admission volume, instead
  of the simple 3-month moving average currently in the SQL layer
- Real EHR-adjacent features (comorbidity count, prior admission history) if this were
  ever run against real (de-identified, IRB-approved) data - operational features alone
  cap out readmission model performance around the AUC seen here, which matches what
  the published clinical literature on this problem reports

---

**Author:** Ravikant Yadav · [LinkedIn](https://linkedin.com/in/ravikant-yadav-39936a1a8) · [GitHub](https://github.com/ravi020410)
