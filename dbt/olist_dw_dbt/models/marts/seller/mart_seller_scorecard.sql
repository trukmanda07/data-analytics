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
        count(DISTINCT product_id) AS unique_products,
        count(DISTINCT product_category_name_english) AS unique_categories,
        mode() WITHIN GROUP (ORDER BY product_category_name_english) AS top_category
    FROM order_items
    WHERE product_category_name_english IS NOT null
    GROUP BY seller_id
),

-- Seller geographic reach
seller_geography AS (
    SELECT
        seller_id,
        count(DISTINCT customer_zip_code_prefix) AS unique_customer_locations,
        count(DISTINCT customer_state) AS unique_customer_states,
        mode() WITHIN GROUP (ORDER BY customer_state) AS top_customer_state,
        count(DISTINCT CASE WHEN is_same_state THEN order_id END) AS same_state_orders,
        count(DISTINCT CASE WHEN is_same_city THEN order_id END) AS same_city_orders,
        count(DISTINCT order_id) AS total_orders
    FROM order_items
    GROUP BY seller_id
),

-- Seller price metrics
seller_pricing AS (
    SELECT
        seller_id,
        avg(item_price) AS avg_product_price,
        min(item_price) AS min_product_price,
        max(item_price) AS max_product_price,
        stddev(item_price) AS price_stddev,
        avg(freight_value) AS avg_freight,
        avg(freight_percentage) AS avg_freight_percentage
    FROM order_items
    GROUP BY seller_id
),

-- Seller volume metrics over time
seller_volume AS (
    SELECT
        seller_id,
        min(order_purchase_timestamp) AS first_sale_date,
        max(order_purchase_timestamp) AS last_sale_date,
        count(DISTINCT date_trunc('month', order_purchase_timestamp)) AS active_months,

        -- Recent activity (last 30, 90, 180 days from max date)
        count(DISTINCT CASE
            WHEN
                date_diff(
                    'day', order_purchase_timestamp,
                    (SELECT max(order_purchase_timestamp) FROM order_items)
                ) <= 30
                THEN order_id
        END) AS orders_last_30_days,

        count(DISTINCT CASE
            WHEN
                date_diff(
                    'day', order_purchase_timestamp,
                    (SELECT max(order_purchase_timestamp) FROM order_items)
                ) <= 90
                THEN order_id
        END) AS orders_last_90_days,

        count(DISTINCT CASE
            WHEN
                date_diff(
                    'day', order_purchase_timestamp,
                    (SELECT max(order_purchase_timestamp) FROM order_items)
                ) <= 180
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
        coalesce(sv.active_months, 0) AS active_months,
        coalesce(sv.orders_last_30_days, 0) AS orders_last_30_days,
        coalesce(sv.orders_last_90_days, 0) AS orders_last_90_days,
        coalesce(sv.orders_last_180_days, 0) AS orders_last_180_days,

        -- Product diversity
        s.unique_products_sold,
        coalesce(sp.unique_categories, 0) AS unique_categories,
        sp.top_category,

        -- Price metrics
        spr.avg_product_price,
        spr.min_product_price,
        spr.max_product_price,
        spr.price_stddev,
        spr.avg_freight_percentage,

        -- Geographic reach
        coalesce(sg.unique_customer_locations, 0) AS unique_customer_locations,
        coalesce(sg.unique_customer_states, 0) AS unique_customer_states,
        sg.top_customer_state,

        -- Local vs distant sales
        coalesce(sg.same_state_orders, 0) AS same_state_orders,
        coalesce(sg.same_city_orders, 0) AS same_city_orders,
        CASE
            WHEN sg.total_orders > 0
                THEN cast(sg.same_state_orders AS DECIMAL) / sg.total_orders * 100
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
        END AS revenue_per_item,

        CASE
            WHEN s.total_orders > 0
                THEN s.total_revenue / s.total_orders
        END AS revenue_per_order,

        CASE
            WHEN s.days_active > 0
                THEN s.total_revenue / s.days_active
        END AS revenue_per_day_active,

        CASE
            WHEN sv.active_months > 0
                THEN s.total_revenue / sv.active_months
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
        percent_rank() OVER (ORDER BY s.total_revenue) * 100 AS revenue_percentile,

        -- Review score (direct mapping: 5 stars = 100)
        CASE
            WHEN s.avg_review_score IS NOT null
                THEN s.avg_review_score * 20
        END AS review_score_100,

        -- Delivery score (100% on time = 100)
        s.on_time_delivery_rate AS delivery_score_100,

        -- Combined performance score (weighted average)
        CASE
            WHEN s.avg_review_score IS NOT null AND s.on_time_delivery_rate IS NOT null
                THEN (
                    (percent_rank() OVER (ORDER BY s.total_revenue) * 100 * 0.4)  -- 40% revenue
                    + (s.avg_review_score * 20 * 0.3)                                 -- 30% reviews
                    + (s.on_time_delivery_rate * 0.3)                                  -- 30% delivery
                )
        END AS overall_performance_score,

        -- Seller health indicators
        CASE
            WHEN
                s.avg_review_score >= 4.5
                AND s.on_time_delivery_rate >= 90
                AND sv.orders_last_90_days > 0
                THEN 'Excellent'
            WHEN
                s.avg_review_score >= 4.0
                AND s.on_time_delivery_rate >= 80
                AND sv.orders_last_90_days > 0
                THEN 'Good'
            WHEN
                s.avg_review_score >= 3.5
                AND s.on_time_delivery_rate >= 70
                THEN 'Average'
            WHEN
                s.avg_review_score < 3.5
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
            WHEN sg.total_orders > 0 AND (cast(sg.same_state_orders AS DECIMAL) / sg.total_orders * 100) >= 80 THEN 'Local Focused'
            WHEN sg.total_orders > 0 AND (cast(sg.same_state_orders AS DECIMAL) / sg.total_orders * 100) >= 50 THEN 'Regional'
            WHEN sg.unique_customer_states >= 15 THEN 'National'
            ELSE 'Multi-Regional'
        END AS geographic_focus,

        -- Current timestamp
        current_timestamp AS dbt_updated_at

    FROM sellers AS s
    LEFT JOIN geography AS g ON s.seller_zip_code_prefix = g.zip_code_prefix
    LEFT JOIN seller_products AS sp ON s.seller_id = sp.seller_id
    LEFT JOIN seller_geography AS sg ON s.seller_id = sg.seller_id
    LEFT JOIN seller_pricing AS spr ON s.seller_id = spr.seller_id
    LEFT JOIN seller_volume AS sv ON s.seller_id = sv.seller_id
)

SELECT * FROM seller_scorecard
