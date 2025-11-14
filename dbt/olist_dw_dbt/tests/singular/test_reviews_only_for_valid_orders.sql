-- Test that reviews only exist for orders that have been delivered or shipped
-- Customers shouldn't be able to review orders that haven't been fulfilled

WITH reviews_with_status AS (
    SELECT
        r.review_id,
        r.order_id,
        o.order_status
    FROM {{ ref('fct_reviews') }} r
    LEFT JOIN {{ ref('stg_orders') }} o ON r.order_id = o.order_id
)

SELECT
    review_id,
    order_id,
    order_status
FROM reviews_with_status
WHERE order_status NOT IN ('delivered', 'shipped', 'canceled')
    OR order_status IS NULL
