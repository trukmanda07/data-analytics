# dbt Tests for Olist Data Warehouse

This directory contains tests and validation scripts for the dbt pipeline.

## Files

### `pipeline_validation.py`
Comprehensive validation script that checks:
- All pipeline layers (staging, intermediate, core)
- Data quality metrics
- Row counts and distributions
- Business metrics

**Usage:**
```bash
cd /home/dhafin/Documents/Projects/EDA
source .venv/bin/activate
python dbt/olist_dw_dbt/tests/pipeline_validation.py
```

### `data_quality_tests.sql`
SQL-based data quality tests for:
- Referential integrity
- Value ranges and constraints
- Business logic validation
- Data consistency checks

**Usage:**
```bash
cd dbt/olist_dw_dbt
dbt test
```

## Test Categories

### 1. Schema Tests (in `schema.yml` files)
- `not_null` - Column cannot be null
- `unique` - Column values must be unique
- `accepted_values` - Column must match specific values
- `relationships` - Foreign key validation

### 2. Data Quality Tests (in `data_quality_tests.sql`)
- Payment/order value reconciliation
- Review score validation
- Delivery performance logic
- Orphaned records

### 3. Pipeline Validation (in `pipeline_validation.py`)
- Layer completeness
- Row count validation
- Business metric sanity checks
- Distribution analysis

## Running Tests

### Run all dbt tests:
```bash
dbt test
```

### Run tests for specific models:
```bash
dbt test --select fct_orders
dbt test --select staging
```

### Run Python validation:
```bash
python tests/pipeline_validation.py
```

## Expected Results

### Staging Layer
- 9 views created in `core_staging` schema
- All CSV sources readable
- No errors on data type conversions

### Intermediate Layer
- 3 ephemeral CTEs (not materialized)
- Joins execute successfully
- Aggregations produce valid results

### Core Layer
- 2 tables in `core_core` schema
- `fct_orders`: ~100K rows
- `dim_customers`: ~99K rows

## Adding New Tests

### Schema tests (add to `schema.yml`):
```yaml
columns:
  - name: column_name
    tests:
      - not_null
      - unique
```

### Custom tests (create `.sql` file in `tests/`):
```sql
SELECT *
FROM {{ ref('model_name') }}
WHERE some_condition_that_should_be_false
```

If the query returns any rows, the test fails.
