{{
    config(
        materialized='ephemeral',
        tags=['intermediate', 'order_items']
    )
}}

-- Combines order items with product and seller information
WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

sellers AS (
    SELECT * FROM {{ ref('stg_sellers') }}
),

category_translation AS (
    SELECT * FROM {{ ref('stg_category_translation') }}
),

items_with_products AS (
    SELECT
        oi.*,
        p.product_category_name,
        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,
        p.product_volume_cm3,
        p.product_completeness_score,
        ct.product_category_name_english,
        ct.category_display_name
    FROM order_items oi
    LEFT JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
),

items_enriched AS (
    SELECT
        ip.*,
        s.seller_zip_code_prefix,
        s.seller_city,
        s.seller_state,
        s.seller_state_clean
    FROM items_with_products ip
    LEFT JOIN sellers s ON ip.seller_id = s.seller_id
)

SELECT * FROM items_enriched
