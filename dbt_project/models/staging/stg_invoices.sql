select 
    invoice_id,
    subscription_id,
    invoice_date,
    amount,
    currency,
    status
from {{ source('raw', 'raw_invoices') }}
