-- ============================================================================
-- Data Quality Tests for Olist dbt Pipeline
-- These tests validate data integrity across the pipeline
-- ============================================================================

-- Test 1: Ensure all orders have a customer_id
-- {{ config(severity='error') }}
SELECT
    order_id,
    'Missing customer_id' as issue
FROM {{ ref('fct_orders') }}
WHERE customer_id IS NULL;

-- Test 2: Ensure order values match payment values (within reasonable tolerance)
-- Uncomment to run:
-- SELECT
--     order_id,
--     total_order_value,
--     total_payment_value,
--     ABS(total_order_value - total_payment_value) as difference,
--     'Order/Payment mismatch' as issue
-- FROM {{ ref('fct_orders') }}
-- WHERE ABS(total_order_value - total_payment_value) > 0.50
--   AND total_order_value > 0
--   AND total_payment_value > 0;

-- Test 3: Ensure review scores are valid (1-5)
-- SELECT
--     order_id,
--     review_score,
--     'Invalid review score' as issue
-- FROM {{ ref('fct_orders') }}
-- WHERE review_score IS NOT NULL
--   AND (review_score < 1 OR review_score > 5);

-- Test 4: Check for orphaned orders (no items)
-- SELECT
--     order_id,
--     item_count,
--     'Order with no items' as issue
-- FROM {{ ref('fct_orders') }}
-- WHERE order_status NOT IN ('canceled', 'unavailable')
--   AND item_count = 0;

-- Test 5: Validate delivery performance categorization
-- SELECT
--     order_id,
--     delivery_performance,
--     days_vs_estimated,
--     'Incorrect delivery performance' as issue
-- FROM {{ ref('fct_orders') }}
-- WHERE delivery_performance IS NOT NULL
--   AND (
--       (delivery_performance = 'early' AND days_vs_estimated >= 0) OR
--       (delivery_performance = 'late' AND days_vs_estimated <= 0) OR
--       (delivery_performance = 'on_time' AND days_vs_estimated != 0)
--   );
