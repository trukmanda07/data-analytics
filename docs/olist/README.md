# Olist E-Commerce Analytics Documentation

**Project:** Olist Brazilian E-Commerce Data Warehouse & Analytics
**Last Updated:** 2025-11-11
**Status:** ✅ Complete - Production Ready

---

## 📚 Documentation Index

### 1. [Star Schema Documentation](star_schema.md)
**Purpose:** Complete data warehouse schema reference with PlantUML diagrams

**Contents:**
- Star schema design (6 dimensions + 4 facts)
- Mart layer pre-aggregated tables
- Data flow architecture
- Grain definitions and design decisions
- Schema statistics

**Use When:** Understanding the data model, planning queries, onboarding new team members

---

### 2. [Available Analysis Capabilities](available_analysis_v2.md)
**Purpose:** Comprehensive guide to what analysis can be performed

**Contents:**
- 10 analysis domains (Executive, Customer, Product, Seller, etc.)
- 300+ specific analysis capabilities
- Recommended notebooks (11 total)
- Advanced analytics opportunities
- Data limitations and gaps

**Use When:** Planning new analysis, understanding data capabilities, prioritizing analytics work

---

### 3. [Notebook Comparison](notebook_comparison.md)
**Purpose:** Gap analysis between existing and recommended notebooks

**Contents:**
- Current vs recommended notebook comparison
- Architecture comparison (DuckDB+DBT vs Direct CSV)
- Coverage analysis (73% complete)
- Missing notebooks identified (3 gaps)
- Action items and recommendations

**Use When:** Assessing analytics maturity, planning new notebooks, understanding architecture

---

### 4. [Business Questions](business_questions.md)
**Purpose:** Original business questions driving the analytics

**Contents:**
- Revenue and growth questions
- Customer behavior questions
- Product and seller performance
- Operational metrics

**Use When:** Aligning analytics with business needs, validating analysis scope

---

## 🎯 Quick Start Guide

### For Analysts & Data Scientists

**1. Explore the Data Model**
```bash
# Read the star schema documentation
cat docs/olist/star_schema.md
```

**2. Check Available Analysis**
```bash
# See what's possible with current data
cat docs/olist/available_analysis_v2.md
```

**3. Run Existing Notebooks**
```bash
source .venv/bin/activate
marimo edit marimo_notebooks/olist/executive_dashboard.py
```

### For Business Users

**1. Review Business Questions**
- See `business_questions.md` for original requirements

**2. Access Pre-Built Dashboards**
```bash
# 11 ready-to-use Marimo notebooks covering:
# - Executive KPIs
# - Customer RFM segmentation
# - Product performance
# - Seller scorecards
# - Revenue & financial analysis
# - And more...
```

**3. Request New Analysis**
- Check `available_analysis_v2.md` to see if capability exists
- If missing, check `notebook_comparison.md` for gaps

---

## 📊 Available Notebooks (11 Total)

### ✅ Tier 1: Executive Priority (Daily/Weekly)

| Notebook | File | Data Source | Status |
|----------|------|-------------|--------|
| **Executive Dashboard** | `executive_dashboard.py` | `fct_orders`, `dim_customers` | ✅ Built |
| **Customer Satisfaction** | `customer_satisfaction_analysis.py` | `fct_orders`, `fct_reviews` | ✅ Built |
| **Revenue & Financial** | `revenue_financial_analysis.py` | `fct_orders`, `fct_payments` | ✅ Built |

### ✅ Tier 2: Business Intelligence (Monthly)

| Notebook | File | Data Source | Status |
|----------|------|-------------|--------|
| **Customer RFM Dashboard** | `customer_rfm_dashboard.py` | `mart_customer_analytics` | ✅ Built ⭐ NEW |
| **Product Performance** | `product_performance_analysis.py` | `mart_product_performance` | ✅ Built ⭐ NEW |
| **Seller Scorecard** | `seller_scorecard_analysis.py` | `mart_seller_scorecard` | ✅ Built ⭐ NEW |
| **Delivery Operations** | `delivery_operations_analysis.py` | `fct_orders`, `dim_geography` | ✅ Built |
| **Order Risk Analysis** | `order_risk_cancellation_analysis.py` | `fct_orders` | ✅ Built (Bonus) |

