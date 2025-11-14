-- Test that all date keys in fact tables exist in the date dimension
-- This ensures referential integrity for date foreign keys

WITH all_date_keys AS (
    SELECT DISTINCT order_date_key AS date_key, 'fct_order_items' AS source_table
    FROM {{ ref('fct_order_items') }}
    WHERE order_date_key IS NOT NULL

    UNION

    SELECT DISTINCT order_date_key AS date_key, 'fct_payments' AS source_table
    FROM {{ ref('fct_payments') }}
    WHERE order_date_key IS NOT NULL

    UNION

    SELECT DISTINCT review_date_key AS date_key, 'fct_reviews' AS source_table
    FROM {{ ref('fct_reviews') }}
    WHERE review_date_key IS NOT NULL

    UNION

    SELECT DISTINCT order_date_key AS date_key, 'fct_reviews' AS source_table
    FROM {{ ref('fct_reviews') }}
    WHERE order_date_key IS NOT NULL
),

date_dimension AS (
    SELECT date_key
    FROM {{ ref('dim_date') }}
)

SELECT
    adk.date_key,
    adk.source_table
FROM all_date_keys adk
LEFT JOIN date_dimension dd ON adk.date_key = dd.date_key
WHERE dd.date_key IS NULL
