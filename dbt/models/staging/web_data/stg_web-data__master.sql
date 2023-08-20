{{ config(materialized="view") }}

with
    unique_ids as (
        select *, row_number() over (partition by cast(link as string)) as rn
        from {{ source("staging", "master") }}
    )
select
    *,
     {{ dbt_utils.surrogate_key(["description", "collected_date", "link"]) }} as trip_id
from unique_ids
where rn = 1
