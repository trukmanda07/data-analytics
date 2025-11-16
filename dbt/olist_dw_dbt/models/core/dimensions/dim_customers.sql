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
        count(DISTINCT order_id) AS total_orders,
        min(order_purchase_timestamp) AS first_order_date,
        max(order_purchase_timestamp) AS last_order_date,
        avg(review_score) AS avg_review_score,
        count(DISTINCT CASE WHEN order_status = 'delivered' THEN order_id END) AS delivered_orders,
        count(DISTINCT CASE WHEN order_status = 'canceled' THEN order_id END) AS canceled_orders
    FROM orders
    GROUP BY customer_id
),

customer_dimension AS (
    SELECT
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(['c.customer_id']) }} AS customer_key,
        c.customer_id,
        c.customer_unique_id,

        -- Location attributes
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        c.customer_state_clean,

        -- Customer metrics
        coalesce(cm.total_orders, 0) AS lifetime_orders,
        cm.first_order_date,
        cm.last_order_date,
        cm.avg_review_score,
        coalesce(cm.delivered_orders, 0) AS delivered_orders,
        coalesce(cm.canceled_orders, 0) AS canceled_orders,

        -- Customer segmentation
        CASE
            WHEN cm.total_orders >= 3 THEN 'Repeat Customer'
            WHEN cm.total_orders = 2 THEN 'Second Time'
            WHEN cm.total_orders = 1 THEN 'One Time'
            ELSE 'No Orders'
        END AS customer_segment,

        -- Recency (days since last order)
        CASE
            WHEN cm.last_order_date IS NOT null
                THEN date_diff('day', cm.last_order_date, current_date)
        END AS days_since_last_order,

        -- Current timestamp
        current_timestamp AS dbt_updated_at

    FROM customers AS c
    LEFT JOIN customer_metrics AS cm ON c.customer_id = cm.customer_id
)

SELECT * FROM customer_dimension
