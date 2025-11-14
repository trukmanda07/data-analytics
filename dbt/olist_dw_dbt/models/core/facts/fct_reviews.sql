{{
    config(
        materialized='table',
        tags=['fact', 'core', 'reviews']
    )
}}

-- Reviews fact table (grain: one row per review)
WITH reviews AS (
    SELECT * FROM {{ ref('stg_reviews') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

order_items AS (
    SELECT
        order_id,
        COUNT(*) AS item_count,
        SUM(price) AS total_order_value
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

reviews_fact AS (
    SELECT
        -- Primary key
        r.review_id,

        -- Foreign keys
        r.order_id,
        o.customer_id,

        -- Date foreign keys
        CAST(STRFTIME(r.review_creation_date, '%Y%m%d') AS INTEGER) AS review_date_key,
        CAST(STRFTIME(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER) AS order_date_key,

        -- Review attributes
        r.review_score,
        r.review_comment_title,
        r.review_comment_message,
        r.review_creation_date,
        r.review_answer_timestamp,
        r.review_sentiment,

        -- Review flags
        r.has_comment,
        r.has_answer,

        -- Score categorization
        CASE
            WHEN r.review_score = 5 THEN 'Excellent'
            WHEN r.review_score = 4 THEN 'Good'
            WHEN r.review_score = 3 THEN 'Average'
            WHEN r.review_score = 2 THEN 'Poor'
            WHEN r.review_score = 1 THEN 'Very Poor'
            ELSE 'Unknown'
        END AS review_score_category,

        -- Sentiment flags
        CASE WHEN r.review_sentiment = 'positive' THEN TRUE ELSE FALSE END AS is_positive,
        CASE WHEN r.review_sentiment = 'neutral' THEN TRUE ELSE FALSE END AS is_neutral,
        CASE WHEN r.review_sentiment = 'negative' THEN TRUE ELSE FALSE END AS is_negative,

        -- Order context
        o.order_status,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,

        -- Customer location (denormalized)
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,

        -- Order value context
        COALESCE(oi.total_order_value, 0) AS order_value,
        COALESCE(oi.item_count, 0) AS order_item_count,

        -- Time metrics
        -- Days from order to review
        CASE
            WHEN r.review_creation_date IS NOT NULL
                AND o.order_purchase_timestamp IS NOT NULL
            THEN DATE_DIFF('day', o.order_purchase_timestamp, r.review_creation_date)
            ELSE NULL
        END AS days_order_to_review,

        -- Days from delivery to review
        CASE
            WHEN r.review_creation_date IS NOT NULL
                AND o.order_delivered_customer_date IS NOT NULL
            THEN DATE_DIFF('day', o.order_delivered_customer_date, r.review_creation_date)
            ELSE NULL
        END AS days_delivery_to_review,

        -- Days to answer review
        CASE
            WHEN r.review_answer_timestamp IS NOT NULL
                AND r.review_creation_date IS NOT NULL
            THEN DATE_DIFF('day', r.review_creation_date, r.review_answer_timestamp)
            ELSE NULL
        END AS days_to_answer,

        -- Review timing category
        CASE
            WHEN r.review_creation_date IS NOT NULL
                AND o.order_delivered_customer_date IS NOT NULL
            THEN
                CASE
                    WHEN DATE_DIFF('day', o.order_delivered_customer_date, r.review_creation_date) <= 1 THEN 'Immediate'
                    WHEN DATE_DIFF('day', o.order_delivered_customer_date, r.review_creation_date) <= 7 THEN 'Within Week'
                    WHEN DATE_DIFF('day', o.order_delivered_customer_date, r.review_creation_date) <= 30 THEN 'Within Month'
                    ELSE 'After Month'
                END
            ELSE 'Unknown'
        END AS review_timing,

        -- Comment length metrics
        CASE
            WHEN r.review_comment_title IS NOT NULL
            THEN LENGTH(r.review_comment_title)
            ELSE 0
        END AS title_length,

        CASE
            WHEN r.review_comment_message IS NOT NULL
            THEN LENGTH(r.review_comment_message)
            ELSE 0
        END AS message_length,

        -- Comment detail level
        CASE
            WHEN r.review_comment_message IS NOT NULL AND LENGTH(r.review_comment_message) > 200 THEN 'Detailed'
            WHEN r.review_comment_message IS NOT NULL AND LENGTH(r.review_comment_message) > 50 THEN 'Moderate'
            WHEN r.review_comment_message IS NOT NULL THEN 'Brief'
            ELSE 'No Comment'
        END AS comment_detail_level,

        -- Answer response time category
        CASE
            WHEN r.review_answer_timestamp IS NULL THEN 'No Answer'
            WHEN DATE_DIFF('day', r.review_creation_date, r.review_answer_timestamp) <= 1 THEN 'Same/Next Day'
            WHEN DATE_DIFF('day', r.review_creation_date, r.review_answer_timestamp) <= 7 THEN 'Within Week'
            WHEN DATE_DIFF('day', r.review_creation_date, r.review_answer_timestamp) <= 30 THEN 'Within Month'
            ELSE 'After Month'
        END AS answer_timing,

        -- Order status flags
        CASE WHEN o.order_status = 'delivered' THEN TRUE ELSE FALSE END AS is_delivered,
        CASE WHEN o.order_status = 'canceled' THEN TRUE ELSE FALSE END AS is_canceled,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM reviews r
    LEFT JOIN orders o ON r.order_id = o.order_id
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_items oi ON r.order_id = oi.order_id
)

SELECT * FROM reviews_fact
