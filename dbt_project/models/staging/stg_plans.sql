select 
    plan_id,
    plan_name,
    monthly_price,
    annual_price
from {{ source('raw', 'raw_plans') }}
