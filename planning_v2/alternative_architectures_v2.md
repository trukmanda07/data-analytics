# Alternative Architectures V2

**Version:** 2.0
**Created:** 2025-11-09

---

## Alternative 1: Event Sourcing + Lakehouse

**Architecture:**
- All changes stored as events (append-only log)
- Current state derived from events
- Apache Iceberg for time travel

**When to use:**
- Full audit trail required
- Need to reconstruct historical state
- Compliance-heavy industry

**Pros:**
- Complete history
- Time travel built-in
- Easy to add new projections

**Cons:**
- Higher complexity
- Eventual consistency
- Larger storage

**Implementation:**
```python
class OrderPlacedEvent:
    event_id: UUID
    order_id: UUID
    customer_id: UUID
    timestamp: datetime

# Event store (append-only)
event_store.append(OrderPlacedEvent(...))

# Projection (derive current state)
current_orders = replay_events(event_store.get_all())
```

---

## Alternative 2: Semantic Layer First (Cube.js/dbt Metrics)

**Architecture:**
- Raw data in PostgreSQL (normalized)
- No pre-aggregation
- Metrics defined in semantic layer
- Query-time aggregation with caching

**When to use:**
- Self-service analytics priority
- Metrics change frequently
- Don't want to manage materialized views

**Pros:**
- Single source of truth for metrics
- No pre-aggregation maintenance
- Self-service for analysts

**Cons:**
- Slower queries (no pre-agg)
- Requires powerful query engine
- Caching complexity

---

## Alternative 3: Data Vault 2.0

**Architecture:**
- Hubs (business keys)
- Links (relationships)
- Satellites (attributes + history)

**When to use:**
- Compliance/audit requirements
- Multiple source systems
- Historical tracking essential

**Pros:**
- Historical tracking by design
- Easy to add sources
- Audit-friendly

**Cons:**
- Complex queries (many JOINs)
- Steeper learning curve
- More tables to manage

---

## Alternative 4: Streaming-First (Kafka + Flink)

**Architecture:**
- Kafka for event streaming
- Flink for stream processing
- Materialized views updated real-time

**When to use:**
- Real-time analytics (<5 min latency)
- High event volume
- Streaming data sources

**Pros:**
- Real-time insights
- Scalable ingestion
- Event-driven by nature

**Cons:**
- Much higher complexity
- Operational overhead
- Overkill for batch data

---

## Alternative 5: Federated Queries (DuckDB/Trino)

**Architecture:**
- No data movement
- Query data in place (CSVs, S3, databases)
- Trino/Presto/DuckDB as query engine

**When to use:**
- Exploratory analysis
- Data sources change frequently
- Don't want to manage ETL

**Pros:**
- No ETL needed
- Always fresh (queries source)
- Low storage

**Cons:**
- Query performance varies
- Dependent on source systems
- No data quality guarantees

---

## Comparison Matrix

| Alternative | Complexity | Cost | Real-time | Audit | Team Skill |
|-------------|------------|------|-----------|-------|------------|
| **V2 (Core)** | Medium | $$ | Batch (daily) | Good | Medium |
| **Event Sourcing** | High | $$$ | Near-real-time | Excellent | High |
| **Semantic Layer** | Low | $ | Query-time | Basic | Low |
| **Data Vault** | High | $$ | Batch | Excellent | High |
| **Streaming** | Very High | $$$$ | Real-time | Good | Very High |
| **Federated** | Low | $ | Real-time | Poor | Low |

---

## Recommendation

**For Olist dataset (99k orders, batch updates):**

Use **V2 Core Architecture** (PostgreSQL + dbt + domain layer)

**Reasons:**
- Right-sized for 100GB-1TB data
- Team can handle complexity
- Production-ready from day 1
- Can add streaming later if needed

**Consider alternatives when:**
- Event Sourcing: Regulatory audit requirements
- Semantic Layer: Self-service analytics priority
- Streaming: Real-time requirements emerge
