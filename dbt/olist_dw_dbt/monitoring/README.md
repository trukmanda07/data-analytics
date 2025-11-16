# dbt Custom Monitoring Solution

A lightweight, DuckDB-compatible monitoring solution for tracking dbt pipeline performance.

## Overview

This custom monitoring solution replaces the dbt-artifacts package (which has limited DuckDB support) with a simple Python-based approach that:
- Parses dbt's `run_results.json` and `manifest.json` artifacts
- Stores execution metrics in DuckDB tables
- Provides a Marimo dashboard for visualization

## Architecture

```
dbt run
   ↓
run_results.json + manifest.json
   ↓
log_run_results.py (Python script)
   ↓
DuckDB Tables:
  - core_monitoring.dbt_run_history
  - core_monitoring.dbt_model_history
   ↓
dbt_performance_dashboard.py (Marimo)
```

## Files

- **`dbt_run_history.sql`** - Table definition for pipeline run history
- **`dbt_model_history.sql`** - Table definition for model execution history
- **`log_run_results.py`** - Python script that parses dbt artifacts and logs to tables
- **`dbt_performance_dashboard.py`** - Marimo dashboard for visualizing performance
- **`check_artifacts_tables.py`** - Diagnostic tool to check table status
- **`../dbt_run.sh`** - Wrapper script that runs dbt + logging automatically

## Usage

### Option 1: Wrapper Script (Recommended)

Use the wrapper script which automatically logs results after each run:

```bash
./dbt_run.sh                              # Run all models and log
./dbt_run.sh --select fct_orders          # Run specific model and log
./dbt_run.sh --exclude dbt_artifacts      # Run with exclusions and log
```

### Option 2: Manual Logging

Run dbt normally, then manually log the results:

```bash
dbt run
python3 monitoring/log_run_results.py
```

### View the Dashboard

Launch the Marimo dashboard to visualize performance metrics:

```bash
marimo edit monitoring/dbt_performance_dashboard.py
```

The dashboard shows:
- **Pipeline Stats**: Total models run, runtime, failed runs (last 7 days)
- **Runtime Trends**: Daily pipeline runtime over last 30 days
- **Slowest Models**: Top 15 slowest models by average execution time
- **Layer Performance**: Execution time breakdown by model layer (staging, core, mart)
- **Recent Runs**: Last 10 pipeline invocations
- **Recent Executions**: Last 20 model executions

## Database Schema

### `core_monitoring.dbt_run_history`

Tracks each dbt run invocation:

| Column | Type | Description |
|--------|------|-------------|
| invocation_id | VARCHAR | Unique ID for this dbt run |
| run_started_at | TIMESTAMP | When the run started |
| run_completed_at | TIMESTAMP | When the run completed |
| dbt_command | VARCHAR | Command executed (run, test, build) |
| success | BOOLEAN | Whether all models succeeded |
| total_models | INTEGER | Number of models executed |
| total_tests | INTEGER | Number of tests executed |
| total_runtime_seconds | DOUBLE | Total runtime in seconds |
| dbt_version | VARCHAR | dbt version used |
| target_name | VARCHAR | dbt target (dev, prod) |

### `core_monitoring.dbt_model_history`

Tracks individual model executions:

| Column | Type | Description |
|--------|------|-------------|
| invocation_id | VARCHAR | Links to dbt_run_history |
| model_name | VARCHAR | Name of the model |
| schema_name | VARCHAR | Schema where model is materialized |
| materialization | VARCHAR | Type (table, view, incremental) |
| status | VARCHAR | Execution status (success, error, skipped) |
| execution_time_seconds | DOUBLE | Time taken to execute |
| rows_affected | INTEGER | Number of rows affected |
| executed_at | TIMESTAMP | Timestamp of execution |
| unique_id | VARCHAR | Unique dbt node ID |

## Example Queries

### Find slow models

```sql
SELECT
    model_name,
    materialization,
    ROUND(AVG(execution_time_seconds), 2) AS avg_seconds,
    COUNT(*) AS run_count
FROM core_monitoring.dbt_model_history
WHERE execution_time_seconds > 1
    AND status = 'success'
GROUP BY model_name, materialization
ORDER BY avg_seconds DESC;
```

### Model performance over time

```sql
SELECT
    model_name,
    DATE_TRUNC('day', executed_at) AS execution_date,
    ROUND(AVG(execution_time_seconds), 2) AS avg_runtime,
    COUNT(*) AS executions
FROM core_monitoring.dbt_model_history
WHERE model_name = 'fct_orders'
    AND executed_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY model_name, DATE_TRUNC('day', executed_at)
ORDER BY execution_date;
```

### Pipeline success rate

```sql
SELECT
    dbt_command,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_runs,
    ROUND(SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS success_rate_pct
FROM core_monitoring.dbt_run_history
GROUP BY dbt_command;
```

## Troubleshooting

### Tables are empty

1. Make sure you've run dbt at least once:
   ```bash
   ./dbt_run.sh --select stg_customers
   ```

2. Check if the monitoring tables exist:
   ```bash
   python3 monitoring/check_artifacts_tables.py
   ```

3. Verify `run_results.json` exists:
   ```bash
   ls -la target/run_results.json
   ```

### Script fails with "File not found"

Ensure you're running from the dbt project directory:
```bash
cd /home/dhafin/Documents/Projects/EDA/dbt/olist_dw_dbt
```

### Database is locked

Close any open connections to the DuckDB database (like Marimo dashboards) before running dbt.

## Benefits Over dbt-artifacts

✅ **DuckDB Compatible**: Works natively with DuckDB
✅ **Lightweight**: Simple Python script, no complex dependencies
✅ **Customizable**: Easy to add custom metrics or modify schema
✅ **Fast**: Direct INSERT statements, no incremental model overhead
✅ **Transparent**: All logging logic visible in `log_run_results.py`

## Future Enhancements

Potential improvements:
- Add test execution tracking
- Include source freshness checks
- Track data quality metrics
- Add alerting for slow/failing models
- Export metrics to external monitoring systems

---

**Created:** 2025-11-16
**Author:** Custom Solution for Olist dbt Project
**Version:** 2.0 (Custom Monitoring)
