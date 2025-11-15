# ETL/ELT Pipeline Design

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Related:** data_warehouse_architecture.md, dimensional_model.md

---

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [ELT vs ETL Approach](#elt-vs-etl-approach)
3. [Data Ingestion Layer](#data-ingestion-layer)
4. [Transformation Layer](#transformation-layer)
5. [Data Quality Framework](#data-quality-framework)
6. [Orchestration Strategy](#orchestration-strategy)
7. [Incremental Processing](#incremental-processing)
8. [Error Handling](#error-handling)
9. [Implementation Code](#implementation-code)

---

## Pipeline Overview

### Architecture Pattern: ELT (Extract-Load-Transform)

**Rationale for ELT:**
- Leverage DuckDB's analytical query engine for transformations
- Keep raw data for auditing and reprocessing
- SQL-based transformations are maintainable and testable
- dbt provides excellent transformation framework
- Separate data movement from business logic

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                      STAGE 1: EXTRACT                            │
│  - Read CSV files from source directory                          │
│  - Validate file structure and encoding                          │
│  - Generate extraction metadata                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STAGE 2: LOAD (Raw)                         │
│  - Load CSV data to staging tables (raw schema)                 │
│  - Minimal transformation (type casting only)                    │
│  - Create load audit log                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  STAGE 3: TRANSFORM (dbt)                        │
│                                                                   │
│  Layer 1: Staging Models (stg_*)                                │
│  - Clean data, standardize columns                               │
│  - Basic data quality checks                                     │
│                                                                   │
│  Layer 2: Intermediate Models (int_*)                            │
│  - Join related tables                                           │
│  - Apply business logic                                          │
│  - Calculate derived metrics                                     │
│                                                                   │
│  Layer 3: Core Dimensional Models (dim_*, fact_*)               │
│  - Build dimension tables (SCD Type 2)                           │
│  - Build fact tables with surrogate keys                         │
│  - Enforce referential integrity                                 │
│                                                                   │
│  Layer 4: Mart Models (mart_*)                                  │
│  - Pre-aggregate for dashboards                                  │
│  - Denormalize for performance                                   │
│  - Business-specific views                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STAGE 4: DATA QUALITY CHECKS                   │
│  - Row count reconciliation                                      │
│  - Business rule validation                                      │
│  - Anomaly detection                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   STAGE 5: PUBLISH & CONSUME                     │
│  - Expose marts to BI tools                                      │
│  - Generate data catalog                                         │
│  - Send completion notifications                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Execution Flow

**Daily Full Refresh (Initial Approach):**
```
1. Extract CSV files → 2 minutes
2. Load to staging → 5 minutes
3. Run dbt transformations → 10-15 minutes
4. Data quality tests → 3 minutes
5. Publish results → 1 minute
──────────────────────────────
Total: ~25 minutes
```

**Future Incremental Approach:**
```
1. Detect new/changed files → 1 minute
2. Load delta to staging → 2 minutes
3. Run incremental dbt models → 5 minutes
4. Data quality tests → 2 minutes
5. Publish results → 1 minute
──────────────────────────────
Total: ~11 minutes
```

---

## ELT vs ETL Approach

### Why ELT for This Project?

| Aspect | ETL (Transform before Load) | ELT (Load then Transform) | Chosen |
|--------|----------------------------|---------------------------|--------|
| **Transformation Location** | Python scripts | SQL in database | **ELT** |
| **Raw Data Preservation** | Optional | Always retained | **ELT** |
| **Reprocessing** | Requires re-extraction | Query raw layer | **ELT** |
| **Performance** | Python processing overhead | Leverage DB engine | **ELT** |
| **Maintainability** | Code-heavy | SQL-based (dbt) | **ELT** |
| **Testing** | Unit tests in Python | dbt tests | **ELT** |
| **Auditing** | Complex | Built-in lineage | **ELT** |

### ELT Benefits for Olist Dataset

1. **Auditability:** Raw CSV data preserved in staging layer
2. **Performance:** DuckDB's columnar engine faster than Python pandas
3. **Simplicity:** dbt handles dependency management automatically
4. **Testability:** dbt tests validate data quality at each layer
5. **Version Control:** SQL models in Git, easy to review
6. **Debugging:** Can query intermediate transformation steps
7. **Scalability:** Easy to parallelize dbt models

---

## Data Ingestion Layer

### Stage 1: Extract (Python)

**Responsibility:** Read CSV files and prepare for loading

#### Extract Script: `extract_csv.py`

```python
"""
CSV Extraction Script
Reads Olist CSV files and validates structure
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

# Configuration
SOURCE_DIR = "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/"
DB_PATH = "olist_dw.duckdb"

# Source file definitions
SOURCE_FILES = {
    'customers': 'olist_customers_dataset.csv',
    'orders': 'olist_orders_dataset.csv',
    'order_items': 'olist_order_items_dataset.csv',
    'order_payments': 'olist_order_payments_dataset.csv',
    'order_reviews': 'olist_order_reviews_dataset.csv',
    'products': 'olist_products_dataset.csv',
    'sellers': 'olist_sellers_dataset.csv',
    'geolocation': 'olist_geolocation_dataset.csv',
    'category_translation': 'product_category_name_translation.csv'
}

class CSVExtractor:
    """Extract and validate CSV files"""

    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.logger = logging.getLogger(__name__)

    def validate_file_exists(self, filename: str) -> bool:
        """Check if file exists and is readable"""
        filepath = self.source_dir / filename
        if not filepath.exists():
            self.logger.error(f"File not found: {filepath}")
            return False
        if not filepath.is_file():
            self.logger.error(f"Not a file: {filepath}")
            return False
        return True

    def get_file_metadata(self, filename: str) -> Dict:
        """Get file metadata"""
        filepath = self.source_dir / filename
        stat = filepath.stat()
        return {
            'filename': filename,
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'modified_time': datetime.fromtimestamp(stat.st_mtime),
            'filepath': str(filepath)
        }

    def validate_csv_structure(self, filepath: Path, expected_columns: List[str] = None) -> Dict:
        """Validate CSV structure without loading full file"""
        try:
            # Read only first row to check structure
            df_sample = pd.read_csv(filepath, nrows=5)

            validation = {
                'valid': True,
                'row_count_sample': len(df_sample),
                'column_count': len(df_sample.columns),
                'columns': list(df_sample.columns),
                'errors': []
            }

            # Check for expected columns if provided
            if expected_columns:
                missing_cols = set(expected_columns) - set(df_sample.columns)
                if missing_cols:
                    validation['valid'] = False
                    validation['errors'].append(f"Missing columns: {missing_cols}")

            # Check for unnamed columns
            unnamed_cols = [col for col in df_sample.columns if 'Unnamed' in str(col)]
            if unnamed_cols:
                validation['valid'] = False
                validation['errors'].append(f"Unnamed columns detected: {unnamed_cols}")

            return validation

        except Exception as e:
            return {
                'valid': False,
                'errors': [str(e)]
            }

    def extract_all(self) -> Dict:
        """Extract metadata for all source files"""
        results = {}

        for table_name, filename in SOURCE_FILES.items():
            self.logger.info(f"Validating {table_name}: {filename}")

            # Check file exists
            if not self.validate_file_exists(filename):
                results[table_name] = {'status': 'ERROR', 'message': 'File not found'}
                continue

            # Get metadata
            metadata = self.get_file_metadata(filename)

            # Validate structure
            filepath = self.source_dir / filename
            validation = self.validate_csv_structure(filepath)

            results[table_name] = {
                'status': 'OK' if validation['valid'] else 'ERROR',
                'metadata': metadata,
                'validation': validation
            }

        return results


def main():
    """Main extraction process"""
    logging.basicConfig(level=logging.INFO)

    extractor = CSVExtractor(SOURCE_DIR)
    results = extractor.extract_all()

    # Print summary
    print("\n" + "="*60)
    print("CSV EXTRACTION SUMMARY")
    print("="*60)

    for table_name, result in results.items():
        status = result['status']
        if status == 'OK':
            metadata = result['metadata']
            validation = result['validation']
            print(f"\n{table_name.upper()}")
            print(f"  Status: ✓ {status}")
            print(f"  File: {metadata['filename']}")
            print(f"  Size: {metadata['size_mb']} MB")
            print(f"  Columns: {validation['column_count']}")
        else:
            print(f"\n{table_name.upper()}")
            print(f"  Status: ✗ {status}")
            print(f"  Errors: {result.get('validation', {}).get('errors', [])}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
```

### Stage 2: Load (Python + DuckDB)

**Responsibility:** Load CSV files to DuckDB staging schema

#### Load Script: `load_to_staging.py`

```python
"""
Load CSV to DuckDB Staging Layer
Creates raw schema and loads CSV files
"""

import duckdb
from pathlib import Path
from datetime import datetime
import logging

SOURCE_DIR = "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/"
DB_PATH = "olist_dw.duckdb"

class DuckDBLoader:
    """Load CSV files to DuckDB staging schema"""

    def __init__(self, db_path: str, source_dir: str):
        self.db_path = db_path
        self.source_dir = Path(source_dir)
        self.logger = logging.getLogger(__name__)
        self.conn = None

    def connect(self):
        """Connect to DuckDB"""
        self.conn = duckdb.connect(self.db_path)
        self.logger.info(f"Connected to DuckDB: {self.db_path}")

    def create_schema(self):
        """Create raw schema if not exists"""
        self.conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        self.logger.info("Created schema: raw")

    def load_csv_to_staging(self, table_name: str, filename: str, type_overrides: dict = None):
        """
        Load CSV file to staging table

        Args:
            table_name: Target table name (e.g., 'stg_orders')
            filename: Source CSV filename
            type_overrides: Dictionary of column name -> DuckDB type for casting
        """
        filepath = self.source_dir / filename
        staging_table = f"raw.{table_name}"

        self.logger.info(f"Loading {filename} → {staging_table}")

        try:
            # Drop existing table
            self.conn.execute(f"DROP TABLE IF EXISTS {staging_table}")

            # Load CSV with DuckDB's CSV reader
            if type_overrides:
                # Build CREATE TABLE statement with types
                self.conn.execute(f"""
                    CREATE TABLE {staging_table} AS
                    SELECT * FROM read_csv_auto('{filepath}')
                """)
            else:
                # Let DuckDB infer types
                self.conn.execute(f"""
                    CREATE TABLE {staging_table} AS
                    SELECT * FROM read_csv_auto('{filepath}')
                """)

            # Get row count
            row_count = self.conn.execute(f"SELECT COUNT(*) FROM {staging_table}").fetchone()[0]

            self.logger.info(f"  ✓ Loaded {row_count:,} rows")

            return {'status': 'OK', 'row_count': row_count}

        except Exception as e:
            self.logger.error(f"  ✗ Failed to load {filename}: {e}")
            return {'status': 'ERROR', 'error': str(e)}

    def add_load_metadata(self, table_name: str):
        """Add ETL metadata columns to staging table"""
        staging_table = f"raw.{table_name}"

        # Check if columns already exist
        columns = self.conn.execute(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'raw' AND table_name = '{table_name.replace('stg_', '')}'
        """).fetchall()

        column_names = [col[0] for col in columns]

        if '_loaded_at' not in column_names:
            self.conn.execute(f"""
                ALTER TABLE {staging_table}
                ADD COLUMN _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)

        if '_source_file' not in column_names:
            self.conn.execute(f"""
                ALTER TABLE {staging_table}
                ADD COLUMN _source_file VARCHAR
            """)

    def load_all(self):
        """Load all CSV files to staging"""
        files_to_load = {
            'stg_customers': 'olist_customers_dataset.csv',
            'stg_orders': 'olist_orders_dataset.csv',
            'stg_order_items': 'olist_order_items_dataset.csv',
            'stg_order_payments': 'olist_order_payments_dataset.csv',
            'stg_order_reviews': 'olist_order_reviews_dataset.csv',
            'stg_products': 'olist_products_dataset.csv',
            'stg_sellers': 'olist_sellers_dataset.csv',
            'stg_geolocation': 'olist_geolocation_dataset.csv',
            'stg_category_translation': 'product_category_name_translation.csv'
        }

        results = {}

        for table_name, filename in files_to_load.items():
            result = self.load_csv_to_staging(table_name, filename)
            results[table_name] = result

        return results

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.logger.info("Closed database connection")


def main():
    """Main load process"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    loader = DuckDBLoader(DB_PATH, SOURCE_DIR)

    try:
        loader.connect()
        loader.create_schema()
        results = loader.load_all()

        # Print summary
        print("\n" + "="*60)
        print("LOAD TO STAGING SUMMARY")
        print("="*60)

        total_rows = 0
        for table_name, result in results.items():
            if result['status'] == 'OK':
                row_count = result['row_count']
                total_rows += row_count
                print(f"{table_name}: {row_count:,} rows ✓")
            else:
                print(f"{table_name}: ERROR - {result['error']} ✗")

        print(f"\nTotal rows loaded: {total_rows:,}")
        print("="*60 + "\n")

    finally:
        loader.close()


if __name__ == "__main__":
    main()
```

---

## Transformation Layer

### dbt Project Structure

```
olist_dw_dbt/
├── dbt_project.yml
├── profiles.yml
├── packages.yml
│
├── models/
│   ├── staging/
│   │   ├── _staging.yml           # Source definitions
│   │   ├── stg_orders.sql
│   │   ├── stg_customers.sql
│   │   ├── stg_products.sql
│   │   ├── stg_sellers.sql
│   │   └── ...
│   │
│   ├── intermediate/
│   │   ├── int_order_enriched.sql
│   │   ├── int_customer_metrics.sql
│   │   ├── int_seller_metrics.sql
│   │   └── int_product_metrics.sql
│   │
│   ├── core/
│   │   ├── dimensions/
│   │   │   ├── dim_customer.sql
│   │   │   ├── dim_product.sql
│   │   │   ├── dim_seller.sql
│   │   │   ├── dim_date.sql
│   │   │   ├── dim_geography.sql
│   │   │   └── dim_category.sql
│   │   │
│   │   └── facts/
│   │       ├── fact_order_items.sql
│   │       ├── fact_orders.sql
│   │       ├── fact_payments.sql
│   │       └── fact_reviews.sql
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
│       ├── operations/
│       │   └── mart_delivery_metrics.sql
│       └── geographic/
│           └── mart_geographic_analysis.sql
│
├── tests/
│   ├── assert_positive_order_amounts.sql
│   ├── assert_valid_date_ranges.sql
│   └── assert_referential_integrity.sql
│
├── macros/
│   ├── generate_surrogate_key.sql
│   ├── scd_type_2.sql
│   └── custom_tests.sql
│
└── snapshots/
    ├── snapshot_dim_customer.sql
    ├── snapshot_dim_product.sql
    └── snapshot_dim_seller.sql
```

### dbt Configuration Files

#### `dbt_project.yml`

```yaml
name: 'olist_dw'
version: '1.0.0'
config-version: 2

profile: 'olist_dw'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

clean-targets:
  - "target"
  - "dbt_packages"

models:
  olist_dw:
    # Staging models - no materialization, views only
    staging:
      +materialized: view
      +schema: staging

    # Intermediate models - ephemeral (CTEs)
    intermediate:
      +materialized: ephemeral

    # Core dimensional models - tables
    core:
      +materialized: table
      +schema: core

      dimensions:
        # SCD Type 2 dimensions as snapshots
        +pre-hook:
          - "{{ log('Building dimension table', info=True) }}"

      facts:
        +post-hook:
          - "{{ log('Fact table built', info=True) }}"

    # Mart models - materialized views or tables
    marts:
      +materialized: table
      +schema: mart

      executive:
        +tags: ['daily', 'executive']

      customer:
        +tags: ['daily', 'customer']

      product:
        +tags: ['daily', 'product']

      seller:
        +tags: ['daily', 'seller']

      operations:
        +tags: ['daily', 'operations']

      geographic:
        +tags: ['weekly', 'geographic']

# Seeds configuration
seeds:
  olist_dw:
    +schema: seed

# Snapshot configuration
snapshots:
  olist_dw:
    +target_schema: snapshots
    +strategy: check
    +check_cols: all
```

#### `profiles.yml`

```yaml
olist_dw:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: '/home/dhafin/Documents/Projects/EDA/olist_dw.duckdb'
      schema: core
      threads: 4

    prod:
      type: duckdb
      path: '/home/dhafin/Documents/Projects/EDA/olist_dw_prod.duckdb'
      schema: core
      threads: 8
```

### Sample dbt Models

#### Staging: `stg_orders.sql`

```sql
{{
    config(
        materialized='view'
    )
}}

WITH source AS (
    SELECT * FROM {{ source('raw', 'stg_orders') }}
),

cleaned AS (
    SELECT
        -- Primary key
        order_id,
        customer_id,

        -- Order status
        order_status,

        -- Timestamps (convert string to timestamp)
        CAST(order_purchase_timestamp AS TIMESTAMP) AS order_purchase_timestamp,
        CAST(order_approved_at AS TIMESTAMP) AS order_approved_at,
        CAST(order_delivered_carrier_date AS TIMESTAMP) AS order_delivered_carrier_date,
        CAST(order_delivered_customer_date AS TIMESTAMP) AS order_delivered_customer_date,
        CAST(order_estimated_delivery_date AS TIMESTAMP) AS order_estimated_delivery_date,

        -- Metadata
        _loaded_at

    FROM source
)

SELECT * FROM cleaned
```

#### Intermediate: `int_order_enriched.sql`

```sql
{{
    config(
        materialized='ephemeral'
    )
}}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

order_items AS (
    SELECT
        order_id,
        COUNT(*) AS total_items,
        SUM(price) AS total_amount,
        SUM(freight_value) AS total_freight,
        COUNT(DISTINCT seller_id) AS num_sellers,
        COUNT(DISTINCT product_id) AS num_products
    FROM {{ ref('stg_order_items') }}
    GROUP BY order_id
),

payments AS (
    SELECT
        order_id,
        SUM(payment_value) AS total_payment
    FROM {{ ref('stg_order_payments') }}
    GROUP BY order_id
),

reviews AS (
    SELECT
        order_id,
        review_score,
        review_creation_date
    FROM {{ ref('stg_order_reviews') }}
),

enriched AS (
    SELECT
        o.*,
        c.customer_state,
        c.customer_city,
        oi.total_items,
        oi.total_amount,
        oi.total_freight,
        oi.num_sellers,
        oi.num_products,
        p.total_payment,
        r.review_score,

        -- Calculated fields
        CASE
            WHEN oi.num_sellers > 1 THEN TRUE
            ELSE FALSE
        END AS is_multivendor,

        DATEDIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date) AS days_to_deliver,

        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN TRUE
            ELSE FALSE
        END AS is_late_delivery

    FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    LEFT JOIN order_items oi ON o.order_id = oi.order_id
    LEFT JOIN payments p ON o.order_id = p.order_id
    LEFT JOIN reviews r ON o.order_id = r.order_id
)

SELECT * FROM enriched
```

#### Core Dimension: `dim_customer.sql`

```sql
{{
    config(
        materialized='table',
        schema='core'
    )
}}

WITH source_customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

customer_metrics AS (
    -- Calculate lifetime metrics from orders
    SELECT
        customer_id,
        MIN(order_purchase_timestamp::DATE) AS first_order_date,
        MAX(order_purchase_timestamp::DATE) AS last_order_date,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_amount) AS total_spent,
        AVG(total_amount) AS avg_order_value
    FROM {{ ref('int_order_enriched') }}
    WHERE order_status = 'delivered'
    GROUP BY customer_id
),

geography AS (
    SELECT DISTINCT
        zip_code_prefix,
        city,
        state,
        CASE state
            WHEN 'AC' THEN 'Norte'
            WHEN 'AL' THEN 'Nordeste'
            WHEN 'AP' THEN 'Norte'
            WHEN 'AM' THEN 'Norte'
            WHEN 'BA' THEN 'Nordeste'
            WHEN 'CE' THEN 'Nordeste'
            WHEN 'DF' THEN 'Centro-Oeste'
            WHEN 'ES' THEN 'Sudeste'
            WHEN 'GO' THEN 'Centro-Oeste'
            WHEN 'MA' THEN 'Nordeste'
            WHEN 'MT' THEN 'Centro-Oeste'
            WHEN 'MS' THEN 'Centro-Oeste'
            WHEN 'MG' THEN 'Sudeste'
            WHEN 'PA' THEN 'Norte'
            WHEN 'PB' THEN 'Nordeste'
            WHEN 'PR' THEN 'Sul'
            WHEN 'PE' THEN 'Nordeste'
            WHEN 'PI' THEN 'Nordeste'
            WHEN 'RJ' THEN 'Sudeste'
            WHEN 'RN' THEN 'Nordeste'
            WHEN 'RS' THEN 'Sul'
            WHEN 'RO' THEN 'Norte'
            WHEN 'RR' THEN 'Norte'
            WHEN 'SC' THEN 'Sul'
            WHEN 'SP' THEN 'Sudeste'
            WHEN 'SE' THEN 'Nordeste'
            WHEN 'TO' THEN 'Norte'
        END AS region
    FROM {{ ref('stg_geolocation') }}
),

final AS (
    SELECT
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['c.customer_id']) }} AS customer_key,

        -- Natural key
        c.customer_id,
        c.customer_unique_id,

        -- Geography
        c.customer_zip_code_prefix,
        c.customer_city,
        c.customer_state,
        g.region AS customer_region,

        -- Metrics
        m.first_order_date,
        m.last_order_date,
        COALESCE(m.total_orders, 0) AS total_orders,
        COALESCE(m.total_spent, 0) AS total_spent,
        m.avg_order_value,

        -- Derived attributes
        CASE
            WHEN m.total_orders >= 2 THEN TRUE
            ELSE FALSE
        END AS is_repeat_customer,

        -- Segmentation
        CASE
            WHEN m.total_orders IS NULL OR m.total_orders = 0 THEN 'NEW'
            WHEN m.total_orders = 1 THEN 'ONE_TIME'
            WHEN m.total_orders BETWEEN 2 AND 5 THEN 'REGULAR'
            WHEN m.total_orders > 5 AND m.total_spent > 1000 THEN 'VIP'
            WHEN m.total_orders > 5 THEN 'LOYAL'
            WHEN DATEDIFF('day', m.last_order_date, CURRENT_DATE) > 180 THEN 'CHURNED'
            ELSE 'ACTIVE'
        END AS customer_segment,

        -- SCD Type 2 fields (for future use)
        CURRENT_TIMESTAMP AS effective_from,
        NULL::TIMESTAMP AS effective_to,
        TRUE AS is_current,

        -- Metadata
        CURRENT_TIMESTAMP AS created_at,
        CURRENT_TIMESTAMP AS updated_at

    FROM source_customers c
    LEFT JOIN customer_metrics m ON c.customer_id = m.customer_id
    LEFT JOIN geography g ON c.customer_zip_code_prefix = g.zip_code_prefix
)

SELECT * FROM final
```

#### Core Fact: `fact_order_items.sql`

```sql
{{
    config(
        materialized='table',
        schema='core'
    )
}}

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
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
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key([
            'oi.order_id',
            'oi.order_item_id'
        ]) }} AS order_item_key,

        -- Degenerate dimensions
        oi.order_id,
        oi.order_item_id,

        -- Foreign keys to dimensions
        dc.customer_key,
        dp.product_key,
        ds.seller_key,
        dd_order.date_key AS order_date_key,
        dd_delivery.date_key AS delivery_date_key,

        -- Measures
        oi.price,
        oi.freight_value,
        1 AS quantity,  -- Always 1 in this dataset
        oi.price + oi.freight_value AS total_amount,

        -- Derived measures
        DATEDIFF('day', o.order_purchase_timestamp, o.order_delivered_carrier_date) AS days_to_ship,
        DATEDIFF('day', o.order_purchase_timestamp, o.order_delivered_customer_date) AS days_to_deliver,
        DATEDIFF('day', o.order_estimated_delivery_date, o.order_delivered_customer_date) AS delivery_vs_estimate,

        CASE
            WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN TRUE
            ELSE FALSE
        END AS is_late_delivery,

        -- Metadata
        CURRENT_TIMESTAMP AS created_at

    FROM order_items oi
    INNER JOIN orders o ON oi.order_id = o.order_id
    LEFT JOIN dim_customer dc ON o.customer_id = dc.customer_id
    LEFT JOIN dim_product dp ON oi.product_id = dp.product_id
    LEFT JOIN dim_seller ds ON oi.seller_id = ds.seller_id
    LEFT JOIN dim_date dd_order ON CAST(o.order_purchase_timestamp AS DATE) = dd_order.full_date
    LEFT JOIN dim_date dd_delivery ON CAST(o.order_delivered_customer_date AS DATE) = dd_delivery.full_date
)

SELECT * FROM final
```

#### Mart: `mart_executive_dashboard.sql`

```sql
{{
    config(
        materialized='table',
        schema='mart'
    )
}}

WITH daily_metrics AS (
    SELECT
        d.full_date,
        d.year,
        d.month,
        d.year_month,

        -- Order metrics
        COUNT(DISTINCT f.order_id) AS order_count,
        SUM(f.total_amount) AS gmv,
        AVG(f.total_amount) AS avg_order_value,

        -- Customer metrics
        COUNT(DISTINCT f.customer_key) AS unique_customers,

        -- Product metrics
        COUNT(DISTINCT f.product_key) AS unique_products,

        -- Seller metrics
        COUNT(DISTINCT f.seller_key) AS active_sellers

    FROM {{ ref('fact_order_items') }} f
    JOIN {{ ref('dim_date') }} d ON f.order_date_key = d.date_key
    GROUP BY d.full_date, d.year, d.month, d.year_month
),

monthly_aggregates AS (
    SELECT
        year_month,
        SUM(order_count) AS monthly_orders,
        SUM(gmv) AS monthly_gmv,
        AVG(avg_order_value) AS monthly_avg_order_value,
        COUNT(DISTINCT full_date) AS days_in_month

    FROM daily_metrics
    GROUP BY year_month
),

final AS (
    SELECT
        d.*,

        -- Month-over-month growth
        LAG(d.gmv) OVER (ORDER BY d.full_date) AS prev_day_gmv,
        (d.gmv - LAG(d.gmv) OVER (ORDER BY d.full_date)) / NULLIF(LAG(d.gmv) OVER (ORDER BY d.full_date), 0) * 100 AS gmv_growth_pct,

        -- Monthly aggregates
        m.monthly_orders,
        m.monthly_gmv,
        m.monthly_avg_order_value

    FROM daily_metrics d
    LEFT JOIN monthly_aggregates m ON d.year_month = m.year_month
)

SELECT * FROM final
ORDER BY full_date
```

---

## Data Quality Framework

### dbt Tests

#### Schema Tests (`models/core/schema.yml`)

```yaml
version: 2

models:
  - name: dim_customer
    description: Customer dimension with SCD Type 2
    columns:
      - name: customer_key
        description: Surrogate key
        tests:
          - unique
          - not_null

      - name: customer_id
        description: Natural key
        tests:
          - not_null

      - name: customer_state
        description: Brazilian state code
        tests:
          - accepted_values:
              values: ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

      - name: total_orders
        description: Lifetime order count
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

  - name: fact_order_items
    description: Order line items fact table
    columns:
      - name: order_item_key
        tests:
          - unique
          - not_null

      - name: customer_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_key

      - name: product_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_product')
              field: product_key

      - name: price
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "> 0"
```

#### Custom Tests (`tests/assert_positive_order_amounts.sql`)

```sql
-- Test: All order amounts should be positive
SELECT
    order_id,
    total_amount
FROM {{ ref('fact_orders') }}
WHERE total_amount <= 0
```

#### Data Quality Macros (`macros/custom_tests.sql`)

```sql
{% macro test_positive_values(model, column_name) %}

SELECT
    {{ column_name }}
FROM {{ model }}
WHERE {{ column_name }} <= 0

{% endmacro %}
```

---

## Orchestration Strategy

### Option 1: Dagster (Recommended)

**Why Dagster:**
- Modern data orchestrator with great dbt integration
- Asset-based lineage tracking
- Built-in data quality checks
- Easy local development
- Better than Airflow for analytics workloads

#### Dagster Pipeline: `olist_pipeline.py`

```python
"""
Dagster pipeline for Olist ELT
"""

from dagster import (
    asset,
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    Definitions,
    ScheduleDefinition
)
from dagster_dbt import DbtCliResource, dbt_assets
from pathlib import Path
import subprocess

DBT_PROJECT_DIR = Path(__file__).parent / "olist_dw_dbt"

@asset(group_name="extract_load")
def extract_csv_files(context: AssetExecutionContext):
    """Extract and validate CSV files"""
    result = subprocess.run(
        ["python", "extract_csv.py"],
        capture_output=True,
        text=True
    )

    context.log.info(result.stdout)

    return MaterializeResult(
        metadata={
            "status": MetadataValue.text(result.stdout)
        }
    )

@asset(group_name="extract_load", deps=[extract_csv_files])
def load_to_staging(context: AssetExecutionContext):
    """Load CSV to DuckDB staging"""
    result = subprocess.run(
        ["python", "load_to_staging.py"],
        capture_output=True,
        text=True
    )

    context.log.info(result.stdout)

    return MaterializeResult(
        metadata={
            "status": MetadataValue.text(result.stdout)
        }
    )

# dbt assets
@dbt_assets(
    manifest=DBT_PROJECT_DIR / "target" / "manifest.json",
    project_dir=DBT_PROJECT_DIR
)
def olist_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# Schedule: Daily at 2 AM
daily_schedule = ScheduleDefinition(
    name="daily_etl",
    target="*",
    cron_schedule="0 2 * * *"
)

# Definitions
defs = Definitions(
    assets=[extract_csv_files, load_to_staging, olist_dbt_assets],
    schedules=[daily_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=DBT_PROJECT_DIR)
    }
)
```

### Option 2: Apache Airflow

#### Airflow DAG: `olist_etl_dag.py`

```python
"""
Airflow DAG for Olist ELT Pipeline
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['data-team@company.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    'olist_etl_pipeline',
    default_args=default_args,
    description='Olist ELT Pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['etl', 'olist']
) as dag:

    extract_task = BashOperator(
        task_id='extract_csv',
        bash_command='python /path/to/extract_csv.py'
    )

    load_task = BashOperator(
        task_id='load_to_staging',
        bash_command='python /path/to/load_to_staging.py'
    )

    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command='cd /path/to/olist_dw_dbt && dbt deps'
    )

    dbt_staging = BashOperator(
        task_id='dbt_staging',
        bash_command='cd /path/to/olist_dw_dbt && dbt run --select staging.*'
    )

    dbt_core = BashOperator(
        task_id='dbt_core',
        bash_command='cd /path/to/olist_dw_dbt && dbt run --select core.*'
    )

    dbt_marts = BashOperator(
        task_id='dbt_marts',
        bash_command='cd /path/to/olist_dw_dbt && dbt run --select marts.*'
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /path/to/olist_dw_dbt && dbt test'
    )

    # Define dependencies
    extract_task >> load_task >> dbt_deps >> dbt_staging >> dbt_core >> dbt_marts >> dbt_test
```

---

## Incremental Processing

### Incremental Load Strategy

For future implementation when new data arrives:

```sql
-- models/core/facts/fact_order_items.sql (incremental version)

{{
    config(
        materialized='incremental',
        unique_key='order_item_key',
        on_schema_change='sync_all_columns'
    )
}}

WITH new_orders AS (
    SELECT * FROM {{ ref('stg_order_items') }}

    {% if is_incremental() %}
        -- Only process orders newer than max existing order date
        WHERE order_id IN (
            SELECT order_id
            FROM {{ ref('stg_orders') }}
            WHERE order_purchase_timestamp > (
                SELECT MAX(created_at) FROM {{ this }}
            )
        )
    {% endif %}
),

-- ... rest of transformation logic

SELECT * FROM final
```

---

## Error Handling

### Error Handling Strategy

1. **Extraction Errors:**
   - File not found → Log error, send alert, skip file
   - Malformed CSV → Log error, quarantine file, alert

2. **Loading Errors:**
   - Schema mismatch → Log error, create error table, alert
   - Data type conversion → Log error, load as VARCHAR, flag for review

3. **Transformation Errors:**
   - dbt model failure → Stop pipeline, rollback transaction, alert
   - Test failure → Mark as warning, continue pipeline, create ticket

4. **Data Quality Errors:**
   - Missing foreign key → Log orphan records, quarantine, alert
   - Business rule violation → Log violations, flag records, continue

### Error Logging Table

```sql
CREATE TABLE etl.error_log (
    error_id BIGINT PRIMARY KEY,
    error_timestamp TIMESTAMP NOT NULL,
    pipeline_stage VARCHAR(50) NOT NULL,  -- extract, load, transform
    table_name VARCHAR(100),
    error_type VARCHAR(50),  -- file_not_found, schema_mismatch, etc.
    error_message TEXT,
    error_details JSON,
    resolution_status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, RESOLVED, IGNORED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation Code

### Complete Orchestration Script

#### `run_pipeline.py`

```python
"""
Complete ELT Pipeline Runner
Executes full pipeline: Extract → Load → Transform
"""

import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PipelineRunner:
    """ELT Pipeline Orchestrator"""

    def __init__(self):
        self.start_time = datetime.now()
        self.errors = []

    def run_step(self, step_name: str, command: list) -> bool:
        """Run a pipeline step"""
        logger.info(f"Starting: {step_name}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"✓ {step_name} completed successfully")
            logger.debug(result.stdout)
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"✗ {step_name} failed")
            logger.error(e.stderr)
            self.errors.append(f"{step_name}: {e.stderr}")
            return False

    def run_pipeline(self):
        """Execute full ELT pipeline"""
        logger.info("="*60)
        logger.info("STARTING OLIST ELT PIPELINE")
        logger.info("="*60)

        # Step 1: Extract
        if not self.run_step("Extract CSV", ["python", "extract_csv.py"]):
            logger.error("Pipeline failed at Extract step")
            return False

        # Step 2: Load
        if not self.run_step("Load to Staging", ["python", "load_to_staging.py"]):
            logger.error("Pipeline failed at Load step")
            return False

        # Step 3: dbt deps
        if not self.run_step("Install dbt dependencies", ["dbt", "deps"]):
            logger.warning("dbt deps failed, continuing...")

        # Step 4: dbt run
        if not self.run_step("Run dbt transformations", ["dbt", "run"]):
            logger.error("Pipeline failed at Transform step")
            return False

        # Step 5: dbt test
        if not self.run_step("Run dbt tests", ["dbt", "test"]):
            logger.warning("Some dbt tests failed, check logs")

        # Pipeline complete
        duration = (datetime.now() - self.start_time).total_seconds()
        logger.info("="*60)
        logger.info(f"PIPELINE COMPLETED in {duration:.2f} seconds")
        logger.info("="*60)

        if self.errors:
            logger.warning(f"Completed with {len(self.errors)} errors:")
            for error in self.errors:
                logger.warning(f"  - {error}")

        return True


def main():
    """Main entry point"""
    runner = PipelineRunner()
    success = runner.run_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

---

## Related Documents

- **data_warehouse_architecture.md** - Overall architecture design
- **dimensional_model.md** - Detailed table schemas
- **implementation_plan.md** - Phased rollout plan

---

**End of ETL/ELT Pipeline Design**
