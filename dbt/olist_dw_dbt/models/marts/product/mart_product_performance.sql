{{
    config(
        materialized='table',
        tags=['mart', 'product', 'performance']
    )
}}

-- Product performance mart with sales and review metrics
WITH products AS (
    SELECT * FROM {{ ref('dim_products') }}
),

categories AS (
    SELECT * FROM {{ ref('dim_category') }}
),

order_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

reviews AS (
    SELECT * FROM {{ ref('fct_reviews') }}
),

-- Product sales metrics
product_sales AS (
    SELECT
        oi.product_id,
        COUNT(DISTINCT oi.order_id) AS total_orders,
        COUNT(*) AS total_units_sold,
        SUM(oi.item_price) AS total_revenue,
        AVG(oi.item_price) AS avg_price,
        MIN(oi.item_price) AS min_price,
        MAX(oi.item_price) AS max_price,
        SUM(oi.freight_value) AS total_freight,
        AVG(oi.freight_value) AS avg_freight,
        AVG(oi.freight_percentage) AS avg_freight_percentage,

        -- Date metrics
        MIN(oi.order_purchase_timestamp) AS first_sale_date,
        MAX(oi.order_purchase_timestamp) AS last_sale_date,

        -- Delivery metrics (for delivered items)
        COUNT(DISTINCT CASE WHEN oi.is_delivered THEN oi.order_id END) AS delivered_orders,
        COUNT(DISTINCT CASE WHEN oi.is_canceled THEN oi.order_id END) AS canceled_orders,
        COUNT(DISTINCT CASE WHEN oi.is_on_time_delivery THEN oi.order_id END) AS on_time_deliveries,
        AVG(CASE WHEN oi.is_delivered THEN oi.days_to_deliver END) AS avg_delivery_days,

        -- Geographic diversity
        COUNT(DISTINCT oi.customer_zip_code_prefix) AS unique_customer_locations,
        COUNT(DISTINCT oi.customer_state) AS unique_customer_states,
        MODE() WITHIN GROUP (ORDER BY oi.customer_state) AS top_customer_state,

        -- Same state sales
        COUNT(DISTINCT CASE WHEN oi.is_same_state THEN oi.order_id END) AS same_state_sales,
        COUNT(DISTINCT CASE WHEN oi.is_same_city THEN oi.order_id END) AS same_city_sales

    FROM order_items oi
    GROUP BY oi.product_id
),

-- Product review metrics
product_reviews AS (
    SELECT
        oi.product_id,
        COUNT(DISTINCT r.review_id) AS total_reviews,
        AVG(r.review_score) AS avg_review_score,
        COUNT(DISTINCT CASE WHEN r.is_positive THEN r.review_id END) AS positive_reviews,
        COUNT(DISTINCT CASE WHEN r.is_neutral THEN r.review_id END) AS neutral_reviews,
        COUNT(DISTINCT CASE WHEN r.is_negative THEN r.review_id END) AS negative_reviews,
        COUNT(DISTINCT CASE WHEN r.has_comment THEN r.review_id END) AS reviews_with_comments,
        AVG(r.days_delivery_to_review) AS avg_days_to_review
    FROM order_items oi
    INNER JOIN reviews r ON oi.order_id = r.order_id
    GROUP BY oi.product_id
),

-- Product seller diversity
product_sellers AS (
    SELECT
        product_id,
        COUNT(DISTINCT seller_id) AS unique_sellers,
        MODE() WITHIN GROUP (ORDER BY seller_id) AS primary_seller_id
    FROM order_items
    GROUP BY product_id
),

