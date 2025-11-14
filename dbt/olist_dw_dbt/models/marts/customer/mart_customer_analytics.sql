{{
    config(
        materialized='table',
        tags=['mart', 'customer', 'analytics']
    )
}}

-- Customer analytics mart with RFM analysis and lifetime metrics
WITH customers AS (
    SELECT * FROM {{ ref('dim_customers') }}
),

orders AS (
    SELECT * FROM {{ ref('fct_orders') }}
),

order_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

reviews AS (
    SELECT * FROM {{ ref('fct_reviews') }}
),

geography AS (
    SELECT * FROM {{ ref('dim_geography') }}
),

-- Customer order metrics
customer_order_metrics AS (
    SELECT
        c.customer_id,
        c.customer_unique_id,

        -- RFM metrics
        MAX(o.order_purchase_timestamp) AS last_order_date,
        MIN(o.order_purchase_timestamp) AS first_order_date,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(o.total_order_value) AS total_revenue,

        -- Recency (days since last order)
        DATE_DIFF('day', MAX(o.order_purchase_timestamp), CURRENT_DATE) AS recency_days,

        -- Frequency
        COUNT(DISTINCT o.order_id) AS frequency,

        -- Monetary
        SUM(o.total_order_value) AS monetary_value,
        AVG(o.total_order_value) AS avg_order_value,

        -- Order behavior
        SUM(o.item_count) AS total_items_purchased,
        AVG(o.item_count) AS avg_items_per_order,
        SUM(o.total_freight) AS total_freight_paid,
        AVG(o.total_freight) AS avg_freight_per_order,

        -- Order status
        COUNT(DISTINCT CASE WHEN o.is_delivered THEN o.order_id END) AS delivered_orders,
        COUNT(DISTINCT CASE WHEN o.is_canceled THEN o.order_id END) AS canceled_orders,

        -- Payment behavior
        COUNT(DISTINCT CASE WHEN o.used_installments THEN o.order_id END) AS installment_orders,
        AVG(o.max_installments) AS avg_max_installments,

        -- Timing metrics
        AVG(o.days_to_delivery) AS avg_delivery_days,
        COUNT(DISTINCT CASE
            WHEN o.delivery_performance = 'on_time'
            THEN o.order_id
        END) AS on_time_deliveries,

        -- Review behavior
        AVG(o.review_score) AS avg_review_score,
        COUNT(DISTINCT CASE WHEN o.has_comment THEN o.order_id END) AS orders_with_comments,

        -- Time between orders (for repeat customers)
        CASE
            WHEN COUNT(DISTINCT o.order_id) > 1
            THEN DATE_DIFF('day',
                MIN(o.order_purchase_timestamp),
                MAX(o.order_purchase_timestamp)
            ) / (COUNT(DISTINCT o.order_id) - 1.0)
            ELSE NULL
        END AS avg_days_between_orders

    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.customer_unique_id
),

-- Customer product preferences
customer_product_metrics AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT oi.product_id) AS unique_products,
        COUNT(DISTINCT oi.product_category_name_english) AS unique_categories,
        MODE() WITHIN GROUP (ORDER BY oi.product_category_name_english) AS favorite_category
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.product_category_name_english IS NOT NULL
    GROUP BY o.customer_id
),

-- RFM scoring (quintiles)
rfm_scores AS (
    SELECT
        customer_id,
        -- Recency score (lower is better, so reverse the quintile)
        6 - NTILE(5) OVER (ORDER BY recency_days) AS r_score,
        -- Frequency score (higher is better)
        NTILE(5) OVER (ORDER BY frequency) AS f_score,
        -- Monetary score (higher is better)
        NTILE(5) OVER (ORDER BY monetary_value) AS m_score
    FROM customer_order_metrics
    WHERE recency_days IS NOT NULL
),

