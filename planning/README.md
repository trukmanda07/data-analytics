# Olist Data Warehouse - Planning Documentation

**Project:** Olist Brazilian E-Commerce Data Warehouse
**Version:** 1.0
**Last Updated:** 2025-11-08
**Status:** Planning Phase

---

## Overview

This directory contains comprehensive planning documentation for building a production-ready data warehouse for the Olist Brazilian e-commerce dataset (2016-2018, 99k+ orders).

The data warehouse will support 100+ business questions across 10 functional areas including executive dashboards, revenue analytics, operations, customer experience, product performance, seller management, geographic analysis, marketing, risk management, and predictive analytics.

---

## Documentation Structure

### 1. **data_warehouse_architecture.md** (Main Architecture Document)
**Purpose:** Complete architectural design including technology stack options, logical and physical architecture, data flow, performance optimization, and cost analysis.

**Key Sections:**
- Architecture overview and principles
- Technology stack comparison (DuckDB vs PostgreSQL vs ClickHouse)
- Logical architecture (4-layer design: Raw → Staging → Core → Mart)
- Physical architecture (schemas, storage, partitioning)
- Performance optimization strategies
- Scalability roadmap
- Cost analysis for 3 technology options

**Read This If:** You need to understand the overall system design or choose a technology stack.

**Key Decision:** Recommends starting with **DuckDB + dbt + Python** for MVP (Phase 1), with optional migration to PostgreSQL for production multi-user access.

---

### 2. **dimensional_model.md** (Data Model Specification)
**Purpose:** Detailed dimensional model using Kimball-style star schema approach with complete table schemas, business logic, and relationships.

**Key Sections:**
- Star schema design with 6 dimensions and 4 fact tables
- Complete column specifications for all tables
- Business logic rules (customer segmentation, seller tiers, etc.)
- SCD Type 2 implementation for dimensions
- Sample SQL DDL for DuckDB/PostgreSQL
- Data dictionary and naming conventions

**Read This If:** You need to implement tables, understand data relationships, or write queries.

**Core Tables:**
- **Dimensions:** dim_customer, dim_product, dim_seller, dim_date, dim_geography, dim_category
- **Facts:** fact_order_items (primary), fact_orders, fact_payments, fact_reviews

---

### 3. **etl_pipeline.md** (ETL/ELT Pipeline Design)
**Purpose:** Complete ETL/ELT pipeline design using modern ELT approach with dbt for transformations.

**Key Sections:**
- ELT vs ETL approach (rationale for choosing ELT)
- 5-stage pipeline: Extract → Load → Transform → Quality Check → Publish
- Python scripts for Extract and Load (with code examples)
- dbt project structure and sample models
- Data quality framework with dbt tests
- Orchestration strategy (Dagster or Airflow)
- Incremental processing strategy
- Error handling and logging

**Read This If:** You need to build the data pipeline or understand data transformations.

**Key Technologies:** Python + DuckDB + dbt-core + Dagster

---

### 4. **implementation_plan.md** (Phased Implementation Roadmap)
**Purpose:** Detailed 16-week implementation plan broken into 3 phases with sprint-by-sprint tasks, deliverables, and success criteria.

**Key Sections:**
- **Phase 1 (Weeks 1-6):** MVP with core dimensions, facts, executive dashboard
- **Phase 2 (Weeks 7-12):** All data marts, incremental loads, BI integration
- **Phase 3 (Weeks 13-16):** ML models, production hardening, monitoring
- Resource requirements (team, infrastructure, budget)
- Risk assessment and mitigation strategies
- Success criteria and KPIs
- Go-live checklist

**Read This If:** You need to plan resources, estimate costs, or manage the project.

**Total Budget:** ~$51,500 (16 weeks) + $25k/year ongoing

---

## Quick Start Guide

### For Project Managers

1. **Read First:** implementation_plan.md (Executive Summary)
2. **Understand Scope:** 16 weeks, 3 phases, 1-2 FTE
3. **Review Budget:** $51k implementation + $25k/year ongoing
4. **Key Decisions:**
   - Approve phased approach
   - Allocate team resources
   - Choose technology stack (recommend DuckDB for Phase 1)
5. **Next Steps:** Assemble team, begin Sprint 1

---

### For Data Engineers

1. **Read First:** data_warehouse_architecture.md (Sections 3-6)
2. **Understand:** etl_pipeline.md (complete document)
3. **Study:** dimensional_model.md (SQL DDL section)
4. **Key Tasks:**
   - Set up development environment (Python, DuckDB, dbt)
   - Implement Extract-Load pipeline (Python scripts provided)
   - Build staging layer (dbt models)
   - Build core dimensional model
