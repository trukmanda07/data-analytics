{{
    config(
        materialized='view',
        tags=['staging', 'order_items']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_order_items_dataset.csv', header = true, auto_detect = true)
),

cleaned AS (
    SELECT
        -- Composite key (order_id + order_item_id)
        order_id,
        order_item_id,

        -- Foreign keys
        product_id,
        seller_id,

        -- Shipping
        cast(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,

        -- Pricing (cast to DECIMAL for precision)
        cast(price AS DECIMAL(10, 2)) AS price,
        cast(freight_value AS DECIMAL(10, 2)) AS freight_value,

        -- Calculated fields
        cast(price AS DECIMAL(10, 2)) + cast(freight_value AS DECIMAL(10, 2)) AS total_item_value,

        -- Item revenue breakdown
        cast(price AS DECIMAL(10, 2)) AS item_revenue,
        cast(freight_value AS DECIMAL(10, 2)) AS freight_revenue

    FROM source
    WHERE
        order_id IS NOT null
        AND order_item_id IS NOT null
)

SELECT * FROM cleaned
