{{
    config(
        materialized='table',
        schema='monitoring'
    )
}}

-- Create empty table structure for model execution history
SELECT
    cast(null AS VARCHAR) AS invocation_id,
    cast(null AS VARCHAR) AS model_name,
    cast(null AS VARCHAR) AS schema_name,
    cast(null AS VARCHAR) AS materialization,
    cast(null AS VARCHAR) AS status,
    cast(null AS DOUBLE) AS execution_time_seconds,
    cast(null AS INTEGER) AS rows_affected,
    cast(null AS TIMESTAMP) AS executed_at,
    cast(null AS VARCHAR) AS unique_id
WHERE 1 = 0
