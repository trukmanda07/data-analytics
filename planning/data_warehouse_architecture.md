# Data Warehouse Architecture for Olist E-Commerce Analytics

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Author:** Data Architecture Team
**Project:** Olist E-Commerce Data Warehouse

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Context](#business-context)
3. [Architecture Overview](#architecture-overview)
4. [Technology Stack Options](#technology-stack-options)
5. [Logical Architecture](#logical-architecture)
6. [Physical Architecture](#physical-architecture)
7. [Data Flow](#data-flow)
8. [Performance Optimization](#performance-optimization)
9. [Scalability Strategy](#scalability-strategy)
10. [Cost Analysis](#cost-analysis)

---

## Executive Summary

This document outlines a comprehensive data warehouse architecture for the Olist Brazilian E-Commerce platform, designed to support 100+ business questions across strategic, operational, and analytical use cases.

**Key Characteristics:**
- **Data Volume:** 100k-1M rows per table (moderate scale)
- **Query Pattern:** OLAP-heavy, analytical workloads
- **Approach:** ELT (Extract-Load-Transform) with modern data stack
- **Architecture:** Star schema with dimensional modeling
- **Timeline:** 3-phase implementation over 12-16 weeks

**Recommended Technology Stack:** DuckDB + dbt + Dagster (Phase 1 MVP) with migration path to PostgreSQL or ClickHouse for production.

---

## Business Context

### Dataset Overview

**Source Location:** `/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/`

**Time Period:** 2016-2018 (historical dataset)

**Data Sources:**
1. **Orders** (99.4k records) - Order lifecycle events
2. **Order Items** (112k records) - Line-item details
3. **Customers** (99.4k records) - Customer master data
4. **Products** (32.9k records) - Product catalog
5. **Sellers** (3.1k records) - Seller marketplace participants
6. **Payments** (103k records) - Payment transactions
7. **Reviews** (99.2k records) - Customer feedback
8. **Geolocation** (1M records) - Brazilian zip code coordinates
9. **Category Translation** (71 records) - PT to EN mapping

### Business Requirements Summary

**Primary Use Cases:**
1. **Executive Dashboards** - GMV, revenue growth, KPIs (Weekly)
2. **Operational Analytics** - Delivery performance, seller metrics (Daily)
3. **Customer Analytics** - Cohort analysis, retention, LTV (Monthly)
4. **Product Analytics** - Category performance, catalog health (Weekly)
5. **Geographic Analysis** - Regional performance, market penetration (Monthly)
6. **Predictive Analytics** - Forecasting, churn prediction (Quarterly)

**Critical Business Questions (Tier 1):**
- Month-over-month revenue growth
- Customer acquisition trends
- Delivery performance (on-time %)
- Customer satisfaction (NPS proxy)
- GMV trajectory
- Regional revenue distribution

---

## Architecture Overview

### Architectural Principles

1. **Separation of Concerns:** Raw → Staging → Core → Mart layers
2. **Single Source of Truth:** Deduplicated, validated core layer
3. **Modularity:** Reusable dimension tables across fact tables
4. **Incrementality:** Support both full refresh and incremental loads
5. **Auditability:** Track data lineage and transformation history
6. **Performance:** Optimized for analytical queries (aggregations, joins)
7. **Simplicity:** Avoid over-engineering for current data volume

### Logical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOURCE LAYER                              │
│  CSV Files: Orders, Customers, Products, Sellers, Payments, etc.│
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ EXTRACT & LOAD
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STAGING LAYER (Raw)                         │
│  - stg_orders          - stg_order_items                         │
│  - stg_customers       - stg_products                            │
│  - stg_sellers         - stg_payments                            │
│  - stg_reviews         - stg_geolocation                         │
│                                                                   │
│  Purpose: Exact copy with type casting, basic validation        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ TRANSFORM & CLEANSE
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER (Core)                      │
│                                                                   │
│  DIMENSION TABLES:              FACT TABLES:                     │
│  - dim_customer                 - fact_order_items               │
│  - dim_product                  - fact_orders (aggregated)       │
│  - dim_seller                   - fact_payments                  │
│  - dim_date                     - fact_reviews                   │
│  - dim_geography                - fact_order_status_events       │
│  - dim_category                                                  │
│                                                                   │
│  Purpose: Clean, conformed dimensions; granular facts            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ AGGREGATE & OPTIMIZE
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (Marts)                    │
│                                                                   │
│  - mart_executive_dashboard                                      │
│  - mart_customer_analytics                                       │
│  - mart_product_performance                                      │
│  - mart_seller_scorecard                                         │
│  - mart_delivery_metrics                                         │
│  - mart_geographic_analysis                                      │
│  - mart_financial_metrics                                        │
│                                                                   │
│  Purpose: Pre-aggregated, denormalized views for BI tools        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ CONSUME
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CONSUMPTION LAYER                            │
│  - Marimo Notebooks                                              │
│  - Plotly Dashboards                                             │
│  - BI Tools (future: Metabase, Superset)                        │
│  - ML Models (Python/scikit-learn)                              │
└─────────────────────────────────────────────────────────────────┘
```

### Physical Architecture Layers

#### Layer 1: Staging (Raw Zone)
- **Purpose:** Landing zone for raw CSV data
- **Retention:** Keep historical snapshots for audit
- **Schema:** Mirrors source CSV structure with minimal transformation
- **Naming:** `stg_<source_name>`
- **Data Quality:** Basic type validation, null checks

#### Layer 2: Integration (Core Zone)
- **Purpose:** Single source of truth with business logic applied
- **Schema:** Dimensional model (star schema)
- **Naming:** `dim_<entity>`, `fact_<process>`
- **Data Quality:** Deduplication, referential integrity, business rules
- **SCD:** Type 2 for customers, products, sellers (track history)

#### Layer 3: Presentation (Mart Zone)
- **Purpose:** Optimized for specific business questions
- **Schema:** Denormalized, pre-aggregated
- **Naming:** `mart_<business_domain>`
- **Refresh:** Incremental where possible, materialized views
- **Access:** Primary interface for BI tools and analysts

---

## Technology Stack Options

### Option 1: DuckDB + dbt + Python (RECOMMENDED for MVP)

**Technology Components:**
- **Database:** DuckDB (embedded analytical database)
- **Transformation:** dbt-core (SQL-based transformations)
- **Orchestration:** Dagster or Apache Airflow
- **Visualization:** Marimo notebooks + Plotly
- **Language:** Python 3.10+

**Architecture Pattern:**
```
CSV Files → DuckDB (in-file or in-memory) → dbt models → Materialized views → Query layer
```

**Pros:**
- **Zero infrastructure cost** - Runs entirely on local machine
- **Blazing fast** - Columnar storage, vectorized execution
- **Simple setup** - Single-file database or in-memory
- **SQL-native** - Standard SQL with excellent PostgreSQL compatibility
- **Python integration** - Direct DuckDB Python API
- **Perfect for dataset size** - Handles millions of rows effortlessly
- **Development velocity** - No server management, instant iteration
- **Version control friendly** - Database is a file, commit to Git
- **Excellent for analytics** - Built for OLAP workloads
- **dbt compatible** - Use dbt-duckdb adapter

**Cons:**
- **Single-user** - No concurrent writes (reads are fine)
- **Limited ecosystem** - Fewer tools compared to PostgreSQL
- **No built-in auth** - Need application-layer security
- **Scaling ceiling** - Eventually need multi-user database
- **Not for transactional workloads** - OLAP-optimized only

**Cost Estimate:**
- **Infrastructure:** $0 (local development)
- **Licenses:** $0 (all open-source)
- **Development effort:** 4-6 weeks for MVP
- **Maintenance:** Minimal (no server ops)

**Best For:**
- MVP and proof-of-concept
- Single-analyst or small team environments
- Local development and testing
- Cost-sensitive projects
- Fast iteration and prototyping

---

### Option 2: PostgreSQL + dbt + Docker (Production-Ready)

**Technology Components:**
- **Database:** PostgreSQL 15+ with analytical extensions
- **Extensions:** TimescaleDB (time-series), pg_partman (partitioning)
- **Transformation:** dbt-core
- **Orchestration:** Apache Airflow or Dagster
- **Containerization:** Docker + Docker Compose
- **Visualization:** Metabase or Apache Superset

**Architecture Pattern:**
```
CSV → Python ETL → PostgreSQL (staging schema) → dbt → Core/Mart schemas → BI Tools
```

**Pros:**
- **Production-grade** - Battle-tested, 30+ years of development
- **Multi-user support** - Concurrent reads/writes with ACID guarantees
- **Rich ecosystem** - Extensive tooling, extensions, community
- **SQL standards compliance** - Industry-standard SQL
- **Robust security** - Row-level security, roles, SSL
- **Horizontal scaling** - Replication, read replicas
- **Full-text search** - Built-in search capabilities
- **JSON support** - Handle semi-structured data
- **Mature dbt support** - dbt-postgres adapter is primary
- **Free and open-source** - No licensing costs

**Cons:**
- **Infrastructure overhead** - Requires server management
- **Performance tuning** - Needs indexes, vacuum, analyze
- **Resource requirements** - More memory/CPU than DuckDB
- **Setup complexity** - Installation, configuration, backups
- **Not as fast for pure analytics** - Row-store vs columnar

**Cost Estimate:**
- **Infrastructure:**
  - Local Docker: $0
  - Cloud VM (4 vCPU, 16GB RAM): $50-100/month
  - Managed RDS: $150-300/month
- **Licenses:** $0 (open-source)
- **Development effort:** 6-8 weeks for MVP
- **Maintenance:** Moderate (backups, updates, monitoring)

**Best For:**
- Production deployments
- Multi-user teams
- Need for transactional integrity
- Integration with existing PostgreSQL infrastructure
- Long-term scalability (to ~10M rows/table)

---

### Option 3: ClickHouse + dbt + Docker (High-Performance Analytics)

**Technology Components:**
- **Database:** ClickHouse (columnar OLAP database)
- **Transformation:** dbt-clickhouse
- **Orchestration:** Apache Airflow
- **Visualization:** Metabase or built-in ClickHouse UI
- **Deployment:** Docker or ClickHouse Cloud

**Architecture Pattern:**
```
CSV → Python/ClickHouse client → ClickHouse (MergeTree tables) → Materialized views → Query layer
```

**Pros:**
- **Extreme performance** - 100-1000x faster than PostgreSQL for analytics
- **Columnar storage** - Optimized for aggregations and scans
- **Compression** - 10x compression ratios, saves storage
- **Real-time analytics** - Sub-second queries on billions of rows
- **Time-series native** - Excellent for temporal analysis
- **Horizontal scaling** - Distributed tables across cluster
- **SQL interface** - Familiar SQL syntax
- **Materialized views** - Incremental aggregations
- **Handles massive scale** - Proven at petabyte scale

**Cons:**
- **Steeper learning curve** - Different from traditional RDBMS
- **No transactions** - Eventually consistent, not ACID
- **Limited UPDATE/DELETE** - Optimized for append-only
- **Smaller ecosystem** - Fewer tools than PostgreSQL
- **Overkill for dataset size** - 100k rows don't need ClickHouse
- **Resource intensive** - Wants lots of RAM and CPU
- **Complex operations** - Cluster management overhead

**Cost Estimate:**
- **Infrastructure:**
  - Local Docker: $0
  - Cloud VM (8 vCPU, 32GB RAM): $150-250/month
  - ClickHouse Cloud: $0.30-0.50/hour (~$200-350/month)
- **Licenses:** $0 (open-source)
- **Development effort:** 8-10 weeks (learning curve)
- **Maintenance:** Moderate-to-high (monitoring, optimization)

**Best For:**
- Very large datasets (10M+ rows)
- Real-time analytics requirements
- Time-series heavy workloads
- Need for extreme query performance
- Future-proofing for massive scale

---

### Comparison Matrix

| Criteria | DuckDB | PostgreSQL | ClickHouse |
|----------|--------|------------|------------|
| **Setup Time** | Minutes | Hours | Hours-Days |
| **Query Performance (100k rows)** | Excellent | Good | Excellent |
| **Query Performance (100M+ rows)** | Good | Fair | Excellent |
| **Multi-user Support** | No | Yes | Yes |
| **Learning Curve** | Low | Low | Medium-High |
| **Operational Overhead** | Minimal | Moderate | High |
| **Cost (monthly)** | $0 | $50-300 | $200-500 |
| **Ecosystem Maturity** | Growing | Mature | Moderate |
| **dbt Support** | Good | Excellent | Good |
| **Best Use Case** | Local/MVP | Production | Big Data |
| **Migration Effort (from current)** | Minimal | Low | Medium |

---

### Recommended Approach: Hybrid Strategy

**Phase 1 (Weeks 1-6): DuckDB MVP**
- Build complete data warehouse in DuckDB
- Develop all dbt models and transformations
- Create initial dashboards and reports
- Validate dimensional model and business logic
- **Deliverable:** Functional analytics platform answering Tier 1 questions

**Phase 2 (Weeks 7-12): PostgreSQL Migration (if needed)**
- Migrate to PostgreSQL for multi-user access
- Maintain same dbt codebase (minimal changes)
- Add orchestration with Airflow/Dagster
- Deploy on Docker or cloud VM
- **Deliverable:** Production-ready data warehouse

**Phase 3 (Weeks 13-16): Optimization & Advanced Features**
- Add incremental models for large tables
- Implement data quality checks (dbt tests)
- Build ML pipelines for predictive analytics
- Consider ClickHouse if performance becomes bottleneck
- **Deliverable:** Enterprise-grade analytics platform

**Why This Works:**
- DuckDB and PostgreSQL use nearly identical SQL syntax
- dbt code is portable between adapters
- Validate business logic before infrastructure investment
- Defer scaling decisions until needed
- Zero upfront cost, pay only when scaling required

---

## Logical Architecture

### Data Modeling Philosophy

**Approach:** Kimball-style dimensional modeling (star schema)

**Rationale:**
- **Simplicity:** Easy to understand for business users
- **Performance:** Optimized for analytical queries (fewer joins)
- **Flexibility:** Easy to add new facts and dimensions
- **Incrementality:** Support for slowly changing dimensions
- **BI Tool Compatibility:** Standard pattern for reporting tools

### Core Dimensional Model Components

#### Fact Tables (Grain Definitions)

1. **fact_order_items** (Primary Fact Table)
   - **Grain:** One row per order line item
   - **Foreign Keys:** order_id, customer_key, product_key, seller_key, order_date_key, delivery_date_key
   - **Measures:** price, freight_value, quantity (always 1 in this dataset)
   - **Row Count:** ~112k

2. **fact_orders** (Order-level Aggregations)
   - **Grain:** One row per order
   - **Foreign Keys:** order_id, customer_key, order_date_key, delivery_date_key, geography_key
   - **Measures:** total_amount, total_items, total_freight, delivery_days, days_to_ship
   - **Row Count:** ~99k

3. **fact_payments**
   - **Grain:** One row per payment transaction
   - **Foreign Keys:** order_id, payment_date_key
   - **Measures:** payment_value, payment_installments
   - **Dimensions:** payment_type (degenerate dimension)
   - **Row Count:** ~103k

4. **fact_reviews**
   - **Grain:** One row per customer review
   - **Foreign Keys:** order_id, review_date_key
   - **Measures:** review_score, comment_length
   - **Dimensions:** has_comment (flag)
   - **Row Count:** ~99k

5. **fact_order_status_events** (Optional - Advanced)
   - **Grain:** One row per order status change event
   - **Foreign Keys:** order_id, event_date_key
   - **Measures:** hours_in_status
   - **Dimensions:** status_from, status_to
   - **Purpose:** Analyze order lifecycle and bottlenecks

#### Dimension Tables (Attributes)

1. **dim_customer** (SCD Type 2)
   - **Surrogate Key:** customer_key (auto-increment)
   - **Natural Key:** customer_id
   - **Attributes:**
     - customer_city, customer_state
     - customer_zip_code_prefix
     - first_order_date, last_order_date, total_orders, total_spent
     - customer_segment (derived: new, regular, VIP)
   - **SCD Fields:** effective_from, effective_to, is_current
   - **Row Count:** ~99k

2. **dim_product** (SCD Type 2)
   - **Surrogate Key:** product_key
   - **Natural Key:** product_id
   - **Attributes:**
     - product_category_name (English translation)
     - product_name_length, product_description_length, product_photos_qty
     - product_weight_g, product_length_cm, product_height_cm, product_width_cm
     - product_volume_cm3 (calculated)
     - first_sale_date, last_sale_date, total_sales
   - **SCD Fields:** effective_from, effective_to, is_current
   - **Row Count:** ~33k

3. **dim_seller** (SCD Type 2)
   - **Surrogate Key:** seller_key
   - **Natural Key:** seller_id
   - **Attributes:**
     - seller_city, seller_state, seller_zip_code_prefix
     - seller_tenure_days
     - total_revenue, total_orders, avg_review_score
     - seller_tier (derived: bronze, silver, gold, platinum)
   - **SCD Fields:** effective_from, effective_to, is_current
   - **Row Count:** ~3k

4. **dim_date** (Type 1)
   - **Primary Key:** date_key (YYYYMMDD integer)
   - **Attributes:**
     - full_date, year, quarter, month, month_name, week, day_of_week, day_name
     - is_weekend, is_holiday (Brazilian holidays)
     - fiscal_year, fiscal_quarter (if different from calendar)
     - relative_period_flags (is_current_month, is_last_30_days, etc.)
   - **Row Count:** ~1,500 (2016-2020 coverage)
   - **Generation:** Pre-populated calendar table

5. **dim_geography** (Type 1)
   - **Primary Key:** geography_key
   - **Natural Key:** zip_code_prefix
   - **Attributes:**
     - city, state, state_abbr
     - lat, lng (from geolocation dataset)
     - region (Norte, Nordeste, Centro-Oeste, Sudeste, Sul)
     - is_metropolitan, population_tier (if available)
   - **Row Count:** ~1000 unique zip prefixes

6. **dim_category** (Type 1)
   - **Primary Key:** category_key
   - **Natural Key:** category_name_english
   - **Attributes:**
     - category_name_portuguese
     - category_group (derived: Electronics, Fashion, Home, etc.)
     - category_tier (based on sales volume)
   - **Row Count:** 71

### Degenerate Dimensions

Attributes stored directly in fact tables (no separate dimension table):
- `payment_type` (credit_card, boleto, voucher, debit_card)
- `order_status` (delivered, shipped, canceled, etc.)
- `shipping_limit_date`

### Outrigger Dimensions (Snowflake Pattern - Optional)

For normalized geography:
```
dim_geography → dim_city → dim_state → dim_region
```

**Recommendation:** Start with star schema (denormalized), add snowflaking only if needed for specific use cases.

---

## Physical Architecture

### Database Schema Design

**Schema Structure:**
```
olist_dw/
├── raw/              # Staging layer (exact CSV copy)
│   ├── stg_orders
│   ├── stg_customers
│   ├── stg_products
│   ├── stg_sellers
│   └── ...
├── core/             # Integration layer (dimensional model)
│   ├── dim_customer
│   ├── dim_product
│   ├── dim_seller
│   ├── dim_date
│   ├── dim_geography
│   ├── dim_category
│   ├── fact_order_items
│   ├── fact_orders
│   ├── fact_payments
│   └── fact_reviews
└── mart/             # Presentation layer (business-specific)
    ├── mart_executive_dashboard
    ├── mart_customer_analytics
    ├── mart_product_performance
    ├── mart_seller_scorecard
    ├── mart_delivery_metrics
    ├── mart_geographic_analysis
    └── mart_financial_metrics
```

### Naming Conventions

**Tables:**
- Staging: `stg_<source_table_name>`
- Dimensions: `dim_<entity>`
- Facts: `fact_<business_process>`
- Marts: `mart_<business_domain>`

**Columns:**
- Surrogate keys: `<table>_key` (e.g., `customer_key`)
- Natural keys: `<entity>_id` (e.g., `customer_id`)
- Foreign keys: Match dimension naming (e.g., `product_key`)
- Dates: `<event>_date` (e.g., `order_date`)
- Timestamps: `<event>_timestamp`
- Flags: `is_<condition>` or `has_<attribute>`
- Counts: `num_<items>` or `<item>_count`
- Amounts: `<type>_amount` or `<type>_value`

### Storage Strategy

**DuckDB Implementation:**
```python
# Persistent file-based database
db = duckdb.connect('olist_dw.duckdb')

# Or partitioned by schema
db_raw = duckdb.connect('raw.duckdb')
db_core = duckdb.connect('core.duckdb')
db_mart = duckdb.connect('mart.duckdb')
```

**PostgreSQL Implementation:**
```sql
-- Separate schemas in single database
CREATE SCHEMA raw;
CREATE SCHEMA core;
CREATE SCHEMA mart;

-- Or separate databases
CREATE DATABASE olist_dw_raw;
CREATE DATABASE olist_dw_core;
CREATE DATABASE olist_dw_mart;
```

### Partitioning Strategy

**Time-based Partitioning (for future scalability):**

```sql
-- Partition fact_order_items by month
CREATE TABLE core.fact_order_items (
    order_item_id BIGINT,
    order_date DATE,
    -- other columns
) PARTITION BY RANGE (order_date);

-- Create monthly partitions
CREATE TABLE fact_order_items_2016_01 PARTITION OF fact_order_items
    FOR VALUES FROM ('2016-01-01') TO ('2016-02-01');
-- ... repeat for each month
```

**Recommendation for Current Dataset:**
- **Don't partition yet** - 100k rows per table don't require it
- **Add partitioning when:** Tables exceed 10M rows or queries become slow
- **Partition key:** order_date (most common filter)

---

## Data Flow

### ELT Pipeline Architecture

**Extract → Load → Transform (ELT) Approach**

```
┌──────────────┐
│ CSV Files    │
│ (Source)     │
└──────┬───────┘
       │
       │ 1. EXTRACT & LOAD (Python script)
       │    - Read CSV files
       │    - Basic type casting
       │    - Load to staging tables
       ▼
┌──────────────┐
│ Staging      │
│ (raw schema) │
└──────┬───────┘
       │
       │ 2. TRANSFORM (dbt models)
       │    - Data quality checks
       │    - Business logic
       │    - Dimension building (SCD)
       │    - Fact table population
       ▼
┌──────────────┐
│ Core         │
│ (core schema)│
└──────┬───────┘
       │
       │ 3. AGGREGATE (dbt models)
       │    - Pre-aggregate metrics
       │    - Denormalize for performance
       │    - Build mart tables
       ▼
┌──────────────┐
│ Marts        │
│ (mart schema)│
└──────┬───────┘
       │
       │ 4. CONSUME
       ▼
┌──────────────┐
│ Dashboards   │
│ Notebooks    │
└──────────────┘
```

### Data Refresh Patterns

**For Historical Dataset (2016-2018):**

1. **Initial Load (Full Refresh):**
   ```
   - Load all CSVs to staging (one-time)
   - Build all dimensions (full refresh)
   - Build all facts (full refresh)
   - Build all marts (full refresh)
   ```

2. **Incremental Updates (if new data arrives):**
   ```
   - Load new CSV data to staging (append)
   - Update dimensions with SCD logic (merge)
   - Append new facts (incremental insert)
   - Refresh affected marts (incremental or full)
   ```

3. **Refresh Schedule (for production):**
   - **Staging layer:** Daily at 1:00 AM
   - **Core layer:** Daily at 2:00 AM (after staging completes)
   - **Mart layer:** Daily at 3:00 AM (after core completes)
   - **On-demand:** Triggered by data quality alerts

### Data Quality Framework

**Validation Stages:**

1. **Source Validation (Pre-load):**
   - File existence check
   - Column count and names
   - Row count reasonableness
   - Encoding and delimiter validation

2. **Staging Validation (Post-load):**
   - Row count reconciliation
   - Null checks on critical fields
   - Data type conformity
   - Duplicate detection

3. **Core Validation (Post-transform):**
   - Referential integrity (FK constraints)
   - Uniqueness constraints (PK)
   - Business rule validation
   - Orphan record detection
   - SCD logic correctness

4. **Mart Validation (Post-aggregate):**
   - Metric reconciliation with source
   - Logical consistency checks
   - Trend anomaly detection

**dbt Tests Implementation:**
```yaml
# Example dbt schema.yml
version: 2

models:
  - name: fact_order_items
    columns:
      - name: order_item_id
        tests:
          - unique
          - not_null
      - name: product_key
        tests:
          - relationships:
              to: ref('dim_product')
              field: product_key
      - name: price
        tests:
          - not_null
          - positive_values  # custom test
```

---

## Performance Optimization

### Indexing Strategy

**For PostgreSQL:**

```sql
-- Dimension tables: Index natural keys and common filters
CREATE INDEX idx_dim_customer_natural_key ON dim_customer(customer_id);
CREATE INDEX idx_dim_customer_state ON dim_customer(customer_state);
CREATE INDEX idx_dim_customer_current ON dim_customer(is_current) WHERE is_current = true;

-- Fact tables: Index foreign keys and date columns
CREATE INDEX idx_fact_items_order ON fact_order_items(order_id);
CREATE INDEX idx_fact_items_customer ON fact_order_items(customer_key);
CREATE INDEX idx_fact_items_product ON fact_order_items(product_key);
CREATE INDEX idx_fact_items_date ON fact_order_items(order_date_key);

-- Composite indexes for common query patterns
CREATE INDEX idx_fact_items_date_category ON fact_order_items(order_date_key, category_key);
```

**For DuckDB:**
- DuckDB auto-indexes many operations
- Explicit indexes less critical due to columnar storage
- Focus on data layout and filtering

### Materialized Views

**Pre-aggregated Metrics:**

```sql
-- Daily sales by category
CREATE MATERIALIZED VIEW mv_daily_category_sales AS
SELECT
    d.full_date,
    c.category_name_english,
    COUNT(DISTINCT f.order_id) as order_count,
    SUM(f.price) as revenue,
    AVG(f.price) as avg_item_price
FROM fact_order_items f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_category c ON f.category_key = c.category_key
GROUP BY d.full_date, c.category_name_english;

-- Refresh schedule
REFRESH MATERIALIZED VIEW mv_daily_category_sales;
```

### Query Optimization Techniques

1. **Predicate Pushdown:** Filter early in query execution
2. **Column Pruning:** Select only needed columns
3. **Join Order:** Join smallest tables first
4. **Covering Indexes:** Include all query columns in index
5. **Parallel Query Execution:** Leverage DuckDB's parallelism

**Example Optimized Query:**
```sql
-- SLOW: Full table scan with late filtering
SELECT customer_state, SUM(revenue)
FROM fact_orders f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE order_date >= '2018-01-01'
GROUP BY customer_state;

-- FAST: Early filtering on indexed date column
SELECT customer_state, SUM(revenue)
FROM fact_orders f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.order_date_key >= 20180101  -- Integer comparison faster
GROUP BY customer_state;
```

### Caching Strategy

**Query Result Caching:**
- Use DuckDB's built-in query cache
- Implement application-layer caching (Redis) for API responses
- Cache mart table results in memory for dashboards

**Data Caching:**
- Hot data (last 30 days) in separate partition/table
- Cold data archived or compressed

---

## Scalability Strategy

### Vertical Scaling

**Current State (MVP):**
- Local machine with 8-16GB RAM
- DuckDB in-memory or file-based

**Scaling Up (Phase 2):**
- Cloud VM: 32-64GB RAM, 8-16 vCPUs
- PostgreSQL with tuned configuration
- SSD storage for faster I/O

**Limits:**
- Single machine scales to ~100M rows efficiently
- Beyond that, consider horizontal scaling

### Horizontal Scaling

**Read Replicas (PostgreSQL):**
```
Primary (Write) → Replica 1 (Read) → BI Tools
               → Replica 2 (Read) → Dashboards
               → Replica 3 (Read) → ML Workloads
```

**Sharding (Future):**
- Shard by geography (state-level)
- Shard by time period (year-level)
- Use federation layer (Presto, Trino) to query across shards

**ClickHouse Distributed Tables:**
```sql
-- Distributed table across 3 nodes
CREATE TABLE fact_orders_distributed AS fact_orders
ENGINE = Distributed(cluster, core, fact_orders, rand());
```

### Data Archival Strategy

**Hot-Warm-Cold Architecture:**

1. **Hot Data (0-6 months):**
   - Full detail in operational tables
   - Fast SSD storage
   - Indexed and optimized
   - Real-time queries

2. **Warm Data (6-24 months):**
   - Summarized or downsampled
   - Standard storage
   - Fewer indexes
   - Batch queries

3. **Cold Data (24+ months):**
   - Archived to object storage (S3/Parquet)
   - Accessible via external tables
   - Rarely queried
   - Compliance retention

**Implementation:**
```sql
-- Move old data to archive table
INSERT INTO fact_orders_archive
SELECT * FROM fact_orders WHERE order_date < '2020-01-01';

DELETE FROM fact_orders WHERE order_date < '2020-01-01';

-- Query both if needed
CREATE VIEW fact_orders_all AS
SELECT * FROM fact_orders
UNION ALL
SELECT * FROM fact_orders_archive;
```

### Future Architecture (Real-Time)

**For Streaming Analytics:**

```
Live Data → Kafka → Stream Processing (Flink/Spark) → ClickHouse → Real-time Dashboards
                                                     ↓
                                                  DuckDB/PostgreSQL (Batch)
```

**Lambda Architecture:**
- **Speed Layer:** Streaming pipeline for last 24-48 hours
- **Batch Layer:** Historical data warehouse (current design)
- **Serving Layer:** Merge results from both layers

---

## Cost Analysis

### Option 1: DuckDB (Local Development)

**Infrastructure Costs:**
- Compute: $0 (local machine)
- Storage: $0 (local disk)
- Networking: $0
- **Total: $0/month**

**Development Costs:**
- Setup: 1 week (1 FTE)
- Development: 3-4 weeks (1 FTE)
- **Total: ~$10,000-12,000 one-time**

**Ongoing Costs:**
- Maintenance: 2-4 hours/month
- **Total: ~$500-1,000/month**

**Total First Year: ~$16,000-24,000**

---

### Option 2: PostgreSQL (Self-Hosted)

**Infrastructure Costs (Cloud VM):**
- Compute: EC2 t3.xlarge (4 vCPU, 16GB) = $120/month
- Storage: 500GB SSD = $50/month
- Backups: 1TB snapshots = $20/month
- Networking: ~$10/month
- **Total: ~$200/month = $2,400/year**

**Development Costs:**
- Setup: 1-2 weeks (1 FTE)
- Development: 4-6 weeks (1 FTE)
- **Total: ~$12,000-16,000 one-time**

**Ongoing Costs:**
- Maintenance: 8-10 hours/month
- Monitoring tools: $50/month
- **Total: ~$2,000-2,500/month**

**Total First Year: ~$40,000-50,000**

---

### Option 3: PostgreSQL (Managed RDS)

**Infrastructure Costs:**
- RDS db.m5.xlarge (4 vCPU, 16GB): $280/month
- Storage: 500GB SSD: $115/month
- Backups: Automated (included)
- **Total: ~$400/month = $4,800/year**

**Development Costs:**
- Setup: 3-5 days (1 FTE)
- Development: 4-6 weeks (1 FTE)
- **Total: ~$10,000-14,000 one-time**

**Ongoing Costs:**
- Maintenance: 4-6 hours/month (less than self-hosted)
- **Total: ~$1,200-1,500/month**

**Total First Year: ~$28,000-36,000**

---

### Option 4: ClickHouse (Self-Hosted)

**Infrastructure Costs (Cloud VM):**
- Compute: 8 vCPU, 32GB RAM = $250/month
- Storage: 1TB SSD = $100/month
- Backups: $30/month
- **Total: ~$380/month = $4,560/year**

**Development Costs:**
- Setup: 2-3 weeks (1 FTE)
- Development: 6-8 weeks (1 FTE)
- **Total: ~$16,000-22,000 one-time**

**Ongoing Costs:**
- Maintenance: 10-15 hours/month
- **Total: ~$2,500-3,500/month**

**Total First Year: ~$52,000-64,000**

---

### Cost Comparison Summary

| Option | Year 1 Total | Year 2+ Annual | Best For |
|--------|--------------|----------------|----------|
| DuckDB (Local) | $16k-24k | $6k-12k | MVP, POC, Single User |
| PostgreSQL (Self-Hosted) | $40k-50k | $30k-35k | Small Team, Cost-Conscious |
| PostgreSQL (RDS) | $28k-36k | $20k-25k | Production, Managed |
| ClickHouse | $52k-64k | $40k-50k | Large Scale, High Performance |

**Recommendation:** Start with DuckDB ($0 infrastructure), validate with stakeholders, then migrate to PostgreSQL RDS when multi-user access or higher availability is needed.

---

## Conclusion

This architecture provides a robust foundation for analytics on the Olist e-commerce dataset, with clear migration paths as requirements evolve. The dimensional model supports all 100 business questions identified, and the technology stack recommendations balance cost, performance, and simplicity.

**Next Steps:**
1. Review dimensional model with stakeholders
2. Choose technology stack based on budget and timeline
3. Proceed to implementation planning
4. Set up development environment
5. Begin Phase 1 ETL development

**Related Documents:**
- `dimensional_model.md` - Detailed table schemas and relationships
- `etl_pipeline.md` - ETL process specifications
- `implementation_plan.md` - Phased rollout timeline
