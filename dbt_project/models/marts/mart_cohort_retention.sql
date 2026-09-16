with cohorts as (
    select
        customer_id,
        date_trunc('month', signup_date) as cohort_month
    from {{ ref('dim_customers') }}
),

activity as (
    select
        h.customer_id,
        date_trunc('month', h.valid_from) as active_month
    from {{ ref('int_subscriptions_history') }} h
    where h.status = 'active'
)

select
    c.cohort_month,
    a.active_month,
    date_diff('month', c.cohort_month, a.active_month) as months_since_signup,
    count(distinct a.customer_id) as active_customers
from cohorts c
join activity a on c.customer_id = a.customer_id
group by 1, 2, 3
order by 1, 2
