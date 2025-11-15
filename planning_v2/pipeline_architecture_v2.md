# Pipeline Architecture V2 - Idempotent & Transactional

**Version:** 2.0
**Created:** 2025-11-09

---

## Critical Issues Fixed from V1

| Issue | V1 Problem | V2 Solution |
|-------|------------|-------------|
| **Non-idempotent** | Re-running creates duplicates | Watermarks + MERGE/UPSERT |
| **No transactions** | Partial failures leave inconsistent state | Transaction boundaries defined |
| **No rollback** | Can't undo bad loads | Snapshots + rollback scripts |
| **No lineage** | Can't trace metrics to source | OpenLineage integration |
| **Schema evolution** | Breaking changes | Backward-compatible migrations |

---

## Idempotent Pipeline Design

### Core Principle

**Every stage can be re-run safely without side effects.**

### Approach: Watermark-Based Processing

```python
# application/etl/use_cases/load_orders.py

class LoadOrdersUseCase:
    """Idempotent order loading"""

    def execute(self, start_date: datetime, end_date: datetime):
        """Load orders for date range (idempotent)"""

        # Step 1: Load to staging (always full replace for date range)
        staging_data = self.data_source.read_orders(start_date, end_date)
        self.staging_repo.replace(staging_data, start_date, end_date)

        # Step 2: MERGE into core (upsert based on PK)
        self.core_repo.merge_orders(staging_data)

        # Step 3: Update watermark
        self.watermark_repo.set('orders', end_date)

        return LoadResult(count=len(staging_data))
```

### SQL Pattern: MERGE (Upsert)

```sql
-- dbt/models/core/dim_customer.sql
{{
  config(
    materialized='incremental',
    unique_key='customer_id',
    incremental_strategy='merge'  -- PostgreSQL MERGE
  )
}}

-- Idempotent: Running multiple times produces same result
MERGE INTO {{ this }} AS target
USING (
    SELECT
        customer_id,
        customer_unique_id,
        customer_city,
        customer_state,
        customer_zip_code_prefix
    FROM {{ source('staging', 'customers') }}
    WHERE updated_at >= '{{ var("watermark_start") }}'
      AND updated_at < '{{ var("watermark_end") }}'
) AS source
ON target.customer_id = source.customer_id

WHEN MATCHED THEN
    UPDATE SET
        customer_city = source.customer_city,
        customer_state = source.customer_state,
        customer_zip_code_prefix = source.customer_zip_code_prefix,
        updated_at = CURRENT_TIMESTAMP

WHEN NOT MATCHED THEN
    INSERT (customer_id, customer_unique_id, customer_city, customer_state, customer_zip_code_prefix, created_at)
    VALUES (source.customer_id, source.customer_unique_id, source.customer_city, source.customer_state, source.customer_zip_code_prefix, CURRENT_TIMESTAMP)
```

---

## Transaction Boundaries

### Layer 1: Staging (Atomic Replacement)

```python
def load_to_staging(date: datetime):
    """Load to staging with transaction"""

    with transaction():
        # Delete existing data for date
        staging.execute("DELETE FROM staging.orders WHERE order_date = %s", [date])

        # Insert new data
        staging.bulk_insert(orders_for_date)

        # Commit or rollback (atomic)
```

**Atomicity:** Either all data for date is loaded, or none.

### Layer 2: Core (MERGE with Optimistic Locking)

```sql
-- Optimistic locking prevents lost updates
UPDATE core.dim_customer
SET
    total_orders = total_orders + 1,
    version = version + 1  -- Increment version
WHERE customer_id = 'abc123'
  AND version = 5;  -- Only update if version hasn't changed

-- If 0 rows updated, version conflict (someone else updated)
```

### Layer 3: Marts (Materialized with Version)

```sql
-- Marts reference specific core version
CREATE MATERIALIZED VIEW mart.customer_analytics_v2 AS
SELECT
    c.customer_id,
    c.customer_segment,
    COUNT(o.order_id) AS total_orders
FROM core.dim_customer AS c  -- Version 2
LEFT JOIN core.fact_orders AS o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_segment;
```

---

## Rollback Procedures

### Scenario 1: Bad data loaded to staging

```bash
# Rollback: Delete bad batch
DELETE FROM staging.orders
WHERE batch_id = 'batch_20251109_bad';

# Re-run with correct data
python load_staging.py --date=2025-11-09 --batch-id=batch_20251109_fixed
```

### Scenario 2: Corrupted dimension table

```sql
-- Restore from snapshot (created nightly)
BEGIN;
    DROP TABLE core.dim_customer;
    CREATE TABLE core.dim_customer AS
        SELECT * FROM snapshots.dim_customer_20251108;
    ANALYZE core.dim_customer;
COMMIT;
```

### Scenario 3: Bad dbt model deployed

```bash
# Rollback dbt model to previous version
git revert abc123
dbt run --models dim_customer

# Or use blue/green deployment
UPDATE metadata.active_version
SET version = 'v1.2.0'
WHERE table_name = 'dim_customer';
```

---

## Data Lineage Tracking

### Implementation: OpenLineage

```python
# infrastructure/lineage/openlineage_adapter.py
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job

class LineageTracker:
    def __init__(self):
        self.client = OpenLineageClient(url="http://marquez:5000")

    def track_transformation(
        self,
        job_name: str,
        inputs: List[str],
        outputs: List[str]
    ):
        """Track data lineage"""

        run_event = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now().isoformat(),
            run=Run(runId=str(uuid4())),
            job=Job(
                namespace="olist_dw",
                name=job_name
            ),
            inputs=[Dataset(namespace="olist_dw", name=i) for i in inputs],
            outputs=[Dataset(namespace="olist_dw", name=o) for o in outputs]
        )

        self.client.emit(run_event)
```

