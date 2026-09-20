# Tableau Public dashboard

https://public.tableau.com/app/profile/iris.htet/viz/saas-analytics-dashboard/Dashboard

Four views, built from the CSVs that `dashboards/export_csvs.py` writes:

| View | Source CSV |
|---|---|
| MRR trend by plan | `mrr_by_month.csv` |
| MRR movement (expansion vs contraction) | `mrr_movements.csv` |
| Churn by month and plan | `churn_by_month.csv` |
| Cohort retention heatmap (months 0 to 12) | `cohort_retention.csv` |

The dashboard reflects the synthetic dataset produced with seed 42. Regenerating with a different seed changes the numbers.
