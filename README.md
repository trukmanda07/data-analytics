# Olist E-Commerce Analysis Project

Comprehensive analytics platform for the Olist Brazilian E-Commerce dataset using marimo notebooks and dbt data warehouse.

## 🚀 Quick Start

### Option 1: Interactive Analysis (Marimo Notebooks)
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Test the setup (optional)
python olist_utils.py

# 3. Browse available notebooks
ls marimo_notebooks/olist/

# 4. Run a notebook (example: executive dashboard)
marimo edit marimo_notebooks/olist/executive_dashboard.py
```

### Option 2: Data Warehouse (dbt)
```bash
# 1. Navigate to dbt project
cd dbt/olist_dw_dbt

# 2. Install dependencies
dbt deps

# 3. Build the data warehouse
dbt build

# 4. View documentation
dbt docs generate && dbt docs serve
```

### Option 3: Column Lineage (dbt-colibri)
```bash
# 1. Navigate to dbt project
cd dbt/olist_dw_dbt

# 2. Generate dbt artifacts
dbt compile && dbt docs generate

# 3. Generate column lineage report
colibri generate

# 4. View lineage dashboard
xdg-open dist/index.html  # Linux
# or open dist/index.html  # macOS
```

## 📁 Project Structure

```
EDA/
├── marimo_notebooks/
│   └── olist/                # 11 interactive analysis notebooks
│       ├── executive_dashboard.py
│       ├── revenue_financial_analysis.py
│       ├── customer_retention_cohort_analysis.py
│       ├── customer_rfm_dashboard.py
│       ├── customer_satisfaction_analysis.py
│       ├── product_performance_analysis.py
│       ├── seller_scorecard_analysis.py
│       ├── delivery_operations_analysis.py
│       ├── geographic_market_analysis.py
│       ├── marketing_sales_timing_analysis.py
│       └── order_risk_cancellation_analysis.py
│
├── dbt/
│   └── olist_dw_dbt/         # dbt data warehouse
│       ├── models/
│       │   ├── staging/      # 9 staging models (CSV ingestion)
│       │   ├── intermediate/ # 3 enriched models
│       │   ├── core/         # Star schema (dimensions + facts)
│       │   │   ├── dimensions/  # 6 dimension tables
│       │   │   └── facts/       # 4 fact tables
│       │   └── marts/        # 4 business-specific marts
│       └── tests/            # Data quality tests
│
├── .env                      # Environment configuration
├── requirements.txt          # Python dependencies
├── olist_utils.py           # Reusable data loading utilities
├── CLAUDE.md                # Instructions for Claude Code agent
└── README.md                # This file
```

## 📊 Dataset Information

**Location:** `/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/`

**Period:** 2016-2018

**Tables Available:**
- `customers` (99.4k unique customers)
- `orders` (99.4k orders)
- `order_items` (112k line items)
- `payments` (103k payment records)
- `reviews` (99.2k reviews)
- `products` (32.9k products)
- `sellers` (3.1k sellers)
- `geolocation` (1M zip code entries)
- `category_translation` (71 categories)

## 📓 Available Marimo Notebooks

### Executive & Revenue
- **executive_dashboard.py** - High-level KPIs and business metrics
- **revenue_financial_analysis.py** - Revenue trends, growth, and forecasting

### Customer Analytics
- **customer_retention_cohort_analysis.py** - Cohort retention and LTV analysis
- **customer_rfm_dashboard.py** - RFM segmentation and customer value
- **customer_satisfaction_analysis.py** - Review scores and NPS analysis

### Product & Seller
- **product_performance_analysis.py** - Top products, categories, and pricing
- **seller_scorecard_analysis.py** - Seller performance and ratings

### Operations & Risk
- **delivery_operations_analysis.py** - Delivery times, delays, and logistics
- **order_risk_cancellation_analysis.py** - Order cancellations and risk factors

### Market Analysis
- **geographic_market_analysis.py** - Regional sales and market penetration
- **marketing_sales_timing_analysis.py** - Seasonal patterns and timing insights

## 🏗️ dbt Data Warehouse

### Staging Layer (9 models)
Raw CSV ingestion with basic cleaning:
- `stg_customers`, `stg_orders`, `stg_order_items`, `stg_payments`
- `stg_reviews`, `stg_products`, `stg_sellers`, `stg_geolocation`
- `stg_category_translation`

### Intermediate Layer (3 models)
Enriched datasets for core model consumption:
- `int_orders_enriched` - Orders with customer and payment data
- `int_order_items_enriched` - Order items with product and seller data
- `int_order_payments_aggregated` - Aggregated payment information

### Core Layer - Star Schema
**Dimensions (6 models):**
- `dim_customers` - Customer dimension with demographics
- `dim_products` - Product catalog with categories
- `dim_sellers` - Seller information and locations
- `dim_category` - Product category translations
- `dim_geography` - Geographic data (zip codes, coordinates)
- `dim_date` - Date dimension for time-based analysis

**Facts (4 models):**
- `fct_orders` - Order-level facts (dates, status, totals)
- `fct_order_items` - Line item-level facts (products, prices, freight)
- `fct_payments` - Payment transactions (methods, installments)
- `fct_reviews` - Customer review facts (scores, comments)

### Marts Layer (4 models)
Pre-aggregated business-specific datasets:
- `mart_executive_dashboard` - Executive KPIs and metrics
- `mart_customer_analytics` - Customer behavior and segmentation
- `mart_product_performance` - Product and category analytics
- `mart_seller_scorecard` - Seller performance metrics

## 🎯 Usage Guide

### Working with Marimo Notebooks

**Create a New Notebook:**

```python
import marimo

