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
        cast(min(date_trunc('day', order_purchase_timestamp)) AS DATE) AS min_date,
        cast(max(date_trunc('day', order_purchase_timestamp)) AS DATE) AS max_date
    FROM {{ ref('stg_orders') }}
),

date_spine AS (
    -- Generate all dates between min and max
    SELECT cast(d AS DATE) AS date_day
    FROM (
        SELECT
            unnest(
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
        cast(strftime(date_day, '%Y%m%d') AS INTEGER) AS date_key,

        -- Full date
        date_day,

        -- Year attributes
        extract(YEAR FROM date_day) AS year,
        cast(strftime(date_day, '%Y') AS INTEGER) AS year_number,
        cast(strftime(date_day, '%Y') AS VARCHAR) AS year_name,

        -- Quarter attributes
        extract(QUARTER FROM date_day) AS quarter,
        cast(strftime(date_day, '%Y-Q') AS VARCHAR)
        || cast(extract(QUARTER FROM date_day) AS VARCHAR) AS quarter_name,

        -- Month attributes
        extract(MONTH FROM date_day) AS month_number,
        strftime(date_day, '%B') AS month_name,
        strftime(date_day, '%b') AS month_name_short,
        cast(strftime(date_day, '%Y-%m') AS VARCHAR) AS year_month,

        -- Week attributes
        extract(WEEK FROM date_day) AS week_of_year,
        extract(dayofweek FROM date_day) AS day_of_week,
        strftime(date_day, '%A') AS day_name,
        strftime(date_day, '%a') AS day_name_short,

        -- Day attributes
        extract(DAY FROM date_day) AS day_of_month,
        extract(DAYOFYEAR FROM date_day) AS day_of_year,

        -- Weekend flag
        coalesce(extract(dayofweek FROM date_day) IN (0, 6), false) AS is_weekend,

        -- Weekday flag
        coalesce(extract(dayofweek FROM date_day) BETWEEN 1 AND 5, false) AS is_weekday,

        -- Month start/end flags
        coalesce(extract(DAY FROM date_day) = 1, false) AS is_month_start,

        coalesce(date_day = last_day(date_day), false) AS is_month_end,

        -- Quarter start/end flags
        coalesce(
            extract(MONTH FROM date_day) IN (1, 4, 7, 10)
            AND extract(DAY FROM date_day) = 1, false
        ) AS is_quarter_start,

        coalesce(
            extract(MONTH FROM date_day) IN (3, 6, 9, 12)
            AND date_day = last_day(date_day), false
        ) AS is_quarter_end,

        -- Year start/end flags
        coalesce(
            extract(MONTH FROM date_day) = 1
            AND extract(DAY FROM date_day) = 1, false
        ) AS is_year_start,

        coalesce(
            extract(MONTH FROM date_day) = 12
            AND extract(DAY FROM date_day) = 31, false
        ) AS is_year_end,

        -- Fiscal attributes (assuming calendar year = fiscal year)
        extract(YEAR FROM date_day) AS fiscal_year,
        extract(QUARTER FROM date_day) AS fiscal_quarter,

        -- Brazilian holidays (major ones)
        CASE
            WHEN extract(MONTH FROM date_day) = 1 AND extract(DAY FROM date_day) = 1 THEN 'New Year''s Day'
            WHEN extract(MONTH FROM date_day) = 4 AND extract(DAY FROM date_day) = 21 THEN 'Tiradentes'' Day'
            WHEN extract(MONTH FROM date_day) = 5 AND extract(DAY FROM date_day) = 1 THEN 'Labor Day'
            WHEN extract(MONTH FROM date_day) = 9 AND extract(DAY FROM date_day) = 7 THEN 'Independence Day'
            WHEN extract(MONTH FROM date_day) = 10 AND extract(DAY FROM date_day) = 12 THEN 'Our Lady of Aparecida'
            WHEN extract(MONTH FROM date_day) = 11 AND extract(DAY FROM date_day) = 2 THEN 'All Souls'' Day'
            WHEN extract(MONTH FROM date_day) = 11 AND extract(DAY FROM date_day) = 15 THEN 'Proclamation of the Republic'
            WHEN extract(MONTH FROM date_day) = 11 AND extract(DAY FROM date_day) = 20 THEN 'Black Consciousness Day'
            WHEN extract(MONTH FROM date_day) = 12 AND extract(DAY FROM date_day) = 25 THEN 'Christmas Day'
        END AS holiday_name,

        -- Is holiday flag
        coalesce(
            (extract(MONTH FROM date_day) = 1 AND extract(DAY FROM date_day) = 1)
            OR (extract(MONTH FROM date_day) = 4 AND extract(DAY FROM date_day) = 21)
            OR (extract(MONTH FROM date_day) = 5 AND extract(DAY FROM date_day) = 1)
            OR (extract(MONTH FROM date_day) = 9 AND extract(DAY FROM date_day) = 7)
            OR (extract(MONTH FROM date_day) = 10 AND extract(DAY FROM date_day) = 12)
            OR (extract(MONTH FROM date_day) = 11 AND extract(DAY FROM date_day) IN (2, 15, 20))
            OR (extract(MONTH FROM date_day) = 12 AND extract(DAY FROM date_day) = 25), false
        ) AS is_holiday,

        -- Current timestamp
        current_timestamp AS dbt_updated_at

    FROM date_spine
)

SELECT * FROM date_dimension
ORDER BY date_day
