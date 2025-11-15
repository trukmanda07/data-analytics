# dbt Tools Integration Guide - Priority Implementation

This guide provides step-by-step instructions for integrating essential dbt tools into the Olist data warehouse project, organized by implementation priority.

---

## Table of Contents

- [High Priority Tools](#high-priority-tools)
  - [1. SQLFluff + dbt-checkpoint](#1-sqlfluff--dbt-checkpoint)
  - [2. dbt-expectations](#2-dbt-expectations)
  - [3. dbt-artifacts](#3-dbt-artifacts)
- [Medium Priority Tools](#medium-priority-tools)
  - [4. Elementary](#4-elementary)
  - [5. dbt-project-evaluator](#5-dbt-project-evaluator)
  - [6. vscode-dbt-power-user](#6-vscode-dbt-power-user)
- [Implementation Roadmap](#implementation-roadmap)

---

# High Priority Tools

## 1. SQLFluff + dbt-checkpoint

**Purpose:** Enforce SQL code quality and style consistency across the project

**Benefits:**
- Catch syntax errors before they reach production
- Maintain consistent SQL formatting across team
- Enforce naming conventions automatically
- Prevent common dbt mistakes (missing tests, docs, etc.)

### Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install SQLFluff with dbt support
uv pip install sqlfluff sqlfluff-templater-dbt

# Install pre-commit framework
uv pip install pre-commit
```

### Configuration

#### Step 1: Create SQLFluff Configuration

Create `.sqlfluff` in your dbt project root (`dbt/olist_dw_dbt/.sqlfluff`):

```ini
[sqlfluff]
# Core config
templater = dbt
dialect = duckdb
max_line_length = 100
indent_unit = space

# Exclude paths
exclude_rules = L034,L031
# L034: Allow wildcard in SELECT statements
# L031: Allow table aliases that don't use AS

[sqlfluff:templater:dbt]
project_dir = .
profiles_dir = ~/.dbt
profile = olist_dw

[sqlfluff:indentation]
indent_unit = space
tab_space_size = 4

[sqlfluff:rules]
# Allow trailing commas
allow_trailing_commas = True

[sqlfluff:rules:L010]
# Capitalization: keywords uppercase
capitalisation_policy = upper

[sqlfluff:rules:L014]
# Unquoted identifiers lowercase
extended_capitalisation_policy = lower

[sqlfluff:rules:L030]
# Function names uppercase
extended_capitalisation_policy = upper
```

#### Step 2: Create Pre-commit Configuration

Create `.pre-commit-config.yaml` in project root (`/home/dhafin/Documents/Projects/EDA/.pre-commit-config.yaml`):

```yaml
repos:
  # SQLFluff for SQL linting and formatting
  - repo: https://github.com/sqlfluff/sqlfluff
    rev: 3.2.5
    hooks:
      - id: sqlfluff-lint
        name: SQLFluff Lint
        entry: sqlfluff lint
        language: python
        files: \.sql$
        args: ["--config", "dbt/olist_dw_dbt/.sqlfluff"]

      - id: sqlfluff-fix
        name: SQLFluff Fix
        entry: sqlfluff fix
        language: python
        files: \.sql$
        args: ["--config", "dbt/olist_dw_dbt/.sqlfluff", "--force"]

  # dbt-checkpoint for dbt-specific validations
  - repo: https://github.com/dbt-checkpoint/dbt-checkpoint
    rev: v2.0.5
    hooks:
      # Check model has description
      - id: check-model-has-description
        name: Check model has description

      # Check model has tests
      - id: check-model-has-tests
        name: Check model has tests
        args: ["--test-cnt", "1", "--"]

      # Check column names are lowercase
      - id: check-column-name-contract
        name: Check column names are lowercase
        args: ["--pattern", "^[a-z_][a-z0-9_]*$", "--"]

      # Check model naming conventions
      - id: check-model-name-contract
        name: Check model naming conventions
        args:
          - "--pattern"
          - "^(stg|int|dim|fct|mart)_[a-z0-9_]+$"
          - "--"

      # Check script has no table locks
      - id: check-script-has-no-table-locks
        name: Check script has no table locks

      # Check sources have tests
      - id: check-source-has-tests
        name: Check sources have tests
        args: ["--test-cnt", "1", "--"]
```

#### Step 3: Install Pre-commit Hooks

```bash
# From project root
cd /home/dhafin/Documents/Projects/EDA

# Install the hooks
pre-commit install

# Optional: Run against all files (first time)
pre-commit run --all-files
```

### Usage

**Automatic (on git commit):**
```bash
# Hooks run automatically when you commit
git add dbt/olist_dw_dbt/models/staging/stg_orders.sql
git commit -m "Update staging model"
# Pre-commit hooks will run and fix issues automatically
```

**Manual linting:**
```bash
# Lint specific file
sqlfluff lint dbt/olist_dw_dbt/models/staging/stg_orders.sql

# Lint all models
sqlfluff lint dbt/olist_dw_dbt/models/

# Auto-fix issues
sqlfluff fix dbt/olist_dw_dbt/models/staging/stg_orders.sql
```

**Run specific hook manually:**
```bash
# Check model descriptions
pre-commit run check-model-has-description --all-files

# Check model tests
pre-commit run check-model-has-tests --all-files
```

### Troubleshooting

**Issue: "dbt compilation failed"**
```bash
# Ensure dbt can compile
cd dbt/olist_dw_dbt
dbt compile
```

**Issue: "Profile not found"**
```bash
# Verify profiles.yml exists
cat ~/.dbt/profiles.yml
```

**Issue: Hooks too strict initially**
```bash
# Disable specific hooks temporarily in .pre-commit-config.yaml
# Add 'exclude: ^path/to/exclude/' to hook
```

---

## 2. dbt-expectations

**Purpose:** Advanced data quality testing with 50+ additional test types

**Benefits:**
- Statistical tests (distributions, outliers, correlations)
- Pattern matching (regex, format validation)
- Relationship tests across tables
- Time-series validation
- Data profiling capabilities

### Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Already installed as part of dbt setup, but if needed:
uv pip install dbt-expectations
```

### Configuration

#### Step 1: Add to packages.yml

Edit or create `dbt/olist_dw_dbt/packages.yml`:

```yaml
packages:
  - package: calogica/dbt_expectations
    version: 0.10.4

  - package: dbt-labs/dbt_utils
    version: 1.3.0
```

#### Step 2: Install the package

```bash
cd dbt/olist_dw_dbt
dbt deps
```

### Usage Examples

#### Example 1: Test for Valid Values with Pattern

Add to `models/staging/schema.yml`:

```yaml
version: 2

models:
  - name: stg_orders
    columns:
      - name: order_status
        description: Current status of the order
        tests:
          # Standard dbt test
          - not_null

          # dbt-expectations: Check valid values
          - dbt_expectations.expect_column_values_to_be_in_set:
              value_set: ['delivered', 'shipped', 'processing', 'canceled', 'unavailable', 'invoiced', 'created']

      - name: order_id
        tests:
          # dbt-expectations: Check UUID format
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^[a-f0-9]{32}$"

      - name: order_purchase_timestamp
        tests:
          # dbt-expectations: Check date is not in future
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: "'2016-01-01'"
              max_value: "current_date"

  - name: stg_order_items
    columns:
      - name: price
        tests:
          # dbt-expectations: Check for reasonable price range
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 10000
              strictly: false

          # dbt-expectations: Check for outliers using IQR method
          - dbt_expectations.expect_column_quantile_values_to_be_between:
              quantile: 0.95
              min_value: 0
              max_value: 1000
```

#### Example 2: Row-level Tests

```yaml
models:
  - name: stg_order_items
    tests:
      # dbt-expectations: Check price + freight >= 0
      - dbt_expectations.expect_column_pair_values_A_to_be_greater_than_B:
          column_A: price
          column_B: 0
          or_equal: true

      # dbt-expectations: Row count in expected range
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 100000
          max_value: 200000
```

#### Example 3: Multi-column Tests

```yaml
models:
  - name: fct_order_items
    tests:
      # dbt-expectations: Check primary key combination is unique
      - dbt_expectations.expect_compound_columns_to_be_unique:
          column_list: ["order_id", "order_item_id"]

      # dbt-expectations: Check specific columns have no nulls
      - dbt_expectations.expect_table_columns_to_not_contain_null:
          column_list: ["order_id", "product_id", "seller_id"]
```

#### Example 4: Schema Validation

```yaml
models:
  - name: dim_customers
    tests:
      # dbt-expectations: Ensure all expected columns exist
      - dbt_expectations.expect_table_columns_to_match_ordered_list:
          column_list:
            - customer_key
            - customer_id
            - customer_zip_code_prefix
            - customer_city
            - customer_state
```

### Advanced: Data Profiling

Create a profiling model `models/analysis/data_profile.sql`:

```sql
{{
  config(
    materialized='table',
    tags=['analysis', 'profiling']
  )
}}

WITH order_stats AS (
    SELECT
        '{{ var("run_date", modules.datetime.datetime.now().strftime("%Y-%m-%d")) }}' AS profile_date,
        COUNT(*) AS total_orders,
        COUNT(DISTINCT customer_id) AS unique_customers,
        MIN(order_purchase_timestamp) AS earliest_order,
        MAX(order_purchase_timestamp) AS latest_order,
        AVG(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) AS delivery_rate
    FROM {{ ref('stg_orders') }}
)

SELECT * FROM order_stats
```

### Best Practices for Olist Project

**1. Start with Critical Tables**
- Begin with `stg_orders`, `stg_order_items`
- Expand to fact and dimension tables
- Finally add to marts

**2. Layer Your Tests**
```yaml
# Staging: Format and basic constraints
stg_orders:
  - expect_column_values_to_match_regex  # Format checks
  - expect_column_values_to_be_in_set    # Valid values

# Intermediate: Business logic
int_order_items_enriched:
  - expect_column_pair_values_A_to_be_greater_than_B  # Logic checks

# Core: Relationship integrity
fct_orders:
  - expect_compound_columns_to_be_unique  # PK checks
  - relationships  # FK checks

# Marts: Aggregation validation
mart_executive_dashboard:
  - expect_table_row_count_to_be_between  # Expected volumes
```

**3. Use Severity Levels**
```yaml
tests:
  - dbt_expectations.expect_column_values_to_be_in_set:
      value_set: ['valid_value']
      config:
        severity: error  # Fail pipeline

  - dbt_expectations.expect_column_values_to_be_between:
      min_value: 0
      max_value: 1000
      config:
        severity: warn  # Log but don't fail
```

### Running Tests

```bash
# Run all tests
dbt test

# Run only dbt-expectations tests
dbt test --select test_type:dbt_expectations

# Run tests for specific model
dbt test --select stg_orders

# Run with warnings
dbt test --warn-error
```

---

## 3. dbt-artifacts

**Purpose:** Monitor dbt pipeline performance and execution history

**Benefits:**
- Track model run times over time
- Identify slow models and bottlenecks
- Monitor test failures and trends
- Analyze resource usage
- Dashboard for dbt operations metrics

### Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# No additional Python packages needed
# This is a dbt package only
```

### Configuration

#### Step 1: Add to packages.yml

Edit `dbt/olist_dw_dbt/packages.yml`:

```yaml
packages:
  - package: calogica/dbt_expectations
    version: 0.10.4

  - package: dbt-labs/dbt_utils
    version: 1.3.0

  - package: brooklyn-data/dbt_artifacts
    version: 2.7.0
```

#### Step 2: Install the package

```bash
cd dbt/olist_dw_dbt
dbt deps
```

#### Step 3: Configure dbt_project.yml

Add to `dbt/olist_dw_dbt/dbt_project.yml`:

```yaml
# ... existing config ...

vars:
  # dbt-artifacts configuration
  dbt_artifacts_database: olist_dw  # Your database name
  dbt_artifacts_schema: dbt_artifacts  # Schema for metadata tables

models:
  # ... existing model configs ...

  # dbt-artifacts models
  dbt_artifacts:
    +schema: dbt_artifacts
    +materialized: incremental
    staging:
      +materialized: ephemeral

# Add on-run-end hook to capture metadata
on-run-end:
  - "{{ dbt_artifacts.upload_results(results) }}"
```

#### Step 4: Create artifacts schema

```bash
# Run dbt to create the schema and tables
cd dbt/olist_dw_dbt
dbt run --select dbt_artifacts
```

### What Gets Tracked

After configuration, dbt-artifacts automatically captures:

**1. Model Execution Metadata:**
- Run times (execution duration)
- Status (success/failure/skipped)
- Rows affected
- Compilation time

**2. Test Results:**
- Test name and type
- Pass/fail status
- Failure count (for tests that don't halt)
- Execution time

**3. Source Freshness:**
- Freshness check results
- Last load time
- Freshness thresholds

**4. Incremental Tracking:**
- Each run appends new data
- Historical trend analysis
- Performance comparison over time

### Database Structure

dbt-artifacts creates the following tables in `olist_dw.dbt_artifacts`:

```
dbt_artifacts/
├── dim_dbt__models          # Model metadata and properties
├── dim_dbt__tests           # Test definitions
├── dim_dbt__sources         # Source table metadata
├── dim_dbt__seeds           # Seed file metadata
├── fct_dbt__model_executions    # Model run history
├── fct_dbt__test_executions     # Test run history
├── fct_dbt__source_freshness    # Freshness check results
└── fct_dbt__latest_full_model_executions  # Most recent runs
```

### Usage and Analysis

#### Query 1: Slowest Models

```sql
-- Find the slowest running models
SELECT
    m.name AS model_name,
    m.materialized,
    AVG(e.execution_time) AS avg_execution_seconds,
    MAX(e.execution_time) AS max_execution_seconds,
    COUNT(*) AS run_count
FROM olist_dw.dbt_artifacts.fct_dbt__model_executions e
JOIN olist_dw.dbt_artifacts.dim_dbt__models m
    ON e.model_execution_id = m.model_id
WHERE e.status = 'success'
GROUP BY m.name, m.materialized
ORDER BY avg_execution_seconds DESC
LIMIT 10;
```

#### Query 2: Test Failure Trends

```sql
-- Track test failures over time
SELECT
    DATE_TRUNC('day', t.generated_at) AS test_date,
    COUNT(*) AS total_tests,
    SUM(CASE WHEN t.status = 'fail' THEN 1 ELSE 0 END) AS failed_tests,
    ROUND(SUM(CASE WHEN t.status = 'fail' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100, 2) AS failure_rate_pct
FROM olist_dw.dbt_artifacts.fct_dbt__test_executions t
GROUP BY DATE_TRUNC('day', t.generated_at)
ORDER BY test_date DESC
LIMIT 30;
```

#### Query 3: Daily Pipeline Performance

```sql
-- Daily pipeline execution summary
SELECT
    DATE_TRUNC('day', execution_started_at) AS run_date,
    COUNT(DISTINCT model_execution_id) AS models_run,
    ROUND(SUM(execution_time) / 60, 2) AS total_runtime_minutes,
    ROUND(AVG(execution_time), 2) AS avg_model_seconds,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS errors
FROM olist_dw.dbt_artifacts.fct_dbt__model_executions
GROUP BY DATE_TRUNC('day', execution_started_at)
ORDER BY run_date DESC
LIMIT 14;
```

#### Query 4: Model Execution by Layer

```sql
-- Performance by model layer (staging, intermediate, core, marts)
SELECT
    SPLIT_PART(m.name, '_', 1) AS model_layer,
    COUNT(DISTINCT m.name) AS model_count,
    ROUND(AVG(e.execution_time), 2) AS avg_execution_seconds,
    ROUND(SUM(e.execution_time), 2) AS total_execution_seconds
FROM olist_dw.dbt_artifacts.fct_dbt__model_executions e
JOIN olist_dw.dbt_artifacts.dim_dbt__models m
    ON e.model_execution_id = m.model_id
WHERE e.status = 'success'
    AND e.execution_started_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY SPLIT_PART(m.name, '_', 1)
ORDER BY total_execution_seconds DESC;
```

### Create Monitoring Dashboard (Marimo)

Create `monitoring/dbt_performance_dashboard.py`:

```python
import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")

@app.cell
def __():
    import marimo as mo
    import duckdb
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    return mo, duckdb, pd, px, go, datetime, timedelta

@app.cell
def __(mo):
    mo.md("""
    # dbt Pipeline Performance Dashboard

    Monitor your dbt pipeline execution metrics, test results, and model performance.
    """)
    return

@app.cell
def __():
    con = duckdb.connect('/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/olist_dw.duckdb')
    return con,

@app.cell
def __(con, mo):
    # Latest pipeline stats
    latest_stats = con.execute("""
        SELECT
            COUNT(DISTINCT model_execution_id) AS models_run,
            ROUND(SUM(execution_time), 2) AS total_runtime_seconds,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS errors,
            MAX(execution_started_at) AS last_run
        FROM olist_dw.dbt_artifacts.fct_dbt__model_executions
        WHERE execution_started_at >= CURRENT_DATE
    """).df()

    mo.hstack([
        mo.stat(label="Models Run Today", value=f"{latest_stats['models_run'][0]:,}"),
        mo.stat(label="Runtime (seconds)", value=f"{latest_stats['total_runtime_seconds'][0]:,.1f}"),
        mo.stat(label="Errors", value=f"{latest_stats['errors'][0]:,}"),
    ])
    return latest_stats,

@app.cell
def __(con, px):
    # Model execution trend
    trend_data = con.execute("""
        SELECT
            DATE_TRUNC('day', execution_started_at) AS run_date,
            ROUND(SUM(execution_time) / 60, 2) AS runtime_minutes
        FROM olist_dw.dbt_artifacts.fct_dbt__model_executions
        WHERE execution_started_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', execution_started_at)
        ORDER BY run_date
    """).df()

    fig_trend = px.line(
        trend_data,
        x='run_date',
        y='runtime_minutes',
        title='Daily Pipeline Runtime (Last 30 Days)',
        labels={'run_date': 'Date', 'runtime_minutes': 'Runtime (minutes)'}
    )
    fig_trend
    return trend_data, fig_trend

@app.cell
def __(con, px):
    # Slowest models
    slow_models = con.execute("""
        SELECT
            m.name,
            ROUND(AVG(e.execution_time), 2) AS avg_seconds
        FROM olist_dw.dbt_artifacts.fct_dbt__model_executions e
        JOIN olist_dw.dbt_artifacts.dim_dbt__models m ON e.model_execution_id = m.model_id
        WHERE e.status = 'success'
            AND e.execution_started_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY m.name
        ORDER BY avg_seconds DESC
        LIMIT 15
    """).df()

    fig_slow = px.bar(
        slow_models,
        x='avg_seconds',
        y='name',
        orientation='h',
        title='Top 15 Slowest Models (7 Day Average)',
        labels={'avg_seconds': 'Avg Execution Time (seconds)', 'name': 'Model'}
    )
    fig_slow
    return slow_models, fig_slow

if __name__ == "__main__":
    app.run()
```

### Running and Viewing Results

```bash
# Run dbt pipeline (artifacts automatically captured via hook)
cd dbt/olist_dw_dbt
dbt build

# Query artifacts directly
dbt run-operation query --args '{"sql": "SELECT * FROM olist_dw.dbt_artifacts.fct_dbt__model_executions LIMIT 10"}'

# View dashboard
source .venv/bin/activate
marimo edit monitoring/dbt_performance_dashboard.py
```

### Best Practices

**1. Regular Cleanup**
```sql
-- Archive old data (keep last 90 days)
DELETE FROM olist_dw.dbt_artifacts.fct_dbt__model_executions
WHERE execution_started_at < CURRENT_DATE - INTERVAL '90 days';
```

**2. Set Alerts for Slow Models**
```sql
-- Identify models slower than threshold
SELECT
    m.name,
    e.execution_time AS seconds
FROM olist_dw.dbt_artifacts.fct_dbt__model_executions e
JOIN olist_dw.dbt_artifacts.dim_dbt__models m ON e.model_execution_id = m.model_id
WHERE e.execution_time > 300  -- 5 minutes
    AND e.execution_started_at >= CURRENT_DATE
ORDER BY e.execution_time DESC;
```

**3. Include in CI/CD**
- Artifacts track every run automatically
- Use in deployment pipelines
- Compare production vs development performance

---

# Medium Priority Tools

## 4. Elementary

**Purpose:** Comprehensive data observability and anomaly detection

**Benefits:**
- Automated anomaly detection on data and metrics
- Data quality monitoring dashboard
- Slack/Teams alerts for issues
- Column-level lineage (complementary to dbt-colibri)
- Test failure tracking and analysis
- Schema change detection

### Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install Elementary
uv pip install elementary-data
```

### Configuration

#### Step 1: Add to packages.yml

Edit `dbt/olist_dw_dbt/packages.yml`:

```yaml
packages:
  - package: calogica/dbt_expectations
    version: 0.10.4

  - package: dbt-labs/dbt_utils
    version: 1.3.0

  - package: brooklyn-data/dbt_artifacts
    version: 2.7.0

  - package: elementary-data/elementary
    version: 0.16.3
```

#### Step 2: Install and Setup

```bash
cd dbt/olist_dw_dbt

# Install package
dbt deps

# Run Elementary's setup models
dbt run --select elementary

# Generate Elementary's baseline data
dbt run-operation elementary.upload_source_freshness
```

#### Step 3: Configure dbt_project.yml

Add to `dbt/olist_dw_dbt/dbt_project.yml`:

```yaml
vars:
  # ... existing vars ...

  # Elementary configuration
  elementary_schema: elementary  # Schema for Elementary tables

models:
  # ... existing model configs ...

  # Elementary models
  elementary:
    +schema: elementary
```

### Adding Elementary Tests

Elementary provides several types of tests:

#### Test Type 1: Volume Anomalies

Detect unusual row count changes:

```yaml
# models/staging/schema.yml
version: 2

models:
  - name: stg_orders
    tests:
      # Elementary: Detect anomalies in row count
      - elementary.volume_anomalies:
          timestamp_column: order_purchase_timestamp
          where_expression: "order_status = 'delivered'"
          anomaly_direction: both  # spike or drop
          sensitivity: 3  # 1-4, higher = less sensitive
```

#### Test Type 2: Freshness Anomalies

Detect when data stops arriving:

```yaml
models:
  - name: stg_orders
    tests:
      # Elementary: Detect freshness issues
      - elementary.freshness_anomalies:
          timestamp_column: order_purchase_timestamp
          time_bucket:
            period: day
            count: 1
```

#### Test Type 3: Schema Changes

Track column additions/removals:

```yaml
models:
  - name: dim_customers
    tests:
      # Elementary: Detect schema changes
      - elementary.schema_changes
```

#### Test Type 4: Dimension Anomalies

Monitor categorical columns:

```yaml
models:
  - name: stg_orders
    columns:
      - name: order_status
        tests:
          # Elementary: Detect anomalies in status distribution
          - elementary.dimension_anomalies:
              timestamp_column: order_purchase_timestamp
              dimensions:
                - order_status
```

#### Test Type 5: All Columns Anomalies

Automatic monitoring of all numeric columns:

```yaml
models:
  - name: fct_order_items
    tests:
      # Elementary: Monitor all columns automatically
      - elementary.all_columns_anomalies:
          timestamp_column: order_purchase_timestamp
          exclude_prefix: "_"
          exclude_regexp: ".*_id$"
```

### Example Configuration for Olist

Create comprehensive monitoring in `models/staging/schema.yml`:

```yaml
version: 2

models:
  - name: stg_orders
    description: Cleaned and standardized order data
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: order_status
        tests:
          - dbt_expectations.expect_column_values_to_be_in_set:
              value_set: ['delivered', 'shipped', 'processing', 'canceled', 'unavailable', 'invoiced', 'created']
          # Elementary dimension monitoring
          - elementary.dimension_anomalies:
              timestamp_column: order_purchase_timestamp
              dimensions:
                - order_status
    tests:
      # Elementary volume monitoring
      - elementary.volume_anomalies:
          timestamp_column: order_purchase_timestamp
          where_expression: "order_status IN ('delivered', 'shipped')"
      # Elementary schema change detection
      - elementary.schema_changes
      # Elementary freshness monitoring
      - elementary.freshness_anomalies:
          timestamp_column: order_purchase_timestamp

  - name: stg_order_items
    tests:
      - elementary.volume_anomalies:
          timestamp_column: shipping_limit_date
      - elementary.all_columns_anomalies:
          timestamp_column: shipping_limit_date
          exclude_regexp: ".*_id$"
```

### Generate Elementary Dashboard

```bash
# From dbt project directory
cd dbt/olist_dw_dbt

# Generate the HTML report
edr report

# Open the report (Linux)
xdg-open edr_target/elementary_report.html

# Or specify output location
edr report --output-path /home/dhafin/Documents/Projects/EDA/reports/elementary.html
```

### Dashboard Features

The Elementary dashboard shows:

1. **Test Results Overview**
   - Pass/fail rates
   - Test trends over time
   - Failed test details

2. **Data Anomalies**
   - Volume anomalies (row count changes)
   - Freshness issues
   - Schema changes
   - Dimension distribution changes

3. **Model Lineage**
   - Visual lineage graph
   - Column-level dependencies
   - Test coverage per model

4. **Model Performance**
   - Run times
   - Execution history
   - Resource usage

### Slack/Email Alerts (Optional)

Configure alerts in `profiles.yml`:

```yaml
# ~/.dbt/profiles.yml
olist_dw:
  outputs:
    dev:
      # ... existing config ...

  target: dev

elementary:
  slack:
    token: "{{ env_var('SLACK_BOT_TOKEN') }}"
    channel: "data-alerts"

  # Or email
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    from: "alerts@yourdomain.com"
    to: ["team@yourdomain.com"]
```

Send alerts:

```bash
# Send test results to Slack
edr send-report --slack-webhook "YOUR_WEBHOOK_URL"

# Send email
edr send-report --email
```

### Running Elementary

```bash
# Run tests
dbt test

# Generate and view report
edr report
xdg-open edr_target/elementary_report.html

# Include in regular workflow
dbt build && edr report
```

### Best Practices

**1. Start with Critical Models**
```yaml
# Begin monitoring your most important tables
# staging/schema.yml - base data quality
# core/schema.yml - business logic validation
# marts/schema.yml - final output monitoring
```

**2. Tune Sensitivity**
```yaml
# Adjust based on data patterns
- elementary.volume_anomalies:
    sensitivity: 4  # Less sensitive (fewer alerts)

- elementary.volume_anomalies:
    sensitivity: 1  # Very sensitive (more alerts)
```

**3. Training Period**
```yaml
# Elementary learns from history
# Run for 2-4 weeks to establish baselines
# Initial false positives are normal
```

---

## 5. dbt-project-evaluator

**Purpose:** Validate dbt project against best practices

**Benefits:**
- Automated best practice checks
- Project structure validation
- Performance anti-pattern detection
- Documentation quality assessment
- Actionable recommendations

### Installation

```bash
# No additional Python packages needed
# This is a dbt package only
```

### Configuration

#### Step 1: Add to packages.yml

Edit `dbt/olist_dw_dbt/packages.yml`:

```yaml
packages:
  - package: calogica/dbt_expectations
    version: 0.10.4

  - package: dbt-labs/dbt_utils
    version: 1.3.0

  - package: brooklyn-data/dbt_artifacts
    version: 2.7.0

  - package: elementary-data/elementary
    version: 0.16.3

  - package: dbt-labs/dbt_project_evaluator
    version: 0.10.0
```

#### Step 2: Install and Run

```bash
cd dbt/olist_dw_dbt

# Install package
dbt deps

# Build the evaluator models
dbt build --select package:dbt_project_evaluator
```

### What It Checks

**1. Model Naming Conventions**
- Staging models start with `stg_`
- Intermediate models start with `int_`
- Fact tables start with `fct_`
- Dimension tables start with `dim_`
- Marts start with `mart_`

**2. Testing Coverage**
- All models have tests
- Sources have freshness checks
- Primary keys tested for uniqueness and not_null

**3. Documentation**
- All models have descriptions
- All columns have descriptions
- Sources are documented

**4. Model Structure**
- No direct source references in marts
- Proper layering (staging → intermediate → core → marts)
- No circular dependencies

**5. Performance**
- Models using appropriate materialization
- No SELECT * in production models
- Incremental models configured correctly

### View Results

```bash
# Query the results
dbt run-operation dbt_project_evaluator.query --args '{"query": "SELECT * FROM dbt_project_evaluator.fct_all_issues"}'

# Or query directly in DuckDB
# Results are in models under package:dbt_project_evaluator
```

### Results Tables

The evaluator creates several tables:

```
dbt_project_evaluator/
├── fct_all_issues           # All identified issues
├── fct_missing_primary_key_tests
├── fct_test_coverage
├── fct_documentation_coverage
├── fct_model_fanout         # Models referenced by too many downstream
├── fct_root_models          # Models with no upstream dependencies
└── fct_unused_sources       # Defined but not referenced sources
```

### Query Issues

Create `monitoring/dbt_project_health.py`:

```python
import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")

@app.cell
def __():
    import marimo as mo
    import duckdb
    import pandas as pd
    return mo, duckdb, pd

@app.cell
def __(mo):
    mo.md("""
    # dbt Project Health Report

    Evaluation results from dbt-project-evaluator showing best practice violations and recommendations.
    """)
    return

@app.cell
def __():
    con = duckdb.connect('/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/olist_dw.duckdb')
    return con,

@app.cell
def __(con):
    # All issues summary
    issues = con.execute("""
        SELECT
            issue_type,
            COUNT(*) AS issue_count
        FROM olist_dw.dbt_project_evaluator.fct_all_issues
        GROUP BY issue_type
        ORDER BY issue_count DESC
    """).df()

    issues
    return issues,

@app.cell
def __(con):
    # Missing primary key tests
    missing_pk = con.execute("""
        SELECT
            model_name,
            column_name
        FROM olist_dw.dbt_project_evaluator.fct_missing_primary_key_tests
        ORDER BY model_name
    """).df()

    missing_pk
    return missing_pk,

@app.cell
def __(con):
    # Test coverage by model
    test_coverage = con.execute("""
        SELECT
            model_name,
            number_of_tests,
            test_coverage_pct
        FROM olist_dw.dbt_project_evaluator.fct_test_coverage
        WHERE test_coverage_pct < 100
        ORDER BY test_coverage_pct ASC
    """).df()

    test_coverage
    return test_coverage,

if __name__ == "__main__":
    app.run()
```

### Customize Evaluation

Configure variables in `dbt_project.yml`:

```yaml
vars:
  # ... existing vars ...

  # dbt-project-evaluator customization
  dbt_project_evaluator:
    # Disable specific checks
    disable_test_coverage: false
    disable_documentation_coverage: false

    # Set thresholds
    models_fanout_threshold: 3  # Max downstream dependencies

    # Exclude specific models from checks
    exclude_packages: ['dbt_artifacts', 'elementary']
```

### Running Evaluation

```bash
# Run evaluation
cd dbt/olist_dw_dbt
dbt build --select package:dbt_project_evaluator

# View specific issues
dbt show --select fct_missing_primary_key_tests
dbt show --select fct_documentation_coverage
```

### Fix Common Issues

**Issue 1: Missing Primary Key Tests**
```yaml
# Add to schema.yml
models:
  - name: stg_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
```

**Issue 2: Missing Documentation**
```yaml
models:
  - name: stg_orders
    description: "Cleaned and standardized order data from source system"
    columns:
      - name: order_id
        description: "Unique identifier for each order"
```

**Issue 3: Direct Source References in Marts**
```sql
-- BAD: Direct source reference in mart
SELECT * FROM {{ source('olist', 'orders') }}

-- GOOD: Reference staging model
SELECT * FROM {{ ref('stg_orders') }}
```

---

## 6. vscode-dbt-power-user

**Purpose:** Enhanced dbt development experience in VS Code

**Benefits:**
- Column-level lineage in IDE
- Query preview without running
- Model documentation preview
- SQL formatting
- Quick navigation to models/sources
- dbt command palette

### Installation

#### Step 1: Install VS Code Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "dbt Power User"
4. Click Install

Or install via command line:

```bash
code --install-extension innoverio.vscode-dbt-power-user
```

#### Step 2: Install Python Package

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dbt-power-user
uv pip install dbt-power-user
```

#### Step 3: Configure VS Code

Create or edit `.vscode/settings.json` in project root:

```json
{
  "dbt.dbtProjectLocation": "dbt/olist_dw_dbt",
  "dbt.dbtProfilesLocation": "~/.dbt",
  "dbt.queryTemplate": "select * from ({query}) as my_query limit {limit}",
  "dbt.queryLimit": 100,

  "dbt-power-user.enablePreviewFeatures": true,
  "dbt-power-user.showGraphOnLoad": false,

  "files.associations": {
    "*.sql": "jinja-sql"
  },

  "sqlfluff.dialect": "duckdb",
  "sqlfluff.executablePath": ".venv/bin/sqlfluff"
}
```

### Features

#### Feature 1: Model Lineage

- Right-click any model reference: `{{ ref('model_name') }}`
- Select "Show Lineage"
- Visual graph appears showing upstream/downstream

#### Feature 2: Compiled Query Preview

- Open any dbt model `.sql` file
- Click "Compile Current Model" in status bar
- See Jinja-free SQL in preview pane

#### Feature 3: Column Lineage

- Hover over column name
- See where column originates
- Click to jump to source

#### Feature 4: Go to Definition

- Cmd/Ctrl + Click on `{{ ref('model_name') }}`
- Jump directly to model file

#### Feature 5: Documentation Preview

- View model documentation inline
- See column descriptions
- Preview schema.yml content

#### Feature 6: dbt Command Palette

- Cmd/Ctrl + Shift + P
- Type "dbt"
- Run dbt commands from palette:
  - dbt run
  - dbt test
  - dbt compile
  - dbt build

### Keyboard Shortcuts

Add to `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+c",
    "command": "dbt.compileCurrentModel",
    "when": "editorLangId == jinja-sql"
  },
  {
    "key": "ctrl+shift+r",
    "command": "dbt.runCurrentModel",
    "when": "editorLangId == jinja-sql"
  },
  {
    "key": "ctrl+shift+t",
    "command": "dbt.testCurrentModel",
    "when": "editorLangId == jinja-sql"
  },
  {
    "key": "ctrl+shift+l",
    "command": "dbt.showModelLineage",
    "when": "editorLangId == jinja-sql"
  }
]
```

### Usage Tips

**1. Quick Model Navigation**
- Use "Go to Symbol" (Ctrl+Shift+O) in SQL files
- Lists all CTEs and selections
- Jump to specific CTE

**2. Query Results**
- Click "Run Current Model" icon
- Results appear in VS Code panel
- No need to switch to terminal

**3. SQL Formatting**
- Right-click → Format Document
- Uses SQLFluff configuration
- Formats with dbt/Jinja awareness

**4. Documentation Generation**
- Right-click model in explorer
- Select "Generate Documentation"
- Creates schema.yml entry automatically

### Troubleshooting

**Issue: "dbt executable not found"**
```bash
# Ensure dbt is in PATH
which dbt  # Should show .venv/bin/dbt

# Or set explicit path in settings.json
{
  "dbt.dbtExecutablePath": "/home/dhafin/Documents/Projects/EDA/.venv/bin/dbt"
}
```

**Issue: "Cannot compile model"**
```bash
# Check profiles.yml
cat ~/.dbt/profiles.yml

# Test dbt connection
cd dbt/olist_dw_dbt
dbt debug
```

**Issue: Extension slow**
```json
// Disable graph auto-load
{
  "dbt-power-user.showGraphOnLoad": false
}
```

---

# Implementation Roadmap

## Phase 1: Code Quality (Week 1)

**Day 1-2: SQLFluff + Pre-commit**
- [ ] Install SQLFluff and pre-commit
- [ ] Configure `.sqlfluff` and `.pre-commit-config.yaml`
- [ ] Run initial format on all SQL files
- [ ] Fix any linting errors
- [ ] Test pre-commit hooks on sample commit

**Day 3-4: dbt-checkpoint**
- [ ] Add dbt-checkpoint hooks
- [ ] Run checks on existing models
- [ ] Fix naming convention violations
- [ ] Add missing descriptions/tests
- [ ] Document in team wiki

**Day 5-7: Buffer and Training**
- [ ] Team training on new tools
- [ ] Update contribution guidelines
- [ ] Create troubleshooting guide

## Phase 2: Data Quality (Week 2)

**Day 1-3: dbt-expectations**
- [ ] Install and configure package
- [ ] Add tests to staging models
- [ ] Add tests to core models
- [ ] Add tests to marts
- [ ] Document test strategy

**Day 4-5: Test Development**
- [ ] Create custom test suite
- [ ] Set up severity levels
- [ ] Configure test selectors
- [ ] Run full test suite

**Day 6-7: Validation**
- [ ] Review test results
- [ ] Fix data quality issues
- [ ] Tune test thresholds
- [ ] Document test coverage

## Phase 3: Monitoring (Week 3)

**Day 1-2: dbt-artifacts**
- [ ] Install and configure package
- [ ] Set up metadata schema
- [ ] Create monitoring queries
- [ ] Build performance dashboard

**Day 2-3: Elementary**
- [ ] Install Elementary
- [ ] Add anomaly detection tests
- [ ] Generate first report
- [ ] Configure alerts (optional)

**Day 4-5: Dashboard Development**
- [ ] Create Marimo dashboards
- [ ] Set up automated reporting
- [ ] Document monitoring process

**Day 6-7: Baseline Establishment**
- [ ] Run for full week to establish baselines
- [ ] Tune anomaly sensitivity
- [ ] Document normal patterns

## Phase 4: Optimization (Week 4)

**Day 1-2: dbt-project-evaluator**
- [ ] Install and run evaluator
- [ ] Review all issues
- [ ] Prioritize fixes
- [ ] Create remediation plan

**Day 3-5: Project Cleanup**
- [ ] Fix evaluator issues
- [ ] Improve documentation
- [ ] Add missing tests
- [ ] Optimize materializations

**Day 6-7: IDE Setup**
- [ ] Install VS Code Power User
- [ ] Configure team settings
- [ ] Create keyboard shortcuts
- [ ] Team training session

---

## Quick Start Checklist

For fastest value, implement in this order:

### Immediate Value (Do First)
1. ✅ **SQLFluff** - Instant code quality improvement
2. ✅ **dbt-expectations** - Better data quality tests
3. ✅ **VS Code Power User** - Better developer experience

### Short-term Value (Do Second)
4. ✅ **dbt-artifacts** - Track performance trends
5. ✅ **dbt-checkpoint** - Prevent common mistakes
6. ✅ **dbt-project-evaluator** - Identify issues

### Long-term Value (Do Third)
7. ✅ **Elementary** - Comprehensive observability

---

## Maintenance Schedule

**Daily:**
- Pre-commit hooks run automatically
- Review Elementary anomaly alerts
- Check test failures

**Weekly:**
- Review dbt-artifacts dashboard
- Analyze slow model trends
- Check test coverage reports

**Monthly:**
- Run dbt-project-evaluator
- Review and tune Elementary baselines
- Update documentation
- Team retro on tool effectiveness

---

## Success Metrics

Track these metrics to measure tool effectiveness:

**Code Quality:**
- % of models with linting errors (target: 0%)
- Pre-commit hook success rate (target: >95%)

**Data Quality:**
- % of models with tests (target: 100%)
- Test pass rate (target: >99%)
- Anomalies detected per week

**Performance:**
- Average pipeline runtime
- Number of models >5min runtime
- Week-over-week performance trends

**Developer Experience:**
- Time to onboard new team member
- Average PR review time
- Developer satisfaction score

---

## Resources and Documentation

- **SQLFluff**: https://docs.sqlfluff.com
- **dbt-expectations**: https://github.com/calogica/dbt-expectations
- **dbt-artifacts**: https://github.com/brooklyn-data/dbt_artifacts
- **Elementary**: https://docs.elementary-data.com
- **dbt-project-evaluator**: https://github.com/dbt-labs/dbt-project-evaluator
- **dbt-checkpoint**: https://github.com/dbt-checkpoint/dbt-checkpoint
- **VS Code Power User**: https://marketplace.visualstudio.com/items?itemName=innoverio.vscode-dbt-power-user

---

**Created:** 2025-11-15
**Last Updated:** 2025-11-15
**Author:** Documentation for Olist EDA Project
**Version:** 1.0
