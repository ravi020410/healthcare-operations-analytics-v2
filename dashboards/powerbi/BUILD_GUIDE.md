# Building the Real Power BI File (.pbix)

The HTML dashboard (`dashboards/dashboard.html`) is the recruiter-facing, no-install
version. This guide is for producing the actual `.pbix` file on your Windows machine —
do this once, then commit the `.pbix` to the repo so both exist.

**Time: ~15 minutes.**

## 1. Get Power BI Desktop
Free download from the Microsoft Store or powerbi.microsoft.com if you don't have it.

## 2. Import the data
Open Power BI Desktop → **Get Data → Text/CSV** → import these four files:
- `data/cleaned/admissions_features.csv`
- `data/raw/billing.csv`
- `data/raw/departments.csv`
- `data/raw/satisfaction_surveys.csv`

## 3. Set relationships (Model view)
- `admissions_features[admission_id]` → `billing[admission_id]` (1:1)
- `admissions_features[admission_id]` → `satisfaction_surveys[admission_id]` (1:many, since ~58% response rate)
- `admissions_features[department]` → `departments[department]` (1:many)

## 4. Add the Calendar table
New Table → paste:
```
Calendar = CALENDAR ( DATE(2023,1,1), DATE(2025,12,31) )
```
Right-click it → **Mark as Date Table**. Relate `Calendar[Date]` to
`admissions_features[admission_date]` (convert that column to Date type first, not Datetime).

## 5. Paste in the measures
Copy every measure from `dashboards/powerbi/measures.dax` into new DAX measures on the
`admissions_features` table.

## 6. Build the report pages
Mirror the HTML dashboard layout so the two stay consistent:
- **Page 1 — Executive Summary:** KPI cards (use the 6 measures) + monthly admissions line chart + department table
- **Page 2 — Financial:** Gross Billings & Margin by department (clustered bar) + Margin % card
- **Page 3 — Clinical Quality:** Readmission Rate by discharge-efficiency bucket (bar) + the Rushed vs Excellent relative-risk callout

Use the color tokens from `dashboards/theme.json` so it visually matches the HTML version.

## 7. Export and commit
Save as `dashboards/powerbi/healthcare_operations_analytics.pbix`, then:
```bash
git add dashboards/powerbi/healthcare_operations_analytics.pbix
git commit -m "Add Power BI desktop file"
git push
```

Take 2–3 screenshots of the finished report pages and drop them in `visuals/powerbi/` —
those are what actually render in the README, since GitHub can't preview `.pbix` files inline.
