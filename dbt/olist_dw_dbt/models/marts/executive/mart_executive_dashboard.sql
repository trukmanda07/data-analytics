{{
    config(
        materialized='table',
        tags=['mart', 'executive', 'dashboard']
    )
}}

-- Executive dashboard mart with key business metrics by day
WITH orders AS (
    SELECT * FROM {{ ref('fct_orders') }}
),

order_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

payments AS (
    SELECT * FROM {{ ref('fct_payments') }}
),

reviews AS (
    SELECT * FROM {{ ref('fct_reviews') }}
),

date_dim AS (
    SELECT * FROM {{ ref('dim_date') }}
),

-- Daily aggregations
daily_metrics AS (
    SELECT
        d.date_day,
        d.year,
        d.quarter,
        d.month_name,
        d.year_month,
        d.day_name,
        d.is_weekend,
        d.is_holiday,
        d.holiday_name,

        -- Order metrics
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT CASE WHEN o.is_delivered THEN o.order_id END) AS delivered_orders,
        COUNT(DISTINCT CASE WHEN o.is_canceled THEN o.order_id END) AS canceled_orders,

        -- Revenue metrics
        SUM(o.total_order_value) AS total_revenue,
        SUM(o.total_freight) AS total_freight,
        SUM(o.total_payment_value) AS total_payments,
        AVG(o.total_order_value) AS avg_order_value,

        -- Customer metrics
        COUNT(DISTINCT o.customer_id) AS unique_customers,

        -- Item metrics
        SUM(o.item_count) AS total_items,
        AVG(o.item_count) AS avg_items_per_order,

        -- Review metrics
        COUNT(DISTINCT r.review_id) AS total_reviews,
        AVG(r.review_score) AS avg_review_score,
        COUNT(DISTINCT CASE WHEN r.is_positive THEN r.review_id END) AS positive_reviews,
        COUNT(DISTINCT CASE WHEN r.is_negative THEN r.review_id END) AS negative_reviews,

        -- Payment method metrics
        COUNT(DISTINCT CASE WHEN p.is_credit_card THEN p.order_id END) AS credit_card_orders,
        COUNT(DISTINCT CASE WHEN p.is_boleto THEN p.order_id END) AS boleto_orders,
        COUNT(DISTINCT CASE WHEN p.uses_installments THEN p.order_id END) AS installment_orders,

        -- Delivery metrics (for delivered orders)
        AVG(CASE WHEN o.is_delivered THEN o.days_to_delivery END) AS avg_delivery_days,
        COUNT(DISTINCT CASE
            WHEN o.is_delivered AND o.delivery_performance = 'on_time'
            THEN o.order_id
        END) AS on_time_deliveries,

        -- Seller/product diversity
        COUNT(DISTINCT oi.seller_id) AS unique_sellers,
        COUNT(DISTINCT oi.product_id) AS unique_products

    FROM date_dim d
    LEFT JOIN orders o ON CAST(STRFTIME(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER) = d.date_key
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN payments p ON o.order_id = p.order_id AND p.is_primary_payment
    LEFT JOIN reviews r ON o.order_id = r.order_id
    GROUP BY
        d.date_day, d.year, d.quarter, d.month_name, d.year_month,
        d.day_name, d.is_weekend, d.is_holiday, d.holiday_name
),

-- Add calculated metrics and moving averages
enriched_metrics AS (
    SELECT
        *,

        -- Rates and percentages
        CASE
            WHEN total_orders > 0
            THEN CAST(delivered_orders AS DECIMAL) / total_orders * 100
            ELSE NULL
        END AS delivery_rate,

        CASE
            WHEN total_orders > 0
            THEN CAST(canceled_orders AS DECIMAL) / total_orders * 100
            ELSE NULL
        END AS cancellation_rate,

        CASE
            WHEN total_reviews > 0
            THEN CAST(positive_reviews AS DECIMAL) / total_reviews * 100
            ELSE NULL
        END AS positive_review_rate,

        CASE
            WHEN delivered_orders > 0
            THEN CAST(on_time_deliveries AS DECIMAL) / delivered_orders * 100
            ELSE NULL
        END AS on_time_delivery_rate,

        CASE
            WHEN total_orders > 0
            THEN CAST(installment_orders AS DECIMAL) / total_orders * 100
            ELSE NULL
        END AS installment_usage_rate,

        -- Revenue per customer
        CASE
            WHEN unique_customers > 0
            THEN total_revenue / unique_customers
            ELSE NULL
        END AS revenue_per_customer,

        -- 7-day moving averages
        AVG(total_orders) OVER (
            ORDER BY date_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS ma7_orders,

        AVG(total_revenue) OVER (
            ORDER BY date_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS ma7_revenue,

        AVG(avg_review_score) OVER (
            ORDER BY date_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS ma7_review_score,

        -- 30-day moving averages
        AVG(total_orders) OVER (
            ORDER BY date_day
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS ma30_orders,

        AVG(total_revenue) OVER (
            ORDER BY date_day
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS ma30_revenue,

        -- Running totals
        SUM(total_revenue) OVER (
            PARTITION BY year
            ORDER BY date_day
        ) AS ytd_revenue,

        SUM(total_orders) OVER (
            PARTITION BY year
            ORDER BY date_day
        ) AS ytd_orders,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM daily_metrics
)

SELECT * FROM enriched_metrics
ORDER BY date_day
