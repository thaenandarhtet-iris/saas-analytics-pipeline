select
    date_trunc('month', h.valid_from) as month,
    h.plan_name,
    c.region,
    count(distinct h.customer_id) as customer_count,
    sum(h.monthly_price) as total_mrr
from {{ ref('int_subscriptions_history') }} h
join {{ ref('dim_customers') }} c on h.customer_id = c.customer_id
where h.status = 'active'
group by 1, 2, 3
order by 1