### Lineage Example

```
CSV: orders.csv
  ↓ (extracted by LoadOrdersUseCase)
staging.orders
  ↓ (transformed by dbt::stg_orders)
staging.stg_orders
  ↓ (loaded by dbt::fact_orders)
core.fact_orders
  ↓ (aggregated by dbt::mart_revenue)
mart.mart_revenue
  ↓ (visualized by dashboard)
Executive Dashboard (Marimo)
```

---

## Schema Evolution Strategy

### Approach: Backward-Compatible Changes Only

**Allowed:**
- Add new column (with default value)
- Add new table
- Add new index

**Not allowed (breaking):**
- Remove column
- Rename column
- Change data type
- Add NOT NULL constraint to existing column

### Migration Example

```python
# migrations/versions/002_add_customer_segment.py
"""Add customer_segment column

Revision ID: 002
"""

def upgrade():
    # Add column with default
    op.add_column(
        'dim_customer',
        sa.Column('customer_segment', sa.String(20), server_default='NEW')
    )

    # Backfill using domain logic
    connection = op.get_bind()
    customers = connection.execute("SELECT customer_id, total_orders, total_spent FROM dim_customer")

    for customer in customers:
        segment = calculate_segment(customer.total_orders, customer.total_spent)
        connection.execute(
            "UPDATE dim_customer SET customer_segment = %s WHERE customer_id = %s",
            [segment, customer.customer_id]
        )

    # Now safe to make NOT NULL
    op.alter_column('dim_customer', 'customer_segment', nullable=False)

def downgrade():
    op.drop_column('dim_customer', 'customer_segment')
```

---

## Error Handling & Retry

### Error Taxonomy

| Error Type | Recoverable? | Action |
|------------|--------------|--------|
| **Transient** (network timeout) | Yes | Retry with exponential backoff |
| **Data Quality** (NULL in required field) | No | Quarantine + alert |
| **Schema Mismatch** (missing column) | No | Stop pipeline + alert |
| **Resource** (out of memory) | Maybe | Reduce batch size + retry |

### Retry Logic

```python
# infrastructure/retry/retry_policy.py
from tenacity import retry, stop_after_attempt, wait_exponential

class RetryPolicy:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True
    )
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute with retry for transient errors"""
        try:
            return func(*args, **kwargs)
        except TransientError as e:
            logger.warning(f"Transient error, will retry: {e}")
            raise  # Trigger retry
        except PermanentError as e:
            logger.error(f"Permanent error, stopping: {e}")
            raise  # Don't retry
```

---

## Observability

### Structured Logging

```python
# infrastructure/logging/structured_logger.py
import structlog

logger = structlog.get_logger()

logger.info(
    "order_loaded",
    order_id=order.order_id,
    customer_id=order.customer_id,
    total_amount=float(order.total_amount()),
    duration_ms=elapsed_ms
)

# Logs in JSON for easy parsing
# {"event": "order_loaded", "order_id": "abc123", "total_amount": 120.50, "timestamp": "2025-11-09T10:30:00Z"}
```

### Metrics (Prometheus)

```python
# infrastructure/metrics/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Counters
orders_loaded = Counter('orders_loaded_total', 'Total orders loaded')
load_errors = Counter('load_errors_total', 'Total load errors', ['error_type'])

# Histograms (for timing)
load_duration = Histogram('load_duration_seconds', 'Load duration', ['stage'])

# Gauges
data_freshness_lag = Gauge('data_freshness_lag_seconds', 'Data freshness lag')

# Usage
with load_duration.labels(stage='staging').time():
    load_to_staging()
    orders_loaded.inc(len(orders))
```

---

## Pipeline DAG

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACT (CSV Adapter)                     │
│  Input: CSV files                                            │
│  Output: Python objects (domain entities)                    │
│  Idempotency: None (read-only)                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  LOAD TO STAGING (Atomic)                    │
│  Input: Domain entities                                      │
│  Output: staging.* tables                                    │
│  Idempotency: DELETE + INSERT for date range                 │
│  Transaction: BEGIN/COMMIT per batch                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│             TRANSFORM (dbt Staging Models)                   │
│  Input: staging.* tables                                     │
│  Output: staging.stg_* views                                 │
│  Idempotency: Views always reflect current staging data      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              LOAD TO CORE (MERGE/Upsert)                     │
│  Input: staging.stg_* views                                  │
│  Output: core.dim_*, core.fact_* tables                      │
│  Idempotency: MERGE based on primary key                     │
│  Transaction: One per table                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│            BUILD MARTS (Materialized Views)                  │
│  Input: core.* tables                                        │
│  Output: mart.* materialized views                           │
│  Idempotency: REFRESH MATERIALIZED VIEW                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│             DATA QUALITY CHECKS                              │
│  Input: core.*, mart.* tables                                │
│  Output: Quality report, alerts                              │
│  Idempotency: Read-only validation                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusion

This pipeline architecture fixes all V1 flaws:

1. **Idempotent:** Watermarks + MERGE ensure re-runs are safe
2. **Transactional:** Clear boundaries, rollback supported
3. **Traceable:** OpenLineage tracks data from source to dashboard
4. **Evolvable:** Backward-compatible schema migrations
5. **Observable:** Structured logs, Prometheus metrics
6. **Resilient:** Retry logic, error handling, dead letter queue

**Next:** See data_quality_framework_v2.md for quality validation.
