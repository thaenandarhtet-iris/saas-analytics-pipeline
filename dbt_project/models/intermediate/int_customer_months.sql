-- One row per customer per month in the window: the shared base for every monthly metric.
-- plan_name and mrr describe the version live on the last day of the month
-- (valid_from <= day < valid_to), so they are null and 0 when nothing is live then.
-- is_active is true if any version was live at some point during the month, which
-- includes a customer who churned partway through it.
with customer_months as (
    select c.customer_id, s.month_start
    from {{ ref('stg_customers') }} c
    cross join {{ ref('int_month_spine') }} s
),

month_end_version as (
    select cm.customer_id, cm.month_start, h.plan_name, h.monthly_price
    from customer_months cm
    join {{ ref('int_subscriptions_history') }} h
      on h.customer_id = cm.customer_id
     and h.valid_from <= last_day(cm.month_start)
     and coalesce(h.valid_to, date '9999-12-31') > last_day(cm.month_start)
),

active_in_month as (
    select distinct cm.customer_id, cm.month_start
    from customer_months cm
    join {{ ref('int_subscriptions_history') }} h
      on h.customer_id = cm.customer_id
     and h.valid_from <= last_day(cm.month_start)
     and coalesce(h.valid_to, date '9999-12-31') >= cm.month_start
)

select
    cm.customer_id,
    cm.month_start,
    v.plan_name,
    coalesce(v.monthly_price, 0) as mrr,
    a.customer_id is not null as is_active
from customer_months cm
left join month_end_version v
  on cm.customer_id = v.customer_id and cm.month_start = v.month_start
left join active_in_month a
  on cm.customer_id = a.customer_id and cm.month_start = a.month_start
