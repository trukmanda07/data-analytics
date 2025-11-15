# Technology Decision Matrix V2 - Honest Comparison

**Version:** 2.0
**Created:** 2025-11-09

---

## Executive Summary

**V1 Claim:** "DuckDB and PostgreSQL use nearly identical SQL syntax. Migration requires minimal changes."

**V2 Reality:** This is architectural fiction. These databases have fundamentally different execution models, and migration is a complete rewrite, not "minimal changes."

---

## The Database Portability Myth (Debunked)

### What V1 Got Wrong

V1 proposed this migration path:
1. **Phase 1:** DuckDB (MVP)
2. **Phase 2:** PostgreSQL (scale to 100 users)
3. **Phase 3:** ClickHouse (enterprise scale)

**Claimed effort:** "Minimal code changes, dbt adapter swap"

**Actual effort:**
- DuckDB → PostgreSQL: 8-12 weeks of rewriting
- PostgreSQL → ClickHouse: 12-16 weeks of complete redesign

---

## Technology Comparison Matrix

| Feature | DuckDB | PostgreSQL | ClickHouse |
|---------|--------|------------|------------|
| **Storage Model** | Columnar, in-process file | Row-oriented, client-server | Columnar, distributed |
| **Transaction Model** | MVCC (limited, single-writer) | Full ACID, multi-writer | Eventually consistent |
| **Concurrency** | Read-only concurrent queries | Full concurrent CRUD | Append-optimized |
| **Indexes** | Automatic (zone maps) | Manual (B-tree, GiST, BRIN) | MergeTree, sparse indexes |
| **SCD Type 2** | Poor (no UPDATE concurrency) | Excellent | Poor (insert-only) |
| **Connection Pooling** | N/A (embedded) | PgBouncer required | ClickHouse proxy |
| **Replication** | None (file-based) | Streaming, logical | Built-in distributed |
| **Deployment** | Single Python process | Database server | Cluster (3+ nodes) |
| **Operational Complexity** | Low | Medium | High |
| **Learning Curve** | Low | Low | Medium-High |
| **Community Support** | Growing | Excellent | Good |
| **Cost (100GB data)** | $0 (embedded) | $80-150/month | $300-500/month |

---

## Decision Framework

### When to Use DuckDB

**Use cases:**
- Proof of concept / Prototyping
- Single-user analytics
- Data science notebooks
- Embedded analytics in applications
- No concurrent writes needed

**Do NOT use for:**
- Multi-user data warehouse
- Concurrent writes (SCD Type 2)
- Production applications
- Client-server architecture

