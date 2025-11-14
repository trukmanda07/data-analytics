# dbt Tests for Olist Data Warehouse

This directory contains comprehensive tests for the Olist e-commerce data warehouse models.

## Test Organization

### 1. Schema Tests (`models/core/dimensions/schema.yml` and `models/core/facts/schema.yml`)
Schema tests are defined in YAML files alongside the models they test. These include:
- **Not null tests**: Ensure primary keys and critical fields are populated
- **Unique tests**: Verify primary key uniqueness
- **Relationships tests**: Validate foreign key integrity
- **Accepted values tests**: Check that categorical fields contain only valid values
- **Range tests**: Ensure numeric values fall within expected bounds

### 2. Generic Tests (`tests/generic/`)
Custom reusable test macros for domain-specific validation:

#### `test_valid_brazilian_state.sql`
Validates that state codes match valid Brazilian state abbreviations (AC, AL, AP, etc.)

**Usage:**
```yaml
columns:
  - name: state_clean
    tests:
      - valid_brazilian_state
```

#### `test_valid_zip_code_prefix.sql`
Ensures zip code prefixes are 5-digit values between 01000 and 99999

**Usage:**
```yaml
columns:
  - name: zip_code_prefix
    tests:
      - valid_zip_code_prefix
```

#### `test_date_range_valid.sql`
Validates dates fall within the expected range for the Olist dataset (2016-2019)

**Parameters:**
- `min_date` (default: '2016-01-01')
- `max_date` (default: '2019-12-31')

**Usage:**
```yaml
columns:
  - name: order_date
    tests:
      - date_range_valid:
          min_date: '2016-09-01'
          max_date: '2018-10-01'
```

#### `test_percentage_range.sql`
Checks that percentage values are within valid range (0-100 by default)

**Parameters:**
- `min_value` (default: 0)
- `max_value` (default: 100)

**Usage:**
```yaml
columns:
  - name: discount_percentage
    tests:
      - percentage_range
```

### 3. Singular Tests (`tests/singular/`)
SQL-based tests for complex business logic validation:

#### Data Integrity Tests

**`test_order_items_total_matches_payments.sql`**
- Validates that total order item values match payment totals per order
- Allows for small rounding differences (< 0.01 BRL)
- Ensures financial data consistency

**`test_product_category_consistency.sql`**
- Verifies products have consistent category assignments across fact and dimension tables
- Prevents category mismatches

**`test_date_keys_exist_in_dim_date.sql`**
- Ensures all date keys in fact tables exist in the date dimension
- Validates referential integrity for date foreign keys

#### Business Logic Tests

**`test_delivery_dates_logical_order.sql`**
- Validates delivery-related dates follow logical sequence
- Checks: purchase < approved < delivered
- Identifies timing anomalies in the order lifecycle

**`test_reviews_only_for_valid_orders.sql`**
- Ensures reviews only exist for orders that have been delivered or shipped
- Prevents reviews for unfulfilled orders

**`test_review_dates_after_purchase.sql`**
- Validates that review creation dates come after order purchase dates
- Ensures temporal consistency

**`test_review_score_sentiment_alignment.sql`**
- Verifies review sentiment aligns with review scores
- positive: 4-5, neutral: 3, negative: 1-2

#### Aggregation Tests

**`test_seller_metrics_match_facts.sql`**
- Validates seller dimension metrics match aggregated fact table values
- Checks: total orders, total items, total revenue
- Allows for small rounding differences (0.01 BRL)

**`test_category_metrics_match_facts.sql`**
- Ensures category dimension metrics match aggregated fact table values
- Validates: total orders, total items, total revenue
- Maintains consistency between dimensions and facts

**`test_geography_entity_counts_positive.sql`**
- Verifies geography locations with entities have positive counts
- Validates location_type field matches actual counts

#### Data Quality Tests

**`test_no_negative_values.sql`**
- Comprehensive check for negative values in financial metrics
- Covers: item prices, freight values, payment values, revenue
- Spans all fact tables and dimension aggregates

## Running Tests

