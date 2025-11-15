{{
    config(
        materialized='view',
        tags=['staging', 'payments']
    )
}}

WITH source AS (
    SELECT * FROM read_csv('{{ var("csv_source_path") }}/olist_order_payments_dataset.csv', header = true, auto_detect = true)
),

cleaned AS (
    SELECT
        -- Foreign key
        order_id,

        -- Payment sequence
        payment_sequential,

        -- Payment method
        payment_type,

        -- Installments
        cast(payment_installments AS INTEGER) AS payment_installments,

        -- Payment amount
        cast(payment_value AS DECIMAL(10, 2)) AS payment_value,

        -- Payment type categorization
        CASE
            WHEN payment_type = 'credit_card' THEN 'Credit Card'
            WHEN payment_type = 'boleto' THEN 'Boleto'
            WHEN payment_type = 'voucher' THEN 'Voucher'
            WHEN payment_type = 'debit_card' THEN 'Debit Card'
            ELSE 'Other'
        END AS payment_type_display

    FROM source
    WHERE order_id IS NOT null
)

SELECT * FROM cleaned
