{{
    config(
        materialized='table',
        tags=['dimension', 'core', 'customers']
    )
}}

-- Customer dimension with aggregated metrics
WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
),

customer_metrics AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_orders,
        MIN(order_purchase_timestamp) AS first_order_date,
        MAX(order_purchase_timestamp) AS last_order_date,
        AVG(review_score) AS avg_review_score,
        COUNT(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id END) AS delivered_orders,
        COUNT(DISTINCT CASE WHEN order_status = 'canceled' THEN order_id END) AS canceled_orders
    FROM orders
    GROUP BY customer_id
),

customer_dimension AS (
    SELECT
        -- Primary key
        c.customer_id,
        c.customer_unique_id,

        -- Location attributes
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        c.customer_state_clean,

        -- Customer metrics
        COALESCE(cm.total_orders, 0) AS lifetime_orders,
        cm.first_order_date,
        cm.last_order_date,
        cm.avg_review_score,
        COALESCE(cm.delivered_orders, 0) AS delivered_orders,
        COALESCE(cm.canceled_orders, 0) AS canceled_orders,

        -- Customer segmentation
        CASE
            WHEN cm.total_orders >= 3 THEN 'Repeat Customer'
            WHEN cm.total_orders = 2 THEN 'Second Time'
            WHEN cm.total_orders = 1 THEN 'One Time'
            ELSE 'No Orders'
        END AS customer_segment,

        -- Recency (days since last order)
        CASE
            WHEN cm.last_order_date IS NOT NULL
            THEN DATE_DIFF('day', cm.last_order_date, CURRENT_DATE)
            ELSE NULL
        END AS days_since_last_order,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM customers c
    LEFT JOIN customer_metrics cm ON c.customer_id = cm.customer_id
)

SELECT * FROM customer_dimension
