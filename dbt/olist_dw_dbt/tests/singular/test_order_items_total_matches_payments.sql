-- Test that total order item values match payment totals per order
-- Allows for small rounding differences (< 0.01 BRL)

WITH order_item_totals AS (
    SELECT
        order_id,
        SUM(total_item_value) AS total_items
    FROM {{ ref('fct_order_items') }}
    GROUP BY order_id
),

payment_totals AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payments
    FROM {{ ref('fct_payments') }}
    GROUP BY order_id
),

comparison AS (
    SELECT
        COALESCE(oi.order_id, p.order_id) AS order_id,
        oi.total_items,
        p.total_payments,
        ABS(COALESCE(oi.total_items, 0) - COALESCE(p.total_payments, 0)) AS difference
    FROM order_item_totals oi
    FULL OUTER JOIN payment_totals p ON oi.order_id = p.order_id
)

SELECT
    order_id,
    total_items,
    total_payments,
    difference
FROM comparison
WHERE difference > 0.01
    AND total_items IS NOT NULL
    AND total_payments IS NOT NULL
