-- Test that products have consistent category assignments across all tables
-- A product should always belong to the same category

WITH product_categories_in_facts AS (
    SELECT DISTINCT
        product_id,
        product_category_name
    FROM {{ ref('fct_order_items') }}
    WHERE product_category_name IS NOT NULL
),

product_categories_in_dim AS (
    SELECT DISTINCT
        product_id,
        product_category_name
    FROM {{ ref('dim_products') }}
    WHERE product_category_name IS NOT NULL
),

category_comparison AS (
    SELECT
        COALESCE(f.product_id, d.product_id) AS product_id,
        f.product_category_name AS fact_category,
        d.product_category_name AS dim_category
    FROM product_categories_in_facts f
    FULL OUTER JOIN product_categories_in_dim d ON f.product_id = d.product_id
)

SELECT
    product_id,
    fact_category,
    dim_category
FROM category_comparison
WHERE fact_category != dim_category
    OR (fact_category IS NULL AND dim_category IS NOT NULL)
    OR (fact_category IS NOT NULL AND dim_category IS NULL)
