{{
    config(
        materialized='table',
        tags=['dimension', 'core', 'sellers']
    )
}}

-- Seller dimension with performance metrics
WITH sellers AS (
    SELECT * FROM {{ ref('stg_sellers') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_reviews') }}
),

seller_sales_metrics AS (
    SELECT
        oi.seller_id,
        COUNT(DISTINCT oi.order_id) AS total_orders,
        COUNT(*) AS total_items_sold,
        SUM(oi.price) AS total_revenue,
        AVG(oi.price) AS avg_item_price,
        SUM(oi.freight_value) AS total_freight,
        AVG(oi.freight_value) AS avg_freight,
        MIN(o.order_purchase_timestamp) AS first_sale_date,
        MAX(o.order_purchase_timestamp) AS last_sale_date,
        COUNT(DISTINCT oi.product_id) AS unique_products_sold
    FROM order_items oi
    LEFT JOIN orders o ON oi.order_id = o.order_id
    GROUP BY oi.seller_id
),

seller_review_metrics AS (
    SELECT
        oi.seller_id,
        AVG(r.review_score) AS avg_review_score,
        COUNT(DISTINCT CASE WHEN r.review_score >= 4 THEN r.review_id END) AS positive_reviews,
        COUNT(DISTINCT CASE WHEN r.review_score <= 2 THEN r.review_id END) AS negative_reviews,
        COUNT(DISTINCT r.review_id) AS total_reviews
    FROM order_items oi
    LEFT JOIN reviews r ON oi.order_id = r.order_id
    WHERE r.review_id IS NOT NULL
    GROUP BY oi.seller_id
),

seller_delivery_metrics AS (
    SELECT
        oi.seller_id,
        AVG(DATE_DIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date)) AS avg_delivery_days,
        COUNT(DISTINCT CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
            THEN o.order_id
        END) AS on_time_deliveries,
        COUNT(DISTINCT CASE
            WHEN o.order_status = 'delivered'
            THEN o.order_id
        END) AS total_delivered_orders
    FROM order_items oi
    LEFT JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_status IN ('delivered', 'shipped')
    GROUP BY oi.seller_id
),

seller_dimension AS (
    SELECT
        -- Primary key
        s.seller_id,

        -- Location attributes
        s.seller_zip_code_prefix,
        s.seller_city,
        s.seller_state,
        s.seller_state_clean,

        -- Sales metrics
        COALESCE(ssm.total_orders, 0) AS total_orders,
        COALESCE(ssm.total_items_sold, 0) AS total_items_sold,
        COALESCE(ssm.total_revenue, 0) AS total_revenue,
        ssm.avg_item_price,
        COALESCE(ssm.total_freight, 0) AS total_freight,
        ssm.avg_freight,
        ssm.first_sale_date,
        ssm.last_sale_date,
        COALESCE(ssm.unique_products_sold, 0) AS unique_products_sold,

        -- Review metrics
        srm.avg_review_score,
        COALESCE(srm.positive_reviews, 0) AS positive_reviews,
        COALESCE(srm.negative_reviews, 0) AS negative_reviews,
        COALESCE(srm.total_reviews, 0) AS total_reviews,

        -- Review performance
        CASE
            WHEN srm.total_reviews > 0
            THEN CAST(srm.positive_reviews AS DECIMAL) / srm.total_reviews * 100
            ELSE NULL
        END AS positive_review_rate,

        -- Delivery metrics
        sdm.avg_delivery_days,
        COALESCE(sdm.on_time_deliveries, 0) AS on_time_deliveries,
        COALESCE(sdm.total_delivered_orders, 0) AS total_delivered_orders,

        -- On-time delivery rate
        CASE
            WHEN sdm.total_delivered_orders > 0
            THEN CAST(sdm.on_time_deliveries AS DECIMAL) / sdm.total_delivered_orders * 100
            ELSE NULL
        END AS on_time_delivery_rate,

        -- Days active
        CASE
            WHEN ssm.first_sale_date IS NOT NULL AND ssm.last_sale_date IS NOT NULL
            THEN DATE_DIFF('day', ssm.first_sale_date, ssm.last_sale_date)
            ELSE NULL
        END AS days_active,

        -- Seller performance tier (based on revenue and reviews)
        CASE
            WHEN ssm.total_revenue >= 50000 AND srm.avg_review_score >= 4.5 THEN 'Top Performer'
            WHEN ssm.total_revenue >= 20000 AND srm.avg_review_score >= 4.0 THEN 'High Performer'
            WHEN ssm.total_revenue >= 5000 AND srm.avg_review_score >= 3.5 THEN 'Medium Performer'
            WHEN ssm.total_revenue > 0 THEN 'Low Performer'
            ELSE 'No Sales'
        END AS seller_performance_tier,

        -- Seller size based on items sold
        CASE
            WHEN ssm.total_items_sold >= 500 THEN 'Large Seller'
            WHEN ssm.total_items_sold >= 100 THEN 'Medium Seller'
            WHEN ssm.total_items_sold >= 10 THEN 'Small Seller'
            WHEN ssm.total_items_sold >= 1 THEN 'Micro Seller'
            ELSE 'No Sales'
        END AS seller_size_tier,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM sellers s
    LEFT JOIN seller_sales_metrics ssm ON s.seller_id = ssm.seller_id
    LEFT JOIN seller_review_metrics srm ON s.seller_id = srm.seller_id
    LEFT JOIN seller_delivery_metrics sdm ON s.seller_id = sdm.seller_id
)

SELECT * FROM seller_dimension
