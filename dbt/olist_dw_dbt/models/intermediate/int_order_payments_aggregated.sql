{{
    config(
        materialized='ephemeral',
        tags=['intermediate', 'payments']
    )
}}

-- Aggregates payment information by order
WITH payments AS (
    SELECT * FROM {{ ref('stg_payments') }}
),

payment_summary AS (
    SELECT
        order_id,

        -- Total payment value
        sum(payment_value) AS total_payment_value,

        -- Payment method counts
        count(*) AS payment_method_count,
        count(DISTINCT payment_type) AS unique_payment_types,

        -- Primary payment method (most common)
        mode(payment_type) AS primary_payment_method,

        -- Installment info
        max(payment_installments) AS max_installments,
        avg(payment_installments) AS avg_installments,

        -- Payment breakdown by type
        sum(CASE WHEN payment_type = 'credit_card' THEN payment_value ELSE 0 END) AS credit_card_value,
        sum(CASE WHEN payment_type = 'boleto' THEN payment_value ELSE 0 END) AS boleto_value,
        sum(CASE WHEN payment_type = 'voucher' THEN payment_value ELSE 0 END) AS voucher_value,
        sum(CASE WHEN payment_type = 'debit_card' THEN payment_value ELSE 0 END) AS debit_card_value,

        -- Flags
        max(CASE WHEN payment_type = 'credit_card' THEN 1 ELSE 0 END)::BOOLEAN AS used_credit_card,
        max(CASE WHEN payment_type = 'boleto' THEN 1 ELSE 0 END)::BOOLEAN AS used_boleto,
        max(CASE WHEN payment_type = 'voucher' THEN 1 ELSE 0 END)::BOOLEAN AS used_voucher,
        max(CASE WHEN payment_installments > 1 THEN 1 ELSE 0 END)::BOOLEAN AS used_installments

    FROM payments
    GROUP BY order_id
)

SELECT * FROM payment_summary
