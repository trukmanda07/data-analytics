-- Test that seller dimension metrics match aggregated fact table values
-- Seller total revenue should equal sum of their order items

WITH seller_fact_metrics AS (
    SELECT
        seller_id,
        COUNT(DISTINCT order_id) AS fact_total_orders,
        COUNT(*) AS fact_total_items,
        ROUND(SUM(item_price), 2) AS fact_total_revenue
    FROM {{ ref('fct_order_items') }}
    GROUP BY seller_id
),

seller_dim_metrics AS (
    SELECT
        seller_id,
        total_orders AS dim_total_orders,
        total_items_sold AS dim_total_items,
        ROUND(total_revenue, 2) AS dim_total_revenue
    FROM {{ ref('dim_sellers') }}
)

SELECT
    COALESCE(f.seller_id, d.seller_id) AS seller_id,
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
FROM seller_fact_metrics f
FULL OUTER JOIN seller_dim_metrics d ON f.seller_id = d.seller_id
WHERE
    f.fact_total_orders != d.dim_total_orders
    OR f.fact_total_items != d.dim_total_items
    OR ABS(f.fact_total_revenue - d.dim_total_revenue) > 0.01
