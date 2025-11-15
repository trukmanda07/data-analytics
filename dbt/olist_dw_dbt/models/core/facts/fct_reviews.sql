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
        count(*) AS item_count,
        sum(price) AS total_order_value
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
        cast(strftime(r.review_creation_date, '%Y%m%d') AS INTEGER) AS review_date_key,
        cast(strftime(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER) AS order_date_key,

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
        coalesce(r.review_sentiment = 'positive', false) AS is_positive,
        coalesce(r.review_sentiment = 'neutral', false) AS is_neutral,
        coalesce(r.review_sentiment = 'negative', false) AS is_negative,

        -- Order context
        o.order_status,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,

        -- Customer location (denormalized)
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,

        -- Order value context
        coalesce(oi.total_order_value, 0) AS order_value,
        coalesce(oi.item_count, 0) AS order_item_count,

        -- Time metrics
        -- Days from order to review
        CASE
            WHEN
                r.review_creation_date IS NOT null
                AND o.order_purchase_timestamp IS NOT null
                THEN date_diff('day', o.order_purchase_timestamp, r.review_creation_date)
        END AS days_order_to_review,

        -- Days from delivery to review
        CASE
            WHEN
                r.review_creation_date IS NOT null
                AND o.order_delivered_customer_date IS NOT null
                THEN date_diff('day', o.order_delivered_customer_date, r.review_creation_date)
        END AS days_delivery_to_review,

        -- Days to answer review
        CASE
            WHEN
                r.review_answer_timestamp IS NOT null
                AND r.review_creation_date IS NOT null
                THEN date_diff('day', r.review_creation_date, r.review_answer_timestamp)
        END AS days_to_answer,

        -- Review timing category
        CASE
            WHEN
                r.review_creation_date IS NOT null
                AND o.order_delivered_customer_date IS NOT null
                THEN
                    CASE
                        WHEN date_diff('day', o.order_delivered_customer_date, r.review_creation_date) <= 1 THEN 'Immediate'
                        WHEN date_diff('day', o.order_delivered_customer_date, r.review_creation_date) <= 7 THEN 'Within Week'
                        WHEN date_diff('day', o.order_delivered_customer_date, r.review_creation_date) <= 30 THEN 'Within Month'
                        ELSE 'After Month'
                    END
            ELSE 'Unknown'
        END AS review_timing,

        -- Comment length metrics
        CASE
            WHEN r.review_comment_title IS NOT null
                THEN length(r.review_comment_title)
            ELSE 0
        END AS title_length,

        CASE
            WHEN r.review_comment_message IS NOT null
                THEN length(r.review_comment_message)
            ELSE 0
        END AS message_length,

        -- Comment detail level
        CASE
            WHEN r.review_comment_message IS NOT null AND length(r.review_comment_message) > 200 THEN 'Detailed'
            WHEN r.review_comment_message IS NOT null AND length(r.review_comment_message) > 50 THEN 'Moderate'
            WHEN r.review_comment_message IS NOT null THEN 'Brief'
            ELSE 'No Comment'
        END AS comment_detail_level,

        -- Answer response time category
        CASE
            WHEN r.review_answer_timestamp IS null THEN 'No Answer'
            WHEN date_diff('day', r.review_creation_date, r.review_answer_timestamp) <= 1 THEN 'Same/Next Day'
            WHEN date_diff('day', r.review_creation_date, r.review_answer_timestamp) <= 7 THEN 'Within Week'
            WHEN date_diff('day', r.review_creation_date, r.review_answer_timestamp) <= 30 THEN 'Within Month'
            ELSE 'After Month'
        END AS answer_timing,

        -- Order status flags
        coalesce(o.order_status = 'delivered', false) AS is_delivered,
        coalesce(o.order_status = 'canceled', false) AS is_canceled,

        -- Current timestamp
        current_timestamp AS dbt_updated_at

    FROM reviews AS r
    LEFT JOIN orders AS o ON r.order_id = o.order_id
    LEFT JOIN customers AS c ON o.customer_id = c.customer_id
    LEFT JOIN order_items AS oi ON r.order_id = oi.order_id
)

SELECT * FROM reviews_fact
