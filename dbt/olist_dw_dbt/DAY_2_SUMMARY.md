# Day 2 Summary: Staging + Core Models Complete ✅

**Date:** 2025-11-10
**Status:** SUCCESS - Full data pipeline operational

---

## 🎉 What We Accomplished

### Data Pipeline Built (3 Layers)

#### Layer 1: Staging (9 Views)
All CSV sources successfully loaded as views in `core_staging` schema:

| Model | Purpose | Status |
|-------|---------|--------|
| `stg_orders` | Order details with delivery metrics | ✅ |
| `stg_customers` | Customer information & location | ✅ |
| `stg_order_items` | Line items with pricing calculations | ✅ |
| `stg_payments` | Payment method and installments | ✅ |
| `stg_reviews` | Customer reviews with sentiment analysis | ✅ |
| `stg_products` | Product catalog with dimensions | ✅ |
| `stg_sellers` | Seller information & location | ✅ |
| `stg_geolocation` | Zip code coordinates (deduplicated) | ✅ |
| `stg_category_translation` | PT → EN category translations | ✅ |

#### Layer 2: Intermediate (3 Ephemeral CTEs)
Reusable joins and aggregations (not materialized):

| Model | Purpose | Status |
|-------|---------|--------|
| `int_orders_enriched` | Orders + customers + reviews | ✅ |
| `int_order_items_enriched` | Items + products + sellers + categories | ✅ |
| `int_order_payments_aggregated` | Payment summaries by order | ✅ |

#### Layer 3: Core (2 Tables)
Materialized tables in `core_core` schema:

| Model | Type | Rows | Status |
|-------|------|------|--------|
| `dim_customers` | Dimension | 99,441 | ✅ |
| `fct_orders` | Fact | 99,992 | ✅ |

---

## 📊 Data Quality Metrics

### Coverage
- **Orders with payment data:** 99,988 / 99,992 (100.0%)
- **Orders with reviews:** 99,224 / 99,992 (99.2%)
- **Delivered orders:** 97,007 / 99,992 (97.0%)

### Business Metrics
- **Average order value:** R$ 160.42
- **Top state:** SP (41,964 orders, 42% of total)
- **Positive reviews:** 76,470 (77.1%)
- **Negative reviews:** 14,575 (14.7%)

### Order Status Distribution
- Delivered: 97.0%
- Shipped: 1.1%
- Canceled: 0.6%
- Unavailable: 0.6%
- Other: 0.6%

---

## 🛠️ Technical Details

### Files Created (14 total)

**Staging Layer:**
```
models/staging/
├── _sources.yml              # CSV source definitions (9 sources)
├── schema.yml                # Model docs & tests (43 tests)
├── stg_orders.sql
├── stg_customers.sql
├── stg_order_items.sql
├── stg_payments.sql
├── stg_reviews.sql
├── stg_products.sql
├── stg_sellers.sql
├── stg_geolocation.sql
└── stg_category_translation.sql
```

**Intermediate Layer:**
```
models/intermediate/
├── int_orders_enriched.sql
├── int_order_items_enriched.sql
└── int_order_payments_aggregated.sql
```

**Core Layer:**
```
models/core/
├── dimensions/
│   └── dim_customers.sql
└── facts/
    └── fct_orders.sql
```

**Tests:**
```
tests/
├── README.md                  # Test documentation
├── pipeline_validation.py     # Python validation script
└── data_quality_tests.sql     # SQL quality tests
```

### Database Schema

```
olist_analytical.duckdb
│
├── core_staging (schema)
│   ├── stg_orders (VIEW)
│   ├── stg_customers (VIEW)
│   ├── stg_order_items (VIEW)
│   ├── stg_payments (VIEW)
│   ├── stg_reviews (VIEW)
│   ├── stg_products (VIEW)
│   ├── stg_sellers (VIEW)
│   ├── stg_geolocation (VIEW)
│   └── stg_category_translation (VIEW)
│
└── core_core (schema)
    ├── dim_customers (TABLE) - 99,441 rows
    └── fct_orders (TABLE) - 99,992 rows
```

---

## 🔧 Issues Resolved

### 1. CSV Header Detection
**Problem:** DuckDB `read_csv_auto()` not detecting column names
**Solution:** Changed to `read_csv(..., header=true, auto_detect=true)`

