{{
    config(
        materialized='table',
        tags=['mart', 'seller', 'scorecard']
    )
}}

-- Seller scorecard mart with comprehensive performance metrics
WITH sellers AS (
    SELECT * FROM {{ ref('dim_sellers') }}
),

geography AS (
    SELECT * FROM {{ ref('dim_geography') }}
),

order_items AS (
    SELECT * FROM {{ ref('fct_order_items') }}
),

reviews AS (
    SELECT * FROM {{ ref('fct_reviews') }}
),

-- Seller product diversity
seller_products AS (
    SELECT
        seller_id,
        COUNT(DISTINCT product_id) AS unique_products,
        COUNT(DISTINCT product_category_name_english) AS unique_categories,
        MODE() WITHIN GROUP (ORDER BY product_category_name_english) AS top_category
    FROM order_items
    WHERE product_category_name_english IS NOT NULL
    GROUP BY seller_id
),

-- Seller geographic reach
seller_geography AS (
    SELECT
        seller_id,
        COUNT(DISTINCT customer_zip_code_prefix) AS unique_customer_locations,
        COUNT(DISTINCT customer_state) AS unique_customer_states,
        MODE() WITHIN GROUP (ORDER BY customer_state) AS top_customer_state,
        COUNT(DISTINCT CASE WHEN is_same_state THEN order_id END) AS same_state_orders,
        COUNT(DISTINCT CASE WHEN is_same_city THEN order_id END) AS same_city_orders,
        COUNT(DISTINCT order_id) AS total_orders
    FROM order_items
    GROUP BY seller_id
),

-- Seller price metrics
seller_pricing AS (
    SELECT
        seller_id,
        AVG(item_price) AS avg_product_price,
        MIN(item_price) AS min_product_price,
        MAX(item_price) AS max_product_price,
        STDDEV(item_price) AS price_stddev,
        AVG(freight_value) AS avg_freight,
        AVG(freight_percentage) AS avg_freight_percentage
    FROM order_items
    GROUP BY seller_id
),

-- Seller volume metrics over time
seller_volume AS (
    SELECT
        seller_id,
        MIN(order_purchase_timestamp) AS first_sale_date,
        MAX(order_purchase_timestamp) AS last_sale_date,
        COUNT(DISTINCT DATE_TRUNC('month', order_purchase_timestamp)) AS active_months,

        -- Recent activity (last 30, 90, 180 days from max date)
        COUNT(DISTINCT CASE
            WHEN DATE_DIFF('day', order_purchase_timestamp,
                (SELECT MAX(order_purchase_timestamp) FROM order_items)) <= 30
            THEN order_id
        END) AS orders_last_30_days,

        COUNT(DISTINCT CASE
            WHEN DATE_DIFF('day', order_purchase_timestamp,
                (SELECT MAX(order_purchase_timestamp) FROM order_items)) <= 90
            THEN order_id
        END) AS orders_last_90_days,

        COUNT(DISTINCT CASE
            WHEN DATE_DIFF('day', order_purchase_timestamp,
                (SELECT MAX(order_purchase_timestamp) FROM order_items)) <= 180
            THEN order_id
        END) AS orders_last_180_days

    FROM order_items
    GROUP BY seller_id
),

