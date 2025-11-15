# Olist Data Warehouse - Architecture V2
## Production-Ready Architecture (Revised)

**Document Version:** 2.0
**Created:** 2025-11-09
**Status:** Architecture Design Phase
**Supersedes:** planning/v1.0 (see challenge report)

---

## Executive Summary

This is a **complete architectural redesign** of the Olist e-commerce data warehouse project, addressing **8 critical flaws** identified in the architecture challenge report.

### What Changed from V1

| Critical Issue | V1 Approach | V2 Solution |
|----------------|-------------|-------------|
| **Database Portability Myth** | Claimed easy DuckDB→PostgreSQL→ClickHouse migration | Choose PostgreSQL upfront, honest migration analysis |
| **Anemic Domain Model** | Business logic in SQL CASE statements | Domain layer with aggregates, value objects, business rules |
| **No Bounded Contexts** | Single monolithic schema | 4 bounded contexts with clear boundaries |
| **Hidden Dependencies** | Hardcoded CSV file paths | Ports & Adapters pattern, dependency injection |
| **No Aggregate Protection** | Open writes to fact tables | Aggregate roots with invariant enforcement |
| **SCD Type 2 Overkill** | SCD Type 2 for 3 dimensions | SCD Type 1 for MVP, selective Type 2 where justified |
| **Data Quality Afterthought** | dbt tests only | Data Quality as first-class bounded context |
| **Orchestration Coupling** | Business logic in Dagster assets | Hexagonal architecture, orchestration as adapter |

### Realistic Estimates

| Metric | V1 (Claimed) | V1 (Actual) | V2 (Realistic) |
|--------|--------------|-------------|----------------|
| **Timeline** | 16 weeks | 16 weeks + 6-9 months rework | 22-24 weeks (includes foundation) |
| **Budget** | $51.5k | $150-200k (with rework) | $100-120k (done right first time) |
| **Team Size** | 1 FTE | 1 FTE (struggling) | 1 domain expert + 1 data engineer |
| **Success Probability** | 30% | N/A | 85% |

### Key Architectural Decisions

1. **Technology Stack:** PostgreSQL (not DuckDB MVP) for production-grade features
2. **Architecture Pattern:** Clean Architecture / Hexagonal Architecture (Ports & Adapters)
3. **Domain Model:** Domain-Driven Design with bounded contexts
4. **Data Quality:** Separate bounded context, not just testing
5. **Security:** First-class concern from day 1
6. **Historical Tracking:** SCD Type 1 by default, Type 2 only where justified

---

## Navigation Guide

### Core Architecture Documents

1. **[Architecture V2](./architecture_v2.md)** - Complete system architecture
   - Bounded contexts and context map
   - Clean architecture layers
   - Technology stack selection
   - Security architecture
   - Deployment model

2. **[Domain Model V2](./domain_model_v2.md)** - Domain-driven design
   - Domain entities and aggregates
   - Value objects
   - Domain events
   - Business rules
   - Aggregate invariants

3. **[Implementation Strategy V2](./implementation_strategy_v2.md)** - Realistic execution plan
   - Phased approach (22-24 weeks)
   - Reduced MVP scope
   - Team composition
   - Risk mitigation
   - Decision gates

### Technical Specifications

4. **[Pipeline Architecture V2](./pipeline_architecture_v2.md)** - ETL/ELT design
   - Idempotent operations
   - Transaction boundaries
   - Error handling and retry
   - Data lineage tracking
   - Schema evolution

5. **[Data Quality Framework V2](./data_quality_framework_v2.md)** - Quality as domain
   - Quality dimensions and metrics
   - Quality domain model
   - Automated checks
   - Failure handling
   - Quality SLAs

6. **[Security & Compliance V2](./security_compliance_v2.md)** - Security architecture
   - Authentication and authorization
   - Data encryption
   - PII handling (LGPD compliance)
   - Audit logging
   - Incident response

### Decision Support

7. **[Technology Decision Matrix V2](./technology_decision_matrix_v2.md)** - Honest tech comparison
   - DuckDB vs PostgreSQL vs ClickHouse
   - Migration complexity analysis
   - Total cost of ownership
   - Team capability assessment
   - Decision framework

8. **[Alternative Architectures V2](./alternative_architectures_v2.md)** - 5 alternative approaches
   - Event Sourcing + Lakehouse
   - Semantic Layer First
   - Data Vault 2.0
   - Streaming-First
   - Federated Queries
   - When to choose each

9. **[Roadmap V2](./roadmap_v2.md)** - 22-24 week implementation plan
   - Weekly milestones
   - Decision points
   - Go/No-Go gates
   - Resource allocation
   - Risk checkpoints

---

## Quick Decision Trees

### "Which technology should I use?"

