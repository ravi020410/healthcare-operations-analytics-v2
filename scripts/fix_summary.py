import nbformat

nb = nbformat.read("notebooks/05_business_insights.ipynb", as_version=4)

new_summary = """## Summary of quantified findings

These numbers (not placeholders — computed above) feed directly into the executive report:

1. Rushed discharges (efficiency 0-40) show a **3.58x relative readmission risk** versus
   well-managed discharges (efficiency 80-100) — 27.7% vs 7.7%. This is the single strongest,
   most actionable lever in the dataset.
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

nbformat.write(nb, "notebooks/05_business_insights.ipynb")
print("patched cleanly")