### ✅ Tier 3: Strategic Planning (Quarterly)

| Notebook | File | Data Source | Status |
|----------|------|-------------|--------|
| **Geographic Market** | `geographic_market_analysis.py` | `fct_orders`, `dim_geography` | ✅ Built |
| **Customer Cohorts** | `customer_retention_cohort_analysis.py` | `fct_orders`, `dim_customers` | ✅ Built |
| **Marketing Timing** | `marketing_sales_timing_analysis.py` | `fct_orders`, `dim_date` | ✅ Built |

**Coverage:** 100% of recommended notebooks ✅

---

## 🏗️ Data Architecture

### Architecture Stack

```
Raw CSV Files (9 files)
    ↓
DBT Transformation Pipeline
    ├── Staging Layer (9 models) - Data cleaning
    ├── Intermediate Layer (3 models) - Business logic
    ├── Core Layer - Star Schema
    │   ├── Dimensions (6 models) - Master data
    │   └── Facts (4 models) - Transactions
    └── Marts Layer (4 models) - Pre-aggregated views
    ↓
DuckDB Analytical Database (olist_analytical.duckdb)
    ↓
Marimo Notebooks (11 notebooks)
```

### Key Design Principles

**1. Star Schema**
- Simple joins for analysts
- Fast aggregations
- Business-aligned structure

**2. Layered Transformation**
- Staging: Clean & standardize
- Intermediate: Enrich & join
- Core: Dimensions & facts
- Marts: Business views

**3. Pre-Aggregated Marts**
- Faster query performance
- Consistent business logic
- User-friendly column names

---

## 📈 Data Coverage

### Dataset Statistics

| Metric | Value | Period |
|--------|-------|--------|
| **Total Orders** | 99,441 | 2016-09 to 2018-08 |
| **Total Customers** | 99,441 (96,096 unique) | 24 months |
| **Total Products** | 32,951 | - |
| **Total Sellers** | 3,095 | - |
| **Order Items** | 112,650 | - |
| **Reviews** | 99,224 | - |

### Analysis Domains Covered

✅ **Executive & Strategic** - Revenue, growth, KPIs
✅ **Customer Analytics** - RFM, segmentation, lifecycle
✅ **Product & Category** - Performance, reviews, attributes
✅ **Seller Performance** - Scorecards, health, activity
✅ **Delivery & Logistics** - On-time rates, freight costs
✅ **Payment & Financial** - Methods, installments, risk
✅ **Customer Satisfaction** - Reviews, NPS proxy, drivers
✅ **Geographic Markets** - Regional distribution, opportunities
✅ **Time-Series** - Seasonality, trends, patterns
✅ **Risk & Operations** - Cancellations, fulfillment

---

## 🎨 Visualization Tools

### Marimo Notebooks
- **Interactive dashboards** with filters and drill-downs
- **Plotly visualizations** for rich, interactive charts
- **Reactive UI** - Auto-update on filter changes
- **Export capabilities** - HTML, PDF for sharing

### Available Chart Types
- Line charts (trends over time)
- Bar charts (comparisons)
- Pie/donut charts (composition)
- Scatter plots (correlations)
- Heatmaps (geographic, temporal)
- Box plots (distributions)
- Sunburst charts (hierarchies)

---

## 💡 Best Practices

### For Querying

**1. Use Marts for Standard Reports**
```sql
-- Fast, pre-aggregated
SELECT * FROM marts_executive.mart_executive_dashboard
WHERE date_day >= '2018-01-01'
```