```
START: What's your primary constraint?

├─ Team has PostgreSQL experience
│  └─ Use: PostgreSQL
│     Reason: Leverage existing knowledge, production-ready
│
├─ Budget is extremely limited (<$30k)
│  └─ Use: DuckDB for POC only
│     Warning: Plan migration to PostgreSQL within 6 months
│
├─ Need real-time analytics (< 5 min latency)
│  └─ Consider: Streaming architecture (see Alternative #4)
│     Warning: Much higher complexity
│
├─ Data volume will exceed 10TB within 2 years
│  └─ Consider: ClickHouse or Lakehouse (see Alternative #1)
│     Warning: Higher operational overhead
│
└─ Unsure / Default
   └─ Use: PostgreSQL
      Reason: Best balance of features, community, flexibility
```

### "Should I use SCD Type 2?"

```
START: Do you REALLY need historical dimension tracking?

├─ NO - Current state is sufficient
│  └─ Use: SCD Type 1
│     Benefit: Simple queries, better performance
│
├─ YES - But only for specific dimensions
│  ├─ Customer address history needed?
│  │  └─ Use: Separate customer_address_history table
│  │     Reason: Don't pollute main dimension
│  │
│  ├─ Product pricing history needed?
│  │  └─ Use: Temporal table or fact_price_changes
│  │     Reason: Price is a fact, not dimension attribute
│  │
│  └─ Regulatory/compliance requirement?
│     └─ Consider: Event Sourcing (see Alternative #1)
│        Reason: Full audit trail, reconstruction capability
│
└─ DEFAULT: Use SCD Type 1
   Caveat: Add history only when proven necessary
```

### "Which architecture alternative should I choose?"

```
START: What's your primary business driver?

├─ Speed to market (< 8 weeks)
│  └─ Use: Federated Queries (Alternative #5)
│     Tradeoff: Less performant, always dependent on source
│
├─ Real-time insights (< 5 min freshness)
│  └─ Use: Streaming-First (Alternative #4)
│     Tradeoff: High complexity, requires Kafka/Flink skills
│
├─ Compliance / Auditability paramount
│  └─ Use: Data Vault 2.0 (Alternative #3) or Event Sourcing (Alternative #1)
│     Tradeoff: More complex queries, steeper learning curve
│
├─ Self-service analytics for business users
│  └─ Use: Semantic Layer First (Alternative #2)
│     Tradeoff: Requires powerful query engine, caching layer
│
└─ Balanced approach (recommended)
   └─ Use: Core Architecture V2 (this plan)
      Benefit: Production-ready, maintainable, team can handle
```

---

## Bounded Context Overview

The Olist domain is divided into **4 bounded contexts**:

### 1. Sales Context
**Responsibility:** Order placement, payment processing, invoicing
**Core Aggregates:** Order, Payment, Invoice
**Key Events:** OrderPlaced, PaymentReceived, OrderCancelled

### 2. Fulfillment Context
**Responsibility:** Order delivery, logistics, carrier management
**Core Aggregates:** Shipment, Delivery, CarrierPerformance
**Key Events:** ShipmentDispatched, DeliveryCompleted, DeliveryDelayed

### 3. Marketplace Context
**Responsibility:** Product catalog, seller management, inventory
**Core Aggregates:** Product, Seller, ProductCatalog
**Key Events:** ProductListed, SellerRegistered, InventoryUpdated

### 4. Customer Context
**Responsibility:** Customer profiles, reviews, loyalty
**Core Aggregates:** Customer, Review, LoyaltyProfile
**Key Events:** CustomerRegistered, ReviewSubmitted, SegmentChanged

**Shared Kernel:** Money, Address, DateRange, Geolocation value objects

---

## Key Metrics & SLAs

### Data Freshness
- **Daily Batch:** Data available by 8 AM local time
- **Incremental Loads:** Maximum 4-hour lag for operational reports
- **SLA:** 95% of loads complete within freshness window

### Query Performance
- **Dashboard Loads:** < 3 seconds (p95)
- **Ad-hoc Queries:** < 10 seconds (p95)
- **Complex Analytics:** < 60 seconds (p95)
- **SLA:** 90% of queries meet performance targets

### Data Quality
- **Completeness:** > 98% for critical fields
- **Accuracy:** > 99.5% (validated against source)
- **Timeliness:** Data loaded within 4 hours of availability
- **Consistency:** Zero cross-table integrity violations
- **SLA:** Quality score > 95% overall

### Availability
- **System Uptime:** 99.5% (excludes planned maintenance)
- **Planned Downtime:** < 4 hours/month (off-peak hours)
- **Recovery Time Objective (RTO):** < 2 hours
- **Recovery Point Objective (RPO):** < 1 hour

---

## Cost Breakdown (Realistic)

### Phase 0: Foundation (4 weeks) - $18,000
- Domain modeling workshop
- Architecture design
- Security framework
- Team training

### Phase 1: Core (8 weeks) - $36,000
- Domain layer implementation
- 2 bounded contexts (Sales, Customer)
- 2 dimensions + 1 fact table
- Data quality framework
- Observability setup

### Phase 2: Expansion (6 weeks) - $27,000
- Remaining 2 contexts (Fulfillment, Marketplace)
- Additional dimensions + facts
- Advanced analytics
- Performance optimization

