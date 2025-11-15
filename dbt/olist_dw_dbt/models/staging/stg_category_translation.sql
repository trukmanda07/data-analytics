{{
    config(
        materialized='view',
        tags=['staging', 'category_translation']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/product_category_name_translation.csv', header = true, auto_detect = true)
),

cleaned AS (
    SELECT
        -- Portuguese category name (primary key)
        product_category_name,

        -- English translation
        product_category_name_english,

        -- Clean English name for display (replace underscores with spaces)
        replace(product_category_name_english, '_', ' ') AS category_display_name

    FROM source
    WHERE product_category_name IS NOT null
)

SELECT * FROM cleaned
