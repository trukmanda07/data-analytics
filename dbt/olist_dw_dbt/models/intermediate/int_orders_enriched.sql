{{
    config(
        materialized='ephemeral',
        tags=['intermediate', 'orders']
    )
}}

-- Combines orders with customer location and review data
WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_reviews') }}
),

orders_with_customers AS (
    SELECT
        o.*,
        c.customer_unique_id,
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        c.customer_state_clean
    FROM orders AS o
    LEFT JOIN customers AS c ON o.customer_id = c.customer_id
),

orders_enriched AS (
    SELECT
        oc.*,
        r.review_id,
        r.review_score,
        r.review_sentiment,
        r.has_comment,
        r.review_creation_date
    FROM orders_with_customers AS oc
    LEFT JOIN reviews AS r ON oc.order_id = r.order_id
)

SELECT * FROM orders_enriched
