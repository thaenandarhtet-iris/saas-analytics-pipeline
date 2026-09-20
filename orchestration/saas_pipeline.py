"""Run the whole pipeline locally: generate -> load -> dbt run -> dbt test -> export.

Usage:
    python orchestration/saas_pipeline.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
DBT = str(Path(sys.executable).with_name("dbt"))

STEPS = [
    ("Generate synthetic data", [PYTHON, "data_generation/generate_synthetic_data.py"], ROOT),
    ("Load raw JSON into DuckDB", [PYTHON, "ingestion/load_to_duckdb.py"], ROOT),
    ("Run dbt models", [DBT, "run", "--full-refresh"], ROOT / "dbt_project"),
    ("Run dbt tests", [DBT, "test"], ROOT / "dbt_project"),
    ("Export CSVs for Tableau", [PYTHON, "dashboards/export_csvs.py"], ROOT),
]


def main():
    for number, (name, command, cwd) in enumerate(STEPS, start=1):
        print(f"\n[{number}/{len(STEPS)}] {name}", flush=True)
        if subprocess.run(command, cwd=cwd).returncode != 0:
            sys.exit(f"Step failed: {name}")
    print("\nPipeline finished.")


if __name__ == "__main__":
    main()
