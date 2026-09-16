select
    c.customer_id,
    c.company_name,
    c.industry,
    c.region,
    c.employee_size_band,
    c.signup_date,
    date_trunc('month', c.signup_date) as signup_cohort_month,
    case
        when churned.customer_id is not null then 'churned'
        else 'active'
    end as customer_status
from {{ ref('stg_customers') }} c
left join (
    select distinct s.customer_id
    from {{ ref('stg_subscription_events') }} e
    join {{ ref('stg_subscriptions') }} s on e.subscription_id = s.subscription_id
    where e.event_type = 'cancel'
) churned on c.customer_id = churned.customer_id
