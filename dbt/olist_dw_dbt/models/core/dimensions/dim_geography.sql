{{
    config(
        materialized='table',
        tags=['dimension', 'core', 'geography']
    )
}}

-- Geography dimension combining customer, seller, and geolocation data
WITH geolocation AS (
    SELECT * FROM {{ ref('stg_geolocation') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

sellers AS (
    SELECT * FROM {{ ref('stg_sellers') }}
),

-- All unique zip codes from customers
customer_zips AS (
    SELECT DISTINCT
        customer_zip_code_prefix AS zip_code_prefix,
        customer_city AS city,
        customer_state AS state,
        customer_state_clean AS state_clean,
        'Customer' AS location_type
    FROM customers
),

-- All unique zip codes from sellers
seller_zips AS (
    SELECT DISTINCT
        seller_zip_code_prefix AS zip_code_prefix,
        seller_city AS city,
        seller_state AS state,
        seller_state_clean AS state_clean,
        'Seller' AS location_type
    FROM sellers
),

-- Combine all zip codes
all_zips AS (
    SELECT * FROM customer_zips
    UNION ALL
    SELECT * FROM seller_zips
),

-- Deduplicate and combine with geolocation data
unique_locations AS (
    SELECT
        zip_code_prefix,
        -- Take the first city/state (should be consistent per zip)
        min(city) AS city,
        min(state) AS state,
        min(state_clean) AS state_clean
    FROM all_zips
    GROUP BY zip_code_prefix
),

-- Count customers and sellers per location
customer_counts AS (
    SELECT
        customer_zip_code_prefix AS zip_code_prefix,
        count(DISTINCT customer_id) AS customer_count
    FROM customers
    GROUP BY customer_zip_code_prefix
),

seller_counts AS (
    SELECT
        seller_zip_code_prefix AS zip_code_prefix,
        count(DISTINCT seller_id) AS seller_count
    FROM sellers
    GROUP BY seller_zip_code_prefix
),

geography_dimension AS (
    SELECT
        -- Primary key
        ul.zip_code_prefix,

        -- Location attributes
        ul.city,
        ul.state,
        ul.state_clean,

        -- Coordinates from geolocation
        g.geolocation_lat AS latitude,
        g.geolocation_lng AS longitude,

        -- Has coordinates flag
        coalesce(g.geolocation_lat IS NOT null AND g.geolocation_lng IS NOT null, false) AS has_coordinates,

        -- Counts
        coalesce(cc.customer_count, 0) AS customer_count,
        coalesce(sc.seller_count, 0) AS seller_count,
        coalesce(cc.customer_count, 0) + coalesce(sc.seller_count, 0) AS total_entities,

        -- Location type
        CASE
            WHEN cc.customer_count > 0 AND sc.seller_count > 0 THEN 'Both'
            WHEN cc.customer_count > 0 THEN 'Customer Only'
            WHEN sc.seller_count > 0 THEN 'Seller Only'
            ELSE 'Unknown'
        END AS location_type,

        -- Brazilian regions (approximate based on state)
        CASE
            WHEN ul.state_clean IN ('AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO') THEN 'North'
            WHEN ul.state_clean IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE') THEN 'Northeast'
            WHEN ul.state_clean IN ('DF', 'GO', 'MT', 'MS') THEN 'Central-West'
            WHEN ul.state_clean IN ('ES', 'MG', 'RJ', 'SP') THEN 'Southeast'
            WHEN ul.state_clean IN ('PR', 'RS', 'SC') THEN 'South'
            ELSE 'Unknown'
        END AS region,

        -- State full names (major states)
        CASE
            WHEN ul.state_clean = 'SP' THEN 'São Paulo'
            WHEN ul.state_clean = 'RJ' THEN 'Rio de Janeiro'
            WHEN ul.state_clean = 'MG' THEN 'Minas Gerais'
            WHEN ul.state_clean = 'BA' THEN 'Bahia'
            WHEN ul.state_clean = 'PR' THEN 'Paraná'
            WHEN ul.state_clean = 'RS' THEN 'Rio Grande do Sul'
            WHEN ul.state_clean = 'SC' THEN 'Santa Catarina'
            WHEN ul.state_clean = 'GO' THEN 'Goiás'
            WHEN ul.state_clean = 'PE' THEN 'Pernambuco'
            WHEN ul.state_clean = 'CE' THEN 'Ceará'
            WHEN ul.state_clean = 'PA' THEN 'Pará'
            WHEN ul.state_clean = 'DF' THEN 'Distrito Federal'
            WHEN ul.state_clean = 'ES' THEN 'Espírito Santo'
            WHEN ul.state_clean = 'MT' THEN 'Mato Grosso'
            WHEN ul.state_clean = 'AM' THEN 'Amazonas'
            WHEN ul.state_clean = 'MA' THEN 'Maranhão'
            WHEN ul.state_clean = 'RN' THEN 'Rio Grande do Norte'
            WHEN ul.state_clean = 'AL' THEN 'Alagoas'
            WHEN ul.state_clean = 'PB' THEN 'Paraíba'
            WHEN ul.state_clean = 'PI' THEN 'Piauí'
            WHEN ul.state_clean = 'MS' THEN 'Mato Grosso do Sul'
            WHEN ul.state_clean = 'SE' THEN 'Sergipe'
            WHEN ul.state_clean = 'RO' THEN 'Rondônia'
            WHEN ul.state_clean = 'TO' THEN 'Tocantins'
            WHEN ul.state_clean = 'AC' THEN 'Acre'
            WHEN ul.state_clean = 'AP' THEN 'Amapá'
            WHEN ul.state_clean = 'RR' THEN 'Roraima'
            ELSE ul.state
        END AS state_name,

        -- Population tier (based on customer + seller count as proxy)
        CASE
            WHEN coalesce(cc.customer_count, 0) + coalesce(sc.seller_count, 0) >= 1000 THEN 'Major City'
            WHEN coalesce(cc.customer_count, 0) + coalesce(sc.seller_count, 0) >= 100 THEN 'Large City'
            WHEN coalesce(cc.customer_count, 0) + coalesce(sc.seller_count, 0) >= 10 THEN 'Medium City'
            WHEN coalesce(cc.customer_count, 0) + coalesce(sc.seller_count, 0) >= 1 THEN 'Small City'
            ELSE 'Rural'
        END AS city_size_tier,

        -- Current timestamp
        current_timestamp AS dbt_updated_at

    FROM unique_locations AS ul
    LEFT JOIN geolocation AS g ON ul.zip_code_prefix = g.geolocation_zip_code_prefix
    LEFT JOIN customer_counts AS cc ON ul.zip_code_prefix = cc.zip_code_prefix
    LEFT JOIN seller_counts AS sc ON ul.zip_code_prefix = sc.zip_code_prefix
)

SELECT * FROM geography_dimension