### Phase 3: Production (4 weeks) - $18,000
- Security hardening
- Disaster recovery testing
- Production deployment
- Knowledge transfer
- Initial support

**Total: $99,000** (conservative estimate)
**Contingency (20%):** $20,000
**Grand Total: $119,000**

---

## Success Criteria

This architecture succeeds if:

- **Technical Excellence**
  - All 8 critical issues from challenge report addressed
  - Domain model is NOT anemic (business logic in domain layer)
  - Bounded contexts with clear boundaries
  - Security is first-class concern
  - Data quality has its own domain model
  - Rollback and disaster recovery procedures tested

- **Operational Excellence**
  - System meets defined SLAs (freshness, performance, quality)
  - Team can maintain system without external consultants
  - Observability enables proactive issue detection
  - Incident response time < 30 minutes (detection to action)

- **Business Value**
  - Stakeholders can answer business questions independently
  - Data-driven decisions increase by 50%
  - Time to insight decreases from days to hours
  - Data trust score > 90% (stakeholder survey)

- **Evolvability**
  - Can add new data sources without architectural changes
  - Can evolve bounded contexts independently
  - Can migrate to different technology within 6 months if needed
  - Technical debt remains manageable (< 20% of velocity)

---

## How to Use This Documentation

### For Architects
1. Start with [Architecture V2](./architecture_v2.md) for system overview
2. Review [Domain Model V2](./domain_model_v2.md) for DDD patterns
3. Study [Alternative Architectures](./alternative_architectures_v2.md) for trade-offs
4. Use [Technology Decision Matrix](./technology_decision_matrix_v2.md) for tech choices

### For Developers
1. Read [Domain Model V2](./domain_model_v2.md) for business logic placement
2. Follow [Pipeline Architecture V2](./pipeline_architecture_v2.md) for ETL patterns
3. Implement [Data Quality Framework](./data_quality_framework_v2.md) checks
4. Consult [Security & Compliance](./security_compliance_v2.md) for requirements

### For Project Managers
1. Review [Roadmap V2](./roadmap_v2.md) for timeline and milestones
2. Check [Implementation Strategy V2](./implementation_strategy_v2.md) for risks
3. Track against success criteria (above)
4. Use Go/No-Go gates for decision points

### For Business Stakeholders
1. Read this README for executive summary
2. Review success criteria and SLAs
3. Participate in domain modeling workshop (Phase 0)
4. Validate bounded context boundaries match business understanding

---

## Lessons Learned from V1

### What We Changed

1. **Stopped pretending databases are interchangeable**
   - V1: "Minimal changes to migrate DuckDB → PostgreSQL"
   - V2: "Choose PostgreSQL upfront, or accept complete rewrite"

2. **Extracted business logic from SQL**
   - V1: Customer segmentation in SQL CASE statements
   - V2: Customer.calculate_segment() in domain layer

3. **Defined bounded contexts**
   - V1: Single monolithic schema with global foreign keys
   - V2: 4 contexts with event-based integration

4. **Made dependencies explicit**
   - V1: Hardcoded file paths, tight coupling to frameworks
   - V2: Dependency injection, ports & adapters

5. **Protected data integrity**
   - V1: Open writes to fact tables, no invariants
   - V2: Aggregate roots enforce business rules

6. **Simplified historical tracking**
   - V1: SCD Type 2 for 3 dimensions "just in case"
   - V2: SCD Type 1 by default, Type 2 only where justified

7. **Elevated data quality**
   - V1: dbt tests as afterthought
   - V2: Data Quality bounded context with domain model

8. **Decoupled from orchestration**
   - V1: Business logic embedded in Dagster assets
   - V2: Use cases in domain layer, Dagster as thin adapter

### What We Kept

- dbt for SQL transformation (but not as core dependency)
- Dimensional modeling (but simplified)
- Incremental loading (but made idempotent)
- Marimo for analytics (but with API layer)
- Phased implementation (but realistic timeline)

---

## Contact & Support

### Architecture Questions
- Review [Technology Decision Matrix](./technology_decision_matrix_v2.md)
- Check [Alternative Architectures](./alternative_architectures_v2.md)
- Consult architecture team for clarification

### Implementation Questions
- Follow [Implementation Strategy](./implementation_strategy_v2.md)
- Reference [Roadmap](./roadmap_v2.md) for sequencing
- Use decision trees (above) for guidance

### Domain Questions
- Conduct domain modeling workshop (Phase 0)
- Validate against [Domain Model V2](./domain_model_v2.md)
- Ensure ubiquitous language is maintained

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0 | 2025-11-09 | Complete redesign addressing challenge report | Architecture Team |
| 1.0 | 2025-11-08 | Initial architecture (deprecated) | Original Team |

---

## Next Steps

1. **Review** - Read through all documents in order
2. **Decide** - Use decision trees to make technology choices
3. **Workshop** - Conduct domain modeling session (Phase 0)
4. **Validate** - Get stakeholder approval on bounded contexts
5. **Begin** - Start Phase 0 foundation work

**Ready to build a production-ready data warehouse the right way.**
