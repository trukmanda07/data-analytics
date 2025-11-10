{{
    config(
        materialized='table',
        tags=['fact', 'core', 'orders']
    )
}}

-- Orders fact table combining all order-level information
WITH orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
),

payments AS (
    SELECT * FROM {{ ref('int_order_payments_aggregated') }}
),

order_items_summary AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS total_item_price,
        SUM(freight_value) AS total_freight,
        SUM(total_item_value) AS total_order_value,
        AVG(price) AS avg_item_price
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

orders_fact AS (
    SELECT
        -- Primary key
        o.order_id,

        -- Foreign keys
        o.customer_id,

        -- Order attributes
        o.order_status,
        o.order_purchase_timestamp,
        o.order_approved_at,
        o.order_delivered_carrier_date,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,

        -- Date dimensions
        o.order_date,
        o.order_month,
        o.order_year,

        -- Time metrics
        o.hours_to_approval,
        o.days_to_delivery,
        o.delivery_performance,
        o.days_vs_estimated,

        -- Customer location
        o.customer_city,
        o.customer_state,
        o.customer_state_clean,

        -- Review metrics
        o.review_id,
        o.review_score,
        o.review_sentiment,
        o.has_comment,

        -- Order item metrics
        COALESCE(oi.item_count, 0) AS item_count,
        COALESCE(oi.total_item_price, 0) AS total_item_price,
        COALESCE(oi.total_freight, 0) AS total_freight,
        COALESCE(oi.total_order_value, 0) AS total_order_value,
        COALESCE(oi.avg_item_price, 0) AS avg_item_price,

        -- Payment metrics
        COALESCE(p.total_payment_value, 0) AS total_payment_value,
        p.payment_method_count,
        p.primary_payment_method,
        p.max_installments,
        p.used_credit_card,
        p.used_boleto,
        p.used_voucher,
        p.used_installments,

        -- Payment vs order value reconciliation
        COALESCE(p.total_payment_value, 0) - COALESCE(oi.total_order_value, 0) AS payment_order_diff,

        -- Flags
        CASE WHEN o.order_status = 'delivered' THEN TRUE ELSE FALSE END AS is_delivered,
        CASE WHEN o.order_status = 'canceled' THEN TRUE ELSE FALSE END AS is_canceled,
        CASE WHEN o.review_score >= 4 THEN TRUE ELSE FALSE END AS is_positive_review,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM orders o
    LEFT JOIN payments p ON o.order_id = p.order_id
    LEFT JOIN order_items_summary oi ON o.order_id = oi.order_id
)

SELECT * FROM orders_fact
