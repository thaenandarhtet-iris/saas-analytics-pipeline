-- Any row returned is a failure. Two versions of one customer's subscription must never be
-- live on the same day; every monthly metric assumes at most one live version at a time.
select
    a.customer_id,
    a.subscription_id as first_version,
    b.subscription_id as second_version
from {{ ref('int_subscriptions_history') }} a
join {{ ref('int_subscriptions_history') }} b
  on a.customer_id = b.customer_id
 and a.subscription_id < b.subscription_id
 and a.valid_from < coalesce(b.valid_to, date '9999-12-31')
 and b.valid_from < coalesce(a.valid_to, date '9999-12-31')
