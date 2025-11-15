{{
    config(
        materialized='view',
        tags=['staging', 'reviews']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_order_reviews_dataset.csv', header = true, auto_detect = true)
),

cleaned AS (
    SELECT
        -- Primary key
        review_id,

        -- Foreign key
        order_id,

        -- Review score
        cast(review_score AS INTEGER) AS review_score,

        -- Review text
        review_comment_title,
        review_comment_message,

        -- Timestamps
        cast(review_creation_date AS TIMESTAMP) AS review_creation_date,
        cast(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp,

        -- Calculated fields
        coalesce(review_comment_title IS NOT null OR review_comment_message IS NOT null, false) AS has_comment,

        coalesce(review_answer_timestamp IS NOT null, false) AS has_answer,

        -- Review sentiment
        CASE
            WHEN cast(review_score AS INTEGER) >= 4 THEN 'positive'
            WHEN cast(review_score AS INTEGER) = 3 THEN 'neutral'
            WHEN cast(review_score AS INTEGER) <= 2 THEN 'negative'
        END AS review_sentiment

    FROM source
    WHERE review_id IS NOT null
)

SELECT * FROM cleaned
