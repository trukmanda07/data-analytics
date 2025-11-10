{{
    config(
        materialized='view',
        tags=['staging', 'customers']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_customers_dataset.csv', header=true, auto_detect=true)
),

cleaned AS (
    SELECT
        -- Primary key
        customer_id,

        -- Unique customer identifier (for tracking same person across multiple customer_ids)
        customer_unique_id,

        -- Location attributes
        customer_zip_code_prefix,
        customer_city,
        customer_state,

        -- Standardize state abbreviation (uppercase, trim)
        UPPER(TRIM(customer_state)) AS customer_state_clean

    FROM source
    WHERE customer_id IS NOT NULL
)

SELECT * FROM cleaned
