{{
    config(
        materialized='view',
        tags=['staging', 'geolocation']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_geolocation_dataset.csv', header=true, auto_detect=true)
),

-- Remove duplicates by taking average coordinates per zip code
deduplicated AS (
    SELECT
        geolocation_zip_code_prefix,
        AVG(CAST(geolocation_lat AS DECIMAL(10,6))) AS geolocation_lat,
        AVG(CAST(geolocation_lng AS DECIMAL(10,6))) AS geolocation_lng,
        -- Take the first city/state for this zip (they should be consistent)
        MIN(geolocation_city) AS geolocation_city,
        MIN(geolocation_state) AS geolocation_state
    FROM source
    WHERE geolocation_zip_code_prefix IS NOT NULL
    GROUP BY geolocation_zip_code_prefix
),

cleaned AS (
    SELECT
        -- Primary key
        geolocation_zip_code_prefix,

        -- Coordinates
        geolocation_lat,
        geolocation_lng,

        -- Location
        geolocation_city,
        geolocation_state,

        -- Standardize state abbreviation
        UPPER(TRIM(geolocation_state)) AS geolocation_state_clean

    FROM deduplicated
)

SELECT * FROM cleaned