### Run All Tests
```bash
cd /home/dhafin/Documents/Projects/EDA/dbt/olist_dw_dbt
dbt test
```

### Run Tests for Specific Models
```bash
# Test a specific model
dbt test --select dim_sellers

# Test a model and its children
dbt test --select dim_sellers+

# Test all dimension models
dbt test --select models/core/dimensions/*

# Test all fact models
dbt test --select models/core/facts/*
```

### Run Specific Test Types
```bash
# Run only singular tests
dbt test --select test_type:singular

# Run only generic tests
dbt test --select test_type:generic

# Run only schema tests
dbt test --select test_type:schema
```

### Run Tests by Tag
```bash
# Test dimension models
dbt test --select tag:dimension

# Test fact models
dbt test --select tag:fact
```

## Test Coverage Summary

### Dimension Tables

**dim_category** (18 tests)
- Primary key validation
- Metric range checks
- Tier/category value validation
- Aggregation consistency

**dim_date** (13 tests)
- Primary key validation
- Date component range checks
- Calendar attribute validation
- Boolean flag checks

**dim_geography** (14 tests)
- Primary key validation
- Coordinate boundary checks
- Brazilian state validation
- Entity count validation
- Location type validation

**dim_products** (11 tests)
- Primary key validation
- Physical measurement ranges
- Quality score validation
- Category tier validation

**dim_sellers** (16 tests)
- Primary key validation
- Location data validation
- Metric range checks
- Performance tier validation
- Percentage validation (0-100)

### Fact Tables

**fct_order_items** (17 tests)
- Primary and foreign key validation
- Referential integrity (products, sellers, dates)
- Price and freight range checks
- Calculation validation (total = price + freight)
- Status flag validation
- Delivery metric ranges

**fct_payments** (14 tests)
- Primary and foreign key validation
- Referential integrity (orders, dates)
- Payment type validation
- Installment calculation validation
- Value range checks
- Status flag validation

**fct_reviews** (17 tests)
- Primary and foreign key validation
- Referential integrity (orders, dates)
- Review score range (1-5)
- Sentiment classification validation
- Timing metric ranges
- Category value validation

## Test Dependencies

### Required dbt Packages
Some tests use the `dbt_utils` package. Ensure it's installed:

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
```

Install packages:
```bash
dbt deps
```

## Interpreting Test Results

### Test Passes
```
Completed successfully
```
All data meets the test criteria.

### Test Fails
```
FAIL 1 test_name
  Got 5 results, configured to fail if != 0
```
The test query returned rows, indicating issues. Review the test SQL to understand what failed.

### Viewing Failed Test Results
Failed tests output the actual failing rows. Check the test SQL file to see what data was returned.

## Best Practices

1. **Run tests regularly**: Execute tests after each model build
2. **Test in development**: Run tests before committing changes
3. **Monitor test performance**: Some complex tests may be slow on large datasets
4. **Document failures**: If tests fail, investigate and document the root cause
5. **Update tests**: Keep tests current as business logic evolves

## Adding New Tests

### Adding Schema Tests
Edit the appropriate `schema.yml` file:
```yaml
columns:
  - name: new_column
    tests:
      - not_null
      - unique
```

### Adding Generic Tests
Create a new file in `tests/generic/`:
```sql
{% test my_custom_test(model, column_name) %}
SELECT {{ column_name }}
FROM {{ model }}
WHERE <failing_condition>
{% endtest %}
```

### Adding Singular Tests
Create a new SQL file in `tests/singular/`:
```sql
-- Test description
SELECT
    id,
    problematic_field
FROM {{ ref('model_name') }}
WHERE <condition_that_should_not_occur>
```

## Test Maintenance

### When Models Change
- Update schema tests in corresponding `schema.yml` files
- Update singular tests that reference changed models
- Add tests for new columns or business logic

### When Business Rules Change
- Update singular tests to reflect new logic
- Update accepted values in schema tests
- Document changes in git commits

## Support

For issues or questions about tests:
1. Check test SQL files for detailed logic
2. Review dbt documentation: https://docs.getdbt.com/docs/build/tests
3. Check model lineage: `dbt docs generate && dbt docs serve`
