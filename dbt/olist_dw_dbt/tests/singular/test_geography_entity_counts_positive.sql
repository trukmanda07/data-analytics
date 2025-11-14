-- Test that geography locations with entities have positive counts
-- If a location appears in data, it should have at least 1 customer or seller

SELECT
    zip_code_prefix,
    city,
    state,
    customer_count,
    seller_count,
    total_entities,
    location_type
FROM {{ ref('dim_geography') }}
WHERE (customer_count = 0 AND seller_count = 0)
    OR total_entities = 0
    OR (location_type = 'Customer Only' AND customer_count = 0)
    OR (location_type = 'Seller Only' AND seller_count = 0)
    OR (location_type = 'Both' AND (customer_count = 0 OR seller_count = 0))