5. **Timeline:** Weeks 1-6 (Phase 1 MVP)

**Development Environment:**
```bash
# Prerequisites
Python 3.10+, Git, 8GB RAM, 10GB disk

# Setup
git clone <repo>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd olist_dw_dbt && dbt deps
dbt debug
```

---

### For Analytics Engineers

1. **Read First:** dimensional_model.md (Star schema, business logic)
2. **Understand:** etl_pipeline.md (dbt transformation layer)
3. **Review:** implementation_plan.md (Phase 2 data marts)
4. **Key Tasks:**
   - Build dbt models for staging, core, and marts
   - Write dbt tests for data quality
   - Create data marts for each business domain
   - Build Marimo dashboards for visualization
5. **Timeline:** Weeks 3-12 (Phases 1-2)

**dbt Project Structure:**
```
olist_dw_dbt/
├── models/
│   ├── staging/      # Clean source data
│   ├── intermediate/ # Join and enrich
│   ├── core/         # Dimensions & facts
│   └── marts/        # Business-specific views
├── tests/            # Custom data quality tests
└── macros/           # Reusable SQL functions
```

---

### For Business Stakeholders

1. **Read First:** data_warehouse_architecture.md (Executive Summary, Business Context)
2. **Understand:** What questions can be answered (100 business questions in business_questions.md)
3. **Review:** implementation_plan.md (Phase 1 deliverables)
4. **Key Benefits:**
   - Answer all 100 business questions with data
   - Daily-refreshed dashboards (GMV, revenue growth, customer metrics)
   - Self-service analytics capability
   - Predictive insights (churn, demand forecasting)
5. **Timeline:** 6 weeks to MVP, 12 weeks to full platform

**What You'll Get:**
- **Week 6:** Executive dashboard (Tier 1 questions)
- **Week 12:** 6 interactive dashboards covering all business domains
- **Week 16:** Predictive analytics and ML models

---

## Key Architectural Decisions

### Technology Stack (Recommended)

**Phase 1 MVP:**
- **Database:** DuckDB (embedded, zero infrastructure cost)
- **Transformations:** dbt-core with dbt-duckdb adapter
- **Orchestration:** Python scripts (manual for MVP)
- **Visualization:** Marimo notebooks + Plotly
- **Cost:** $0 infrastructure, ~$18k labor

**Phase 2 Production (Optional):**
- **Database:** PostgreSQL (multi-user, cloud-hosted)
- **Transformations:** dbt-core with dbt-postgres adapter (same code)
- **Orchestration:** Dagster or Apache Airflow
- **Visualization:** Metabase or Apache Superset
- **Cost:** $200-400/month infrastructure, ~$20k labor

**Why This Approach:**
- Start with zero infrastructure cost (DuckDB)
- Validate business logic before scaling
- dbt code is portable between DuckDB and PostgreSQL
- Pay for infrastructure only when multi-user access needed

---

### Data Modeling Approach

**Star Schema (Kimball Methodology):**
- Simple, understandable by business users
- Optimized for analytical queries (aggregations, joins)
- Standard pattern for BI tools
- 6 dimensions + 4 facts = complete business model

**Layers:**
1. **Raw/Staging:** Exact copy of source CSVs
2. **Core:** Clean, conformed dimensions and granular facts
3. **Mart:** Pre-aggregated, denormalized for dashboards

**Why Star Schema:**
- Proven approach for analytics (30+ years)
- Easier to query than normalized schemas
- Better performance for aggregations
- Flexible for adding new metrics

---

### ELT vs ETL

**Chosen Approach: ELT (Extract-Load-Transform)**

**Pipeline Flow:**
```
CSV Files → DuckDB (raw) → dbt (transform) → DuckDB (core/mart) → Dashboards
```

**Why ELT:**
- Preserve raw data for audit and reprocessing
- Leverage DuckDB's analytical engine (faster than Python)
- SQL-based transformations (dbt) are testable and maintainable
- Built-in lineage tracking and documentation

---

## Business Questions Coverage

The data warehouse will answer **100 business questions** across 10 categories:

| Category | Questions | Example Questions |
|----------|-----------|-------------------|
| Strategic & Executive | 10 | Revenue growth, GMV, customer acquisition |
| Revenue & Monetization | 10 | Pricing, take rate, revenue concentration |
| Operations & Logistics | 10 | Delivery performance, fulfillment cycle |
| Customer Experience | 10 | NPS, repeat rate, retention, churn |
| Product & Catalog | 10 | Top products, category trends, catalog health |
| Seller Performance | 10 | Top sellers, performance distribution, health |
| Geographic Analysis | 10 | Revenue by region, market penetration |
| Marketing & Acquisition | 10 | Cohort analysis, campaign planning |
| Risk & Fraud | 10 | Cancellations, payment failures, fraud patterns |
| Predictive Analytics | 10 | Demand forecasting, churn prediction, LTV |

