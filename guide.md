# Data Analysis Agents Guide
## Marimo + DuckDB for Olist Dataset

This guide helps you quickly perform analysis on the Olist Brazilian E-Commerce dataset using marimo notebooks and DuckDB.

---

## 🚀 Quick Setup

### Environment Setup
```bash
# Create uv environment (already done)
uv venv .venv

# Install dependencies
uv pip install marimo duckdb pandas polars matplotlib seaborn plotly
```

### Activate Environment
```bash
source .venv/bin/activate
```

---

## 📊 Dataset Location

**Path:** `/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/`

**Available Files:**
- `olist_customers_dataset.csv` - Customer information
- `olist_orders_dataset.csv` - Order details
- `olist_order_items_dataset.csv` - Items in each order
- `olist_order_payments_dataset.csv` - Payment information
- `olist_order_reviews_dataset.csv` - Customer reviews
- `olist_products_dataset.csv` - Product catalog
- `olist_sellers_dataset.csv` - Seller information
- `olist_geolocation_dataset.csv` - Brazilian zip code coordinates
- `product_category_name_translation.csv` - Category translations PT->EN

---

## 🎯 Creating Analysis Notebooks

### Method 1: Create New Marimo Notebook
```bash
marimo edit analysis_name.py
```

### Method 2: Use Template Below

Create a new file `template_analysis.py`:

```python
import marimo

__generated_with = "0.9.0"
app = marimo.App()


@app.cell
def __():
    import marimo as mo
    import duckdb
    import pandas as pd
    return mo, duckdb, pd


@app.cell
def __(duckdb):
    # Initialize DuckDB connection
    con = duckdb.connect()

    # Set dataset path
    dataset_path = "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/"
    return con, dataset_path


@app.cell
def __(con, dataset_path):
    # Load all datasets into DuckDB
    con.execute(f"""
        CREATE OR REPLACE VIEW customers AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_customers_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW orders AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_orders_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW order_items AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_order_items_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW payments AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_order_payments_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW reviews AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_order_reviews_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW products AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_products_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW sellers AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_sellers_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW geolocation AS
        SELECT * FROM read_csv_auto('{dataset_path}olist_geolocation_dataset.csv')
    """)

    con.execute(f"""
        CREATE OR REPLACE VIEW category_translation AS
        SELECT * FROM read_csv_auto('{dataset_path}product_category_name_translation.csv')
    """)

    return


@app.cell
def __(mo):
    mo.md("""
    # Olist E-Commerce Analysis

    Dataset loaded successfully! Start your analysis below.
    """)
    return


@app.cell
def __(con):
    # Example: Show table schemas
    tables = con.execute("SHOW TABLES").df()
    tables
    return


@app.cell
def __(con):
    # Example query: Top 10 product categories by revenue
    query = """
    SELECT
        p.product_category_name,
        ct.product_category_name_english,
        COUNT(DISTINCT oi.order_id) as order_count,
        ROUND(SUM(oi.price), 2) as total_revenue,
        ROUND(AVG(oi.price), 2) as avg_price
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN category_translation ct ON p.product_category_name = ct.product_category_name
    GROUP BY p.product_category_name, ct.product_category_name_english
    ORDER BY total_revenue DESC
    LIMIT 10
    """

    result = con.execute(query).df()
    result
    return


if __name__ == "__main__":
    app.run()
```

Then run:
```bash
marimo edit template_analysis.py
```

---

## 💡 Common Analysis Patterns

### Pattern 1: Revenue Analysis
```python
@app.cell
def __(con):
    revenue_by_month = con.execute("""
        SELECT
            DATE_TRUNC('month', CAST(o.order_purchase_timestamp AS TIMESTAMP)) as month,
            COUNT(DISTINCT o.order_id) as orders,
            ROUND(SUM(oi.price + oi.freight_value), 2) as total_revenue,
            ROUND(AVG(oi.price), 2) as avg_order_value
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY month
        ORDER BY month
    """).df()
    return revenue_by_month
```

### Pattern 2: Customer Satisfaction
```python
@app.cell
def __(con):
    satisfaction_analysis = con.execute("""
        SELECT
            r.review_score,
            COUNT(*) as review_count,
            ROUND(AVG(CAST(o.order_delivered_customer_date AS TIMESTAMP) -
                      CAST(o.order_purchase_timestamp AS TIMESTAMP)), 2) as avg_delivery_days
        FROM reviews r
        JOIN orders o ON r.order_id = o.order_id
        WHERE o.order_delivered_customer_date IS NOT NULL
        GROUP BY r.review_score
        ORDER BY r.review_score DESC
    """).df()
    return satisfaction_analysis
```

