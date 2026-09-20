"""
Synthetic SaaS subscription data: 100 customers, 3 years of history.

Patterns baked in on purpose:
  * churn is highest in the first 3 months of a customer's life
  * Starter churns more than Pro, Pro more than Enterprise
  * signups spike in January and September
  * some customers upgrade or downgrade, so the SCD2 table has real history

Subscription status describes how each version ended: 'active' for versions
replaced by a plan change or still open, 'canceled' for a customer's last version.
"""
import json
import random
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

from dateutil.relativedelta import relativedelta
from faker import Faker

SEED = 42
N_CUSTOMERS = 100
START_DATE = date(2023, 9, 16)
END_DATE = date(2026, 9, 16)
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

PLANS = [
    {"plan_id": 1, "plan_name": "Starter", "monthly_price": 29, "annual_price": 290},
    {"plan_id": 2, "plan_name": "Pro", "monthly_price": 99, "annual_price": 990},
    {"plan_id": 3, "plan_name": "Enterprise", "monthly_price": 299, "annual_price": 2990},
]
PRICE = {p["plan_id"]: p["monthly_price"] for p in PLANS}

MONTHLY_CHURN = {1: 0.025, 2: 0.015, 3: 0.005}
EARLY_CHURN_MULTIPLIER = 3
UPGRADE_PROB = {1: 0.025, 2: 0.015, 3: 0.0}
DOWNGRADE_PROB = {1: 0.0, 2: 0.020, 3: 0.020}
SIGNUP_SEASONALITY = {1: 3.0, 9: 2.5}

INDUSTRIES = ["SaaS", "FinTech", "Healthcare", "E-commerce", "Education", "Manufacturing"]
REGIONS = ["US", "EU", "APAC", "LATAM"]
SIZE_BANDS = ["1-10", "11-50", "51-200", "200+"]


def rand_day(start, end):
    return start + timedelta(days=random.randrange(1, (end - start).days))


def signup_dates(n):
    days = [START_DATE + timedelta(days=i) for i in range((END_DATE - START_DATE).days - 30)]
    weights = [SIGNUP_SEASONALITY.get(d.month, 1.0) for d in days]
    return sorted(random.choices(days, weights=weights, k=n))


def simulate_customer(signup_date):
    plan_id = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
    periods = []
    period_start, opened_by = signup_date, "signup"
    month = 1
    while True:
        window_start = signup_date + relativedelta(months=month - 1)
        window_end = min(signup_date + relativedelta(months=month), END_DATE)
        if (window_end - window_start).days < 2:
            break
        churn_p = MONTHLY_CHURN[plan_id] * (EARLY_CHURN_MULTIPLIER if month <= 3 else 1)
        up_p = UPGRADE_PROB[plan_id] if month >= 2 else 0
        down_p = DOWNGRADE_PROB[plan_id] if month >= 2 else 0
        roll = random.random()
        if roll < churn_p:
            periods.append((plan_id, period_start, rand_day(window_start, window_end), opened_by))
            return periods, True
        if roll < churn_p + up_p + down_p:
            change_date = rand_day(window_start, window_end)
            periods.append((plan_id, period_start, change_date, opened_by))
            if roll < churn_p + up_p:
                plan_id = 3 if plan_id == 2 else random.choices([2, 3], weights=[0.8, 0.2])[0]
                opened_by = "upgrade"
            else:
                plan_id -= 1
                opened_by = "downgrade"
            period_start = change_date
        month += 1
    periods.append((plan_id, period_start, None, opened_by))
    return periods, False


def build_tables(customers):
    subscriptions, events, invoices = [], [], []
    sub_n = evt_n = inv_n = 0
    for c in customers:
        periods, canceled = simulate_customer(date.fromisoformat(c["signup_date"]))
        prev_plan = None
        for i, (plan_id, start, end, opened_by) in enumerate(periods):
            is_last = i == len(periods) - 1
            sub_n += 1
            sub_id = f"SUB_{sub_n:06d}"
            subscriptions.append({
                "subscription_id": sub_id,
                "customer_id": c["customer_id"],
                "plan_id": plan_id,
                "status": "canceled" if (is_last and canceled) else "active",
                "valid_from": start.isoformat(),
                "valid_to": end.isoformat() if end else None,
                "is_current": is_last and not canceled,
            })
            evt_n += 1
            events.append({
                "event_id": f"EVT_{evt_n:06d}",
                "subscription_id": sub_id,
                "event_type": opened_by,
                "event_date": start.isoformat(),
                "old_plan_id": prev_plan,
                "new_plan_id": plan_id,
            })
            if is_last and canceled:
                evt_n += 1
                events.append({
                    "event_id": f"EVT_{evt_n:06d}",
                    "subscription_id": sub_id,
                    "event_type": "cancel",
                    "event_date": end.isoformat(),
                    "old_plan_id": plan_id,
                    "new_plan_id": None,
                })
            k, bill = 0, start
            stop = end or END_DATE
            while bill < stop and bill <= END_DATE:
                inv_n += 1
                invoices.append({
                    "invoice_id": f"INV_{inv_n:08d}",
                    "subscription_id": sub_id,
                    "invoice_date": bill.isoformat(),
                    "amount": PRICE[plan_id],
                    "currency": "USD",
                    "status": random.choices(["paid", "failed", "refunded"], weights=[0.93, 0.05, 0.02])[0],
                })
                k += 1
                bill = start + relativedelta(months=k)
            prev_plan = plan_id
    return subscriptions, events, invoices


def main():
    random.seed(SEED)
    Faker.seed(SEED)
    fake = Faker()

    customers = [
        {
            "customer_id": f"CUST_{i + 1:04d}",
            "company_name": fake.company(),
            "industry": random.choice(INDUSTRIES),
            "region": random.choice(REGIONS),
            "employee_size_band": random.choice(SIZE_BANDS),
            "signup_date": d.isoformat(),
        }
        for i, d in enumerate(signup_dates(N_CUSTOMERS))
    ]
    subscriptions, events, invoices = build_tables(customers)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in {
        "customers": customers,
        "plans": PLANS,
        "subscriptions": subscriptions,
        "subscription_events": events,
        "invoices": invoices,
    }.items():
        (OUTPUT_DIR / f"{name}.json").write_text(json.dumps(rows, indent=2))

    counts = Counter(e["event_type"] for e in events)
    signups = Counter(date.fromisoformat(c["signup_date"]).month for c in customers)
    print(f"customers: {len(customers)}, subscription versions: {len(subscriptions)}, invoices: {len(invoices)}")
    print(f"events: {dict(counts)}")
    print(f"churned customers: {counts['cancel']} ({counts['cancel'] / len(customers):.0%})")
    print(f"signups by calendar month: {dict(sorted(signups.items()))}")


if __name__ == "__main__":
    main()
