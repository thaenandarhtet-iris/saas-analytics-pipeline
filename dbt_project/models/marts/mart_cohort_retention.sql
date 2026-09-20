with month_spine as (
    select cast(month_start as date) as month_start
    from generate_series(timestamp '2023-09-01', timestamp '2026-09-01', interval 1 month) as t(month_start)
),

cohorts as (
    select
        customer_id,
        cast(date_trunc('month', signup_date) as date) as cohort_month
    from {{ ref('dim_customers') }}
),

cohort_sizes as (
    select cohort_month, count(*) as cohort_size
    from cohorts
    group by 1
),

activity as (
    select distinct h.customer_id, m.month_start as active_month
    from {{ ref('int_subscriptions_history') }} h
    join month_spine m
      on h.valid_from < m.month_start + interval 1 month
     and coalesce(h.valid_to, date '9999-12-31') >= m.month_start
)

select
    c.cohort_month,
    a.active_month,
    date_diff('month', c.cohort_month, a.active_month) as months_since_signup,
    count(distinct a.customer_id) as active_customers,
    s.cohort_size,
    round(100.0 * count(distinct a.customer_id) / s.cohort_size, 1) as retention_pct
from cohorts c
join activity a on c.customer_id = a.customer_id and a.active_month >= c.cohort_month
join cohort_sizes s on c.cohort_month = s.cohort_month
group by c.cohort_month, a.active_month, s.cohort_size
order by 1, 2
