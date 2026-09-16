select
    date_trunc('month', e.event_date) as churn_month,
    h.plan_name,
    count(distinct e.subscription_id) as churned_subscriptions,
    avg(date_diff('day', h.valid_from, e.event_date)) as avg_days_to_churn
from {{ ref('stg_subscription_events') }} e
join {{ ref('int_subscriptions_history') }} h on e.subscription_id = h.subscription_id
where e.event_type = 'cancel'
group by 1, 2
order by 1