-- Product performance mart
product_performance AS (
    SELECT
        -- Product identifiers
        p.product_id,
        p.product_category_name,
        p.product_category_name_english,
        p.category_display_name,

        -- Category context
        c.category_group,
        c.revenue_tier AS category_revenue_tier,
        c.category_size_tier,

        -- Product attributes
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,
        p.product_volume_cm3,
        p.product_size_category,
        p.product_weight_category,
        p.product_completeness_score,
        p.product_quality_tier,

        -- Sales metrics
        COALESCE(ps.total_orders, 0) AS total_orders,
        COALESCE(ps.total_units_sold, 0) AS total_units_sold,
        COALESCE(ps.total_revenue, 0) AS total_revenue,
        ps.avg_price,
        ps.min_price,
        ps.max_price,
        COALESCE(ps.total_freight, 0) AS total_freight,
        ps.avg_freight,
        ps.avg_freight_percentage,

        -- Date metrics
        ps.first_sale_date,
        ps.last_sale_date,
        CASE
            WHEN ps.first_sale_date IS NOT NULL AND ps.last_sale_date IS NOT NULL
            THEN DATE_DIFF('day', ps.first_sale_date, ps.last_sale_date)
            ELSE NULL
        END AS days_on_sale,

        -- Order fulfillment
        COALESCE(ps.delivered_orders, 0) AS delivered_orders,
        COALESCE(ps.canceled_orders, 0) AS canceled_orders,
        CASE
            WHEN ps.total_orders > 0
            THEN CAST(ps.delivered_orders AS DECIMAL) / ps.total_orders * 100
            ELSE NULL
        END AS delivery_rate,
        CASE
            WHEN ps.total_orders > 0
            THEN CAST(ps.canceled_orders AS DECIMAL) / ps.total_orders * 100
            ELSE NULL
        END AS cancellation_rate,

        -- Delivery performance
        COALESCE(ps.on_time_deliveries, 0) AS on_time_deliveries,
        CASE
            WHEN ps.delivered_orders > 0
            THEN CAST(ps.on_time_deliveries AS DECIMAL) / ps.delivered_orders * 100
            ELSE NULL
        END AS on_time_delivery_rate,
        ps.avg_delivery_days,

        -- Geographic reach
        COALESCE(ps.unique_customer_locations, 0) AS unique_customer_locations,
        COALESCE(ps.unique_customer_states, 0) AS unique_customer_states,
        ps.top_customer_state,
        COALESCE(ps.same_state_sales, 0) AS same_state_sales,
        COALESCE(ps.same_city_sales, 0) AS same_city_sales,
        CASE
            WHEN ps.total_orders > 0
            THEN CAST(ps.same_state_sales AS DECIMAL) / ps.total_orders * 100
            ELSE NULL
        END AS same_state_sales_rate,

        -- Review metrics
        COALESCE(pr.total_reviews, 0) AS total_reviews,
        pr.avg_review_score,
        COALESCE(pr.positive_reviews, 0) AS positive_reviews,
        COALESCE(pr.neutral_reviews, 0) AS neutral_reviews,
        COALESCE(pr.negative_reviews, 0) AS negative_reviews,
        CASE
            WHEN pr.total_reviews > 0
            THEN CAST(pr.positive_reviews AS DECIMAL) / pr.total_reviews * 100
            ELSE NULL
        END AS positive_review_rate,
        COALESCE(pr.reviews_with_comments, 0) AS reviews_with_comments,
        pr.avg_days_to_review,

        -- Seller diversity
        COALESCE(psl.unique_sellers, 0) AS unique_sellers,
        psl.primary_seller_id,

        -- Performance indicators
        CASE
            WHEN ps.total_units_sold >= 100 THEN 'Best Seller'
            WHEN ps.total_units_sold >= 50 THEN 'Top Seller'
            WHEN ps.total_units_sold >= 10 THEN 'Good Seller'
            WHEN ps.total_units_sold >= 1 THEN 'Low Seller'
            ELSE 'No Sales'
        END AS sales_tier,

        CASE
            WHEN pr.avg_review_score >= 4.5 THEN 'Excellent'
            WHEN pr.avg_review_score >= 4.0 THEN 'Very Good'
            WHEN pr.avg_review_score >= 3.5 THEN 'Good'
            WHEN pr.avg_review_score >= 3.0 THEN 'Average'
            WHEN pr.avg_review_score IS NOT NULL THEN 'Below Average'
            ELSE 'No Reviews'
        END AS review_tier,

        -- Combined performance score (normalized)
        CASE
            WHEN ps.total_units_sold > 0 AND pr.avg_review_score IS NOT NULL
            THEN (
                -- Normalize units sold (0-50 scale)
                LEAST(CAST(ps.total_units_sold AS DECIMAL) / 2, 50) +
                -- Normalize review score (0-50 scale)
                (pr.avg_review_score * 10)
            ) / 10
            ELSE NULL
        END AS performance_score,

        -- Revenue efficiency
        CASE
            WHEN ps.total_units_sold > 0
            THEN ps.total_revenue / ps.total_units_sold
            ELSE NULL
        END AS revenue_per_unit,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM products p
    LEFT JOIN product_sales ps ON p.product_id = ps.product_id
    LEFT JOIN product_reviews pr ON p.product_id = pr.product_id
    LEFT JOIN product_sellers psl ON p.product_id = psl.product_id
    LEFT JOIN categories c ON p.product_category_name = c.product_category_name
)

SELECT * FROM product_performance
