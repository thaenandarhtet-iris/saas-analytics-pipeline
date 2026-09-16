"""
Generate synthetic SaaS subscription data for analytics pipeline.
100 customers, 3 years of history (2023-2026).
Patterns: early churn, tier-based churn, seasonality, upgrades/downgrades.
"""

import json
from datetime import datetime, timedelta
from faker import Faker
import random

fake = Faker()

def generate_customers(n=100):
    """Generate customer records."""
    customers = []
    industries = ["SaaS", "FinTech", "Healthcare", "E-commerce", "Education", "Manufacturing"]
    regions = ["US", "EU", "APAC", "LATAM"]
    employee_bands = ["1-10", "11-50", "51-200", "200+"]
    
    for i in range(n):
        customers.append({
            "customer_id": f"CUST_{i+1:04d}",
            "company_name": fake.company(),
            "industry": random.choice(industries),
            "region": random.choice(regions),
            "employee_size_band": random.choice(employee_bands),
            "signup_date": fake.date_between(start_date="-3y", end_date="today")
        })
    return customers

def generate_plans():
    """Generate plan offerings."""
    return [
        {"plan_id": 1, "plan_name": "Starter", "monthly_price": 29, "annual_price": 290},
        {"plan_id": 2, "plan_name": "Pro", "monthly_price": 99, "annual_price": 990},
        {"plan_id": 3, "plan_name": "Enterprise", "monthly_price": 299, "annual_price": 2990}
    ]

def generate_subscriptions(customers, plans):
    """Generate subscriptions with SCD2 records."""
    subscriptions = []
    subscription_events = []
    sub_id = 1
    event_id = 1
    
    for customer in customers:
        signup_date = datetime.strptime(str(customer["signup_date"]), "%Y-%m-%d")
        current_date = datetime.now()
        
        # Initial plan assignment (biased toward Starter/Pro)
        plan_weights = {1: 0.5, 2: 0.35, 3: 0.15}
        initial_plan = random.choices(list(plan_weights.keys()), weights=list(plan_weights.values()))[0]
        
        # Churn logic: 40% in first 3 months, less for Enterprise
        days_since_signup = (current_date - signup_date).days
        should_churn = False
        churn_date = None
        
        if days_since_signup >= 90:
            if initial_plan == 1:  # Starter churns more
                should_churn = random.random() < 0.35
            elif initial_plan == 2:
                should_churn = random.random() < 0.20
            else:
                should_churn = random.random() < 0.08
                
            if should_churn:
                churn_date = signup_date + timedelta(days=random.randint(30, min(120, days_since_signup)))
        
        # Handle upgrades/downgrades (30% of non-churned customers)
        has_upgrade = False
        upgrade_date = None
        upgrade_plan = initial_plan
        
        if not should_churn and random.random() < 0.30:
            has_upgrade = True
            upgrade_date = signup_date + timedelta(days=random.randint(60, 500))
            if upgrade_date < churn_date if churn_date else current_date:
                # Upgrade to higher tier
                if initial_plan == 1:
                    upgrade_plan = random.choice([2, 3])
                elif initial_plan == 2:
                    upgrade_plan = 3
        
        # Create subscription records (SCD2)
        # Initial subscription
        subscriptions.append({
            "subscription_id": f"SUB_{sub_id:06d}",
            "customer_id": customer["customer_id"],
            "plan_id": initial_plan,
            "status": "active",
            "valid_from": signup_date.date(),
            "valid_to": (upgrade_date.date() if has_upgrade else churn_date.date() if should_churn else None),
            "is_current": False if has_upgrade or should_churn else True
        })
        
        subscription_events.append({
            "event_id": f"EVT_{event_id:06d}",
            "subscription_id": f"SUB_{sub_id:06d}",
            "event_type": "signup",
            "event_date": signup_date.date(),
            "old_plan_id": None,
            "new_plan_id": initial_plan
        })
        event_id += 1
        
        # Upgrade record if applicable
        if has_upgrade:
            sub_id += 1
            subscriptions.append({
                "subscription_id": f"SUB_{sub_id:06d}",
                "customer_id": customer["customer_id"],
                "plan_id": upgrade_plan,
                "status": "active",
                "valid_from": upgrade_date.date(),
                "valid_to": churn_date.date() if should_churn else None,
                "is_current": not should_churn
            })
            
            subscription_events.append({
                "event_id": f"EVT_{event_id:06d}",
                "subscription_id": f"SUB_{sub_id:06d}",
                "event_type": "upgrade" if upgrade_plan > initial_plan else "downgrade",
                "event_date": upgrade_date.date(),
                "old_plan_id": initial_plan,
                "new_plan_id": upgrade_plan
            })
            event_id += 1
        
        # Cancel event if churned
        if should_churn:
            subscription_events.append({
                "event_id": f"EVT_{event_id:06d}",
                "subscription_id": f"SUB_{sub_id:06d}",
                "event_type": "cancel",
                "event_date": churn_date.date(),
                "old_plan_id": upgrade_plan if has_upgrade else initial_plan,
                "new_plan_id": None
            })
            event_id += 1
        
        sub_id += 1
    
    return subscriptions, subscription_events

def generate_invoices(subscriptions):
    """Generate invoice records based on subscriptions."""
    invoices = []
    plans = {1: 29, 2: 99, 3: 299}  # monthly prices
    invoice_id = 1
    
    for sub in subscriptions:
        if sub["status"] == "active":
            start = datetime.strptime(str(sub["valid_from"]), "%Y-%m-%d")
            end = datetime.strptime(str(sub["valid_to"]), "%Y-%m-%d") if sub["valid_to"] else datetime.now()
            
            current = start
            while current < end:
                invoices.append({
                    "invoice_id": f"INV_{invoice_id:08d}",
                    "subscription_id": sub["subscription_id"],
                    "invoice_date": current.date(),
                    "amount": plans.get(sub["plan_id"], 29),
                    "currency": "USD",
                    "status": random.choice(["paid", "paid", "paid", "failed"])  # 75% paid
                })
                invoice_id += 1
                current += timedelta(days=30)
    
    return invoices

def save_data(customers, plans, subscriptions, subscription_events, invoices):
    """Save data as JSON files."""
    output_dir = "data_generation/output"
    
    with open(f"{output_dir}/customers.json", "w") as f:
        json.dump(customers, f, indent=2, default=str)
    
    with open(f"{output_dir}/plans.json", "w") as f:
        json.dump(plans, f, indent=2, default=str)
    
    with open(f"{output_dir}/subscriptions.json", "w") as f:
        json.dump(subscriptions, f, indent=2, default=str)
    
    with open(f"{output_dir}/subscription_events.json", "w") as f:
        json.dump(subscription_events, f, indent=2, default=str)
    
    with open(f"{output_dir}/invoices.json", "w") as f:
        json.dump(invoices, f, indent=2, default=str)
    
    print(f"✓ Generated data for {len(customers)} customers")
    print(f"✓ {len(subscriptions)} subscription records (SCD2)")
    print(f"✓ {len(subscription_events)} events")
    print(f"✓ {len(invoices)} invoices")

if __name__ == "__main__":
    import os
    os.makedirs("data_generation/output", exist_ok=True)
    
    customers = generate_customers(100)
    plans = generate_plans()
    subscriptions, subscription_events = generate_subscriptions(customers, plans)
    invoices = generate_invoices(subscriptions)
    
    save_data(customers, plans, subscriptions, subscription_events, invoices)
