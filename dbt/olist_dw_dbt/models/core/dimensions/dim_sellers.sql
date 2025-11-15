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
        count(DISTINCT oi.order_id) AS total_orders,
        count(*) AS total_items_sold,
        sum(oi.price) AS total_revenue,
        avg(oi.price) AS avg_item_price,
        sum(oi.freight_value) AS total_freight,
        avg(oi.freight_value) AS avg_freight,
        min(o.order_purchase_timestamp) AS first_sale_date,
        max(o.order_purchase_timestamp) AS last_sale_date,
        count(DISTINCT oi.product_id) AS unique_products_sold
    FROM order_items AS oi
    LEFT JOIN orders AS o ON oi.order_id = o.order_id
    GROUP BY oi.seller_id
),

seller_review_metrics AS (
    SELECT
        oi.seller_id,
        avg(r.review_score) AS avg_review_score,
        count(DISTINCT CASE WHEN r.review_score >= 4 THEN r.review_id END) AS positive_reviews,
        count(DISTINCT CASE WHEN r.review_score <= 2 THEN r.review_id END) AS negative_reviews,
        count(DISTINCT r.review_id) AS total_reviews
    FROM order_items AS oi
    LEFT JOIN reviews AS r ON oi.order_id = r.order_id
    WHERE r.review_id IS NOT null
    GROUP BY oi.seller_id
),

seller_delivery_metrics AS (
    SELECT
        oi.seller_id,
        avg(date_diff('day', o.order_purchase_timestamp, o.order_delivered_customer_date)) AS avg_delivery_days,
        count(DISTINCT CASE
            WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date
                THEN o.order_id
        END) AS on_time_deliveries,
        count(DISTINCT CASE
            WHEN o.order_status = 'delivered'
                THEN o.order_id
        END) AS total_delivered_orders
    FROM order_items AS oi
    LEFT JOIN orders AS o ON oi.order_id = o.order_id
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
        coalesce(ssm.total_orders, 0) AS total_orders,
        coalesce(ssm.total_items_sold, 0) AS total_items_sold,
        coalesce(ssm.total_revenue, 0) AS total_revenue,
        ssm.avg_item_price,
        coalesce(ssm.total_freight, 0) AS total_freight,
        ssm.avg_freight,
        ssm.first_sale_date,
        ssm.last_sale_date,
        coalesce(ssm.unique_products_sold, 0) AS unique_products_sold,

        -- Review metrics
        srm.avg_review_score,
        coalesce(srm.positive_reviews, 0) AS positive_reviews,
        coalesce(srm.negative_reviews, 0) AS negative_reviews,
        coalesce(srm.total_reviews, 0) AS total_reviews,

        -- Review performance
        CASE
            WHEN srm.total_reviews > 0
                THEN cast(srm.positive_reviews AS DECIMAL) / srm.total_reviews * 100
        END AS positive_review_rate,

        -- Delivery metrics
        sdm.avg_delivery_days,
        coalesce(sdm.on_time_deliveries, 0) AS on_time_deliveries,
        coalesce(sdm.total_delivered_orders, 0) AS total_delivered_orders,

        -- On-time delivery rate
        CASE
            WHEN sdm.total_delivered_orders > 0
                THEN cast(sdm.on_time_deliveries AS DECIMAL) / sdm.total_delivered_orders * 100
        END AS on_time_delivery_rate,

        -- Days active
        CASE
            WHEN ssm.first_sale_date IS NOT null AND ssm.last_sale_date IS NOT null
                THEN date_diff('day', ssm.first_sale_date, ssm.last_sale_date)
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
        current_timestamp AS dbt_updated_at

    FROM sellers AS s
    LEFT JOIN seller_sales_metrics AS ssm ON s.seller_id = ssm.seller_id
    LEFT JOIN seller_review_metrics AS srm ON s.seller_id = srm.seller_id
    LEFT JOIN seller_delivery_metrics AS sdm ON s.seller_id = sdm.seller_id
)

SELECT * FROM seller_dimension
