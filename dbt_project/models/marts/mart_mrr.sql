-- MRR snapshot at each month end, by plan and region.
-- A subscription version is live on a date when valid_from <= date < valid_to.
with month_spine as (
    select cast(m as date) as month_start
    from generate_series(
        cast(date_trunc('month', date '{{ var("start_date") }}') as timestamp),
        cast(date_trunc('month', date '{{ var("end_date") }}') as timestamp),
        interval 1 month
    ) as t(m)
)

select
    s.month_start as month,
    h.plan_name,
    c.region,
    count(distinct h.customer_id) as customer_count,
    sum(h.monthly_price) as total_mrr
from month_spine s
join {{ ref('int_subscriptions_history') }} h
  on h.valid_from <= last_day(s.month_start)
 and coalesce(h.valid_to, date '9999-12-31') > last_day(s.month_start)
join {{ ref('dim_customers') }} c on h.customer_id = c.customer_id
group by 1, 2, 3
order by 1, 2, 3