### Pattern 3: Geographic Analysis
```python
@app.cell
def __(con):
    revenue_by_state = con.execute("""
        SELECT
            c.customer_state,
            COUNT(DISTINCT o.order_id) as orders,
            ROUND(SUM(oi.price), 2) as revenue,
            COUNT(DISTINCT c.customer_id) as customers
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state
        ORDER BY revenue DESC
    """).df()
    return revenue_by_state
```

### Pattern 4: Seller Performance
```python
@app.cell
def __(con):
    top_sellers = con.execute("""
        SELECT
            s.seller_id,
            s.seller_city,
            s.seller_state,
            COUNT(DISTINCT oi.order_id) as total_orders,
            ROUND(SUM(oi.price), 2) as total_revenue,
            ROUND(AVG(r.review_score), 2) as avg_review_score
        FROM sellers s
        JOIN order_items oi ON s.seller_id = oi.seller_id
        JOIN orders o ON oi.order_id = o.order_id
        LEFT JOIN reviews r ON o.order_id = r.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY s.seller_id, s.seller_city, s.seller_state
        HAVING COUNT(DISTINCT oi.order_id) >= 10
        ORDER BY total_revenue DESC
        LIMIT 20
    """).df()
    return top_sellers
```

---

## 🎨 Visualization Examples

### Using Plotly
```python
@app.cell
def __(revenue_by_month):
    import plotly.express as px

    fig = px.line(
        revenue_by_month,
        x='month',
        y='total_revenue',
        title='Revenue Trend Over Time',
        labels={'total_revenue': 'Revenue (R$)', 'month': 'Month'}
    )
    fig
    return
```

### Using Marimo's Built-in Charts
```python
@app.cell
def __(mo, revenue_by_state):
    mo.ui.plotly(
        revenue_by_state.head(10).plot.bar(
            x='customer_state',
            y='revenue'
        )
    )
    return
```

---

## 🔍 Quick Analysis Workflows

### Workflow 1: Executive Dashboard
1. Create `executive_dashboard.py`
2. Add cells for:
   - Revenue trends (monthly/quarterly)
   - Order volume trends
   - Customer satisfaction scores
   - Top product categories
   - Geographic performance

### Workflow 2: Delivery Performance
1. Create `delivery_analysis.py`
2. Add cells for:
   - Delivery time distribution
   - Late delivery analysis by state
   - Correlation between delivery time and reviews
   - Freight cost analysis

### Workflow 3: Customer Behavior
1. Create `customer_analysis.py`
2. Add cells for:
   - Repeat purchase rate
   - Customer cohort analysis
   - Average order value by segment
   - Payment method preferences

### Workflow 4: Product Analysis
1. Create `product_analysis.py`
2. Add cells for:
   - Best/worst selling categories
   - Price distribution by category
   - Product review analysis
   - Category growth trends

---

## 🛠️ Useful DuckDB Commands

### List All Tables
```sql
SHOW TABLES;
```

### Describe Table Schema
```sql
DESCRIBE customers;
```

### Sample Data
```sql
SELECT * FROM orders LIMIT 5;
```

### Count Rows
```sql
SELECT COUNT(*) FROM orders;
```

### Export Results to CSV
```python
con.execute("COPY (SELECT * FROM revenue_by_month) TO 'output.csv' (HEADER, DELIMITER ',')");
```

---

## 📝 Tips for Efficient Analysis

1. **Use Views**: Create reusable views for common joins
2. **Parameterize Queries**: Use marimo UI elements for interactive filters
3. **Cache Results**: Store intermediate results in DuckDB tables
4. **Incremental Development**: Build queries cell by cell
5. **Document Assumptions**: Use markdown cells to explain your logic

### Example: Interactive Filtering
```python
@app.cell
def __(mo):
    state_filter = mo.ui.dropdown(
        options=['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA'],
        value='SP',
        label='Select State'
    )
    state_filter
    return state_filter


@app.cell
def __(con, state_filter):
    filtered_data = con.execute(f"""
        SELECT * FROM customers
        WHERE customer_state = '{state_filter.value}'
    """).df()
    return filtered_data
```

---

## 🚀 Running Your Analysis

### Start Marimo Server
```bash
marimo edit your_analysis.py
```

### Run in Browser
The marimo UI will automatically open at `http://localhost:2718`

### Export as HTML
```bash
marimo export html your_analysis.py -o output.html
```

---

## 📚 Additional Resources

- **Marimo Docs**: https://docs.marimo.io
- **DuckDB Docs**: https://duckdb.org/docs/
- **Dataset Info**: `/media/dhafin/.../Olist/dataset_information.md`
- **Business Questions**: `business_questions.md` in this directory

---

## 🎯 Next Steps

1. Choose a business question from `business_questions.md`
2. Create a new marimo notebook using the template
3. Write your DuckDB queries
4. Add visualizations
5. Share insights with stakeholders

**Happy Analyzing!** 🚀
