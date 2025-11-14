-- Test that financial metrics don't have negative values
-- Prices, freight, and payment values should always be >= 0

WITH negative_checks AS (
    -- Check order items
    SELECT
        'fct_order_items' AS table_name,
        order_id AS record_id,
        'item_price' AS column_name,
        item_price AS value
    FROM {{ ref('fct_order_items') }}
    WHERE item_price < 0

    UNION ALL

    SELECT
        'fct_order_items' AS table_name,
        order_id AS record_id,
        'freight_value' AS column_name,
        freight_value AS value
    FROM {{ ref('fct_order_items') }}
    WHERE freight_value < 0

    UNION ALL

    -- Check payments
    SELECT
        'fct_payments' AS table_name,
        order_id AS record_id,
        'payment_value' AS column_name,
        payment_value AS value
    FROM {{ ref('fct_payments') }}
    WHERE payment_value < 0

    UNION ALL

    -- Check dimension metrics
    SELECT
        'dim_sellers' AS table_name,
        seller_id AS record_id,
        'total_revenue' AS column_name,
        total_revenue AS value
    FROM {{ ref('dim_sellers') }}
    WHERE total_revenue < 0

    UNION ALL

    SELECT
        'dim_category' AS table_name,
        product_category_name AS record_id,
        'total_revenue' AS column_name,
        total_revenue AS value
    FROM {{ ref('dim_category') }}
    WHERE total_revenue < 0

    UNION ALL

    SELECT
        'dim_products' AS table_name,
        product_id AS record_id,
        'total_revenue' AS column_name,
        total_revenue AS value
    FROM {{ ref('dim_products') }}
    WHERE total_revenue < 0
)

SELECT
    table_name,
    record_id,
    column_name,
    value
FROM negative_checks
