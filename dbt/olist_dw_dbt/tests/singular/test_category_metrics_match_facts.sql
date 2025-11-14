-- Test that category dimension metrics match aggregated fact table values
-- Category total revenue should equal sum of order items in that category

WITH category_fact_metrics AS (
    SELECT
        product_category_name,
        COUNT(DISTINCT order_id) AS fact_total_orders,
        COUNT(*) AS fact_total_items,
        ROUND(SUM(item_price), 2) AS fact_total_revenue
    FROM {{ ref('fct_order_items') }}
    WHERE product_category_name IS NOT NULL
    GROUP BY product_category_name
),

category_dim_metrics AS (
    SELECT
        product_category_name,
        total_orders AS dim_total_orders,
        total_items_sold AS dim_total_items,
        ROUND(total_revenue, 2) AS dim_total_revenue
    FROM {{ ref('dim_category') }}
)

SELECT
    COALESCE(f.product_category_name, d.product_category_name) AS product_category_name,
    f.fact_total_orders,
    d.dim_total_orders,
    f.fact_total_items,
    d.dim_total_items,
    f.fact_total_revenue,
    d.dim_total_revenue,
    CASE
        WHEN f.fact_total_orders != d.dim_total_orders THEN 'Orders mismatch'
        WHEN f.fact_total_items != d.dim_total_items THEN 'Items mismatch'
        WHEN ABS(f.fact_total_revenue - d.dim_total_revenue) > 0.01 THEN 'Revenue mismatch'
        ELSE 'Unknown mismatch'
    END AS issue_type
FROM category_fact_metrics f
FULL OUTER JOIN category_dim_metrics d ON f.product_category_name = d.product_category_name
WHERE
    f.fact_total_orders != d.dim_total_orders
    OR f.fact_total_items != d.dim_total_items
    OR ABS(f.fact_total_revenue - d.dim_total_revenue) > 0.01
