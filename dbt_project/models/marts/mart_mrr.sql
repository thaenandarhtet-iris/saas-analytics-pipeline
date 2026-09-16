-- Mart: Monthly Recurring Revenue
-- Aggregated at month level by plan and customer cohort

with subscriptions as (
    select * from {{ ref('int_subscriptions_history') }}
),

plans as (
    select * from {{ source('raw', 'plans') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

mrr as (
    select 
        date_trunc('month', s.valid_from) as month,
        p.plan_name,
        c.region,
        count(distinct s.customer_id) as customer_count,
        sum(p.monthly_price) as total_mrr
    from subscriptions s
    join plans p on s.plan_id = p.plan_id
    join customers c on s.customer_id = c.customer_id
    where s.status = 'active'
    group by 1, 2, 3
)

select * from mrr
