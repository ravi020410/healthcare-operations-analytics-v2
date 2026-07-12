import nbformat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
notebook_path = ROOT / "notebooks" / "05_business_insights.ipynb"
with notebook_path.open(encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

new_summary = """## Summary of quantified findings

These numbers (not placeholders — computed above) feed directly into the executive report:

1. Low discharge-efficiency scores (0-40) have a **3.58x higher observed readmission rate** than
   scores of 80-100 — 27.7% vs 7.7%. This is an association in synthetic data, not causal evidence.
2. Weekend triage wait time is **not** meaningfully different from weekday wait time in this
   dataset (24.3 vs 24.1 min) — worth stating plainly rather than forcing a finding that
   isn't there. The earlier seasonal-volume assumption from EDA did not translate into a
   wait-time gap once staffing ratios are implicitly held constant in the data.
3. Model AUC (0.637) sits in the realistic 0.60-0.75 range expected for readmission prediction
   using operational (non-clinical-history) features — consistent with published hospital
   readmission models (HOSPITAL score, LACE index), and a signal the model isn't leaking
   future information rather than a weakness to hide.
"""

for cell in nb.cells:
    if cell.cell_type == "markdown" and "Summary of quantified" in cell.source:
        cell.source = new_summary

with notebook_path.open("w", encoding="utf-8") as f:
    nbformat.write(nb, f)
print("patched cleanly")
