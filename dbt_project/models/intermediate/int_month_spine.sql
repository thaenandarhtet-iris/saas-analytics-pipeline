-- One row per calendar month in the window set by the start_date and end_date vars.
select cast(m as date) as month_start
from generate_series(
    cast(date_trunc('month', date '{{ var("start_date") }}') as timestamp),
    cast(date_trunc('month', date '{{ var("end_date") }}') as timestamp),
    interval 1 month
) as t(m)
