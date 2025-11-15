# Option B: dbt-Only Architecture (SQL-First Approach)

**Document Version:** 3.0
**Date:** 2025-11-09
**Purpose:** Simplified architecture using only dbt (SQL) without Python domain layer
**Status:** Alternative Implementation Path

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [Simplified Data Flow](#simplified-data-flow)
4. [dbt Project Structure](#dbt-project-structure)
5. [Business Logic in SQL](#business-logic-in-sql)
6. [Implementation Guide](#implementation-guide)
7. [Pros and Cons](#pros-and-cons)
8. [When to Choose This Option](#when-to-choose-this-option)

---

## Overview

### What is Option B?

**Option B** is a **simplified architecture** that uses **only dbt (SQL)** for the entire data pipeline. No Python domain layer, no aggregates, no value objects - just pure SQL transformations.

**Core Principle:** "Let the database do the work"

### Architecture Philosophy

```
CSV Files → dbt (SQL transformations) → Star Schema → Dashboards
```

**Key Differences from Option A:**
- ❌ No Python domain layer
- ❌ No business rule validation before load
- ❌ No aggregates or value objects
- ✅ Pure SQL (dbt models only)
- ✅ Simpler architecture
- ✅ Faster initial development

---

## Architecture Comparison

### Option A (Hybrid: Python + dbt)

```
┌─────────────────────────────────────────────────────────┐
│  CSV Files                                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Python Domain Layer (Business Logic)                   │
│  ├── Validate: Order must have items                    │
│  ├── Validate: Payment = Total                          │
│  ├── Validate: Positive amounts                         │
│  └── Raise errors BEFORE database                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Load to DuckDB Staging (only valid data)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  dbt Transformations (SQL)                               │
│  └── Transform validated data                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Star Schema → Dashboards                               │
└─────────────────────────────────────────────────────────┘
```

### Option B (dbt-Only: SQL)

```
┌─────────────────────────────────────────────────────────┐
│  CSV Files                                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  dbt: Load CSV to Staging                                │
│  └── Load ALL data (including potentially invalid)      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  dbt: Staging Models (SQL)                               │
│  ├── Basic cleaning (nulls, types)                      │
│  ├── dbt tests flag issues                              │
│  └── Invalid data may pass through                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  dbt: Core Models (SQL)                                  │
│  ├── Business logic in SQL (CASE statements)            │
│  ├── Create dimensions and facts                        │
│  └── Handle edge cases with WHERE clauses               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  Star Schema → Dashboards                               │
└─────────────────────────────────────────────────────────┘
```

**Key Difference:** Validation happens IN the database (SQL), not BEFORE the database (Python)

---

## Simplified Data Flow

### End-to-End Pipeline (Option B)

```bash
# 1. Load CSV directly to DuckDB using dbt
dbt seed  # Load reference data (categories, geolocation)

# 2. Create external tables pointing to CSV
dbt run --select staging.*  # Uses read_csv_auto()

# 3. Transform with SQL
dbt run --select core.*     # Build dimensions and facts

# 4. Create marts
dbt run --select marts.*    # Pre-aggregations

# 5. Test data quality
dbt test  # Run dbt tests

# 6. Generate docs
dbt docs generate
dbt docs serve
```

**No Python code needed!** Just SQL and dbt commands.

---

## dbt Project Structure

### Directory Layout (Simplified)

```
olist_dw_dbt/
├── dbt_project.yml
├── profiles.yml
│
├── models/
│   ├── staging/
│   │   ├── _sources.yml              # CSV sources
│   │   ├── _staging.yml              # Tests & docs
│   │   ├── stg_orders.sql
│   │   ├── stg_customers.sql
│   │   ├── stg_order_items.sql
│   │   ├── stg_payments.sql
│   │   ├── stg_reviews.sql
│   │   ├── stg_products.sql
│   │   ├── stg_sellers.sql
│   │   └── stg_geolocation.sql
│   │
│   ├── intermediate/
│   │   ├── int_orders_enriched.sql   # Orders + items + payments
│   │   ├── int_customer_metrics.sql  # Customer aggregations
│   │   ├── int_seller_metrics.sql    # Seller aggregations
│   │   └── int_product_metrics.sql   # Product aggregations
│   │
│   ├── core/
│   │   ├── dimensions/
│   │   │   ├── dim_customer.sql      # Customer dimension
│   │   │   ├── dim_product.sql       # Product dimension
│   │   │   ├── dim_seller.sql        # Seller dimension
│   │   │   ├── dim_date.sql          # Date dimension
│   │   │   ├── dim_geography.sql     # Geography dimension
│   │   │   └── dim_category.sql      # Category dimension
│   │   │
│   │   └── facts/
│   │       ├── fact_order_items.sql  # Grain: order item
│   │       ├── fact_orders.sql       # Grain: order
│   │       ├── fact_payments.sql     # Grain: payment
│   │       └── fact_reviews.sql      # Grain: review
│   │
│   └── marts/
│       ├── executive/
│       │   └── mart_executive_dashboard.sql
│       ├── customer/
│       │   ├── mart_customer_analytics.sql
│       │   └── mart_cohort_analysis.sql
│       ├── product/
│       │   └── mart_product_performance.sql
│       ├── seller/
│       │   └── mart_seller_scorecard.sql
│       └── operations/
│           └── mart_delivery_metrics.sql
│
├── macros/
│   ├── generate_surrogate_key.sql
│   ├── validate_business_rules.sql   # Business logic as macros
│   ├── calculate_customer_segment.sql
│   └── calculate_delivery_performance.sql
│
├── tests/
│   ├── assert_orders_have_items.sql
│   ├── assert_payments_match_totals.sql
│   └── assert_positive_amounts.sql
│
└── seeds/
    └── brazilian_states.csv
```

---

## Business Logic in SQL

### Example 1: Order Validation (SQL)

**Without Python domain layer, we validate in SQL:**

```sql
-- models/staging/stg_orders.sql

WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

validated AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
        CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,

        -- ✅ Business rule in SQL: Delivery date must be after order date
        CASE
            WHEN order_delivered_customer_date < order_purchase_timestamp THEN NULL
            ELSE order_delivered_customer_date
        END AS validated_delivery_date,

        -- ✅ Business rule: Calculate if late delivery
        CASE
            WHEN order_delivered_customer_date > order_estimated_delivery_date THEN TRUE
            ELSE FALSE
        END AS is_late_delivery

    FROM source
    WHERE
        -- ✅ Filter out obviously invalid orders
        order_id IS NOT NULL
        AND customer_id IS NOT NULL
)

SELECT * FROM validated
```

**dbt Test to Catch Issues:**

```sql
-- tests/assert_valid_delivery_dates.sql

SELECT
    order_id,
    order_purchase_timestamp,
    order_delivered_customer_date
FROM {{ ref('stg_orders') }}
WHERE
    order_delivered_customer_date < order_purchase_timestamp
```

### Example 2: Customer Segmentation (SQL)

**Business logic as dbt macro:**

```sql
-- macros/calculate_customer_segment.sql

{% macro calculate_customer_segment(total_orders, total_spent, last_order_days_ago) %}
    CASE
        WHEN {{ total_orders }} IS NULL OR {{ total_orders }} = 0 THEN 'NEW'
        WHEN {{ total_orders }} = 1 THEN 'ONE_TIME'
        WHEN {{ total_orders }} BETWEEN 2 AND 5 THEN 'REGULAR'
        WHEN {{ total_orders }} > 5 AND {{ total_spent }} > 1000 THEN 'VIP'
        WHEN {{ total_orders }} > 5 THEN 'LOYAL'
        WHEN {{ last_order_days_ago }} > 180 THEN 'CHURNED'
        ELSE 'ACTIVE'
    END
{% endmacro %}
```

**Usage in model:**

```sql
-- models/core/dimensions/dim_customer.sql

WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_amount) AS total_spent,
        MAX(order_date) AS last_order_date,
        DATEDIFF('day', MAX(order_date), CURRENT_DATE) AS last_order_days_ago
    FROM {{ ref('stg_orders') }}
    GROUP BY customer_id
),

final AS (
    SELECT
        customer_id,
        total_orders,
        total_spent,

        -- ✅ Use macro for business logic
        {{ calculate_customer_segment('total_orders', 'total_spent', 'last_order_days_ago') }} AS customer_segment

    FROM customer_metrics
)

SELECT * FROM final
```

### Example 3: Order Total Validation (SQL)

**Ensure payment matches order total:**

```sql
-- models/intermediate/int_orders_enriched.sql

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT
        order_id,
        SUM(price + freight_value) AS total_items_amount
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment_amount
    FROM {{ ref('stg_order_payments') }}
    GROUP BY order_id
),

enriched AS (
    SELECT
        o.*,
        oi.total_items_amount,
        p.total_payment_amount,

        -- ✅ Business rule: Flag mismatches
        CASE
            WHEN ABS(oi.total_items_amount - p.total_payment_amount) > 0.01 THEN TRUE
            ELSE FALSE
        END AS has_payment_mismatch,

        -- ✅ Business rule: Cannot approve if mismatch
        CASE
            WHEN o.order_status = 'approved'
                AND ABS(oi.total_items_amount - p.total_payment_amount) > 0.01
            THEN 'INVALID'
            ELSE o.order_status
        END AS validated_status

    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN payments p ON o.order_id = p.order_id
)

SELECT * FROM enriched
```

**dbt Test:**

```sql
-- tests/assert_payments_match_totals.sql

SELECT
    order_id,
    total_items_amount,
    total_payment_amount,
    ABS(total_items_amount - total_payment_amount) AS difference
FROM {{ ref('int_orders_enriched') }}
WHERE
    order_status = 'approved'
    AND ABS(total_items_amount - total_payment_amount) > 0.01
```

---

## Implementation Guide

### Step 1: Set Up dbt Project (1 day)

```bash
# Create dbt project
cd ~/projects/olist-dw-v3
mkdir dbt
cd dbt
dbt init olist_dw_dbt --skip-profile-setup

# Configure profiles.yml
cat > ~/.dbt/profiles.yml << 'EOF'
olist_dw_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '../data/duckdb/olist_analytical.duckdb'
      schema: core
      threads: 4
EOF

# Test connection
cd olist_dw_dbt
dbt debug
```

### Step 2: Define CSV Sources (1 day)

```yaml
# models/staging/_sources.yml

version: 2

sources:
  - name: raw
    description: "Raw CSV files from Olist dataset"
    meta:
      owner: "data_engineering"

    tables:
      - name: orders
        description: "Order transactions"
        external:
          location: "{{ env_var('CSV_SOURCE_PATH') }}/olist_orders_dataset.csv"
          file_format: csv

      - name: order_items
        description: "Order line items"
        external:
          location: "{{ env_var('CSV_SOURCE_PATH') }}/olist_order_items_dataset.csv"
          file_format: csv

      - name: customers
        description: "Customer master data"
        external:
          location: "{{ env_var('CSV_SOURCE_PATH') }}/olist_customers_dataset.csv"
          file_format: csv
```

### Step 3: Create Staging Models (2-3 days)

```sql
-- models/staging/stg_orders.sql

WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),

cleaned AS (
    SELECT
        order_id,
        customer_id,
        order_status,
        CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
        CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
        CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date
    FROM source
    WHERE
        -- Basic validation
        order_id IS NOT NULL
        AND customer_id IS NOT NULL
)

SELECT * FROM cleaned
```

**Repeat for all 9 source tables.**

### Step 4: Create Business Logic Macros (2 days)

```sql
-- macros/validate_business_rules.sql

{% macro calculate_delivery_performance(order_date, delivered_date, estimated_date) %}
    CASE
        WHEN {{ delivered_date }} IS NULL THEN NULL
        WHEN {{ delivered_date }} <= {{ estimated_date }} THEN 'ON_TIME'
        WHEN DATEDIFF('day', {{ estimated_date }}, {{ delivered_date }}) <= 7 THEN 'SLIGHTLY_LATE'
        ELSE 'VERY_LATE'
    END
{% endmacro %}

{% macro calculate_rfm_score(recency, frequency, monetary) %}
    -- RFM segmentation logic
    CASE
        WHEN {{ frequency }} >= 10 AND {{ monetary }} >= 1000 THEN 'CHAMPION'
        WHEN {{ frequency }} >= 5 AND {{ monetary }} >= 500 THEN 'LOYAL'
        WHEN {{ recency }} <= 30 AND {{ frequency }} >= 3 THEN 'PROMISING'
        WHEN {{ recency }} > 180 THEN 'AT_RISK'
        ELSE 'REGULAR'
    END
{% endmacro %}
```

### Step 5: Create Core Dimensions (5 days)

```sql
-- models/core/dimensions/dim_customer.sql

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

customer_orders AS (
    SELECT
        customer_id,
        MIN(order_purchase_timestamp) AS first_order_date,
        MAX(order_purchase_timestamp) AS last_order_date,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_amount) AS total_spent,
        DATEDIFF('day', MAX(order_purchase_timestamp), CURRENT_DATE) AS recency_days
    FROM {{ ref('stg_orders') }}
    JOIN {{ ref('int_orders_enriched') }} USING (order_id)
    GROUP BY customer_id
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['c.customer_id']) }} AS customer_key,
        c.customer_id,
        c.customer_unique_id,
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,

        -- Metrics
        COALESCE(co.total_orders, 0) AS total_orders,
        COALESCE(co.total_spent, 0) AS total_spent,
        co.first_order_date,
        co.last_order_date,

        -- ✅ Business logic in SQL
        {{ calculate_customer_segment('co.total_orders', 'co.total_spent', 'co.recency_days') }} AS customer_segment,

        {{ calculate_rfm_score('co.recency_days', 'co.total_orders', 'co.total_spent') }} AS rfm_segment

    FROM customers c
    LEFT JOIN customer_orders co ON c.customer_id = co.customer_id
)

SELECT * FROM final
```

**Repeat for all 6 dimensions.**

### Step 6: Create Facts (3 days)

```sql
-- models/core/facts/fact_order_items.sql

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
),

dim_customer AS (
    SELECT customer_key, customer_id FROM {{ ref('dim_customer') }}
),

dim_product AS (
    SELECT product_key, product_id FROM {{ ref('dim_product') }}
),

dim_seller AS (
    SELECT seller_key, seller_id FROM {{ ref('dim_seller') }}
),

dim_date AS (
    SELECT date_key, full_date FROM {{ ref('dim_date') }}
),

final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['oi.order_id', 'oi.order_item_id']) }} AS order_item_key,

        -- Degenerate dimensions
        oi.order_id,
        oi.order_item_id,

        -- Foreign keys
        dc.customer_key,
        dp.product_key,
        ds.seller_key,
        dd.date_key AS order_date_key,

        -- Measures
        oi.price,
        oi.freight_value,
        oi.price + oi.freight_value AS total_amount,

        -- ✅ Business logic: Delivery performance
        {{ calculate_delivery_performance(
            'o.order_purchase_timestamp',
            'o.order_delivered_customer_date',
            'o.order_estimated_delivery_date'
        ) }} AS delivery_performance

    FROM order_items oi
    JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN dim_customer dc ON o.customer_id = dc.customer_id
    LEFT JOIN dim_product dp ON oi.product_id = dp.product_id
    LEFT JOIN dim_seller ds ON oi.seller_id = ds.seller_id
    LEFT JOIN dim_date dd ON CAST(o.order_purchase_timestamp AS DATE) = dd.full_date
)

SELECT * FROM final
```

### Step 7: Create Marts (5 days)

```sql
-- models/marts/executive/mart_executive_dashboard.sql

WITH daily_metrics AS (
    SELECT
        d.full_date,
        d.year,
        d.month,
        d.year_month,

        COUNT(DISTINCT f.order_id) AS order_count,
        SUM(f.total_amount) AS gmv,
        AVG(f.total_amount) AS avg_order_value,
        COUNT(DISTINCT f.customer_key) AS unique_customers

    FROM {{ ref('fact_order_items') }} f
    JOIN {{ ref('dim_date') }} d ON f.order_date_key = d.date_key
    GROUP BY d.full_date, d.year, d.month, d.year_month
)

SELECT * FROM daily_metrics
ORDER BY full_date
```

### Step 8: Add dbt Tests (2 days)

```yaml
# models/core/dimensions/_dimensions.yml

version: 2

models:
  - name: dim_customer
    description: "Customer dimension"
    columns:
      - name: customer_key
        description: "Surrogate key"
        tests:
          - unique
          - not_null

      - name: customer_id
        description: "Natural key"
        tests:
          - not_null

      - name: total_orders
        description: "Total orders"
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

### Step 9: Run Pipeline (1 hour)

```bash
# Install dbt packages
dbt deps

# Run all models
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

---

## Pros and Cons

### ✅ Pros of Option B (dbt-Only)

1. **Simpler Architecture**
   - Only one tool (dbt)
   - No Python domain layer
   - Easier to understand

2. **Faster Initial Development**
   - Skip domain modeling phase
   - Write SQL directly
   - Get to dashboards faster

3. **Fewer Dependencies**
   - Only need: dbt + DuckDB
   - No Python dataclasses, Pydantic, etc.

4. **Easier to Hire For**
   - SQL analysts more common than Python+DDD developers
   - Lower barrier to entry

5. **Leverage Database Engine**
   - DuckDB does the work
   - Optimized query execution
   - Parallel processing

### ❌ Cons of Option B (dbt-Only)

1. **No Early Validation**
   - Invalid data enters the database
   - Find issues during transformation (not before)
   - Harder to debug

2. **Business Logic Scattered**
   - Logic duplicated across SQL files
   - Hard to maintain consistency
   - No single source of truth

3. **Hard to Unit Test**
   - Need database for every test
   - Slower test execution
   - Complex test setup

4. **No Type Safety**
   - Runtime errors only
   - No compile-time checks
   - More bugs in production

5. **Less Reusable**
   - Logic locked in SQL
   - Can't use in APIs, batch jobs
   - Vendor lock-in (DuckDB SQL)

6. **Poor Handling of Complex Rules**
   - Nested CASE statements become unreadable
   - Hard to express complex invariants
   - SQL not designed for business logic

### Comparison Table

| Aspect | Option A (Python + dbt) | Option B (dbt-Only) |
|--------|------------------------|---------------------|
| **Validation Timing** | Before database (Python) | In database (SQL) |
| **Business Logic** | Centralized (Aggregates) | Scattered (SQL files) |
| **Testability** | Easy (unit tests) | Hard (needs database) |
| **Type Safety** | Yes (mypy) | No (runtime only) |
| **Initial Complexity** | High | Low |
| **Long-term Maintainability** | High | Medium |
| **Development Speed** | Slower start, faster later | Fast start, slower later |
| **Team Skill Required** | Python + DDD + SQL | SQL |
| **Reusability** | High (APIs, jobs) | Low (SQL only) |
| **Cost (3-year)** | $146,160 | $142,000 (slightly cheaper) |

---

## When to Choose This Option

### ✅ Choose Option B (dbt-Only) If:

1. **Small Team** (1-2 people)
   - Limited resources
   - Need to deliver fast
   - Short-term project

2. **Simple Business Rules**
   - Basic data transformations
   - No complex invariants
   - Trusted data source

3. **SQL-Heavy Team**
   - Team knows SQL well
   - Limited Python experience
   - Prefer staying in SQL

4. **MVP / Prototype**
   - Proof of concept
   - Will refactor later
   - Short timeline

5. **Read-Only Analytics**
   - No writes to source systems
   - Only dashboards/reports
   - No API consumers

### ❌ Avoid Option B If:

1. **Complex Business Rules**
   - Many invariants to enforce
   - Complex calculations
   - Need early validation

2. **Multiple Consumers**
   - APIs
   - Batch jobs
   - Real-time systems

3. **Long-Term System**
   - Production system (3+ years)
   - Will grow in complexity
   - Need maintainability

4. **Data Quality Critical**
   - Financial data
   - Compliance requirements
   - Zero tolerance for bad data

5. **Team Has Python Skills**
   - Can implement DDD
   - Prefer type safety
   - Value testability

---

## Implementation Timeline (Option B)

### Week 1: Setup & Staging
- Day 1: dbt project setup
- Day 2-3: Define CSV sources
- Day 4-5: Create staging models (9 tables)

### Week 2: Business Logic Macros
- Day 1-2: Customer segmentation macro
- Day 3: Delivery performance macro
- Day 4: RFM scoring macro
- Day 5: Validation macros

### Week 3: Dimensions
- Day 1: dim_date
- Day 2: dim_customer
- Day 3: dim_product, dim_seller
- Day 4: dim_geography, dim_category
- Day 5: dbt tests for dimensions

### Week 4: Facts
- Day 1: fact_order_items
- Day 2: fact_orders
- Day 3: fact_payments, fact_reviews
- Day 4-5: dbt tests for facts

### Week 5-6: Marts
- Week 5: Executive, customer, product marts
- Week 6: Seller, operations, geographic marts

**Total:** 6 weeks (vs. 7 weeks for Option A)

---

## Cost Comparison

### Option A (Python + dbt)
- Implementation: 7 weeks @ $4,400/week = $30,800
- 3-Year TCO: $146,160

### Option B (dbt-Only)
- Implementation: 6 weeks @ $4,200/week = $25,200
- 3-Year TCO: $142,000

**Savings:** $4,160 (implementation) + $4,160 (ongoing) = **$8,320**

**But:** Option A has better long-term maintainability worth far more than $8k

---

## Example: Complete Order Model (dbt-Only)

```sql
-- models/intermediate/int_orders_complete.sql

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT
        order_id,
        COUNT(*) AS total_items,
        SUM(price) AS total_price,
        SUM(freight_value) AS total_freight,
        SUM(price + freight_value) AS total_amount,
        COUNT(DISTINCT seller_id) AS num_sellers,
        COUNT(DISTINCT product_id) AS num_products
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment,
        COUNT(*) AS num_payments,
        LISTAGG(payment_type, ', ') AS payment_types
    FROM {{ ref('stg_order_payments') }}
    GROUP BY order_id
),

reviews AS (
    SELECT
        order_id,
        review_score,
        review_comment_message
    FROM {{ ref('stg_order_reviews') }}
),

enriched AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.order_status,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,

        -- From order_items
        oi.total_items,
        oi.total_amount,
        oi.num_sellers,
        oi.num_products,

        -- From payments
        p.total_payment,
        p.num_payments,
        p.payment_types,

        -- From reviews
        r.review_score,

        -- ✅ Business rule 1: Multi-vendor order
        CASE WHEN oi.num_sellers > 1 THEN TRUE ELSE FALSE END AS is_multivendor,

        -- ✅ Business rule 2: Payment validation
        CASE
            WHEN ABS(oi.total_amount - p.total_payment) < 0.01 THEN TRUE
            ELSE FALSE
        END AS payment_matches_total,

        -- ✅ Business rule 3: Delivery performance
        {{ calculate_delivery_performance(
            'o.order_purchase_timestamp',
            'o.order_delivered_customer_date',
            'o.order_estimated_delivery_date'
        ) }} AS delivery_performance,

        -- ✅ Business rule 4: Order validity
        CASE
            WHEN oi.total_items = 0 THEN 'INVALID_NO_ITEMS'
            WHEN o.order_status = 'approved' AND NOT payment_matches_total THEN 'INVALID_PAYMENT_MISMATCH'
            WHEN o.order_delivered_customer_date < o.order_purchase_timestamp THEN 'INVALID_DELIVERY_DATE'
            ELSE 'VALID'
        END AS order_validity

    FROM orders o
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN payments p ON o.order_id = p.order_id
    LEFT JOIN reviews r ON o.order_id = r.order_id
)

SELECT * FROM enriched
```

---

## Next Steps

1. **Review this document** - Understand dbt-only approach
2. **Compare with Option A** - Decide which fits your needs
3. **See migration plan** - option_b_to_option_a_migration.md (next document)
4. **Start implementation** - Follow timeline above

---

**Document Status:** ✅ Complete
**Related Documents:**
- `option_b_to_option_a_migration.md` - Migration guide
- `domain_implementation_guide.md` - Option A details
- `technology_comparison_v3.md` - Database selection
