-- Intermediate: SCD Type 2 logic applied
-- Tracks full subscription history with validity dates
-- Key insight: one row per (customer, plan, period)

with source as (
    select * from {{ source('raw', 'subscriptions') }}
),

with_row_nums as (
    select 
        *,
        row_number() over (partition by subscription_id order by valid_from) as subscription_version
    from source
)

select 
    subscription_id,
    customer_id,
    plan_id,
    status,
    valid_from,
    valid_to,
    is_current,
    subscription_version,
    current_timestamp as dbt_run_at
from with_row_nums
