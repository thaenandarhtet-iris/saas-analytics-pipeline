-- Cohort retention on a full cohort-by-age grid, counting a customer as retained in any
-- month they were active (see int_customer_months). Cells where the whole cohort has
-- churned are kept, with 0 active customers.
with cohorts as (
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
    join {{ ref('int_month_spine') }} m on m.month_start >= s.cohort_month
),

active_counts as (
    select
        c.cohort_month,
        cm.month_start as active_month,
        count(*) as active_customers
    from cohorts c
    join {{ ref('int_customer_months') }} cm
      on c.customer_id = cm.customer_id and cm.month_start >= c.cohort_month
    where cm.is_active
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
