{{
    config(
        materialized='table',
        tags=['fact', 'core', 'order_items']
    )
}}

-- Order items fact table (grain: one row per order item)
WITH order_items_enriched AS (
    SELECT * FROM {{ ref('int_order_items_enriched') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

order_items_fact AS (
    SELECT
        -- Primary key (composite)
        oi.order_id,
        oi.order_item_id,

        -- Foreign keys
        oi.product_id,
        oi.seller_id,
        o.customer_id,

        -- Date foreign key
        CAST(STRFTIME(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER) AS order_date_key,

        -- Order item attributes
        oi.shipping_limit_date,
        oi.price AS item_price,
        oi.freight_value,
        oi.total_item_value,

        -- Product attributes (denormalized for convenience)
        oi.product_category_name,
        oi.product_category_name_english,
        oi.category_display_name,
        oi.product_weight_g,
        oi.product_length_cm,
        oi.product_height_cm,
        oi.product_width_cm,
        oi.product_volume_cm3,

        -- Seller location (denormalized)
        oi.seller_zip_code_prefix,
        oi.seller_city,
        oi.seller_state,
        oi.seller_state_clean,

        -- Order context
        o.order_status,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,

        -- Customer location (denormalized)
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,

        -- Calculated metrics
        -- Freight as percentage of item price
        CASE
            WHEN oi.price > 0
            THEN (oi.freight_value / oi.price) * 100
            ELSE NULL
        END AS freight_percentage,

        -- Price tier
        CASE
            WHEN oi.price >= 200 THEN 'Premium'
            WHEN oi.price >= 100 THEN 'High'
            WHEN oi.price >= 50 THEN 'Medium'
            WHEN oi.price >= 20 THEN 'Low'
            ELSE 'Budget'
        END AS price_tier,

        -- Volume tier
        CASE
            WHEN oi.product_volume_cm3 IS NULL THEN 'Unknown'
            WHEN oi.product_volume_cm3 >= 100000 THEN 'Extra Large'
            WHEN oi.product_volume_cm3 >= 50000 THEN 'Large'
            WHEN oi.product_volume_cm3 >= 10000 THEN 'Medium'
            WHEN oi.product_volume_cm3 >= 1000 THEN 'Small'
            ELSE 'Extra Small'
        END AS volume_tier,

        -- Same state flag (customer and seller in same state)
        CASE
            WHEN c.customer_state = oi.seller_state THEN TRUE
            ELSE FALSE
        END AS is_same_state,

        -- Same city flag
        CASE
            WHEN c.customer_city = oi.seller_city THEN TRUE
            ELSE FALSE
        END AS is_same_city,

        -- Delivery status flags
        CASE WHEN o.order_status = 'delivered' THEN TRUE ELSE FALSE END AS is_delivered,
        CASE WHEN o.order_status = 'canceled' THEN TRUE ELSE FALSE END AS is_canceled,
        CASE WHEN o.order_status = 'shipped' THEN TRUE ELSE FALSE END AS is_shipped,

        -- On-time delivery flag
        CASE
            WHEN o.order_status = 'delivered'
                AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_estimated_delivery_date IS NOT NULL
                AND o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN TRUE
            WHEN o.order_status = 'delivered'
            THEN FALSE
            ELSE NULL
        END AS is_on_time_delivery,

        -- Days to deliver (for delivered orders)
        CASE
            WHEN o.order_status = 'delivered'
                AND o.order_delivered_customer_date IS NOT NULL
            THEN DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)
            ELSE NULL
        END AS days_to_deliver,

        -- Days vs estimated
        CASE
            WHEN o.order_status = 'delivered'
                AND o.order_delivered_customer_date IS NOT NULL
                AND o.order_estimated_delivery_date IS NOT NULL
            THEN DATE_DIFF('day', o.order_delivered_customer_date, o.order_estimated_delivery_date)
            ELSE NULL
        END AS days_vs_estimated,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM order_items_enriched oi
    LEFT JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN customers c ON o.customer_id = c.customer_id
)

SELECT * FROM order_items_fact
