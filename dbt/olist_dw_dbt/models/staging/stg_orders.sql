{{
    config(
        materialized='view',
        tags=['staging', 'orders']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_orders_dataset.csv', header = true, auto_detect = true)
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
        cast(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        cast(order_approved_at AS TIMESTAMP) AS order_approved_at,
        cast(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
        cast(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        cast(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,

        -- Calculated fields for convenience
        date_trunc('day', cast(order_purchase_timestamp AS TIMESTAMP)) AS order_date,
        date_trunc('month', cast(order_purchase_timestamp AS TIMESTAMP)) AS order_month,
        date_trunc('year', cast(order_purchase_timestamp AS TIMESTAMP)) AS order_year,

        -- Time to approval (in hours)
        CASE
            WHEN order_approved_at IS NOT null
                THEN extract(EPOCH FROM (cast(order_approved_at AS TIMESTAMP) - cast(order_purchase_timestamp AS TIMESTAMP))) / 3600.0
        END AS hours_to_approval,

        -- Time to delivery (in days)
        CASE
            WHEN order_delivered_customer_date IS NOT null
                THEN extract(EPOCH FROM (cast(order_delivered_customer_date AS TIMESTAMP) - cast(order_purchase_timestamp AS TIMESTAMP))) / 86400.0
        END AS days_to_delivery,

        -- Delivery performance (early/on-time/late)
        CASE
            WHEN order_delivered_customer_date IS null THEN null
            WHEN cast(order_delivered_customer_date AS TIMESTAMP) < cast(order_estimated_delivery_date AS TIMESTAMP) THEN 'early'
            WHEN cast(order_delivered_customer_date AS TIMESTAMP) = cast(order_estimated_delivery_date AS TIMESTAMP) THEN 'on_time'
            WHEN cast(order_delivered_customer_date AS TIMESTAMP) > cast(order_estimated_delivery_date AS TIMESTAMP) THEN 'late'
        END AS delivery_performance,

        -- Days difference from estimated (negative = early, positive = late)
        CASE
            WHEN order_delivered_customer_date IS NOT null AND order_estimated_delivery_date IS NOT null
                THEN extract(EPOCH FROM (cast(order_delivered_customer_date AS TIMESTAMP) - cast(order_estimated_delivery_date AS TIMESTAMP))) / 86400.0
        END AS days_vs_estimated

    FROM source
    WHERE order_id IS NOT null
)

SELECT * FROM cleaned
