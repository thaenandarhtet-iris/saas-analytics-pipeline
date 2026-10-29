-- One row per customer per month in the window: the shared base for every monthly metric.
-- A version is live on a day when valid_from <= day < valid_to (valid_to is exclusive).
--   plan_name, mrr: the version live on the last day of the month (null and 0 if none).
--   is_active: some version was live on at least one day of the month.
--   versions_live_at_month_end: should never exceed 1; tested in assert_customer_months_complete.
with customer_months as (
    select c.customer_id, s.month_start, last_day(s.month_start) as month_end
    from {{ ref('stg_customers') }} c
    cross join {{ ref('int_month_spine') }} s
),

versions_in_month as (
    select
        cm.customer_id,
        cm.month_start,
        h.plan_name,
        h.monthly_price,
        coalesce(h.valid_to, date '9999-12-31') > cm.month_end as live_at_month_end
    from customer_months cm
    join {{ ref('int_subscriptions_history') }} h
      on h.customer_id = cm.customer_id
     and h.valid_from <= cm.month_end
     and coalesce(h.valid_to, date '9999-12-31') > cm.month_start
),

per_month as (
    select
        customer_id,
        month_start,
        max(case when live_at_month_end then plan_name end) as plan_name,
        max(case when live_at_month_end then monthly_price end) as monthly_price,
        count(case when live_at_month_end then 1 end) as versions_live_at_month_end
    from versions_in_month
    group by 1, 2
)

select
    cm.customer_id,
    cm.month_start,
    p.plan_name,
    coalesce(p.monthly_price, 0) as mrr,
    p.customer_id is not null as is_active,
    coalesce(p.versions_live_at_month_end, 0) as versions_live_at_month_end
from customer_months cm
left join per_month p
  on cm.customer_id = p.customer_id and cm.month_start = p.month_start
