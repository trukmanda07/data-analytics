-- Test that review creation dates come after order purchase dates
-- Customers can't review orders before they've been placed

SELECT
    r.review_id,
    r.order_id,
    r.review_creation_date,
    o.order_purchase_timestamp,
    DATE_DIFF('day', o.order_purchase_timestamp, r.review_creation_date) AS days_difference
FROM {{ ref('fct_reviews') }} r
LEFT JOIN {{ ref('stg_orders') }} o ON r.order_id = o.order_id
WHERE r.review_creation_date < o.order_purchase_timestamp
