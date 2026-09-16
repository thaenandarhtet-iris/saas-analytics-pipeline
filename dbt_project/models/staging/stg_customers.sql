select 
    customer_id,
    company_name,
    industry,
    region,
    employee_size_band,
    signup_date
from {{ source('raw', 'raw_customers') }}
