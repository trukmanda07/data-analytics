{{
    config(
        materialized='view',
        tags=['staging', 'products']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_products_dataset.csv', header = true, auto_detect = true)
),

cleaned AS (
    SELECT
        -- Primary key
        product_id,

        -- Category
        product_category_name,

        -- Product metadata
        cast(product_name_lenght AS INTEGER) AS product_name_length,
        cast(product_description_lenght AS INTEGER) AS product_description_length,
        cast(product_photos_qty AS INTEGER) AS product_photos_qty,

        -- Dimensions
        cast(product_weight_g AS DECIMAL(10, 2)) AS product_weight_g,
        cast(product_length_cm AS DECIMAL(10, 2)) AS product_length_cm,
        cast(product_height_cm AS DECIMAL(10, 2)) AS product_height_cm,
        cast(product_width_cm AS DECIMAL(10, 2)) AS product_width_cm,

        -- Calculated fields
        cast(product_length_cm AS DECIMAL(10, 2))
        * cast(product_height_cm AS DECIMAL(10, 2))
        * cast(product_width_cm AS DECIMAL(10, 2)) AS product_volume_cm3,

        -- Product completeness score
        CASE WHEN product_name_lenght IS NOT null THEN 1 ELSE 0 END
        + CASE WHEN product_description_lenght IS NOT null THEN 1 ELSE 0 END
        + CASE WHEN product_photos_qty IS NOT null AND cast(product_photos_qty AS INTEGER) > 0 THEN 1 ELSE 0 END
        + CASE WHEN product_category_name IS NOT null THEN 1 ELSE 0 END AS product_completeness_score

    FROM source
    WHERE product_id IS NOT null
)

SELECT * FROM cleaned
