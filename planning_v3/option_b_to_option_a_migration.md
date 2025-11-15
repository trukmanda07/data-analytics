# Migration Guide: Option B (dbt-Only) → Option A (Python + dbt)

**Document Version:** 3.0
**Date:** 2025-11-09
**Purpose:** Step-by-step guide to migrate from SQL-only to hybrid Python+SQL architecture
**Estimated Duration:** 8-12 weeks (depending on complexity)

---

## Table of Contents

1. [Overview](#overview)
2. [Why Migrate?](#why-migrate)
3. [Migration Strategy](#migration-strategy)
4. [Phase 1: Extract Business Logic](#phase-1-extract-business-logic)
5. [Phase 2: Create Value Objects](#phase-2-create-value-objects)
6. [Phase 3: Create Entities](#phase-3-create-entities)
7. [Phase 4: Create Aggregates](#phase-4-create-aggregates)
8. [Phase 5: Refactor dbt Models](#phase-5-refactor-dbt-models)
9. [Phase 6: Add Domain Events](#phase-6-add-domain-events)
10. [Phase 7: Cutover](#phase-7-cutover)
11. [Rollback Plan](#rollback-plan)

---

## Overview

### What This Guide Does

This guide helps you **gradually migrate** from a dbt-only architecture (Option B) to a hybrid Python + dbt architecture (Option A) **without breaking your existing system**.

### Migration Philosophy

**"Strangler Fig Pattern"** - Gradually replace SQL logic with Python domain layer while keeping the system operational.

```
Current State (Option B):
CSV → dbt (all logic in SQL) → DuckDB → Dashboards

Target State (Option A):
CSV → Python (validation) → DuckDB → dbt (transformation only) → Dashboards
```

### Key Principle: Zero Downtime

- ✅ Keep existing dbt models running
- ✅ Build Python layer in parallel
- ✅ Migrate one bounded context at a time
- ✅ Validate before cutover
- ✅ Easy rollback if needed

---

## Why Migrate?

### Signs You Need Option A

1. **Business Logic Duplication**
   ```sql
   -- Same customer segmentation logic in 5 different files!
   -- models/staging/stg_customers.sql
   CASE WHEN total_orders > 10 THEN 'VIP' ... END

   -- models/core/dim_customer.sql
   CASE WHEN total_orders > 10 THEN 'VIP' ... END  -- Duplicate!

   -- models/marts/mart_customers.sql
   CASE WHEN total_orders > 10 THEN 'VIP' ... END  -- Duplicate!
   ```

2. **Complex CASE Statements**
   ```sql
   -- Unreadable nested logic
   CASE
       WHEN total_orders > 10 AND last_order_days < 30 AND total_spent > 1000 THEN
           CASE
               WHEN review_score >= 4 THEN 'VIP_HAPPY'
               ELSE 'VIP_UNHAPPY'
           END
       WHEN total_orders > 5 AND last_order_days < 60 THEN
           CASE
               WHEN has_returned THEN 'LOYAL_RETURNER'
               ELSE 'LOYAL_NEW'
           END
       ...
   END
   ```

3. **Data Quality Issues**
   ```sql
   -- Invalid data reaches the database
   -- Only caught during dbt test phase (too late!)
   SELECT * FROM orders WHERE total_amount < 0  -- Should never happen
   ```

4. **Hard to Test Business Logic**
   ```bash
   # Need full database to test one business rule
   dbt run --select stg_orders  # Slow, requires database
   dbt test --select stg_orders  # Still slow
   ```

5. **Cannot Reuse Logic**
   ```sql
   -- Logic locked in SQL, can't use in:
   -- - REST APIs
   -- - Batch jobs
   -- - Real-time systems
   ```

### Benefits After Migration

| Aspect | Before (Option B) | After (Option A) |
|--------|------------------|------------------|
| **Validation** | In database (too late) | Before database (early) |
| **Business Logic** | Scattered in SQL | Centralized in aggregates |
| **Testing** | Needs database | Unit tests (no database) |
| **Reusability** | SQL only | APIs, jobs, real-time |
| **Type Safety** | None | Full (mypy) |
| **Development Speed** | Slow (long SQL) | Fast (short Python) |

---

## Migration Strategy

### Approach: Gradual, Bounded-Context-by-Bounded-Context

```
┌─────────────────────────────────────────────────────┐
│  Step 1: Identify Business Logic in SQL             │
│  • Customer segmentation                             │
│  • Order validation                                  │
│  • Payment validation                                │
│  • Delivery performance                              │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 2: Extract to Python (in parallel)            │
│  • Create value objects (Money, Address)             │
│  • Create entities (OrderItem, Payment)              │
│  • Create aggregates (Order, Customer)               │
│  • Keep existing SQL running                         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 3: Dual Run (validate correctness)            │
│  • Python validates and loads data                   │
│  • dbt still transforms (unchanged)                  │
│  • Compare outputs (should be identical)             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 4: Simplify dbt (remove business logic)       │
│  • dbt focuses on transformation only                │
│  • Remove complex CASE statements                    │
│  • Remove validation logic (now in Python)           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Step 5: Cutover (switch to new pipeline)           │
│  • Python becomes source of truth                    │
│  • dbt reads from Python-validated data              │
│  • Monitor for issues                                │
└─────────────────────────────────────────────────────┘
```

### Migration Order (Bounded Contexts)

**Recommended order from simplest to most complex:**

1. **Sales Analytics** (Orders, OrderItems, Payments) - Week 1-3
2. **Customer Analytics** (Customer, Segments) - Week 4-5
3. **Marketplace** (Sellers, Products) - Week 6-7
4. **Fulfillment** (Deliveries) - Week 8

---

## Phase 1: Extract Business Logic

**Duration:** 1 week
**Goal:** Document all business logic currently in SQL

### Step 1.1: Audit SQL Files

Create a spreadsheet documenting all business logic:

| SQL File | Business Rule | Complexity | Priority |
|----------|---------------|------------|----------|
| `int_orders_enriched.sql` | Order must have items | Low | High |
| `int_orders_enriched.sql` | Payment must match total | Medium | High |
| `dim_customer.sql` | Customer segmentation (RFM) | High | High |
| `dim_customer.sql` | Churn detection | Medium | Medium |
| `fact_order_items.sql` | Delivery performance | Medium | High |

### Step 1.2: Extract Business Rules

**Example: Order Validation Rules**

From this SQL:
```sql
-- models/intermediate/int_orders_enriched.sql
SELECT
    order_id,
    CASE
        WHEN total_items = 0 THEN 'INVALID_NO_ITEMS'
        WHEN order_status = 'approved' AND ABS(total_amount - total_payment) > 0.01
            THEN 'INVALID_PAYMENT_MISMATCH'
        ELSE 'VALID'
    END AS order_validity
FROM orders
```

Extract to business rules document:
```
Order Business Rules:
1. Order must have at least 1 item
2. Approved orders must have payment matching total (within $0.01)
3. Delivery date must be after order date
4. Cannot cancel delivered orders
```

### Step 1.3: Prioritize Migration

**High Priority** (migrate first):
- Data validation (prevent bad data)
- Complex business logic (hard to maintain in SQL)
- Duplicated logic (appears in multiple files)

**Low Priority** (migrate later):
- Simple transformations (type casting)
- One-off calculations
- Display formatting

---

## Phase 2: Create Value Objects

**Duration:** 1 week
**Goal:** Create immutable value objects for common concepts

### Step 2.1: Identify Value Objects

From SQL:
```sql
-- Money values scattered everywhere
SELECT price, freight_value, payment_value, total_amount
FROM orders;

-- Addresses
SELECT customer_city, customer_state, customer_zip_code_prefix
FROM customers;

-- Review scores
SELECT review_score
FROM reviews;
```

Convert to Python value objects:
```python
# src/domain/value_objects/money.py
# src/domain/value_objects/address.py
# src/domain/value_objects/review_score.py
```

### Step 2.2: Implement Value Objects

**Money Value Object:**

```python
# src/domain/value_objects/money.py
from decimal import Decimal
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    """Immutable money value object"""
    amount: Decimal
    currency: str = 'BRL'

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")
        if self.currency not in ['BRL', 'USD', 'EUR']:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
```

### Step 2.3: Write Tests

```python
# tests/domain/value_objects/test_money.py
import pytest
from decimal import Decimal
from src.domain.value_objects.money import Money

def test_money_creation():
    money = Money(Decimal('100.50'), 'BRL')
    assert money.amount == Decimal('100.50')
    assert money.currency == 'BRL'

def test_money_negative_amount_raises_error():
    with pytest.raises(ValueError, match="cannot be negative"):
        Money(Decimal('-10.00'), 'BRL')

def test_money_addition():
    m1 = Money(Decimal('100.00'), 'BRL')
    m2 = Money(Decimal('50.00'), 'BRL')
    result = m1 + m2
    assert result.amount == Decimal('150.00')

def test_money_different_currency_addition_raises_error():
    m1 = Money(Decimal('100.00'), 'BRL')
    m2 = Money(Decimal('50.00'), 'USD')
    with pytest.raises(ValueError, match="different currencies"):
        m1 + m2
```

---

## Phase 3: Create Entities

**Duration:** 1 week
**Goal:** Create entities with identity

### Step 3.1: Identify Entities

From SQL:
```sql
-- OrderItem entity
SELECT
    order_item_id,
    order_id,
    product_id,
    seller_id,
    price,
    freight_value
FROM order_items;
```

### Step 3.2: Implement Entities

```python
# src/domain/entities/order_item.py
from dataclasses import dataclass
from datetime import datetime
from ..value_objects.money import Money

@dataclass
class OrderItem:
    """Order line item entity"""
    order_item_id: str
    order_id: str
    product_id: str
    seller_id: str
    price: Money
    freight_value: Money
    shipping_limit_date: datetime

    def __post_init__(self):
        if not self.order_item_id:
            raise ValueError("Order item ID cannot be empty")
        if self.price.amount < 0:
            raise ValueError("Price cannot be negative")

    @property
    def total_amount(self) -> Money:
        """Calculate total (price + freight)"""
        return self.price + self.freight_value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OrderItem):
            return False
        return self.order_item_id == other.order_item_id

    def __hash__(self) -> int:
        return hash(self.order_item_id)
```

---

## Phase 4: Create Aggregates

**Duration:** 2-3 weeks
**Goal:** Create aggregate roots that enforce business rules

### Step 4.1: Identify Aggregate Boundaries

**Order Aggregate:**
- Root: Order
- Entities: OrderItem, Payment
- Invariants:
  - Order must have items
  - Payment must match total
  - Cannot modify delivered orders

### Step 4.2: Migrate Business Logic from SQL to Python

**Before (SQL):**
```sql
-- models/intermediate/int_orders_enriched.sql
SELECT
    order_id,
    CASE
        WHEN total_items = 0 THEN 'INVALID_NO_ITEMS'
        WHEN order_status = 'approved'
            AND ABS(total_amount - total_payment) > 0.01
        THEN 'INVALID_PAYMENT_MISMATCH'
        ELSE 'VALID'
    END AS order_validity
FROM orders;
```

**After (Python):**
```python
# src/domain/aggregates/order.py
from dataclasses import dataclass, field
from typing import List
from ..entities.order_item import OrderItem
from ..entities.payment import Payment

@dataclass
class Order:
    """Order aggregate root"""
    order_id: str
    customer_id: str
    items: List[OrderItem] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)

    def __post_init__(self):
        """Validate order after initialization"""
        # ✅ Business rule 1: Order must have items
        if not self.items:
            raise ValueError("Order must have at least one item")

    @property
    def total_items_amount(self) -> Money:
        """Calculate total from items"""
        total = Money.zero('BRL')
        for item in self.items:
            total = total + item.total_amount
        return total

    @property
    def total_payments_amount(self) -> Money:
        """Calculate total from payments"""
        total = Money.zero('BRL')
        for payment in self.payments:
            total = total + payment.value
        return total

    def approve(self) -> None:
        """Approve order"""
        # ✅ Business rule 2: Payment must match total
        if self.total_payments_amount != self.total_items_amount:
            raise ValueError(
                f"Payment mismatch: paid {self.total_payments_amount}, "
                f"total {self.total_items_amount}"
            )
        self.status = OrderStatus.APPROVED
```

### Step 4.3: Create ETL Script Using Domain Model

```python
# src/etl/load_orders.py
import pandas as pd
from decimal import Decimal
from src.domain.aggregates.order import Order
from src.domain.entities.order_item import OrderItem
from src.domain.value_objects.money import Money

def load_orders_from_csv(csv_path: str):
    """Load orders with domain validation"""

    # Read CSV
    orders_df = pd.read_csv(csv_path + '/olist_orders_dataset.csv')
    items_df = pd.read_csv(csv_path + '/olist_order_items_dataset.csv')
    payments_df = pd.read_csv(csv_path + '/olist_order_payments_dataset.csv')

    valid_orders = []
    invalid_orders = []

    for order_id in orders_df['order_id'].unique():
        try:
            # Get order items
            order_items_data = items_df[items_df['order_id'] == order_id]
            items = []
            for _, item_row in order_items_data.iterrows():
                item = OrderItem(
                    order_item_id=item_row['order_item_id'],
                    order_id=order_id,
                    product_id=item_row['product_id'],
                    seller_id=item_row['seller_id'],
                    price=Money(Decimal(str(item_row['price'])), 'BRL'),
                    freight_value=Money(Decimal(str(item_row['freight_value'])), 'BRL'),
                    shipping_limit_date=pd.to_datetime(item_row['shipping_limit_date'])
                )
                items.append(item)

            # Get payments
            order_payments_data = payments_df[payments_df['order_id'] == order_id]
            payments = []
            # ... create Payment entities

            # Create Order aggregate
            order = Order(
                order_id=order_id,
                customer_id=orders_df[orders_df['order_id'] == order_id]['customer_id'].iloc[0],
                items=items,
                payments=payments
            )

            # ✅ Domain validates business rules!
            # If we reach here, order is valid
            valid_orders.append(order)

        except ValueError as e:
            # ❌ Invalid order caught BEFORE database
            invalid_orders.append({'order_id': order_id, 'error': str(e)})

    print(f"✅ Valid orders: {len(valid_orders)}")
    print(f"❌ Invalid orders: {len(invalid_orders)}")

    # Write valid orders to DuckDB
    # Write invalid orders to error table (PostgreSQL)

    return valid_orders, invalid_orders
```

---

## Phase 5: Refactor dbt Models

**Duration:** 2 weeks
**Goal:** Simplify dbt models (remove business logic)

### Step 5.1: Identify What to Remove

**Before migration:**
```sql
-- models/core/dim_customer.sql
-- Complex business logic in SQL
SELECT
    customer_id,
    CASE
        WHEN total_orders > 10 AND total_spent > 1000 THEN 'VIP'
        WHEN total_orders > 5 THEN 'LOYAL'
        WHEN total_orders = 1 THEN 'ONE_TIME'
        ELSE 'NEW'
    END AS customer_segment
FROM customer_orders;
```

**After migration:**
```sql
-- models/core/dim_customer.sql
-- Simple transformation (business logic in Python)
SELECT
    customer_id,
    customer_segment,  -- Already computed by Python domain layer
    total_orders,
    total_spent
FROM staging.customers;  -- Python writes to staging with segment already set
```

### Step 5.2: Update Staging Models

**Before:**
```sql
-- models/staging/stg_orders.sql
-- Validation in SQL
SELECT
    order_id,
    customer_id,
    CASE
        WHEN order_delivered_customer_date < order_purchase_timestamp
        THEN NULL  -- Invalid date
        ELSE order_delivered_customer_date
    END AS validated_delivery_date
FROM raw.orders;
```

**After:**
```sql
-- models/staging/stg_orders.sql
-- No validation (Python already validated)
SELECT
    order_id,
    customer_id,
    order_delivered_customer_date  -- Already validated by Python
FROM raw.orders;  -- Python writes only valid data
```

### Step 5.3: Simplify Intermediate Models

**Before:**
```sql
-- models/intermediate/int_orders_enriched.sql
-- Complex business logic
WITH order_items AS (...),
     payments AS (...),
     enriched AS (
         SELECT
             o.*,
             CASE
                 WHEN ABS(oi.total_amount - p.total_payment) > 0.01
                 THEN TRUE
                 ELSE FALSE
             END AS has_payment_mismatch,
             CASE WHEN oi.num_sellers > 1 THEN TRUE ELSE FALSE END AS is_multivendor
         FROM orders o
         JOIN order_items oi ON o.order_id = oi.order_id
         JOIN payments p ON o.order_id = p.order_id
     )
SELECT * FROM enriched;
```

**After:**
```sql
-- models/intermediate/int_orders_enriched.sql
-- Simple join (business logic computed by Python)
SELECT
    o.*,
    o.has_payment_mismatch,  -- Already computed
    o.is_multivendor         -- Already computed
FROM staging.orders o;
```

---

## Phase 6: Add Domain Events

**Duration:** 1 week
**Goal:** Emit domain events for observability

### Step 6.1: Create Domain Events

```python
# src/domain/events/order_events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class OrderApproved:
    """Order was approved"""
    order_id: str
    approved_at: datetime
    total_amount: str

@dataclass(frozen=True)
class OrderCancelled:
    """Order was cancelled"""
    order_id: str
    reason: str
    cancelled_at: datetime
```

### Step 6.2: Emit Events from Aggregates

```python
# src/domain/aggregates/order.py
@dataclass
class Order:
    # ... existing code ...

    _events: List = field(default_factory=list, init=False, repr=False)

    def approve(self) -> None:
        """Approve order"""
        if self.total_payments_amount != self.total_items_amount:
            raise ValueError("Payment mismatch")

        self.status = OrderStatus.APPROVED
        self.approved_at = datetime.now()

        # ✅ Emit domain event
        self._events.append(OrderApproved(
            order_id=self.order_id,
            approved_at=self.approved_at,
            total_amount=str(self.total_items_amount.amount)
        ))

    def get_events(self) -> List:
        """Get and clear events"""
        events = self._events.copy()
        self._events.clear()
        return events
```

### Step 6.3: Log Events to PostgreSQL

```python
# src/infrastructure/event_store.py
def save_events(events: List, conn):
    """Save domain events to PostgreSQL"""
    for event in events:
        conn.execute("""
            INSERT INTO event_store.domain_events
            (event_type, aggregate_id, payload, occurred_at)
            VALUES (?, ?, ?, ?)
        """, (
            event.__class__.__name__,
            event.order_id,
            json.dumps(dataclasses.asdict(event)),
            event.approved_at
        ))
```

---

## Phase 7: Cutover

**Duration:** 1 week
**Goal:** Switch to new pipeline

### Step 7.1: Parallel Run (Week 1)

Run both pipelines in parallel:

```bash
# Old pipeline (Option B)
dbt run --select staging.*
dbt run --select core.*

# New pipeline (Option A)
python src/etl/run_pipeline.py  # Uses domain layer

# Compare outputs
python src/etl/compare_outputs.py
```

### Step 7.2: Validate Results

```python
# src/etl/compare_outputs.py
import duckdb

conn = duckdb.connect('olist_analytical.duckdb')

# Compare row counts
old_count = conn.execute("SELECT COUNT(*) FROM old.dim_customer").fetchone()[0]
new_count = conn.execute("SELECT COUNT(*) FROM new.dim_customer").fetchone()[0]

assert old_count == new_count, f"Row count mismatch: {old_count} vs {new_count}"

# Compare aggregates
old_revenue = conn.execute("SELECT SUM(revenue) FROM old.fact_orders").fetchone()[0]
new_revenue = conn.execute("SELECT SUM(revenue) FROM new.fact_orders").fetchone()[0]

assert abs(old_revenue - new_revenue) < 0.01, f"Revenue mismatch"

print("✅ Validation passed!")
```

### Step 7.3: Cutover (Week 2)

```bash
# 1. Stop old pipeline
# (Comment out old cron job)

# 2. Switch dbt to use new staging tables
# profiles.yml: schema: new

# 3. Run new pipeline
python src/etl/run_pipeline.py

# 4. Verify dashboards
# Check that all dashboards still work

# 5. Monitor for 1 week
# Watch for issues
```

---

## Rollback Plan

### If Issues Detected During Cutover

**Step 1: Immediate Rollback (< 5 minutes)**
```bash
# Switch dbt back to old tables
dbt run --vars '{schema: old}'

# Restart old pipeline
cron-job-start old_pipeline.sh

# Verify dashboards working
python test_dashboards.py
```

**Step 2: Root Cause Analysis**
- Compare outputs (old vs new)
- Check error logs
- Review domain validation logic

**Step 3: Fix and Re-attempt**
- Fix identified issues
- Re-run parallel validation
- Cutover again when confident

---

## Success Criteria

### Migration Complete When:

- ✅ All business logic moved to Python domain layer
- ✅ dbt models simplified (no complex CASE statements)
- ✅ Parallel run validates correctly (outputs match)
- ✅ New pipeline runs faster (validation catches errors early)
- ✅ Unit tests cover 90%+ of domain logic
- ✅ Dashboards work without changes
- ✅ No increase in error rate
- ✅ Team trained on new architecture

---

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1. Extract Business Logic | 1 week | Business rules documented |
| 2. Create Value Objects | 1 week | Money, Address, ReviewScore |
| 3. Create Entities | 1 week | OrderItem, Payment, Review |
| 4. Create Aggregates | 2-3 weeks | Order, Customer, Seller |
| 5. Refactor dbt | 2 weeks | Simplified SQL models |
| 6. Add Domain Events | 1 week | Event sourcing |
| 7. Cutover | 1 week | Switch to new pipeline |
| **Total** | **8-10 weeks** | **Production-ready hybrid architecture** |

---

## Cost Comparison

### Migration Cost
- Labor: 10 weeks @ $4,500/week = $45,000

### Long-term Savings (vs staying with Option B)
- Faster development: $10,000/year (less SQL duplication)
- Fewer bugs: $5,000/year (early validation)
- Better maintainability: $8,000/year (cleaner code)

**ROI:** Pays for itself in 2 years

---

## Conclusion

Migrating from Option B to Option A is a **significant but worthwhile investment**. The key is to:

1. **Go gradually** - One bounded context at a time
2. **Validate thoroughly** - Parallel runs catch issues
3. **Keep system operational** - Zero downtime migration
4. **Have rollback plan** - Can revert if needed

**Start with the Sales Analytics context (Orders)** as it has the clearest business rules and highest impact.

---

**Document Status:** ✅ Complete
**Related Documents:**
- `option_b_dbt_only.md` - Starting point
- `domain_implementation_guide.md` - Target state
- `migration_guide_v3.md` - Infrastructure setup
