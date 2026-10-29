"""Export the marts as CSVs for Tableau."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboards" / "data_exports"
OUT.mkdir(parents=True, exist_ok=True)

EXPORTS = {
    "mrr_by_month": "select * from main.mart_mrr order by month, plan_name, region",
    "mrr_movements": "select * from main.mart_mrr_movements order by month",
    "churn_by_month": "select * from main.mart_churn order by churn_month, plan_name",
    "cohort_retention": "select * from main.mart_cohort_retention order by cohort_month, active_month",
    "customers": "select * from main.dim_customers",
    "invoices": "select * from main.fct_invoices order by invoice_date",
}

con = duckdb.connect(str(ROOT / "dbt_project" / "dbt.duckdb"), read_only=True)
for name, query in EXPORTS.items():
    # COPY TO does not accept a bound parameter for the path, so quotes are escaped instead.
    target = str(OUT / f"{name}.csv").replace("'", "''")
    rows = con.execute(f"copy ({query}) to '{target}' (header, delimiter ',')").fetchone()[0]
    print(f"{name}.csv: {rows} rows")
con.close()
