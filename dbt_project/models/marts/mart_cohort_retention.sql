-- Cohort retention on a full cohort-by-age grid. A customer counts as active in a
-- month if any of their subscription versions was live at some point in that month.
-- Cells where the whole cohort has churned are kept, with 0 active customers.
with month_spine as (
    select cast(m as date) as month_start
    from generate_series(
        cast(date_trunc('month', date '{{ var("start_date") }}') as timestamp),
        cast(date_trunc('month', date '{{ var("end_date") }}') as timestamp),
        interval 1 month
    ) as t(m)
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

cohort_grid as (
    select
        s.cohort_month,
        s.cohort_size,
        m.month_start as active_month,
        date_diff('month', s.cohort_month, m.month_start) as months_since_signup
    from cohort_sizes s
    join month_spine m on m.month_start >= s.cohort_month
),

activity as (
    select distinct h.customer_id, m.month_start as active_month
    from {{ ref('int_subscriptions_history') }} h
    join month_spine m
      on h.valid_from < m.month_start + interval 1 month
     and coalesce(h.valid_to, date '9999-12-31') >= m.month_start
),

active_counts as (
    select
        c.cohort_month,
        a.active_month,
        count(distinct a.customer_id) as active_customers
    from cohorts c
    join activity a on c.customer_id = a.customer_id and a.active_month >= c.cohort_month
    group by 1, 2
)

select
    g.cohort_month,
    g.active_month,
    g.months_since_signup,
    coalesce(ac.active_customers, 0) as active_customers,
    g.cohort_size,
    round(100.0 * coalesce(ac.active_customers, 0) / g.cohort_size, 1) as retention_pct
from cohort_grid g
left join active_counts ac
  on g.cohort_month = ac.cohort_month and g.active_month = ac.active_month
order by 1, 2
