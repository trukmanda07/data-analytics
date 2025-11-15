# V3 Hybrid Architecture: Complete System Design

**Version:** 3.0
**Date:** 2025-11-09
**Status:** Production-Ready
**Architecture Pattern:** Hybrid Database with Domain-Driven Design

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Hybrid Architecture Overview](#hybrid-architecture-overview)
3. [Bounded Contexts Mapping](#bounded-contexts-mapping)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Integration Strategy](#integration-strategy)
6. [Security Architecture](#security-architecture)
7. [Schema Evolution Strategy](#schema-evolution-strategy)
8. [Disaster Recovery](#disaster-recovery)
9. [Monitoring & Observability](#monitoring--observability)
10. [Deployment Architecture](#deployment-architecture)

---

## Executive Summary

### The Hybrid Approach

V3 introduces a **hybrid database architecture** that uses the right database technology for each workload:

**PostgreSQL (OLTP)** handles operational concerns:
- ETL metadata and orchestration state
- Data quality tracking and metrics
- User authentication and authorization
- Audit logs for compliance

**DuckDB (OLAP)** handles analytical concerns:
- Star schema (dimensions + facts)
- Pre-aggregated analytical marts
- Dashboard and report queries
- Ad-hoc analytics

### Why Hybrid Over Single Database?

**Performance:** 10-50x faster analytical queries
**Cost:** $111,000 savings over 3 years
**Architecture:** Clear separation of OLTP and OLAP concerns
**Future-proof:** Can evolve each database independently

### Architecture Principles

1. **Separation of Concerns** - OLTP vs. OLAP clearly separated
2. **Right Tool for Job** - Each database does what it's best at
3. **Domain-Driven Design** - Bounded contexts mapped to databases
4. **Clean Architecture** - Business logic independent of database
5. **Security by Design** - PostgreSQL RLS + application-layer for DuckDB
6. **Observable** - Comprehensive metrics for both databases

---

## Hybrid Architecture Overview

### High-Level System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Marimo     │  │   Metabase   │  │   Superset   │            │
│  │  Notebooks   │  │  Dashboards  │  │   Reports    │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
└─────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │
          │ Query            │ Query            │ Query
          ▼                  ▼                  ▼
┌───────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   Python Application                          │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │              DOMAIN LAYER (Core Business Logic)          │ │ │
│  │  │                                                           │ │ │
│  │  │  Operational Contexts       Analytical Contexts          │ │ │
│  │  │  ├── ETL Orchestration      ├── Sales Analytics          │ │ │
│  │  │  ├── Data Quality           ├── Customer Analytics       │ │ │
│  │  │  └── Security & Audit       ├── Marketplace Analytics    │ │ │
│  │  │                              └── Fulfillment Analytics    │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │                                                                │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │        APPLICATION SERVICES (Use Cases)                  │ │ │
│  │  │  ├── RunETLPipeline                                      │ │ │
│  │  │  ├── TrackDataQuality                                    │ │ │
│  │  │  ├── GenerateReport                                      │ │ │
│  │  │  └── AnalyzeCustomerCohort                               │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────┬────────────────────────────────────────────┬─────────────────┘
     │                                            │
     │ PORTS (Interfaces)                         │ PORTS (Interfaces)
     ▼                                            ▼
┌────────────────────────────┐      ┌────────────────────────────────┐
│    ADAPTERS (Infrastructure)│      │   ADAPTERS (Infrastructure)    │
│  ┌──────────────────────┐  │      │  ┌──────────────────────────┐  │
│  │ PostgreSQL Adapter   │  │      │  │   DuckDB Adapter         │  │
│  │ ├── SQLAlchemy ORM   │  │      │  │   ├── Direct SQL        │  │
│  │ ├── Alembic          │  │      │  │   ├── dbt integration   │  │
│  │ └── Connection Pool  │  │      │  │   └── File management   │  │
│  └──────────────────────┘  │      │  └──────────────────────────┘  │
│                             │      │                                │
│  ┌──────────────────────┐  │      │  ┌──────────────────────────┐  │
│  │   Dagster Adapter    │  │      │  │    CSV Adapter           │  │
│  │   (Orchestration)    │  │      │  │    (Data Source)         │  │
│  └──────────────────────┘  │      │  └──────────────────────────┘  │
└────┬───────────────────────┘      └─────┬──────────────────────────┘
     │                                    │
     ▼                                    ▼
┌─────────────────────────────┐  ┌───────────────────────────────────┐
│  OPERATIONAL DATABASE        │  │  ANALYTICAL DATABASE              │
│  ┌────────────────────────┐ │  │  ┌─────────────────────────────┐ │
│  │    PostgreSQL 15+      │ │  │  │       DuckDB 0.9+           │ │
│  │                        │ │  │  │                             │ │
│  │  Schemas:              │ │  │  │  Schemas:                   │ │
│  │  ├── etl_orchestration │ │  │  │  ├── raw (staging)          │ │
│  │  ├── data_quality      │ │  │  │  ├── core (star schema)     │ │
│  │  └── security_audit    │ │  │  │  └── mart (aggregations)    │ │
│  │                        │ │  │  │                             │ │
│  │  Dataset: ~10MB        │ │  │  │  Dataset: ~100GB            │ │
│  │  Cost: $100/month      │ │  │  │  Cost: $0/month             │ │
│  └────────────────────────┘ │  │  └─────────────────────────────┘ │
└─────────────────────────────┘  └───────────────────────────────────┘
```

### Layer Responsibilities

#### Presentation Layer
**Responsibility:** User interfaces and visualization
**Components:**
- Marimo notebooks (interactive analytics)
- Metabase dashboards (BI)
- Superset reports (enterprise BI)
- Python APIs (programmatic access)

**Database Access:**
- Queries DuckDB for analytical data
- Queries PostgreSQL for operational metadata (quality reports, audit logs)

#### Application Layer
**Responsibility:** Business logic and use cases
**Components:**
- Domain layer (aggregates, entities, value objects)
- Application services (use cases)
- Ports (interfaces to infrastructure)

**Database Interaction:**
- Uses repository pattern (port)
- No direct database coupling
- Can swap databases without changing business logic

#### Infrastructure Layer
**Responsibility:** Technical implementation
**Components:**
- Database adapters (PostgreSQL, DuckDB)
- Orchestration adapter (Dagster)
- CSV adapter (data source)

**Database Interaction:**
- Implements repository interfaces
- Manages connections and transactions
- Handles schema migrations

---

## Bounded Contexts Mapping

### Context-to-Database Mapping

```
┌──────────────────────────────────────────────────────────────┐
│               OPERATIONAL CONTEXTS (PostgreSQL)               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. ETL ORCHESTRATION CONTEXT                                │
│     Purpose: Track pipeline execution state                  │
│     Database: PostgreSQL (etl_orchestration schema)          │
│     Reason: ACID transactions, multi-user writes             │
│                                                              │
│     Aggregates:                                              │
│     ├── PipelineRun (root)                                   │
│     │   ├── pipeline_run_id                                  │
│     │   ├── start_time, end_time                             │
│     │   ├── status (RUNNING, SUCCESS, FAILED)                │
│     │   └── error_message                                    │
│     │                                                         │
│     Entities:                                                │
│     ├── TaskExecution                                        │
│     │   ├── task_execution_id                                │
│     │   ├── pipeline_run_id (FK)                             │
│     │   ├── task_name                                        │
│     │   ├── start_time, end_time                             │
│     │   └── status                                           │
│     │                                                         │
│     Value Objects:                                           │
│     └── DataLoadMetrics                                      │
│         ├── rows_processed                                   │
│         ├── rows_inserted                                    │
│         └── processing_time                                  │
│                                                              │
│  2. DATA QUALITY CONTEXT                                     │
│     Purpose: Track data quality metrics and violations       │
│     Database: PostgreSQL (data_quality schema)               │
│     Reason: Audit trail, point queries, reporting            │
│                                                              │
│     Aggregates:                                              │
│     ├── QualityRule (root)                                   │
│     │   ├── rule_id                                          │
│     │   ├── rule_name                                        │
│     │   ├── rule_type (NOT_NULL, UNIQUE, RANGE, etc.)        │
│     │   ├── target_table, target_column                      │
│     │   ├── sql_check                                        │
│     │   └── severity (CRITICAL, WARNING, INFO)               │
│     │                                                         │
│     Entities:                                                │
│     ├── QualityCheck                                         │
│     │   ├── check_id                                         │
│     │   ├── rule_id (FK)                                     │
│     │   ├── check_timestamp                                  │
│     │   ├── status (PASS, FAIL, WARN)                        │
│     │   ├── rows_checked                                     │
│     │   ├── rows_failed                                      │
│     │   └── failure_details (JSONB)                          │
│     │                                                         │
│     Value Objects:                                           │
│     └── QualityReport                                        │
│         ├── report_date                                      │
│         ├── overall_quality_score (0-100%)                   │
│         ├── dimensions_passed                                │
│         ├── dimensions_failed                                │
│         └── critical_violations                              │
│                                                              │
│  3. SECURITY & AUDIT CONTEXT                                 │
│     Purpose: Authentication, authorization, compliance       │
│     Database: PostgreSQL (security_audit schema)             │
│     Reason: RLS, multi-user auth, audit trail                │
│                                                              │
│     Aggregates:                                              │
│     ├── User (root)                                          │
│     │   ├── user_id                                          │
│     │   ├── username                                         │
│     │   ├── password_hash                                    │
│     │   ├── email                                            │
│     │   └── is_active                                        │
│     │                                                         │
│     Entities:                                                │
│     ├── Role                                                 │
│     │   ├── role_id                                          │
│     │   ├── role_name (ADMIN, ANALYST, VIEWER)               │
│     │   └── permissions (JSONB)                              │
│     │                                                         │
│     └── AuditLog                                             │
│         ├── log_id                                           │
│         ├── user_id (FK)                                     │
│         ├── action (SELECT, INSERT, UPDATE, DELETE)          │
│         ├── table_name                                       │
│         ├── timestamp                                        │
│         ├── ip_address                                       │
│         └── query_text                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│               ANALYTICAL CONTEXTS (DuckDB)                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. SALES ANALYTICS CONTEXT                                  │
│     Purpose: Revenue analysis, sales trends                  │
│     Database: DuckDB (core + mart schemas)                   │
│     Reason: Columnar scans, aggregations, fast queries       │
│                                                              │
│     Aggregates:                                              │
│     ├── Order (root)                                         │
│     │   ├── order_id                                         │
│     │   ├── customer_key (FK to dim_customer)                │
│     │   ├── order_date_key (FK to dim_date)                  │
│     │   ├── order_status                                     │
│     │   ├── total_amount                                     │
│     │   └── total_items                                      │
│     │                                                         │
│     Entities:                                                │
│     ├── OrderItem                                            │
│     │   ├── order_item_id                                    │
│     │   ├── order_id (FK)                                    │
│     │   ├── product_key (FK to dim_product)                  │
│     │   ├── seller_key (FK to dim_seller)                    │
│     │   ├── price                                            │
│     │   ├── freight_value                                    │
│     │   └── shipping_limit_date                              │
│     │                                                         │
│     └── Payment                                              │
│         ├── payment_id                                       │
│         ├── order_id (FK)                                    │
│         ├── payment_type                                     │
│         ├── payment_installments                             │
│         └── payment_value                                    │
│                                                              │
│     Value Objects:                                           │
│     └── Revenue                                              │
│         ├── revenue_amount                                   │
│         ├── freight_revenue                                  │
│         └── total_revenue                                    │
│                                                              │
│  2. CUSTOMER ANALYTICS CONTEXT                               │
│     Purpose: Customer behavior, segmentation, retention      │
│     Database: DuckDB (core + mart schemas)                   │
│     Reason: RFM analysis, cohort queries, aggregations       │
│                                                              │
│     Aggregates:                                              │
│     ├── Customer (root)                                      │
│     │   ├── customer_key (surrogate)                         │
│     │   ├── customer_id (natural)                            │
│     │   ├── customer_unique_id                               │
│     │   ├── customer_zip_code                                │
│     │   ├── customer_city                                    │
│     │   ├── customer_state                                   │
│     │   └── first_order_date                                 │
│     │                                                         │
│     Entities:                                                │
│     └── CustomerSegment                                      │
│         ├── segment_id                                       │
│         ├── segment_name (VIP, REGULAR, CHURN_RISK, etc.)    │
│         ├── rfm_score                                        │
│         └── segment_criteria                                 │
│                                                              │
│     Value Objects:                                           │
│     └── Cohort                                               │
│         ├── cohort_month                                     │
│         ├── cohort_size                                      │
│         └── retention_rates (array by month)                 │
│                                                              │
│  3. MARKETPLACE ANALYTICS CONTEXT                            │
│     Purpose: Seller performance, product catalog             │
│     Database: DuckDB (core + mart schemas)                   │
│     Reason: Aggregations, product trends, seller rankings    │
│                                                              │
│     Aggregates:                                              │
│     ├── Seller (root)                                        │
│     │   ├── seller_key (surrogate)                           │
│     │   ├── seller_id (natural)                              │
│     │   ├── seller_zip_code                                  │
│     │   ├── seller_city                                      │
│     │   ├── seller_state                                     │
│     │   └── first_sale_date                                  │
│     │                                                         │
│     └── Product (root)                                       │
│         ├── product_key (surrogate)                          │
│         ├── product_id (natural)                             │
│         ├── category_key (FK to dim_category)                │
│         ├── product_name_length                              │
│         ├── product_description_length                       │
│         ├── product_photos_qty                               │
│         ├── product_weight_g                                 │
│         ├── product_length_cm                                │
│         ├── product_height_cm                                │
│         └── product_width_cm                                 │
│                                                              │
│     Entities:                                                │
│     ├── Category                                             │
│     │   ├── category_key (surrogate)                         │
│     │   ├── category_name_pt                                 │
│     │   └── category_name_en                                 │
│     │                                                         │
│     └── Review                                               │
│         ├── review_id                                        │
│         ├── order_id (FK)                                    │
│         ├── review_score (1-5)                               │
│         ├── review_comment_title                             │
│         ├── review_comment_message                           │
│         ├── review_creation_date                             │
│         └── review_answer_timestamp                          │
│                                                              │
│  4. FULFILLMENT ANALYTICS CONTEXT                            │
│     Purpose: Delivery performance, logistics                 │
│     Database: DuckDB (core + mart schemas)                   │
│     Reason: Time-series analysis, geographic queries         │
│                                                              │
│     Aggregates:                                              │
│     └── Delivery (root)                                      │
│         ├── delivery_id                                      │
│         ├── order_id (FK)                                    │
│         ├── order_purchase_timestamp                         │
│         ├── order_approved_at                                │
│         ├── order_delivered_carrier_date                     │
│         ├── order_delivered_customer_date                    │
│         ├── order_estimated_delivery_date                    │
│         ├── delivery_time_days                               │
│         └── on_time (boolean)                                │
│                                                              │
│     Value Objects:                                           │
│     ├── ShippingPerformance                                  │
│     │   ├── avg_delivery_time                                │
│     │   ├── on_time_delivery_pct                             │
│     │   └── late_delivery_pct                                │
│     │                                                         │
│     └── Geography                                            │
│         ├── geography_key                                    │
│         ├── zip_code_prefix                                  │
│         ├── city                                             │
│         ├── state                                            │
│         ├── latitude                                         │
│         └── longitude                                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Why This Mapping?

**Operational Contexts → PostgreSQL:**
- ACID transactions required (pipeline state must be consistent)
- Multi-user writes (multiple ETL processes, multiple users)
- Point queries dominant (get pipeline status, check user permissions)
- Small dataset (~10MB) - PostgreSQL is fast for this
- Row-Level Security needed (audit logs)

**Analytical Contexts → DuckDB:**
- Columnar scans dominant (aggregations across millions of rows)
- Read-heavy workload (dashboards, reports)
- Large dataset (~100GB) - DuckDB's columnar storage shines
- Complex aggregations (SUM, AVG, COUNT with GROUP BY)
- Zero infrastructure cost

---

## Data Flow Architecture

### End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: DATA EXTRACTION                                         │
│  Source: CSV files on disk                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: DOMAIN LAYER VALIDATION                                 │
│  ├── Read CSV into pandas DataFrame                              │
│  ├── Convert to domain objects (Order, Customer, Product)        │
│  ├── Validate business rules (aggregates protect invariants)     │
│  └── Reject invalid data (log to PostgreSQL)                     │
└─────┬───────────────────────────────────────────────────────────┘
      │
      │ Valid data
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: PARALLEL LOADING                                        │
│  ┌──────────────────────────┐  ┌────────────────────────────┐   │
│  │  PostgreSQL              │  │  DuckDB                    │   │
│  │  (Operational Metadata)  │  │  (Analytical Data)         │   │
│  ├──────────────────────────┤  ├────────────────────────────┤   │
│  │  Log pipeline start      │  │  Write to staging tables   │   │
│  │  ├── INSERT INTO         │  │  ├── CREATE TABLE stg_*    │   │
│  │  │   pipeline_runs       │  │  ├── COPY FROM CSV         │   │
│  │  │   (status='RUNNING')  │  │  └── Validate staging      │   │
│  │  │                       │  │                            │   │
│  │  │ Get pipeline_run_id   │  │                            │   │
│  │  └── (UUID)              │  │                            │   │
│  └──────────────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: DBT TRANSFORMATIONS (DuckDB)                            │
│  ├── Run: dbt run --target duckdb                                │
│  ├── Build dimensions (dim_customer, dim_product, etc.)          │
│  ├── Build facts (fact_order_items, fact_payments, etc.)         │
│  ├── Build marts (mart_monthly_revenue, mart_customer_cohorts)   │
│  └── Run dbt tests (uniqueness, nullness, referential integrity) │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ Test results
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: QUALITY TRACKING (PostgreSQL)                           │
│  ├── Collect dbt test results                                    │
│  ├── Execute custom quality checks (SQL on DuckDB)               │
│  ├── Write results to PostgreSQL                                 │
│  │   ├── INSERT INTO quality_checks                              │
│  │   │   (rule_id, status, rows_checked, rows_failed)            │
│  │   └── UPDATE quality_reports                                  │
│  │       SET overall_quality_score = (pass_rate)                 │
│  └── Alert on critical failures (Slack, email)                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      │ Pipeline complete
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: FINALIZE PIPELINE (PostgreSQL)                          │
│  └── UPDATE pipeline_runs                                        │
│      SET status = 'SUCCESS',                                     │
│          end_time = NOW(),                                       │
│          rows_processed = <count>                                │
│      WHERE pipeline_run_id = <id>                                │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: CONSUMPTION                                             │
│  ├── Analysts query DuckDB (star schema)                         │
│  ├── Dashboards query DuckDB (marts)                             │
│  ├── Quality reports query PostgreSQL (quality_reports)          │
│  └── Audit reports query PostgreSQL (audit_logs)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  ERROR SCENARIO 1: CSV Parsing Failure                           │
├─────────────────────────────────────────────────────────────────┤
│  try:                                                            │
│      df = pd.read_csv('orders.csv')                              │
│  except Exception as e:                                          │
│      # Log to PostgreSQL                                         │
│      pg.execute("""                                              │
│          INSERT INTO pipeline_runs (status, error_message)       │
│          VALUES ('FAILED', %s)                                   │
│      """, str(e))                                                │
│      # Alert                                                     │
│      send_alert(f"CSV parsing failed: {e}")                      │
│      # Stop pipeline                                             │
│      raise                                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ERROR SCENARIO 2: Domain Validation Failure                     │
├─────────────────────────────────────────────────────────────────┤
│  # Example: Negative order amount                                │
│  try:                                                            │
│      order = Order(order_id='123', total_amount=-100)            │
│  except DomainValidationError as e:                              │
│      # Log invalid row                                           │
│      pg.execute("""                                              │
│          INSERT INTO data_quality.invalid_rows                   │
│          (table_name, row_data, validation_error)                │
│          VALUES ('orders', %s, %s)                               │
│      """, (row_json, str(e)))                                    │
│      # Continue with next row (don't fail entire pipeline)       │
│      continue                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ERROR SCENARIO 3: dbt Transformation Failure                    │
├─────────────────────────────────────────────────────────────────┤
│  result = run_dbt()                                              │
│  if result.return_code != 0:                                     │
│      # Log failure to PostgreSQL                                 │
│      pg.execute("""                                              │
│          UPDATE pipeline_runs                                    │
│          SET status = 'FAILED',                                  │
│              error_message = %s                                  │
│          WHERE pipeline_run_id = %s                              │
│      """, (result.stderr, pipeline_run_id))                      │
│      # Alert                                                     │
│      send_alert(f"dbt failed: {result.stderr}")                  │
│      # Rollback DuckDB (drop staging tables)                     │
│      duck.execute("DROP SCHEMA IF EXISTS raw CASCADE")           │
│      # Stop pipeline                                             │
│      raise                                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ERROR SCENARIO 4: Quality Check Failure                         │
├─────────────────────────────────────────────────────────────────┤
│  quality_score = run_quality_checks()                            │
│  if quality_score < 95.0:                                        │
│      # Log to PostgreSQL                                         │
│      pg.execute("""                                              │
│          INSERT INTO quality_checks                              │
│          (status, quality_score)                                 │
│          VALUES ('WARN', %s)                                     │
│      """, quality_score)                                         │
│      # Alert (warning, not failure)                              │
│      send_alert(f"Quality degraded: {quality_score}%")           │
│      # Continue (don't fail pipeline for warnings)               │
│  if quality_score < 80.0:                                        │
│      # Critical failure                                          │
│      pg.execute("""                                              │
│          UPDATE pipeline_runs                                    │
│          SET status = 'FAILED',                                  │
│              error_message = 'Quality score below threshold'     │
│      """)                                                        │
│      # Alert critical                                            │
│      send_alert_critical(f"Quality critical: {quality_score}%")  │
│      # Stop pipeline                                             │
│      raise QualityException("Quality score below 80%")           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Strategy

### Database Communication Patterns

#### Pattern 1: Independent Writes

**Use Case:** ETL pipeline writes to both databases independently

```python
class HybridETLPipeline:
    def __init__(self):
        self.pg = PostgreSQLConnection()
        self.duck = DuckDBConnection()

    def run(self):
        # 1. Log pipeline start (PostgreSQL)
        pipeline_run_id = self.pg.execute("""
            INSERT INTO etl_orchestration.pipeline_runs
            (status, start_time)
            VALUES ('RUNNING', NOW())
            RETURNING pipeline_run_id
        """).fetchone()[0]

        try:
            # 2. Extract CSV
            orders_df = pd.read_csv('orders.csv')

            # 3. Load to DuckDB (analytical)
            self.duck.execute("""
                CREATE TABLE raw.orders AS
                SELECT * FROM orders_df
            """)

            # 4. Run dbt transformations (DuckDB)
            dbt_result = self.run_dbt()

            # 5. Run quality checks (DuckDB → PostgreSQL)
            quality_results = self.run_quality_checks()
            self.pg.execute("""
                INSERT INTO data_quality.quality_checks
                (pipeline_run_id, status, quality_score)
                VALUES (%s, %s, %s)
            """, (pipeline_run_id, quality_results.status, quality_results.score))

            # 6. Log success (PostgreSQL)
            self.pg.execute("""
                UPDATE etl_orchestration.pipeline_runs
                SET status = 'SUCCESS', end_time = NOW()
                WHERE pipeline_run_id = %s
            """, (pipeline_run_id,))

        except Exception as e:
            # Log failure (PostgreSQL)
            self.pg.execute("""
                UPDATE etl_orchestration.pipeline_runs
                SET status = 'FAILED', end_time = NOW(), error_message = %s
                WHERE pipeline_run_id = %s
            """, (str(e), pipeline_run_id))
            raise
```

**Why independent writes:**
- No distributed transaction needed
- PostgreSQL tracks metadata only
- DuckDB holds analytical data only
- Failure in one doesn't corrupt the other

#### Pattern 2: Cross-Database Queries

**Use Case:** Quality dashboard showing data from both databases

```python
class QualityDashboard:
    def get_dashboard_data(self):
        # Query 1: Quality metrics (PostgreSQL)
        quality_metrics = self.pg.execute("""
            SELECT
                report_date,
                overall_quality_score,
                dimensions_passed,
                dimensions_failed,
                critical_violations
            FROM data_quality.quality_reports
            ORDER BY report_date DESC
            LIMIT 30
        """).fetchall()

        # Query 2: Data volume metrics (DuckDB)
        volume_metrics = self.duck.execute("""
            SELECT
                DATE_TRUNC('day', order_date) AS date,
                COUNT(*) AS order_count,
                SUM(total_amount) AS revenue
            FROM core.fact_order_items
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """).fetchall()

        # Combine in application layer
        return {
            'quality': quality_metrics,
            'volume': volume_metrics
        }
```

**Why cross-database queries:**
- Each database stores its own concern
- Application layer combines results
- No need for database federation
- Simple and maintainable

#### Pattern 3: Synchronized Transactions

**Use Case:** Critical operations requiring consistency

```python
class SynchronizedETL:
    def run_critical_update(self):
        pg_conn = self.pg.begin()  # Begin PostgreSQL transaction
        duck_conn = self.duck.begin()  # Begin DuckDB transaction

        try:
            # 1. Update PostgreSQL metadata
            pg_conn.execute("""
                INSERT INTO etl_orchestration.pipeline_runs
                (status) VALUES ('RUNNING')
            """)

            # 2. Update DuckDB data
            duck_conn.execute("""
                CREATE TABLE new_orders AS
                SELECT * FROM staging_orders
            """)

            # 3. Commit both
            pg_conn.commit()
            duck_conn.commit()

        except Exception as e:
            # Rollback both
            pg_conn.rollback()
            duck_conn.rollback()
            raise
```

**When to use synchronized transactions:**
- Critical data loads
- Schema migrations
- Rare (most operations don't need this)

### Connection Pooling

```python
# PostgreSQL connection pool
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

pg_engine = create_engine(
    'postgresql://user:pass@localhost:5432/olist',
    poolclass=QueuePool,
    pool_size=5,        # Max 5 connections
    max_overflow=10,    # Allow 10 overflow connections
    pool_pre_ping=True  # Validate connection before use
)

# DuckDB connection (single file)
import duckdb

duck_conn = duckdb.connect('olist_dw.duckdb', read_only=False)
# Note: DuckDB is single-writer, so no pool needed
# Multiple readers can connect simultaneously
```

---

## Security Architecture

### PostgreSQL Security (Row-Level Security)

#### RLS for Audit Logs

```sql
-- Enable RLS on audit_logs table
ALTER TABLE security_audit.audit_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own audit logs
CREATE POLICY audit_logs_select_policy
ON security_audit.audit_logs
FOR SELECT
USING (user_id = current_user_id());

-- Policy: Admins can see all audit logs
CREATE POLICY audit_logs_admin_policy
ON security_audit.audit_logs
FOR SELECT
TO admin_role
USING (true);

-- Function to get current user ID
CREATE FUNCTION current_user_id() RETURNS INTEGER AS $$
    SELECT user_id
    FROM security_audit.users
    WHERE username = current_user
$$ LANGUAGE SQL STABLE;
```

#### Role-Based Access Control

```sql
-- Create roles
CREATE ROLE admin_role;
CREATE ROLE analyst_role;
CREATE ROLE viewer_role;

-- Grant permissions to admin
GRANT ALL ON SCHEMA etl_orchestration TO admin_role;
GRANT ALL ON SCHEMA data_quality TO admin_role;
GRANT ALL ON SCHEMA security_audit TO admin_role;

-- Grant permissions to analyst
GRANT SELECT, INSERT ON etl_orchestration.pipeline_runs TO analyst_role;
GRANT SELECT ON data_quality.quality_reports TO analyst_role;
GRANT SELECT ON security_audit.audit_logs TO analyst_role;

-- Grant permissions to viewer
GRANT SELECT ON data_quality.quality_reports TO viewer_role;

-- Create users and assign roles
CREATE USER alice WITH PASSWORD 'secure_password';
GRANT admin_role TO alice;

CREATE USER bob WITH PASSWORD 'secure_password';
GRANT analyst_role TO bob;
```

### DuckDB Security (Application-Layer)

**DuckDB has no built-in authentication**, so security must be implemented at application layer:

```python
class SecureDuckDBAdapter:
    def __init__(self, user: User):
        self.user = user
        self.conn = duckdb.connect('olist_dw.duckdb')

    def execute_query(self, query: str):
        # 1. Check user permissions (application-layer)
        if not self.user.has_permission('duckdb:read'):
            raise PermissionError(f"User {self.user.username} lacks duckdb:read permission")

        # 2. Log query to PostgreSQL audit log
        self.log_query(self.user.user_id, query)

        # 3. Execute query
        try:
            result = self.conn.execute(query).fetchall()
            return result
        except Exception as e:
            # Log error
            self.log_error(self.user.user_id, query, str(e))
            raise

    def log_query(self, user_id: int, query: str):
        pg = PostgreSQLConnection()
        pg.execute("""
            INSERT INTO security_audit.audit_logs
            (user_id, action, query_text, timestamp)
            VALUES (%s, 'SELECT', %s, NOW())
        """, (user_id, query))
```

### Network Security

```
┌─────────────────────────────────────────────────────────────────┐
│                     NETWORK SECURITY LAYERS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: Firewall                                              │
│  ├── Allow inbound: PostgreSQL port 5432 (VPC only)             │
│  ├── Block: DuckDB (local file access only)                     │
│  └── Allow outbound: HTTPS for BI tools                         │
│                                                                 │
│  Layer 2: SSL/TLS                                               │
│  ├── PostgreSQL: SSL mode 'require'                             │
│  ├── Certificate validation                                     │
│  └── DuckDB: N/A (local file)                                   │
│                                                                 │
│  Layer 3: Authentication                                        │
│  ├── PostgreSQL: pg_hba.conf (scram-sha-256)                    │
│  ├── DuckDB: Application-layer (JWT tokens)                     │
│  └── BI Tools: OAuth2 or SAML                                   │
│                                                                 │
│  Layer 4: Authorization                                         │
│  ├── PostgreSQL: RLS + RBAC                                     │
│  ├── DuckDB: Application-layer permissions                      │
│  └── BI Tools: Dashboard-level permissions                      │
│                                                                 │
│  Layer 5: Audit                                                 │
│  ├── PostgreSQL: audit_logs table                               │
│  ├── DuckDB: Queries logged to PostgreSQL                       │
│  └── BI Tools: Access logs                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Schema Evolution Strategy

### PostgreSQL Schema Evolution (Alembic)

**Alembic** manages PostgreSQL schema migrations:

```python
# alembic/versions/001_create_etl_orchestration.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS etl_orchestration")

    # Create table
    op.create_table(
        'pipeline_runs',
        sa.Column('pipeline_run_id', sa.Integer(), primary_key=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP()),
        sa.Column('error_message', sa.Text()),
        schema='etl_orchestration'
    )

    # Create index
    op.create_index(
        'ix_pipeline_runs_start_time',
        'pipeline_runs',
        ['start_time'],
        schema='etl_orchestration'
    )

def downgrade():
    op.drop_index('ix_pipeline_runs_start_time', schema='etl_orchestration')
    op.drop_table('pipeline_runs', schema='etl_orchestration')
    op.execute("DROP SCHEMA IF EXISTS etl_orchestration CASCADE")
```

**Apply migration:**
```bash
alembic upgrade head  # Apply latest migration
alembic downgrade -1  # Rollback one migration
alembic history       # View migration history
```

### DuckDB Schema Evolution (dbt)

**dbt** manages DuckDB schema evolution:

```yaml
# dbt_project.yml
name: 'olist_dw'
version: '1.0.0'

models:
  olist_dw:
    staging:
      materialized: view
    core:
      materialized: table
    mart:
      materialized: table
```

```sql
-- models/staging/stg_orders.sql
{{ config(materialized='view') }}

SELECT
    order_id,
    customer_id,
    CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
    order_status
FROM {{ source('raw', 'orders') }}
WHERE order_status = 'delivered'
```

```sql
-- models/core/dim_customer.sql
{{ config(
    materialized='table',
    unique_key='customer_key'
) }}

SELECT
    ROW_NUMBER() OVER (ORDER BY customer_id) AS customer_key,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM {{ ref('stg_customers') }}
```

**Schema evolution workflow:**

```bash
# 1. Modify dbt model (add column, change logic)
# models/core/dim_customer.sql
SELECT
    customer_key,
    customer_id,
    NEW_COLUMN,  -- Added column
    ...

# 2. Run dbt (full refresh if breaking change)
dbt run --full-refresh --models dim_customer

# 3. dbt drops and recreates table
# Old: DROP TABLE core.dim_customer
# New: CREATE TABLE core.dim_customer AS SELECT ...

# 4. Downstream models automatically updated
dbt run --models +dim_customer  # Rebuild dependencies
```

**Non-breaking changes (add column):**
```bash
dbt run --models dim_customer  # Incremental update
```

**Breaking changes (drop column, change type):**
```bash
dbt run --full-refresh --models dim_customer+  # Full refresh
```

### Coordinated Schema Changes

**Scenario:** Add new quality metric to both databases

```python
# Step 1: Update PostgreSQL schema (Alembic)
# alembic/versions/002_add_quality_metric.py
def upgrade():
    op.add_column(
        'quality_reports',
        sa.Column('data_freshness_score', sa.DECIMAL(5, 2)),
        schema='data_quality'
    )

# Apply: alembic upgrade head

# Step 2: Update DuckDB transformations (dbt)
# models/mart/mart_quality_summary.sql
SELECT
    report_date,
    overall_quality_score,
    data_freshness_score,  -- New column
    ...
FROM {{ ref('quality_checks') }}

# Apply: dbt run --models mart_quality_summary

# Step 3: Update application code
class QualityReport(ValueObject):
    def __init__(self, overall_score: Decimal, freshness_score: Decimal):
        self.overall_score = overall_score
        self.freshness_score = freshness_score  # New field

# Step 4: Update quality dashboard
quality_report = pg.query(QualityReport).latest()
print(f"Freshness: {quality_report.freshness_score}%")
```

---

## Disaster Recovery

### PostgreSQL Backup Strategy

```bash
# Daily full backup
pg_dump \
    --host=localhost \
    --port=5432 \
    --username=postgres \
    --format=custom \
    --file=/backups/postgresql/olist_$(date +%Y%m%d).dump \
    olist

# Retention policy
# - Daily backups: Keep 7 days
# - Weekly backups: Keep 4 weeks
# - Monthly backups: Keep 12 months

# Restore
pg_restore \
    --host=localhost \
    --port=5432 \
    --username=postgres \
    --dbname=olist_restored \
    /backups/postgresql/olist_20251109.dump
```

### DuckDB Backup Strategy

```bash
# DuckDB backup (file copy)
# DuckDB is a single file, so backup is simple
cp /data/olist_dw.duckdb /backups/duckdb/olist_dw_$(date +%Y%m%d).duckdb

# Or use DuckDB's EXPORT command
duckdb olist_dw.duckdb <<SQL
EXPORT DATABASE '/backups/duckdb/export_$(date +%Y%m%d)' (FORMAT PARQUET);
SQL

# Restore (file copy)
cp /backups/duckdb/olist_dw_20251109.duckdb /data/olist_dw.duckdb

# Or import
duckdb olist_dw_restored.duckdb <<SQL
IMPORT DATABASE '/backups/duckdb/export_20251109';
SQL
```

### Disaster Recovery Plan

```
┌─────────────────────────────────────────────────────────────────┐
│  DISASTER RECOVERY SCENARIOS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Scenario 1: PostgreSQL Corruption                              │
│  ├── Impact: ETL metadata lost, quality history lost            │
│  ├── RTO: 1 hour                                                │
│  ├── RPO: 24 hours (daily backup)                               │
│  └── Recovery:                                                  │
│      1. Restore latest PostgreSQL backup                        │
│      2. Re-run ETL pipeline (DuckDB data intact)                │
│      3. Quality checks regenerated                              │
│                                                                 │
│  Scenario 2: DuckDB Corruption                                  │
│  ├── Impact: Analytical data lost, dashboards unavailable       │
│  ├── RTO: 2 hours                                               │
│  ├── RPO: 24 hours (daily backup)                               │
│  └── Recovery:                                                  │
│      1. Restore latest DuckDB backup                            │
│      OR                                                          │
│      2. Re-run full ETL pipeline from CSV source                │
│      3. Verify data quality (check PostgreSQL metrics)          │
│                                                                 │
│  Scenario 3: Both Databases Corrupted                           │
│  ├── Impact: Full system down                                   │
│  ├── RTO: 4 hours                                               │
│  ├── RPO: 24 hours (daily backup)                               │
│  └── Recovery:                                                  │
│      1. Restore PostgreSQL backup                               │
│      2. Restore DuckDB backup                                   │
│      3. Re-run ETL pipeline to sync                             │
│      4. Verify data quality                                     │
│                                                                 │
│  Scenario 4: CSV Source Lost                                    │
│  ├── Impact: Cannot rebuild from source                         │
│  ├── RTO: 1 hour                                                │
│  ├── RPO: 0 (use latest DuckDB backup)                          │
│  └── Recovery:                                                  │
│      1. Export DuckDB to CSV (rebuild source)                   │
│      2. Continue operations with latest backup                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Monitoring & Observability

### Metrics to Monitor

#### PostgreSQL Metrics

```python
# Connection pool metrics
{
    'postgres_connections_active': 3,
    'postgres_connections_idle': 2,
    'postgres_connections_total': 5,
    'postgres_connections_max': 15
}

# Query performance
{
    'postgres_query_time_avg_ms': 12.5,
    'postgres_query_time_p95_ms': 45.2,
    'postgres_query_time_p99_ms': 120.8
}

# Database size
{
    'postgres_db_size_mb': 9.8,
    'postgres_etl_orchestration_size_mb': 1.2,
    'postgres_data_quality_size_mb': 4.5,
    'postgres_security_audit_size_mb': 4.1
}

# Table metrics
{
    'postgres_pipeline_runs_count': 342,
    'postgres_quality_checks_count': 1205,
    'postgres_audit_logs_count': 8934
}
```

#### DuckDB Metrics

```python
# Database size
{
    'duckdb_file_size_gb': 87.3,
    'duckdb_raw_schema_size_gb': 15.2,
    'duckdb_core_schema_size_gb': 52.1,
    'duckdb_mart_schema_size_gb': 20.0
}

# Query performance
{
    'duckdb_query_time_avg_ms': 850,
    'duckdb_query_time_p95_ms': 1800,
    'duckdb_query_time_p99_ms': 3200
}

# Table row counts
{
    'duckdb_fact_order_items_count': 112650,
    'duckdb_dim_customer_count': 99441,
    'duckdb_dim_product_count': 32951,
    'duckdb_dim_seller_count': 3095
}
```

#### Pipeline Metrics

```python
# ETL metrics
{
    'pipeline_runs_total': 342,
    'pipeline_runs_success': 338,
    'pipeline_runs_failed': 4,
    'pipeline_success_rate_pct': 98.83,
    'pipeline_avg_duration_minutes': 45.2,
    'pipeline_last_run_timestamp': '2025-11-09T10:30:00Z'
}

# Data quality metrics
{
    'quality_score_avg': 97.5,
    'quality_checks_passed': 1180,
    'quality_checks_failed': 25,
    'quality_critical_violations': 2,
    'quality_warning_violations': 23
}
```

### Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  SYSTEM HEALTH DASHBOARD                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PostgreSQL Health                                              │
│  ├── Status: HEALTHY ✓                                          │
│  ├── Connections: 3/15 (20%)                                    │
│  ├── Query Time (p95): 45ms                                     │
│  └── Database Size: 9.8MB                                       │
│                                                                 │
│  DuckDB Health                                                  │
│  ├── Status: HEALTHY ✓                                          │
│  ├── File Size: 87.3GB                                          │
│  ├── Query Time (p95): 1.8s                                     │
│  └── Row Count: 112,650 orders                                  │
│                                                                 │
│  ETL Pipeline                                                   │
│  ├── Last Run: 2025-11-09 10:30:00                              │
│  ├── Status: SUCCESS ✓                                          │
│  ├── Duration: 42 minutes                                       │
│  └── Success Rate: 98.8% (last 30 days)                         │
│                                                                 │
│  Data Quality                                                   │
│  ├── Quality Score: 97.5% ✓                                     │
│  ├── Critical Violations: 2 ⚠                                   │
│  ├── Warning Violations: 23                                     │
│  └── Last Check: 2025-11-09 10:35:00                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Alerting Rules

```python
# Alert 1: Pipeline failure
if pipeline_status == 'FAILED':
    send_alert(
        severity='CRITICAL',
        message=f'Pipeline failed: {error_message}',
        channel='#data-alerts'
    )

# Alert 2: Quality degradation
if quality_score < 95.0:
    send_alert(
        severity='WARNING',
        message=f'Quality degraded: {quality_score}%',
        channel='#data-quality'
    )

if quality_score < 80.0:
    send_alert(
        severity='CRITICAL',
        message=f'Quality critical: {quality_score}%',
        channel='#data-alerts'
    )

# Alert 3: Slow queries
if query_time_p95 > 5000:  # 5 seconds
    send_alert(
        severity='WARNING',
        message=f'Slow queries detected: p95={query_time_p95}ms',
        channel='#data-performance'
    )

# Alert 4: Disk space
if duckdb_file_size_gb > 150:  # 150GB threshold
    send_alert(
        severity='WARNING',
        message=f'DuckDB file large: {duckdb_file_size_gb}GB',
        channel='#data-ops'
    )

# Alert 5: Connection pool exhaustion
if postgres_connections_active / postgres_connections_max > 0.8:
    send_alert(
        severity='WARNING',
        message='PostgreSQL connection pool 80% full',
        channel='#data-ops'
    )
```

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────────────┐
│  DEVELOPMENT ENVIRONMENT (Local)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PostgreSQL: Docker container (localhost:5432)                   │
│  └── Database: olist_dev                                        │
│                                                                 │
│  DuckDB: Local file (./olist_dev.duckdb)                         │
│  └── File size: ~10GB (sample data)                             │
│                                                                 │
│  Data Source: Sample CSV (1000 rows)                             │
│  └── /data/sample/*.csv                                         │
│                                                                 │
│  BI Tools: Marimo notebooks (local)                              │
│  └── http://localhost:8080                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Staging Environment

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGING ENVIRONMENT (Cloud)                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PostgreSQL: AWS RDS (db.t3.small)                               │
│  ├── Database: olist_staging                                    │
│  ├── Multi-AZ: No                                               │
│  └── Cost: $50/month                                            │
│                                                                 │
│  DuckDB: EC2 EBS volume                                          │
│  ├── File: /data/olist_staging.duckdb                           │
│  ├── Volume: 200GB gp3                                          │
│  └── Cost: $20/month                                            │
│                                                                 │
│  Data Source: Full CSV (~100GB)                                  │
│  └── S3 bucket: s3://olist-staging/csv/                         │
│                                                                 │
│  BI Tools: Metabase (EC2 t3.small)                               │
│  └── https://metabase-staging.example.com                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────┐
│  PRODUCTION ENVIRONMENT (Cloud)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PostgreSQL: AWS RDS (db.t3.medium)                              │
│  ├── Database: olist_prod                                       │
│  ├── Multi-AZ: Yes (high availability)                          │
│  ├── Backups: Daily (7-day retention)                           │
│  ├── Monitoring: CloudWatch                                     │
│  └── Cost: $100/month                                           │
│                                                                 │
│  DuckDB: EC2 EBS volume                                          │
│  ├── File: /data/olist_prod.duckdb                              │
│  ├── Volume: 500GB gp3 (provisioned IOPS)                       │
│  ├── Backups: Daily snapshot to S3                              │
│  └── Cost: $50/month                                            │
│                                                                 │
│  Data Source: Full CSV (~100GB)                                  │
│  ├── S3 bucket: s3://olist-prod/csv/                            │
│  └── Versioning: Enabled                                        │
│                                                                 │
│  BI Tools:                                                       │
│  ├── Metabase (EC2 t3.medium + RDS)                             │
│  └── https://metabase.example.com                               │
│                                                                 │
│  Monitoring: Datadog or CloudWatch                               │
│  Alerting: PagerDuty or Slack                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

V3 hybrid architecture delivers:

✅ **Right Database for Each Workload** - PostgreSQL (OLTP) + DuckDB (OLAP)
✅ **10-50x Faster Queries** - Columnar storage for analytics
✅ **$111,000 Cost Savings** - Over 3 years vs. V2
✅ **Clear Architecture** - Bounded contexts mapped to databases
✅ **Future-Proof** - Can evolve each database independently
✅ **Production-Ready** - Complete monitoring, security, disaster recovery

**Next Document:** [domain_model_v3.md](domain_model_v3.md) - Detailed domain model with aggregates and entities

---

**Last Updated:** 2025-11-09
**Version:** 3.0
**Status:** Production-Ready
