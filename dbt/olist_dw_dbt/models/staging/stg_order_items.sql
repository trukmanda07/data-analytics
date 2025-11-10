{{
    config(
        materialized='view',
        tags=['staging', 'order_items']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_order_items_dataset.csv', header=true, auto_detect=true)
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
        CAST(shipping_limit_date AS TIMESTAMP) AS shipping_limit_date,

        -- Pricing (cast to DECIMAL for precision)
        CAST(price AS DECIMAL(10,2)) AS price,
        CAST(freight_value AS DECIMAL(10,2)) AS freight_value,

        -- Calculated fields
        CAST(price AS DECIMAL(10,2)) + CAST(freight_value AS DECIMAL(10,2)) AS total_item_value,

        -- Item revenue breakdown
        CAST(price AS DECIMAL(10,2)) AS item_revenue,
        CAST(freight_value AS DECIMAL(10,2)) AS freight_revenue

    FROM source
    WHERE order_id IS NOT NULL
      AND order_item_id IS NOT NULL
)

SELECT * FROM cleaned
