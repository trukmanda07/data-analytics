{{
    config(
        materialized='table',
        tags=['fact', 'core', 'payments']
    )
}}

-- Payments fact table (grain: one row per payment)
WITH payments AS (
    SELECT * FROM {{ ref('stg_payments') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

payments_fact AS (
    SELECT
        -- Primary key (composite)
        p.order_id,
        p.payment_sequential,

        -- Foreign keys
        o.customer_id,

        -- Date foreign key
        CAST(STRFTIME(o.order_purchase_timestamp, '%Y%m%d') AS INTEGER) AS order_date_key,

        -- Payment attributes
        p.payment_type,
        p.payment_type_display,
        p.payment_installments,
        p.payment_value,

        -- Order context
        o.order_status,
        o.order_purchase_timestamp,

        -- Customer location (denormalized)
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,

        -- Payment method flags
        CASE WHEN p.payment_type = 'credit_card' THEN TRUE ELSE FALSE END AS is_credit_card,
        CASE WHEN p.payment_type = 'boleto' THEN TRUE ELSE FALSE END AS is_boleto,
        CASE WHEN p.payment_type = 'voucher' THEN TRUE ELSE FALSE END AS is_voucher,
        CASE WHEN p.payment_type = 'debit_card' THEN TRUE ELSE FALSE END AS is_debit_card,

        -- Installment flags and categories
        CASE WHEN p.payment_installments > 1 THEN TRUE ELSE FALSE END AS uses_installments,

        CASE
            WHEN p.payment_installments = 1 THEN 'Full Payment'
            WHEN p.payment_installments BETWEEN 2 AND 3 THEN 'Short Term (2-3)'
            WHEN p.payment_installments BETWEEN 4 AND 6 THEN 'Medium Term (4-6)'
            WHEN p.payment_installments BETWEEN 7 AND 12 THEN 'Long Term (7-12)'
            WHEN p.payment_installments > 12 THEN 'Extended Term (12+)'
            ELSE 'Unknown'
        END AS installment_category,

        -- Payment value tiers
        CASE
            WHEN p.payment_value >= 500 THEN 'Very High'
            WHEN p.payment_value >= 200 THEN 'High'
            WHEN p.payment_value >= 100 THEN 'Medium'
            WHEN p.payment_value >= 50 THEN 'Low'
            ELSE 'Very Low'
        END AS payment_value_tier,

        -- Installment value (value per installment)
        CASE
            WHEN p.payment_installments > 0
            THEN p.payment_value / p.payment_installments
            ELSE p.payment_value
        END AS installment_value,

        -- Is this the first/only payment for this order
        CASE WHEN p.payment_sequential = 1 THEN TRUE ELSE FALSE END AS is_primary_payment,

        -- Order status flags
        CASE WHEN o.order_status = 'delivered' THEN TRUE ELSE FALSE END AS is_delivered,
        CASE WHEN o.order_status = 'canceled' THEN TRUE ELSE FALSE END AS is_canceled,

        -- Current timestamp
        CURRENT_TIMESTAMP AS dbt_updated_at

    FROM payments p
    LEFT JOIN orders o ON p.order_id = o.order_id
    LEFT JOIN customers c ON o.customer_id = c.customer_id
)

SELECT * FROM payments_fact
