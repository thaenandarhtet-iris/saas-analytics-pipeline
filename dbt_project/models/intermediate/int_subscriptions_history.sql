-- SCD2: full subscription history with plan details joined in
select
    s.subscription_id,
    s.customer_id,
    s.plan_id,
    p.plan_name,
    p.monthly_price,
    s.status,
    s.valid_from,
    s.valid_to,
    s.is_current,
    row_number() over (partition by s.customer_id order by s.valid_from) as subscription_sequence
from {{ ref('stg_subscriptions') }} s
left join {{ ref('stg_plans') }} p on s.plan_id = p.plan_id
