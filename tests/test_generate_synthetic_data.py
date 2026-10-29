import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pytest
import yaml

import generate_synthetic_data as gen

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def tables():
    return gen.generate()


@pytest.fixture(scope="module")
def large():
    # Big enough that the configured patterns show clearly instead of being lost in noise.
    return gen.generate(n_customers=3000)


def cancel_dates(tables):
    customer_of = {s["subscription_id"]: s["customer_id"] for s in tables["subscriptions"]}
    return {
        customer_of[e["subscription_id"]]: date.fromisoformat(e["event_date"])
        for e in tables["subscription_events"]
        if e["event_type"] == "cancel"
    }


def test_same_seed_gives_identical_data(tables):
    assert gen.generate() == tables


def test_different_seed_gives_different_data(tables):
    assert gen.generate(seed=7) != tables


def test_changing_returned_tables_does_not_affect_later_runs():
    first = gen.generate()
    first["plans"][0]["monthly_price"] = 1
    assert gen.generate()["plans"][0]["monthly_price"] == gen.PRICE[1]


def test_dbt_month_window_matches_the_generator():
    # The dbt month spine and the generator each define the window; drift would silently
    # drop months from every monthly mart without failing any other test.
    project = yaml.safe_load((ROOT / "dbt_project" / "dbt_project.yml").read_text())
    assert project["vars"]["start_date"] == gen.START_DATE.isoformat()
    assert project["vars"]["end_date"] == gen.END_DATE.isoformat()


def test_main_writes_one_json_file_per_table(tables, tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    gen.main()
    assert {p.stem: json.loads(p.read_text()) for p in tmp_path.glob("*.json")} == tables


def test_default_run_matches_published_figures(tables):
    assert len(tables["customers"]) == 100
    assert len(tables["subscriptions"]) == 137
    assert len(tables["subscription_events"]) == 172
    assert len(tables["invoices"]) == 1559
    counts = Counter(e["event_type"] for e in tables["subscription_events"])
    assert counts == {"signup": 100, "upgrade": 22, "downgrade": 15, "cancel": 35}


def test_scd2_versions_are_contiguous_with_one_current_row(tables):
    versions = defaultdict(list)
    for s in tables["subscriptions"]:
        versions[s["customer_id"]].append(s)
    for customer_id, rows in versions.items():
        rows.sort(key=lambda s: s["valid_from"])
        for earlier, later in zip(rows, rows[1:]):
            assert earlier["valid_to"] == later["valid_from"], customer_id
        churned = rows[-1]["status"] == "canceled"
        assert sum(s["is_current"] for s in rows) == (0 if churned else 1), customer_id
        assert (rows[-1]["valid_to"] is None) != churned, customer_id


def test_no_dates_after_the_simulation_end(tables):
    end = gen.END_DATE.isoformat()
    assert all(e["event_date"] <= end for e in tables["subscription_events"])
    assert all(i["invoice_date"] <= end for i in tables["invoices"])
    assert all(s["valid_to"] is None or s["valid_to"] <= end for s in tables["subscriptions"])


def test_plan_changes_move_in_the_right_direction(tables):
    for e in tables["subscription_events"]:
        if e["event_type"] == "upgrade":
            assert e["new_plan_id"] > e["old_plan_id"]
        elif e["event_type"] == "downgrade":
            assert e["new_plan_id"] < e["old_plan_id"]


def test_invoices_bill_the_plan_price(tables):
    plan_of = {s["subscription_id"]: s["plan_id"] for s in tables["subscriptions"]}
    assert all(i["amount"] == gen.PRICE[plan_of[i["subscription_id"]]] for i in tables["invoices"])


def test_churn_is_much_higher_in_the_first_90_days(large):
    cancelled = cancel_dates(large)
    early_days = late_days = early_cancels = late_cancels = 0
    for c in large["customers"]:
        tenure = (cancelled.get(c["customer_id"], gen.END_DATE) - date.fromisoformat(c["signup_date"])).days
        early_days += min(90, tenure)
        late_days += max(0, tenure - 90)
        if c["customer_id"] in cancelled:
            early_cancels += tenure <= 90
            late_cancels += tenure > 90
    early_rate = early_cancels / early_days
    late_rate = late_cancels / late_days
    assert early_rate > 2 * late_rate


def test_cheaper_starting_plans_churn_more(large):
    starting_plan = {}
    for s in sorted(large["subscriptions"], key=lambda s: s["valid_from"]):
        starting_plan.setdefault(s["customer_id"], s["plan_id"])
    customers = Counter(starting_plan.values())
    churned = Counter(starting_plan[c] for c in cancel_dates(large))
    starter, pro, enterprise = (churned[p] / customers[p] for p in (1, 2, 3))
    assert starter > pro > enterprise


def test_signups_spike_in_january_and_september(large):
    days_in_month = Counter(d.month for d in gen.signup_candidate_days())
    signups = Counter(date.fromisoformat(c["signup_date"]).month for c in large["customers"])
    other = [m for m in range(1, 13) if m not in (1, 9)]
    baseline = sum(signups[m] for m in other) / sum(days_in_month[m] for m in other)
    assert signups[1] / days_in_month[1] > 2 * baseline
    assert signups[9] / days_in_month[9] > 1.75 * baseline