-- Seller scorecard
seller_scorecard AS (
    SELECT
        -- Seller identifiers
        s.seller_id,

        -- Location
        s.seller_zip_code_prefix,
        s.seller_city,
        s.seller_state,
        s.seller_state_clean,
        g.region,
        g.city_size_tier,

        -- Performance tiers (from dimension)
        s.seller_performance_tier,
        s.seller_size_tier,

        -- Sales metrics (from dimension)
        s.total_orders,
        s.total_items_sold,
        s.total_revenue,
        s.avg_item_price,
        s.total_freight,
        s.avg_freight,

        -- Time metrics (from dimension)
        s.first_sale_date,
        s.last_sale_date,
        s.days_active,

        -- Volume metrics over time
        COALESCE(sv.active_months, 0) AS active_months,
        COALESCE(sv.orders_last_30_days, 0) AS orders_last_30_days,
        COALESCE(sv.orders_last_90_days, 0) AS orders_last_90_days,
        COALESCE(sv.orders_last_180_days, 0) AS orders_last_180_days,

        -- Product diversity
        s.unique_products_sold,
        COALESCE(sp.unique_categories, 0) AS unique_categories,
        sp.top_category,

        -- Price metrics
        spr.avg_product_price,
        spr.min_product_price,
        spr.max_product_price,
        spr.price_stddev,
        spr.avg_freight_percentage,

        -- Geographic reach
        COALESCE(sg.unique_customer_locations, 0) AS unique_customer_locations,
        COALESCE(sg.unique_customer_states, 0) AS unique_customer_states,
        sg.top_customer_state,

        -- Local vs distant sales
        COALESCE(sg.same_state_orders, 0) AS same_state_orders,
        COALESCE(sg.same_city_orders, 0) AS same_city_orders,
        CASE
            WHEN sg.total_orders > 0
            THEN CAST(sg.same_state_orders AS DECIMAL) / sg.total_orders * 100
            ELSE NULL
        END AS same_state_order_rate,

        -- Review metrics (from dimension)
        s.avg_review_score,
        s.positive_reviews,
        s.negative_reviews,
        s.total_reviews,
        s.positive_review_rate,

        -- Delivery metrics (from dimension)
        s.avg_delivery_days,
        s.on_time_deliveries,
        s.total_delivered_orders,
        s.on_time_delivery_rate,

        -- Revenue efficiency metrics
        CASE
            WHEN s.total_items_sold > 0
            THEN s.total_revenue / s.total_items_sold
            ELSE NULL
        END AS revenue_per_item,

        CASE
            WHEN s.total_orders > 0
            THEN s.total_revenue / s.total_orders
            ELSE NULL
        END AS revenue_per_order,

        CASE
            WHEN s.days_active > 0
            THEN s.total_revenue / s.days_active
            ELSE NULL
        END AS revenue_per_day_active,

        CASE
            WHEN sv.active_months > 0
            THEN s.total_revenue / sv.active_months
            ELSE NULL
        END AS revenue_per_month,

        -- Growth indicators
        CASE
            WHEN sv.orders_last_30_days > 0 THEN 'Active (30d)'
            WHEN sv.orders_last_90_days > 0 THEN 'Recent (90d)'
            WHEN sv.orders_last_180_days > 0 THEN 'Cooling (180d)'
            WHEN s.total_orders > 0 THEN 'Inactive'
            ELSE 'No Sales'
        END AS activity_status,

        -- Performance scores (0-100 scale)
        -- Revenue score (top 10% = 100, scales down)
        PERCENT_RANK() OVER (ORDER BY s.total_revenue) * 100 AS revenue_percentile,

        -- Review score (direct mapping: 5 stars = 100)
        CASE
            WHEN s.avg_review_score IS NOT NULL
            THEN s.avg_review_score * 20
            ELSE NULL
        END AS review_score_100,

        -- Delivery score (100% on time = 100)
        s.on_time_delivery_rate AS delivery_score_100,

        -- Combined performance score (weighted average)
        CASE
            WHEN s.avg_review_score IS NOT NULL AND s.on_time_delivery_rate IS NOT NULL
            THEN (
                (PERCENT_RANK() OVER (ORDER BY s.total_revenue) * 100 * 0.4) +  -- 40% revenue
                (s.avg_review_score * 20 * 0.3) +                                 -- 30% reviews
                (s.on_time_delivery_rate * 0.3)                                  -- 30% delivery
            )
            ELSE NULL
        END AS overall_performance_score,

        -- Seller health indicators
        CASE
            WHEN s.avg_review_score >= 4.5
                AND s.on_time_delivery_rate >= 90
                AND sv.orders_last_90_days > 0
            THEN 'Excellent'
            WHEN s.avg_review_score >= 4.0
                AND s.on_time_delivery_rate >= 80
                AND sv.orders_last_90_days > 0
            THEN 'Good'
            WHEN s.avg_review_score >= 3.5
                AND s.on_time_delivery_rate >= 70
            THEN 'Average'
            WHEN s.avg_review_score < 3.5
                OR s.on_time_delivery_rate < 70
            THEN 'Needs Improvement'
            ELSE 'New/Unknown'
        END AS seller_health,

        -- Specialization indicators
        CASE
            WHEN sp.unique_categories = 1 THEN 'Specialist'
            WHEN sp.unique_categories <= 3 THEN 'Focused'
            WHEN sp.unique_categories <= 5 THEN 'Diverse'
            ELSE 'Generalist'
        END AS product_diversity_type,

        -- Geographic focus
        CASE
            WHEN sg.total_orders > 0 AND (CAST(sg.same_state_orders AS DECIMAL) / sg.total_orders * 100) >= 80 THEN 'Local Focused'
            WHEN sg.total_orders > 0 AND (CAST(sg.same_state_orders AS DECIMAL) / sg.total_orders * 100) >= 50 THEN 'Regional'
            WHEN sg.unique_customer_states >= 15 THEN 'National'
            ELSE 'Multi-Regional'
        END AS geographic_focus,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM sellers s
    LEFT JOIN geography g ON s.seller_zip_code_prefix = g.zip_code_prefix
    LEFT JOIN seller_products sp ON s.seller_id = sp.seller_id
    LEFT JOIN seller_geography sg ON s.seller_id = sg.seller_id
    LEFT JOIN seller_pricing spr ON s.seller_id = spr.seller_id
    LEFT JOIN seller_volume sv ON s.seller_id = sv.seller_id
)

SELECT * FROM seller_scorecard