**2. Use Facts + Dimensions for Custom Analysis**
```sql
-- Full flexibility
SELECT
    d.product_category_name_english,
    SUM(f.total_order_value) as revenue
FROM core_core.fct_orders f
JOIN core_core.fct_order_items oi ON f.order_id = oi.order_id
JOIN core_core.dim_products d ON oi.product_id = d.product_id
WHERE f.is_delivered = true
GROUP BY 1
```

**3. Always Filter Delivered Orders for Revenue**
```sql
WHERE is_delivered = true  -- Critical!
```

### For Analysis

**1. Start with Marts** - Fastest path to insights
**2. Drill into Facts** - When you need custom cuts
**3. Reference Documentation** - Check star_schema.md for column details
**4. Validate Assumptions** - Check available_analysis_v2.md for data limits

---

## 🚀 Getting Started

### Prerequisites
```bash
# Python environment
source .venv/bin/activate

# Environment variables
# .env file should have:
# DUCKDB_DIR=/path/to/duckdb/databases
```

### Running Notebooks

**Option 1: Interactive Mode**
```bash
marimo edit marimo_notebooks/olist/executive_dashboard.py
```

**Option 2: View Mode (Read-only)**
```bash
marimo run marimo_notebooks/olist/executive_dashboard.py
```

**Option 3: Export HTML**
```bash
marimo export html marimo_notebooks/olist/executive_dashboard.py -o dashboard.html
```

### Creating New Notebooks

**1. Choose Data Source**
- Use marts for standard analysis
- Use facts + dimensions for custom analysis

**2. Follow Existing Patterns**
```python
# Standard setup
from pathlib import Path
from dotenv import load_dotenv
import duckdb

env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)
db_path = os.path.join(os.getenv('DUCKDB_DIR'), 'olist_analytical.duckdb')
con = duckdb.connect(database=db_path, read_only=True)
```

**3. Add Filters and Interactivity**
```python
import marimo as mo

date_range = mo.ui.date_range(
    start="2016-09-01",
    stop="2018-08-31"
)
```

---

## 📝 Maintenance & Updates

### DBT Refresh Schedule
- **Staging/Intermediate:** On-demand (during development)
- **Core (Facts/Dims):** Daily batch (production)
- **Marts:** Daily batch (production)

### Documentation Updates
When adding new models or notebooks:
1. Update `star_schema.md` with new tables
2. Update `available_analysis_v2.md` with new capabilities
3. Update `notebook_comparison.md` if relevant
4. Update this README with new notebook entries

---

## 🔗 Related Resources

### Internal Documentation
- `dbt/olist_dw_dbt/models/` - DBT model definitions
- `dbt/olist_dw_dbt/README.md` - DBT project docs
- `.env.example` - Environment setup guide

### External References
- [Olist Dataset on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [Marimo Documentation](https://docs.marimo.io/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [DBT Documentation](https://docs.getdbt.com/)

---

## 🎯 Current Status

### ✅ Completed
- [x] Star schema design and implementation
- [x] 9 staging models
- [x] 3 intermediate models
- [x] 6 dimension tables
- [x] 4 fact tables
- [x] 4 mart tables
- [x] 11 Marimo notebooks
- [x] Complete documentation

### 🎉 Achievements
- **100% notebook coverage** of recommended analysis
- **Production-ready** DBT + DuckDB architecture
- **Comprehensive documentation** with diagrams
- **300+ analysis capabilities** documented

### 📊 Analytics Maturity: Level 4 (Advanced)
- ✅ Descriptive Analytics (What happened?)
- ✅ Diagnostic Analytics (Why did it happen?)
- ✅ Predictive Analytics (What will happen?) - Ready for modeling
- 🔄 Prescriptive Analytics (What should we do?) - In progress

---

## 📧 Contact & Support

For questions, issues, or suggestions:
1. Check this documentation first
2. Review `available_analysis_v2.md` for capabilities
3. Check `star_schema.md` for data model questions
4. Consult `notebook_comparison.md` for architecture questions

---

**Last Updated:** 2025-11-11
**Version:** 1.0
**Status:** Production Ready ✅
