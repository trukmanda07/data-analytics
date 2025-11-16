{{
    config(
        materialized='table',
        schema='monitoring'
    )
}}

-- Create empty table structure for dbt run history
SELECT
    cast(null AS VARCHAR) AS invocation_id,
    cast(null AS TIMESTAMP) AS run_started_at,
    cast(null AS TIMESTAMP) AS run_completed_at,
    cast(null AS VARCHAR) AS dbt_command,
    cast(null AS BOOLEAN) AS success,
    cast(null AS INTEGER) AS total_models,
    cast(null AS INTEGER) AS total_tests,
    cast(null AS DOUBLE) AS total_runtime_seconds,
    cast(null AS VARCHAR) AS dbt_version,
    cast(null AS VARCHAR) AS target_name
WHERE 1 = 0