-- Customer analytics mart
customer_analytics AS (
    SELECT
        -- Customer identifiers
        c.customer_id,
        c.customer_unique_id,

        -- Location
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        c.customer_state_clean,
        g.region,
        g.city_size_tier,

        -- Customer segment from dimension
        c.customer_segment,
        c.days_since_last_order,

        -- Order metrics
        COALESCE(com.total_orders, 0) AS total_orders,
        COALESCE(com.delivered_orders, 0) AS delivered_orders,
        COALESCE(com.canceled_orders, 0) AS canceled_orders,
        com.first_order_date,
        com.last_order_date,

        -- Financial metrics
        COALESCE(com.total_revenue, 0) AS lifetime_value,
        com.avg_order_value,
        COALESCE(com.total_items_purchased, 0) AS total_items,
        com.avg_items_per_order,
        COALESCE(com.total_freight_paid, 0) AS total_freight,
        com.avg_freight_per_order,

        -- RFM metrics
        com.recency_days,
        com.frequency,
        com.monetary_value,
        COALESCE(rfm.r_score, 0) AS recency_score,
        COALESCE(rfm.f_score, 0) AS frequency_score,
        COALESCE(rfm.m_score, 0) AS monetary_score,
        COALESCE(rfm.r_score, 0) + COALESCE(rfm.f_score, 0) + COALESCE(rfm.m_score, 0) AS rfm_total_score,

        -- RFM segment
        CASE
            WHEN rfm.r_score >= 4 AND rfm.f_score >= 4 AND rfm.m_score >= 4 THEN 'Champions'
            WHEN rfm.r_score >= 3 AND rfm.f_score >= 3 AND rfm.m_score >= 3 THEN 'Loyal Customers'
            WHEN rfm.r_score >= 4 AND rfm.f_score <= 2 THEN 'New Customers'
            WHEN rfm.r_score <= 2 AND rfm.f_score >= 3 THEN 'At Risk'
            WHEN rfm.r_score <= 2 AND rfm.f_score <= 2 THEN 'Lost'
            WHEN rfm.m_score >= 4 THEN 'Big Spenders'
            ELSE 'Regular'
        END AS rfm_segment,

        -- Behavior metrics
        com.avg_days_between_orders,
        COALESCE(com.installment_orders, 0) AS installment_orders,
        com.avg_max_installments,

        -- Delivery experience
        com.avg_delivery_days,
        COALESCE(com.on_time_deliveries, 0) AS on_time_deliveries,
        CASE
            WHEN com.delivered_orders > 0
            THEN CAST(com.on_time_deliveries AS DECIMAL) / com.delivered_orders * 100
            ELSE NULL
        END AS on_time_delivery_rate,

        -- Review behavior
        com.avg_review_score,
        COALESCE(com.orders_with_comments, 0) AS orders_with_comments,

        -- Product preferences
        COALESCE(cpm.unique_products, 0) AS unique_products_purchased,
        COALESCE(cpm.unique_categories, 0) AS unique_categories_purchased,
        cpm.favorite_category,

        -- Customer value tiers
        CASE
            WHEN com.total_revenue >= 1000 THEN 'VIP'
            WHEN com.total_revenue >= 500 THEN 'High Value'
            WHEN com.total_revenue >= 200 THEN 'Medium Value'
            WHEN com.total_revenue > 0 THEN 'Low Value'
            ELSE 'No Orders'
        END AS value_tier,

        -- Customer lifecycle stage
        CASE
            WHEN com.total_orders = 0 THEN 'Never Purchased'
            WHEN com.recency_days <= 90 AND com.total_orders >= 3 THEN 'Active Repeat'
            WHEN com.recency_days <= 90 THEN 'Active New'
            WHEN com.recency_days <= 180 THEN 'Cooling Down'
            WHEN com.recency_days <= 365 THEN 'At Risk'
            ELSE 'Dormant'
        END AS lifecycle_stage,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM customers c
    LEFT JOIN customer_order_metrics com ON c.customer_id = com.customer_id
    LEFT JOIN rfm_scores rfm ON c.customer_id = rfm.customer_id
    LEFT JOIN customer_product_metrics cpm ON c.customer_id = cpm.customer_id
    LEFT JOIN geography g ON c.customer_zip_code_prefix = g.zip_code_prefix
)

SELECT * FROM customer_analytics
