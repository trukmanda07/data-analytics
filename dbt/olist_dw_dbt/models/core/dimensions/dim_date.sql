{{
    config(
        materialized='table',
        tags=['dimension', 'core', 'date']
    )
}}

-- Date dimension covering the full range of order dates in the dataset
WITH date_range AS (
    -- Get min and max dates from orders
    SELECT
        CAST(MIN(DATE_TRUNC('day', order_purchase_timestamp)) AS DATE) AS min_date,
        CAST(MAX(DATE_TRUNC('day', order_purchase_timestamp)) AS DATE) AS max_date
    FROM {{ ref('stg_orders') }}
),

date_spine AS (
    -- Generate all dates between min and max
    SELECT
        CAST(d AS DATE) AS date_day
    FROM (
        SELECT
            UNNEST(
                generate_series(
                    (SELECT min_date FROM date_range),
                    (SELECT max_date FROM date_range),
                    INTERVAL '1 day'
                )
            ) AS d
    )
),

date_dimension AS (
    SELECT
        -- Date key (YYYYMMDD format)
        CAST(STRFTIME(date_day, '%Y%m%d') AS INTEGER) AS date_key,

        -- Full date
        date_day,

        -- Year attributes
        EXTRACT(YEAR FROM date_day) AS year,
        CAST(STRFTIME(date_day, '%Y') AS INTEGER) AS year_number,
        CAST(STRFTIME(date_day, '%Y') AS VARCHAR) AS year_name,

        -- Quarter attributes
        EXTRACT(QUARTER FROM date_day) AS quarter,
        CAST(STRFTIME(date_day, '%Y-Q') AS VARCHAR) ||
            CAST(EXTRACT(QUARTER FROM date_day) AS VARCHAR) AS quarter_name,

        -- Month attributes
        EXTRACT(MONTH FROM date_day) AS month_number,
        STRFTIME(date_day, '%B') AS month_name,
        STRFTIME(date_day, '%b') AS month_name_short,
        CAST(STRFTIME(date_day, '%Y-%m') AS VARCHAR) AS year_month,

        -- Week attributes
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        EXTRACT(DAYOFWEEK FROM date_day) AS day_of_week,
        STRFTIME(date_day, '%A') AS day_name,
        STRFTIME(date_day, '%a') AS day_name_short,

        -- Day attributes
        EXTRACT(DAY FROM date_day) AS day_of_month,
        EXTRACT(DAYOFYEAR FROM date_day) AS day_of_year,

        -- Weekend flag
        CASE
            WHEN EXTRACT(DAYOFWEEK FROM date_day) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend,

        -- Weekday flag
        CASE
            WHEN EXTRACT(DAYOFWEEK FROM date_day) BETWEEN 1 AND 5 THEN TRUE
            ELSE FALSE
        END AS is_weekday,

        -- Month start/end flags
        CASE
            WHEN EXTRACT(DAY FROM date_day) = 1 THEN TRUE
            ELSE FALSE
        END AS is_month_start,

        CASE
            WHEN date_day = LAST_DAY(date_day) THEN TRUE
            ELSE FALSE
        END AS is_month_end,

        -- Quarter start/end flags
        CASE
            WHEN EXTRACT(MONTH FROM date_day) IN (1, 4, 7, 10)
                AND EXTRACT(DAY FROM date_day) = 1
            THEN TRUE
            ELSE FALSE
        END AS is_quarter_start,

        CASE
            WHEN EXTRACT(MONTH FROM date_day) IN (3, 6, 9, 12)
                AND date_day = LAST_DAY(date_day)
            THEN TRUE
            ELSE FALSE
        END AS is_quarter_end,

        -- Year start/end flags
        CASE
            WHEN EXTRACT(MONTH FROM date_day) = 1
                AND EXTRACT(DAY FROM date_day) = 1
            THEN TRUE
            ELSE FALSE
        END AS is_year_start,

        CASE
            WHEN EXTRACT(MONTH FROM date_day) = 12
                AND EXTRACT(DAY FROM date_day) = 31
            THEN TRUE
            ELSE FALSE
        END AS is_year_end,

        -- Fiscal attributes (assuming calendar year = fiscal year)
        EXTRACT(YEAR FROM date_day) AS fiscal_year,
        EXTRACT(QUARTER FROM date_day) AS fiscal_quarter,

        -- Brazilian holidays (major ones)
        CASE
            WHEN EXTRACT(MONTH FROM date_day) = 1 AND EXTRACT(DAY FROM date_day) = 1 THEN 'New Year''s Day'
            WHEN EXTRACT(MONTH FROM date_day) = 4 AND EXTRACT(DAY FROM date_day) = 21 THEN 'Tiradentes'' Day'
            WHEN EXTRACT(MONTH FROM date_day) = 5 AND EXTRACT(DAY FROM date_day) = 1 THEN 'Labor Day'
            WHEN EXTRACT(MONTH FROM date_day) = 9 AND EXTRACT(DAY FROM date_day) = 7 THEN 'Independence Day'
            WHEN EXTRACT(MONTH FROM date_day) = 10 AND EXTRACT(DAY FROM date_day) = 12 THEN 'Our Lady of Aparecida'
            WHEN EXTRACT(MONTH FROM date_day) = 11 AND EXTRACT(DAY FROM date_day) = 2 THEN 'All Souls'' Day'
            WHEN EXTRACT(MONTH FROM date_day) = 11 AND EXTRACT(DAY FROM date_day) = 15 THEN 'Proclamation of the Republic'
            WHEN EXTRACT(MONTH FROM date_day) = 11 AND EXTRACT(DAY FROM date_day) = 20 THEN 'Black Consciousness Day'
            WHEN EXTRACT(MONTH FROM date_day) = 12 AND EXTRACT(DAY FROM date_day) = 25 THEN 'Christmas Day'
            ELSE NULL
        END AS holiday_name,

        -- Is holiday flag
        CASE
            WHEN (EXTRACT(MONTH FROM date_day) = 1 AND EXTRACT(DAY FROM date_day) = 1)
                OR (EXTRACT(MONTH FROM date_day) = 4 AND EXTRACT(DAY FROM date_day) = 21)
                OR (EXTRACT(MONTH FROM date_day) = 5 AND EXTRACT(DAY FROM date_day) = 1)
                OR (EXTRACT(MONTH FROM date_day) = 9 AND EXTRACT(DAY FROM date_day) = 7)
                OR (EXTRACT(MONTH FROM date_day) = 10 AND EXTRACT(DAY FROM date_day) = 12)
                OR (EXTRACT(MONTH FROM date_day) = 11 AND EXTRACT(DAY FROM date_day) IN (2, 15, 20))
                OR (EXTRACT(MONTH FROM date_day) = 12 AND EXTRACT(DAY FROM date_day) = 25)
            THEN TRUE
            ELSE FALSE
        END AS is_holiday,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM date_spine
)

SELECT * FROM date_dimension
ORDER BY date_day
