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

select customer_id, month_start, 'billed at month end but not active that month' as issue
from {{ ref('int_customer_months') }}
where mrr > 0 and not is_active
