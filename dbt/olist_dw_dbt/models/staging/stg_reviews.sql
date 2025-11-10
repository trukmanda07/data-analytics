{{
    config(
        materialized='view',
        tags=['staging', 'reviews']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_order_reviews_dataset.csv', header=true, auto_detect=true)
),

cleaned AS (
    SELECT
        -- Primary key
        review_id,

        -- Foreign key
        order_id,

        -- Review score
        CAST(review_score AS INTEGER) AS review_score,

        -- Review text
        review_comment_title,
        review_comment_message,

        -- Timestamps
        CAST(review_creation_date AS TIMESTAMP) AS review_creation_date,
        CAST(review_answer_timestamp AS TIMESTAMP) AS review_answer_timestamp,

        -- Calculated fields
        CASE
            WHEN review_comment_title IS NOT NULL OR review_comment_message IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS has_comment,

        CASE
            WHEN review_answer_timestamp IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS has_answer,

        -- Review sentiment
        CASE
            WHEN CAST(review_score AS INTEGER) >= 4 THEN 'positive'
            WHEN CAST(review_score AS INTEGER) = 3 THEN 'neutral'
            WHEN CAST(review_score AS INTEGER) <= 2 THEN 'negative'
            ELSE NULL
        END AS review_sentiment

    FROM source
    WHERE review_id IS NOT NULL
)

SELECT * FROM cleaned
