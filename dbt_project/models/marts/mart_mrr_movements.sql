-- Month-over-month MRR bridge: new + expansion + contraction + churned = net new.
with with_prev as (
    select
        customer_id,
        month_start,
        mrr,
        coalesce(lag(mrr) over (partition by customer_id order by month_start), 0) as prev_mrr
    from {{ ref('int_customer_months') }}
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
