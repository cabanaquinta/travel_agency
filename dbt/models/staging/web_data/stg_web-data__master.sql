{{ config(materialized="view") }}

with
    unique_ids as (
        select
            *,
            row_number() over (
                partition by cast(link as string)
            ) as rn
        from {{ source("staging", "master") }}
        where collected_date >= 2022
    )
select
    *
    -- {{ get_payment_type("payment_type") }} as payment_type_description,
    -- {{ dbt_utils.surrogate_key(["VendorID", "tpep_pickup_datetime"]) }} as trip_id
from unique_ids
where rn = 1