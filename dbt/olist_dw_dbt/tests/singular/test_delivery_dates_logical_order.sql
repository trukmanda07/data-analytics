-- Test that delivery-related dates follow logical order
-- purchase < approved < delivered < estimated (when all exist)

WITH order_dates AS (
    SELECT DISTINCT
        order_id,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_customer_date,
        order_estimated_delivery_date
    FROM {{ ref('stg_orders') }}
    WHERE order_status = 'delivered'
        AND order_delivered_customer_date IS NOT NULL
)

SELECT
    order_id,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    CASE
        WHEN order_approved_at IS NOT NULL AND order_approved_at < order_purchase_timestamp
            THEN 'Approved before purchase'
        WHEN order_delivered_customer_date < order_purchase_timestamp
            THEN 'Delivered before purchase'
        WHEN order_approved_at IS NOT NULL AND order_delivered_customer_date < order_approved_at
            THEN 'Delivered before approval'
        ELSE 'Other date logic error'
    END AS issue_type
FROM order_dates
WHERE
    -- Check various date logic issues
    (order_approved_at IS NOT NULL AND order_approved_at < order_purchase_timestamp)
    OR (order_delivered_customer_date < order_purchase_timestamp)
    OR (order_approved_at IS NOT NULL AND order_delivered_customer_date < order_approved_at)