**Migration to PostgreSQL:**
- **Effort:** 8-12 weeks
- **Code changes:**
  - Rewrite SCD Type 2 logic (DuckDB can't handle concurrent UPDATEs)
  - Add connection pooling
  - Rewrite indexes (manual tuning needed)
  - Add vacuum/autovacuum management
- **Data migration:** Export to CSV → Import to PostgreSQL (or use pg_dump)

### When to Use PostgreSQL

**Use cases:**
- Multi-user data warehouse (< 1TB)
- OLTP + OLAP hybrid workloads
- Strong consistency required
- Row-level security needed
- Rich extension ecosystem (PostGIS, pg_partman)

**Strengths:**
- Battle-tested reliability
- Full ACID transactions
- Excellent documentation
- Large talent pool
- Mature tooling

**Limitations:**
- Slower than columnar stores for analytics
- Single-node scaling limits
- Requires tuning for OLAP

**Migration to ClickHouse:**
- **Effort:** 12-16 weeks
- **Code changes:**
  - Rewrite schema (no ACID, different data types)
  - Change query patterns (no JOINs on large tables)
  - Rewrite SCD logic (append-only model)
  - Add eventual consistency handling
- **Data migration:** Batch export → Bulk insert (no transactional guarantees)

### When to Use ClickHouse

**Use cases:**
- Very large datasets (> 1TB)
- Real-time analytics at scale
- High ingestion rate (millions of events/sec)
- Aggregation-heavy queries

**Strengths:**
- Blazing fast for OLAP
- Horizontal scaling
- Excellent compression
- Time-series optimized

**Limitations:**
- No transactions (eventual consistency)
- Poor for updates/deletes
- Limited JOIN performance
- Operational complexity (cluster management)

**Not suitable for:**
- SCD Type 2 (use snapshots instead)
- Transactional workloads
- Small datasets (< 100GB)

---

## Recommended Decision for Olist

### Dataset Characteristics

- **Size:** 100GB (current), 500GB (projected 3 years)
- **Users:** 5-10 analysts
- **Queries:** Mostly aggregations, some JOINs
- **Writes:** Daily batch (no real-time)
- **Consistency:** Strong consistency preferred
- **SCD Type 2:** Not needed (V2 uses Type 1)

### Recommendation: PostgreSQL

**Reasons:**

1. **Right-sized:** 500GB easily handled by single PostgreSQL instance
2. **Team capability:** More common than DuckDB/ClickHouse
3. **Production-ready:** Full ACID, replication, backup/restore
4. **Future-proof:** Can scale to 1TB+ before needing ClickHouse
5. **Ecosystem:** Mature tools (dbt, Dagster, Metabase all support Postgres)

**Trade-offs accepted:**

- Slower than ClickHouse for large aggregations (but fast enough for Olist scale)
- More complex than DuckDB (but we need multi-user)
- Requires server management (but manageable with RDS/Cloud SQL)

**Cost:**
- AWS RDS db.t3.medium (2 vCPU, 4GB RAM): $80/month
- Storage (500GB): $60/month
- **Total:** $140/month = $1,680/year

---

## Migration Complexity Analysis

### Scenario 1: DuckDB → PostgreSQL

**What V1 Claimed:**
> "Minimal changes. dbt adapters handle differences. Just swap connection string."

**What Actually Happens:**

1. **Connection Management (1 week)**
   - DuckDB: `con = duckdb.connect('olist.duckdb')`
   - PostgreSQL: Need connection pooling, session management, connection limits

2. **Indexes (2 weeks)**
   - DuckDB: Automatic zone maps
   - PostgreSQL: Must create indexes manually, tune for query patterns

3. **SCD Type 2 Logic (3 weeks)**
   - DuckDB: Concurrent UPDATEs don't work well
   - PostgreSQL: Works, but need optimistic locking, transactions

4. **Vacuum/Maintenance (1 week)**
   - DuckDB: None needed
   - PostgreSQL: Configure autovacuum, analyze, vacuumdb scripts

5. **Query Rewrites (2-4 weeks)**
   - Different query optimizers
   - Different EXPLAIN output
   - Different performance characteristics

**Total effort: 8-12 weeks**

### Scenario 2: PostgreSQL → ClickHouse

**What V1 Claimed:**
> "When you need enterprise scale, move to ClickHouse."

**What Actually Happens:**

1. **Schema Redesign (4 weeks)**
   - ClickHouse has different data types (DateTime64 vs TIMESTAMP)
   - No foreign keys
   - Different NULL handling
   - MergeTree engine selection

2. **SCD Type 2 Elimination (3 weeks)**
   - ClickHouse doesn't support UPDATE/DELETE well
   - Must use snapshots or append-only pattern
   - Rewrite all historical tracking logic

3. **Query Rewrites (4-6 weeks)**
   - JOINs are slow in ClickHouse (denormalize instead)
   - Different aggregation functions
   - Different EXPLAIN plan

4. **Cluster Setup (2 weeks)**
   - ZooKeeper for coordination
   - Replication configuration
   - Sharding strategy

5. **Eventual Consistency Handling (2 weeks)**
   - No ACID transactions
   - Must handle stale reads
   - Retry logic for failures

**Total effort: 12-16 weeks**

---

## Total Cost of Ownership (3 Years)

### Option 1: DuckDB → PostgreSQL (V1 approach)

| Year | DuckDB Phase | Migration | PostgreSQL | Total |
|------|--------------|-----------|------------|-------|
| 1 | $0 (embedded) | $30,000 (8 weeks @ $3750/week) | $1,680 | $31,680 |
| 2 | - | - | $1,680 | $1,680 |
| 3 | - | - | $1,680 | $1,680 |
| **Total** | | | | **$35,040** |

### Option 2: PostgreSQL from Day 1 (V2 approach)

| Year | PostgreSQL | Total |
|------|------------|-------|
| 1 | $1,680 | $1,680 |
| 2 | $1,680 | $1,680 |
| 3 | $1,680 | $1,680 |
| **Total** | | **$5,040** |

**Savings: $30,000 over 3 years**

### Option 3: DuckDB → PostgreSQL → ClickHouse (V1 full path)

| Year | Phase | Migration Cost | Infra Cost | Total |
|------|-------|----------------|------------|-------|
| 1 | DuckDB | - | $0 | $0 |
| 2 | Migrate to PostgreSQL | $30,000 | $1,680 | $31,680 |
| 3 | Migrate to ClickHouse | $45,000 | $6,000 | $51,000 |
| **Total** | | | | **$82,680** |

**V2 saves $77,640 by not pretending databases are interchangeable.**

---

## Vendor Lock-In Analysis

### dbt (Transformation Layer)

**Lock-in Risk:** Medium

**Reasons:**
- Proprietary Jinja templating
- dbt-specific macros
- dbt Cloud features (if used)

**Mitigation:**
- dbt Core is open-source
- Can migrate to custom SQL scripts
- Estimated migration: 4-6 weeks

**Exit Strategy:**
- Extract dbt models to raw SQL
- Replace macros with Python/SQL functions
- Use custom orchestration

### Dagster (Orchestration Layer)

**Lock-in Risk:** Low

**Reasons:**
- Business logic is NOT in Dagster (it's in domain layer)
- Dagster is just a thin adapter

**Mitigation:**
- Use hexagonal architecture (ports & adapters)
- Business logic in domain layer
- Estimated migration: 1-2 weeks

**Exit Strategy:**
- Swap Dagster adapter for Airflow adapter
- Business logic remains unchanged
- Minimal code changes

### PostgreSQL (Database)

**Lock-in Risk:** Medium

**Reasons:**
- SQL is standardized, but dialects differ
- Extensions (PostGIS) are Postgres-specific
- PL/pgSQL stored procedures

**Mitigation:**
- Use standard SQL (avoid Postgres-specific features)
- Don't use stored procedures (business logic in Python)
- Estimated migration to ClickHouse: 12-16 weeks

**Exit Strategy:**
- Export data to Parquet/CSV
- Rewrite schema for target database
- Migrate queries

---

## Team Capability Assessment

### Required Skills by Technology

| Technology | Skills Needed | Team Availability | Training Needed |
|------------|---------------|-------------------|-----------------|
| **DuckDB** | Python, SQL | High | 1 week |
| **PostgreSQL** | SQL, DB admin, tuning | Medium-High | 2 weeks |
| **ClickHouse** | Distributed systems, SQL, cluster mgmt | Low | 4-6 weeks |
| **dbt** | SQL, Jinja, data modeling | Medium | 2 weeks |
| **Dagster** | Python, orchestration concepts | Medium | 1 week |
| **Great Expectations** | Python, data quality concepts | Medium | 1 week |

### Hiring Implications

**DuckDB:**
- Hard to hire (niche skill)
- Most candidates haven't used it
- Training required

**PostgreSQL:**
- Easy to hire (ubiquitous skill)
- Large talent pool
- Less training required

**ClickHouse:**
- Medium difficulty to hire
- Specialized skill
- May require senior engineer

**Recommendation:** Choose PostgreSQL for easier hiring and onboarding.

---

## Honest Decision Tree

```
START: What database should I use?

├─ Is this a PROOF OF CONCEPT (< 3 months lifespan)?
│  └─ Use: DuckDB
│     Reason: Fast setup, embedded, throwaway code
│     Warning: Do NOT use for production
│
├─ Do you need REAL-TIME analytics (< 5 min latency)?
│  └─ Consider: Streaming architecture (not batch DW)
│     Technologies: Kafka + Flink or ksqlDB
│     Warning: Much higher complexity
│
├─ Is your data > 1TB and growing fast?
│  └─ Consider: ClickHouse or Lakehouse
│     Warning: Operational complexity, eventual consistency
│     Alternative: Start with PostgreSQL, migrate later (explicit effort)
│
├─ Do you need STRONG CONSISTENCY (ACID transactions)?
│  └─ Use: PostgreSQL
│     Reason: Full ACID, row-level locks, SCD Type 2 support
│
└─ DEFAULT (Multi-user DW, < 1TB, strong consistency)
   └─ Use: PostgreSQL
      Reason: Best balance of features, maturity, talent pool
      Cost: $140/month AWS RDS
      Migration to ClickHouse: Possible but 12-16 weeks effort
```

---

## Conclusion

### Key Takeaways

1. **No "minimal changes" migration exists.** Databases have fundamentally different models.

2. **Choose PostgreSQL upfront for Olist.** Right-sized for 100GB-1TB, production-ready, team can handle.

3. **DuckDB is for POCs only.** Do not use for multi-user production data warehouse.

4. **Migration to ClickHouse is expensive.** Only do it when data exceeds 1TB and PostgreSQL query performance degrades.

5. **Vendor lock-in is manageable.** Use clean architecture, keep business logic in domain layer.

### Final Recommendation

**Use PostgreSQL from day 1.**

**Cost:** $1,680/year
**Effort saved:** $30,000 (no DuckDB migration)
**Risk mitigation:** Production-ready from day 1, no surprises

**If you outgrow PostgreSQL (> 1TB, queries > 10 seconds):**
- Evaluate ClickHouse or Lakehouse
- Budget 12-16 weeks for migration
- Accept it's a rewrite, not "minimal changes"
