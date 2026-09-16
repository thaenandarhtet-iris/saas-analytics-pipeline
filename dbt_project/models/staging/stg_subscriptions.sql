select 
    subscription_id,
    customer_id,
    plan_id,
    status,
    valid_from,
    valid_to,
    is_current
from {{ source('raw', 'raw_subscriptions') }}
