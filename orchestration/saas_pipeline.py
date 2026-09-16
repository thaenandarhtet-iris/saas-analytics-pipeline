"""
Orchestration script: runs the full SaaS analytics pipeline locally.
Steps: data generation -> dbt staging -> intermediate -> marts -> test

Usage:
  python orchestration/saas_pipeline.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and exit on failure."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(__file__) or ".")
    if result.returncode != 0:
        print(f"❌ {description} failed")
        sys.exit(1)
    print(f"✓ {description} complete")

def main():
    root = Path(__file__).parent.parent
    
    # Step 1: Generate synthetic data
    run_command(
        f"python {root}/data_generation/generate_synthetic_data.py",
        "Step 1: Generate synthetic data"
    )
    
    # Step 2: Run dbt (stages, intermediate, marts)
    run_command(
        f"cd {root}/dbt_project && dbt run --select staging intermediate marts",
        "Step 2: Run dbt models"
    )
    
    # Step 3: Test data quality
    run_command(
        f"cd {root}/dbt_project && dbt test",
        "Step 3: Test data quality"
    )
    
    # Step 4: Generate docs
    run_command(
        f"cd {root}/dbt_project && dbt docs generate",
        "Step 4: Generate dbt documentation"
    )
    
    print(f"\n{'='*60}")
    print("✓ Pipeline complete!")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("  1. Check output tables in DuckDB")
    print("  2. Build Tableau dashboards")
    print("  3. Review dbt docs: open dbt_project/target/index.html")

if __name__ == "__main__":
    main()