**Priority Tiers:**
- **Tier 1 (7 questions):** Weekly executive review - delivered in Phase 1
- **Tier 2 (25 questions):** Monthly business review - delivered in Phase 2
- **Tier 3 (18 questions):** Quarterly strategic planning - delivered in Phase 2
- **Tier 4 (50 questions):** Ad-hoc analysis - delivered in Phase 3

---

## Success Metrics

### Technical KPIs

| Metric | Target | Phase |
|--------|--------|-------|
| Pipeline Success Rate | > 95% | Phase 2 |
| Query Performance | < 5 sec (90% of queries) | Phase 1 |
| Data Freshness | < 24 hours | Phase 2 |
| Test Coverage | 100% core tables | Phase 1 |
| Data Quality Score | > 98% | Phase 2 |

### Business KPIs

| Metric | Target | Phase |
|--------|--------|-------|
| Business Questions Answered | 100/100 | Phase 2 |
| Dashboard Adoption | > 80% target users | Phase 2 |
| Time to Insight | < 5 minutes | Phase 2 |
| User Satisfaction | > 4/5 stars | Phase 3 |

---

## Timeline Summary

```
Week 1-2:   Environment setup, data profiling
Week 3-4:   Extract-Load pipeline, staging layer, dimensions (part 1)
Week 5-6:   Dimensions (part 2), primary fact, executive dashboard
            → MILESTONE: Phase 1 MVP Complete

Week 7-8:   Customer and product analytics marts
Week 9-10:  Seller and operations marts
Week 11-12: Geographic mart, orchestration, incremental loads
            → MILESTONE: Phase 2 Complete (All Marts)

Week 13-14: Predictive analytics (churn, LTV, forecasting)
Week 15-16: Production migration (optional), monitoring, documentation
            → MILESTONE: Phase 3 Complete (Production-Ready)
```

---

## Next Steps

### Immediate Actions (This Week)

1. **Review Documentation:**
   - [ ] Read all 4 planning documents
   - [ ] Discuss architecture with team
   - [ ] Get stakeholder approval on approach

2. **Make Key Decisions:**
   - [ ] Approve 3-phase implementation plan
   - [ ] Allocate team resources (1-2 FTE)
   - [ ] Choose Phase 1 technology stack (recommend DuckDB)
   - [ ] Set project start date

3. **Prepare Environment:**
   - [ ] Set up Git repository
   - [ ] Provision development machines
   - [ ] Install required software (Python, dbt)
   - [ ] Create project Slack/Teams channel

### Week 1 (Sprint 1 Start)

1. **Day 1-2: Environment Setup**
   - Clone Git repository
   - Install Python, DuckDB, dbt
   - Configure dbt project
   - Test connections

2. **Day 3-5: Data Profiling**
   - Run data profiling scripts on CSVs
   - Document data quality issues
   - Finalize dimensional model
   - Review with stakeholders

---

## Questions & Support

### Frequently Asked Questions

**Q: Why DuckDB instead of PostgreSQL from the start?**
A: DuckDB requires zero infrastructure setup and cost, perfect for MVP. Once we validate the business logic and need multi-user access, we can migrate to PostgreSQL using the same dbt code (minimal changes).

**Q: How long until we see value?**
A: Week 6 delivers an executive dashboard answering the top 7 business questions. Full analytics platform is ready by Week 12.

**Q: What if requirements change?**
A: We use 2-week sprints with weekly demos. Stakeholders can provide feedback and adjust priorities between sprints. Phase 1 scope is locked, but Phases 2-3 are flexible.

**Q: Can we handle real-time data?**
A: Phase 1-2 focus on batch processing (daily refresh). Phase 3 can add streaming for real-time use cases if needed.

**Q: What about data security?**
A: Phase 1 (DuckDB) is single-user. Phase 2 (PostgreSQL) adds role-based access control, SSL encryption, and audit logging.

---

### Contact Information

**Project Documentation:** `/home/dhafin/Documents/Projects/EDA/planning/`

**Source Data Location:** `/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/`

**Git Repository:** (To be created)

**Questions?** Create an issue in the project repository or contact the data team.

---

## Document Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-11-08 | 1.0 | Data Architecture Team | Initial planning documentation created |

---

**Last Updated:** 2025-11-08
**Status:** Ready for Review and Approval
