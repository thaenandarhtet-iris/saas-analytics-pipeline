-- Any row returned is a failure.
select customer_id, month_start, 'more than one row for this customer and month' as issue
from {{ ref('int_customer_months') }}
group by 1, 2
having count(*) > 1

union all

select null, null, 'row count is not customers x months' as issue
where (select count(*) from {{ ref('int_customer_months') }})
   != (select count(*) from {{ ref('stg_customers') }}) * (select count(*) from {{ ref('int_month_spine') }})

union all

select customer_id, month_start, 'more than one version live at month end' as issue
from {{ ref('int_customer_months') }}
where versions_live_at_month_end > 1

union all

select customer_id, month_start, 'billed at month end but not active that month' as issue
from {{ ref('int_customer_months') }}
where mrr > 0 and not is_active

union all

-- Checked against cancel events rather than the model's own date logic, so a boundary
-- mistake in int_customer_months cannot also hide here.
select cm.customer_id, cm.month_start, 'active in a month that starts on or after cancellation' as issue
from {{ ref('int_customer_months') }} cm
join (
    select s.customer_id, e.event_date as cancel_date
    from {{ ref('stg_subscription_events') }} e
    join {{ ref('stg_subscriptions') }} s on e.subscription_id = s.subscription_id
    where e.event_type = 'cancel'
) c on cm.customer_id = c.customer_id
where cm.is_active and cm.month_start >= c.cancel_date
