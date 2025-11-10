{{
    config(
        materialized='view',
        tags=['staging', 'orders']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_orders_dataset.csv', header=true, auto_detect=true)
),

cleaned AS (
    SELECT
        -- Primary key
        order_id,

        -- Foreign keys
        customer_id,

        -- Order attributes
        order_status,

        -- Timestamps (cast to proper timestamp type)
        CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
        CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
        CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,

        -- Calculated fields for convenience
        DATE_TRUNC('day', CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_date,
        DATE_TRUNC('month', CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_month,
        DATE_TRUNC('year', CAST(order_purchase_timestamp AS TIMESTAMP)) AS order_year,

        -- Time to approval (in hours)
        CASE
            WHEN order_approved_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (CAST(order_approved_at AS TIMESTAMP) - CAST(order_purchase_timestamp AS TIMESTAMP))) / 3600.0
            ELSE NULL
        END AS hours_to_approval,

        -- Time to delivery (in days)
        CASE
            WHEN order_delivered_customer_date IS NOT NULL
            THEN EXTRACT(EPOCH FROM (CAST(order_delivered_customer_date AS TIMESTAMP) - CAST(order_purchase_timestamp AS TIMESTAMP))) / 86400.0
            ELSE NULL
        END AS days_to_delivery,

        -- Delivery performance (early/on-time/late)
        CASE
            WHEN order_delivered_customer_date IS NULL THEN NULL
            WHEN CAST(order_delivered_customer_date AS TIMESTAMP) < CAST(order_estimated_delivery_date AS TIMESTAMP) THEN 'early'
            WHEN CAST(order_delivered_customer_date AS TIMESTAMP) = CAST(order_estimated_delivery_date AS TIMESTAMP) THEN 'on_time'
            WHEN CAST(order_delivered_customer_date AS TIMESTAMP) > CAST(order_estimated_delivery_date AS TIMESTAMP) THEN 'late'
            ELSE NULL
        END AS delivery_performance,

        -- Days difference from estimated (negative = early, positive = late)
        CASE
            WHEN order_delivered_customer_date IS NOT NULL AND order_estimated_delivery_date IS NOT NULL
            THEN EXTRACT(EPOCH FROM (CAST(order_delivered_customer_date AS TIMESTAMP) - CAST(order_estimated_delivery_date AS TIMESTAMP))) / 86400.0
            ELSE NULL
        END AS days_vs_estimated

    FROM source
    WHERE order_id IS NOT NULL
)

SELECT * FROM cleaned
