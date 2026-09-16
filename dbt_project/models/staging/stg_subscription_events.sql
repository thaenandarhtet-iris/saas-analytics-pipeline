select 
    event_id,
    subscription_id,
    event_type,
    event_date,
    old_plan_id,
    new_plan_id
from {{ source('raw', 'raw_subscription_events') }}
