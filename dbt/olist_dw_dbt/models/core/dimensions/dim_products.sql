{{
    config(
        materialized='table',
        tags=['dimension', 'core', 'products']
    )
}}

-- Product dimension with category information and sales metrics
WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

category_translation AS (
    SELECT * FROM {{ ref('stg_category_translation') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

product_sales_metrics AS (
    SELECT
        product_id,
        count(DISTINCT order_id) AS total_orders,
        count(*) AS total_items_sold,
        sum(price) AS total_revenue,
        avg(price) AS avg_price,
        min(price) AS min_price,
        max(price) AS max_price,
        sum(freight_value) AS total_freight,
        avg(freight_value) AS avg_freight
    FROM order_items
    GROUP BY product_id
),

product_dimension AS (
    SELECT
        -- Primary key
        p.product_id,

        -- Category attributes
        p.product_category_name,
        ct.product_category_name_english,
        ct.category_display_name,

        -- Product metadata
        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,

        -- Dimensions
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,
        p.product_volume_cm3,

        -- Product quality score
        p.product_completeness_score,
        CASE
            WHEN p.product_completeness_score >= 4 THEN 'Excellent'
            WHEN p.product_completeness_score = 3 THEN 'Good'
            WHEN p.product_completeness_score = 2 THEN 'Fair'
            ELSE 'Poor'
        END AS product_quality_tier,

        -- Size category based on volume
        CASE
            WHEN p.product_volume_cm3 IS null THEN 'Unknown'
            WHEN p.product_volume_cm3 < 1000 THEN 'Extra Small'
            WHEN p.product_volume_cm3 < 10000 THEN 'Small'
            WHEN p.product_volume_cm3 < 50000 THEN 'Medium'
            WHEN p.product_volume_cm3 < 100000 THEN 'Large'
            ELSE 'Extra Large'
        END AS product_size_category,

        -- Weight category
        CASE
            WHEN p.product_weight_g IS null THEN 'Unknown'
            WHEN p.product_weight_g < 500 THEN 'Light'
            WHEN p.product_weight_g < 2000 THEN 'Medium'
            WHEN p.product_weight_g < 5000 THEN 'Heavy'
            ELSE 'Extra Heavy'
        END AS product_weight_category,

        -- Sales metrics
        coalesce(psm.total_orders, 0) AS total_orders,
        coalesce(psm.total_items_sold, 0) AS total_items_sold,
        coalesce(psm.total_revenue, 0) AS total_revenue,
        psm.avg_price,
        psm.min_price,
        psm.max_price,
        coalesce(psm.total_freight, 0) AS total_freight,
        psm.avg_freight,

        -- Product performance tier
        CASE
            WHEN psm.total_items_sold >= 100 THEN 'Top Seller'
            WHEN psm.total_items_sold >= 50 THEN 'High Seller'
            WHEN psm.total_items_sold >= 10 THEN 'Medium Seller'
            WHEN psm.total_items_sold >= 1 THEN 'Low Seller'
            ELSE 'No Sales'
        END AS product_performance_tier,

        -- Current timestamp
        current_timestamp AS dbt_updated_at

    FROM products AS p
    LEFT JOIN category_translation AS ct ON p.product_category_name = ct.product_category_name
    LEFT JOIN product_sales_metrics AS psm ON p.product_id = psm.product_id
)

SELECT * FROM product_dimension
