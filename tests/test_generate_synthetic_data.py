import json
from collections import Counter, defaultdict

import pytest

import generate_synthetic_data as gen


def run(tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    gen.main()
    return {p.stem: json.loads(p.read_text()) for p in tmp_path.glob("*.json")}


@pytest.fixture
def tables(tmp_path, monkeypatch):
    return run(tmp_path, monkeypatch)


def test_same_seed_gives_identical_data(tables, tmp_path_factory, monkeypatch):
    assert run(tmp_path_factory.mktemp("second"), monkeypatch) == tables


def test_row_counts_match_readme(tables):
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
