"""Load the generated JSON files into DuckDB as raw_* tables."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "dbt_project" / "dbt.duckdb"
SOURCE_DIR = ROOT / "data_generation" / "output"
TABLES = ["customers", "plans", "subscriptions", "subscription_events", "invoices"]

con = duckdb.connect(str(DB_PATH))
for table in TABLES:
    path = SOURCE_DIR / f"{table}.json"
    con.execute(f"create or replace table raw_{table} as select * from read_json_auto('{path}')")
    rows = con.execute(f"select count(*) from raw_{table}").fetchone()[0]
    print(f"raw_{table}: {rows} rows")
con.close()
