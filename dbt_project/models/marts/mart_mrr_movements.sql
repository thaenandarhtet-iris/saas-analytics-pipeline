-- Month-over-month MRR bridge: new + expansion + contraction + churned = net new.
with month_spine as (
    select cast(m as date) as month_start
    from generate_series(
        cast(date_trunc('month', date '{{ var("start_date") }}') as timestamp),
        cast(date_trunc('month', date '{{ var("end_date") }}') as timestamp),
        interval 1 month
    ) as t(m)
),

customer_months as (
    select c.customer_id, s.month_start
    from {{ ref('dim_customers') }} c
    cross join month_spine s
),

snapshot as (
    select
        cm.customer_id,
        cm.month_start,
        coalesce(h.monthly_price, 0) as mrr
    from customer_months cm
    left join {{ ref('int_subscriptions_history') }} h
      on h.customer_id = cm.customer_id
     and h.valid_from <= last_day(cm.month_start)
     and coalesce(h.valid_to, date '9999-12-31') > last_day(cm.month_start)
),

with_prev as (
    select
        customer_id,
        month_start,
        mrr,
        coalesce(lag(mrr) over (partition by customer_id order by month_start), 0) as prev_mrr
    from snapshot
)

select
    month_start as month,
    sum(mrr) as ending_mrr,
    sum(case when prev_mrr = 0 and mrr > 0 then mrr else 0 end) as new_mrr,
    sum(case when prev_mrr > 0 and mrr > prev_mrr then mrr - prev_mrr else 0 end) as expansion_mrr,
    sum(case when prev_mrr > 0 and mrr > 0 and mrr < prev_mrr then mrr - prev_mrr else 0 end) as contraction_mrr,
    sum(case when prev_mrr > 0 and mrr = 0 then -prev_mrr else 0 end) as churned_mrr,
    sum(mrr - prev_mrr) as net_new_mrr,
    count(case when mrr > 0 then 1 end) as active_customers,
    count(case when prev_mrr > 0 then 1 end) as starting_customers,
    count(case when prev_mrr > 0 and mrr = 0 then 1 end) as churned_customers
from with_prev
group by 1
order by 1
