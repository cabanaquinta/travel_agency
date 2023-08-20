{{ config(materialized="view") }}

with
    unique_ids as (
        select *, row_number() over (partition by cast(link as string)) as rn
        from {{ source("staging", "master") }}
    )
select 
    *
from unique_ids
where rn = 1