### 2. Function Compatibility
**Problem:** DuckDB doesn't support `INITCAP()` function
**Solution:** Used `REPLACE()` to format category names

### 3. Protobuf Warning
**Problem:** dbt throwing protobuf error during reporting
**Solution:** Error is cosmetic, models run successfully. Can be ignored.

---

## 🎯 Key Features Implemented

### In Staging Models:
- ✅ Timestamp conversions (VARCHAR → TIMESTAMP)
- ✅ Data type casting (proper DECIMAL for money)
- ✅ Calculated fields (delivery metrics, volumes, etc.)
- ✅ Data quality filters (NOT NULL checks)
- ✅ State standardization (UPPER, TRIM)
- ✅ Geolocation deduplication (averaging)

### In Intermediate Models:
- ✅ Customer enrichment (location data)
- ✅ Review integration
- ✅ Product categorization (PT → EN)
- ✅ Seller information joins
- ✅ Payment aggregations
- ✅ Installment tracking

### In Core Models:
- ✅ Customer lifetime metrics
- ✅ Customer segmentation
- ✅ Recency calculations
- ✅ Order-level facts
- ✅ Payment reconciliation
- ✅ Delivery performance tracking
- ✅ Review sentiment flags

---

## 📈 Performance

### dbt Run Times
- Staging models (9): ~0.5s each (parallel execution)
- Core models (2): ~2.8s each (sequential, waiting for staging)
- **Total pipeline:** ~4 seconds

### Query Performance
- Individual table counts: < 100ms
- Complex aggregations: < 500ms
- Full validation report: < 2s

---

## ✅ Validation

### Run Pipeline Validation:
```bash
cd /home/dhafin/Documents/Projects/EDA
source .venv/bin/activate
python dbt/olist_dw_dbt/tests/pipeline_validation.py
```

### Run dbt Tests:
```bash
cd dbt/olist_dw_dbt
dbt test
```

### Run Specific Models:
```bash
# Run just staging
dbt run --select staging

# Run core models
dbt run --select +fct_orders +dim_customers

# Run everything
dbt run
```

---

## 🚀 Next Steps (Day 3)

### Remaining Dimensions (4)
- [ ] `dim_products` - Product catalog dimension
- [ ] `dim_sellers` - Seller dimension
- [ ] `dim_date` - Date dimension for time intelligence
- [ ] `dim_locations` - Geographic dimension

### Remaining Facts (3)
- [ ] `fct_order_items` - Order line item fact
- [ ] `fct_reviews` - Review fact
- [ ] `fct_seller_performance` - Seller metrics fact

### Mart Layer (6)
- [ ] `mart_executive_dashboard` - KPI summary
- [ ] `mart_customer_cohort_analysis` - Customer segments
- [ ] `mart_product_performance` - Product metrics
- [ ] `mart_seller_scorecard` - Seller KPIs
- [ ] `mart_delivery_analysis` - Logistics metrics
- [ ] `mart_revenue_analysis` - Revenue breakdown

---

## 📚 Resources

- **dbt Project:** `/home/dhafin/Documents/Projects/EDA/dbt/olist_dw_dbt/`
- **Database:** `/home/dhafin/Documents/Projects/EDA/data/duckdb/olist_analytical.duckdb`
- **CSV Source:** Set in `dbt_project.yml` variable `csv_source_path`
- **Progress Doc:** `/home/dhafin/Documents/Projects/EDA/OPTION_B_PROGRESS.md`

---

## 🎓 Lessons Learned

1. **DuckDB CSV Reading:** Use explicit `header=true` parameter for reliability
2. **Function Compatibility:** Always check DuckDB function support vs PostgreSQL/other DBs
3. **Ephemeral Models:** Great for reusable CTEs without extra storage
4. **Testing Strategy:** Validate early and often with sample queries
5. **Data Quality:** 43 built-in tests catching issues before core models

---

**Summary:** Successfully built a complete 3-layer dbt pipeline (staging → intermediate → core) with 14 models loading 99K+ orders and customers. All data quality checks passing. Ready to expand to full star schema with dimension/fact tables and mart layer.

✅ **Day 2: COMPLETE**