app = marimo.App(width="medium")

@app.cell
def __():
    import marimo as mo
    import plotly.express as px
    return mo, px

@app.cell
def __():
    import sys
    sys.path.append('/home/dhafin/Documents/Projects/EDA')
    from olist_utils import marimo_setup

    # This loads all tables + creates common views
    con, dataset_path = marimo_setup()
    return con, dataset_path

@app.cell
def __(con):
    # Start analyzing!
    result = con.execute("""
        SELECT customer_state, COUNT(*) as orders
        FROM customers
        GROUP BY customer_state
        ORDER BY orders DESC
        LIMIT 10
    """).df()
    result
    return result,

if __name__ == "__main__":
    app.run()
```

**Manual Setup (Advanced):**

```python
from olist_utils import setup_duckdb, load_all_tables, create_common_views

con = setup_duckdb()
load_all_tables(con)
create_common_views(con)
```

### Working with dbt Models

**Build All Models:**
```bash
cd dbt/olist_dw_dbt
dbt build
```

**Build Specific Layers:**
```bash
dbt build --select staging        # Build staging layer only
dbt build --select core           # Build core (dimensions + facts)
dbt build --select marts          # Build marts only
```

**Run Tests:**
```bash
dbt test                          # Run all tests
dbt test --select staging         # Test staging models
```

**Generate Documentation:**
```bash
dbt docs generate
dbt docs serve
```

**Query dbt Models:**
```python
import duckdb

con = duckdb.connect('dbt/olist_dw_dbt/olist.duckdb')

# Query fact tables
revenue = con.execute("""
    SELECT
        d.date_actual,
        SUM(f.price + f.freight_value) as revenue
    FROM core.fct_order_items f
    JOIN core.dim_date d ON f.order_purchase_date = d.date_actual
    GROUP BY d.date_actual
    ORDER BY d.date_actual
""").df()

# Query marts
dashboard_data = con.execute("""
    SELECT * FROM mart.mart_executive_dashboard
""").df()
```

## 💡 Common Queries

### Revenue by Month
```sql
SELECT
    DATE_TRUNC('month', CAST(order_purchase_timestamp AS TIMESTAMP)) as month,
    ROUND(SUM(price + freight_value), 2) as revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE order_status = 'delivered'
GROUP BY month
ORDER BY month
```

### Top Product Categories
```sql
SELECT
    product_category_name_english as category,
    COUNT(DISTINCT order_id) as orders,
    ROUND(SUM(price), 2) as revenue
FROM order_items_complete
WHERE product_category_name_english IS NOT NULL
GROUP BY category
ORDER BY revenue DESC
LIMIT 10
```

### Customer Satisfaction
```sql
SELECT
    review_score,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM reviews
