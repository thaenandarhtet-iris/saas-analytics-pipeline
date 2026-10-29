-- MRR at each month end, by plan and region. A snapshot, so never sum it across months.
select
    cm.month_start as month,
    cm.plan_name,
    c.region,
    count(*) as customer_count,
    sum(cm.mrr) as total_mrr
from {{ ref('int_customer_months') }} cm
join {{ ref('dim_customers') }} c on cm.customer_id = c.customer_id
where cm.plan_name is not null
group by 1, 2, 3
order by 1, 2, 3
