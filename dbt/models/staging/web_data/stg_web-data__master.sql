{{ config(materialized="view") }}

with
    unique_ids as (
        select *, row_number() over (partition by cast(link as string)) as rn
        from {{ source("staging", "master") }}
    )
select
    link,
    description,
    price,
    currency,
    start as start_city,
    unique_ids.end as end_city,
    date_from,
    date_to,
    collected_date,
    DATE_TRUNC(collected_date, DAY) as collected_day,
     {{ dbt_utils.surrogate_key(["description", "collected_date", "link"]) }} as trip_id
from unique_ids
where rn = 1
