-- Any row returned is a failure.
select month, 'movements do not sum to net new MRR' as issue
from {{ ref('mart_mrr_movements') }}
where net_new_mrr != new_mrr + expansion_mrr + contraction_mrr + churned_mrr

union all

select m.month, 'ending MRR does not match the plan/region snapshot' as issue
from {{ ref('mart_mrr_movements') }} m
join (
    select month, sum(total_mrr) as snapshot_mrr
    from {{ ref('mart_mrr') }}
    group by 1
) s on m.month = s.month
where m.ending_mrr != s.snapshot_mrr
