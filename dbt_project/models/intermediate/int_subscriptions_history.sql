-- SCD2 subscription versions with plan name and price joined in.
select
    s.subscription_id,
    s.customer_id,
    s.plan_id,
    p.plan_name,
    p.monthly_price,
    s.status,
    s.valid_from,
    s.valid_to,
    s.is_current
from {{ ref('stg_subscriptions') }} s
left join {{ ref('stg_plans') }} p on s.plan_id = p.plan_id
