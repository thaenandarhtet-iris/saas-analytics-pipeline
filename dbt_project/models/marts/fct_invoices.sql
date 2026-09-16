select
    i.invoice_id,
    i.subscription_id,
    h.customer_id,
    h.plan_name,
    i.invoice_date,
    date_trunc('month', i.invoice_date) as invoice_month,
    i.amount,
    i.currency,
    i.status
from {{ ref('stg_invoices') }} i
left join {{ ref('int_subscriptions_history') }} h on i.subscription_id = h.subscription_id
