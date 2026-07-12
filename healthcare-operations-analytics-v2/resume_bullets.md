# Resume Bullets — Healthcare Operations Analytics

Pick 2–3, tailored to the role. Every number here is real, computed by the code in
this repo — you can defend any of them in an interview by re-running the scripts live.

**Data engineering / SQL focus:**
- Designed and built a 7-table PostgreSQL star-schema data model for a simulated
  46,500-admission hospital dataset, writing 10 advanced SQL queries (CTEs, window
  functions, statistical z-score outlier detection) to surface capacity, financial,
  and clinical-quality KPIs.
- Identified and resolved 3 classes of real-world data quality issues (duplicate
  records, timestamp corruption, categorical inconsistency) affecting ~2% of records,
  documenting root cause and resolution rationale for each.

**Analytics / insight focus:**
- Analyzed 3 years of hospital admissions data to identify that rushed patient
  discharges carry a 3.58x higher 30-day readmission rate than well-managed
  discharges (27.7% vs 7.7%), the single most actionable driver identified in the
  dataset.
- Built an interactive operations dashboard (Chart.js) surfacing admission trends,
  department-level capacity utilization, and financial margin across a 10-department
  network, flagging 2 departments operating above/near licensed bed capacity.

**ML / modeling focus:**
- Trained a Random Forest classifier to predict 30-day patient readmission risk from
  operational features available at discharge, achieving a 0.637 ROC-AUC — consistent
  with published clinical readmission risk models (HOSPITAL score, LACE index) — and
  used feature importance analysis to identify discharge efficiency as the top
  controllable risk factor.

**What NOT to say:**
- Don't claim this used "real hospital data" — it's synthetic, generated to simulate
  realistic operational patterns and data-quality issues, because real EHR data isn't
  publicly available under HIPAA. If asked directly, say exactly that — it's a stronger
  answer than pretending otherwise, and shows you understand the domain constraint.
- Don't inflate the AUC or claim a higher number than 0.637 — a realistic score with a
  clear explanation is more credible to any interviewer who has worked with imbalanced
  classification problems than a suspiciously high one.
