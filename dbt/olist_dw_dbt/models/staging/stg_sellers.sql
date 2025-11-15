{{
    config(
        materialized='view',
        tags=['staging', 'sellers']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_sellers_dataset.csv', header = true, auto_detect = true)
),

cleaned AS (
    SELECT
        -- Primary key
        seller_id,

        -- Location attributes
        seller_zip_code_prefix,
        seller_city,
        seller_state,

        -- Standardize state abbreviation (uppercase, trim)
        upper(trim(seller_state)) AS seller_state_clean

    FROM source
    WHERE seller_id IS NOT null
)

SELECT * FROM cleaned
