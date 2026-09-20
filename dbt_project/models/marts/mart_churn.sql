-- Cancellations by month and plan; tenure is measured from the customer's signup.
select
    cast(date_trunc('month', e.event_date) as date) as churn_month,
    h.plan_name,
    count(distinct e.subscription_id) as churned_subscriptions,
    round(avg(date_diff('day', c.signup_date, e.event_date)), 1) as avg_days_to_churn
from {{ ref('stg_subscription_events') }} e
join {{ ref('int_subscriptions_history') }} h on e.subscription_id = h.subscription_id
join {{ ref('dim_customers') }} c on h.customer_id = c.customer_id
where e.event_type = 'cancel'
group by 1, 2
order by 1, 2