GROUP BY review_score
ORDER BY review_score DESC
```

## 🛠️ Utility Functions

### Available in `olist_utils.py`:

- **`marimo_setup()`** - One-line complete setup for notebooks
- **`setup_duckdb()`** - Create DuckDB connection
- **`load_all_tables(con)`** - Load all CSV files as views
- **`create_common_views(con)`** - Create pre-joined views
- **`get_table_info(con, 'table_name')`** - Inspect table schema
- **`list_all_tables(con)`** - Show all available tables

## 🎨 Architecture Comparison

### Marimo Notebooks (Ad-hoc Analysis)
**Best for:**
- Quick exploratory analysis
- Interactive dashboards
- Prototyping new insights
- Sharing visualizations

**Pros:**
- Instant results
- Interactive UI elements
- No build step required
- Easy to share (.py or HTML export)

### dbt Data Warehouse (Production Analytics)
**Best for:**
- Consistent metrics definitions
- Multi-user environments
- Scheduled data pipelines
- Data quality validation

**Pros:**
- Version-controlled transformations
- Built-in testing framework
- Auto-generated documentation
- Incremental processing
- Lineage tracking

**When to use both:**
- Use **dbt** to build the star schema and marts
- Use **Marimo** to query dbt models for interactive analysis
- Example: `SELECT * FROM mart.mart_executive_dashboard`

### dbt-colibri (Column Lineage)
**Best for:**
- Understanding data flow at column level
- Impact analysis before making changes
- Data quality investigations
- Documentation and onboarding

**Pros:**
- Visual column-level lineage tracking
- Fast generation from existing dbt artifacts
- Self-hosted with no external dependencies
- Interactive HTML dashboard

**When to use:**
- Trace how specific columns flow through transformations
- Identify downstream impacts of schema changes
- Debug data quality issues
- Document complex data flows

**Learn more:** See `/docs/dbt_colibri_integration.md` for detailed usage guide

## 🔧 Configuration

### Marimo Setup
Edit `.env` to change:
- `DATASET_PATH` - Dataset location
- `DUCKDB_MEMORY_LIMIT` - Memory allocation
- `DUCKDB_THREADS` - CPU threads

### dbt Setup
Edit `dbt/olist_dw_dbt/dbt_project.yml`:
- `csv_source_path` - Path to Olist CSV files
- `start_date` / `end_date` - Analysis date range
- Model-specific configurations

## 📚 Resources

- **Marimo:** https://docs.marimo.io
- **dbt:** https://docs.getdbt.com
- **dbt-colibri:** https://github.com/b-ned/dbt-colibri
- **DuckDB:** https://duckdb.org/docs/
- **Plotly:** https://plotly.com/python/

## 🐛 Troubleshooting

### Marimo Issues

**"Dataset path not found"**
- Check external drive is mounted
- Verify path in `.env` or `olist_utils.py`
- Update `DATASET_PATH` environment variable

**"Module not found"**
- Activate environment: `source .venv/bin/activate`
- Reinstall: `uv pip install -r requirements.txt`

**"Table does not exist"**
- Call `marimo_setup()` in your notebook
- Verify with `list_all_tables(con)`

### dbt Issues

**"CSV file not found"**
- Update `csv_source_path` in `dbt_project.yml`
- Ensure all 9 CSV files exist in the path

**"Models failed to build"**
- Run `dbt debug` to check configuration
- Check `dbt/olist_dw_dbt/logs/dbt.log`

**"Tests failing"**
- Review test output: `dbt test --store-failures`
- Check `test_failures` schema in database

## ✅ Verification

### Verify Marimo Setup:
```bash
python olist_utils.py
```

Expected output:
```
✓ DuckDB connection established
✓ Loaded 9/9 tables into DuckDB
✓ Created 3 common views
✅ Setup complete! Ready for analysis.
```

### Verify dbt Setup:
```bash
cd dbt/olist_dw_dbt
dbt debug
dbt build --select staging
```

## 🎓 Getting Started

### For Quick Analysis:
1. Browse available notebooks in `marimo_notebooks/olist/`
2. Run one: `marimo edit marimo_notebooks/olist/executive_dashboard.py`
3. Explore and modify queries
4. Export to HTML for sharing

### For Production Warehouse:
1. Configure CSV path in `dbt_project.yml`
2. Build models: `dbt build`
3. Run tests: `dbt test`
4. View docs: `dbt docs serve`
5. Query marts from notebooks or BI tools

### For Advanced Users:
- Build custom dbt models for specific metrics
- Create marimo notebooks that query dbt marts
- Combine both: dbt for transformations, marimo for exploration
- Schedule dbt runs and refresh marimo dashboards

### For Column Lineage Analysis:
1. Navigate to dbt project: `cd dbt/olist_dw_dbt`
2. Generate artifacts: `dbt compile && dbt docs generate`
3. Run Colibri: `colibri generate`
4. Open dashboard: `xdg-open dist/index.html`
5. Explore column-level data flow
6. See `/docs/dbt_colibri_integration.md` for detailed guide

---

**Happy Analyzing!** 🚀

**Project Structure:** 11 marimo notebooks + complete dbt data warehouse + column lineage
**Dataset:** 100k orders, 32k products, 3k sellers (2016-2018)
**Tools:** Marimo + dbt + dbt-colibri + DuckDB + Plotly
