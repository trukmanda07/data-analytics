import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    return mo, pd, px, go


@app.cell
def __(mo):
    mo.md(
        """
    # Olist E-Commerce Analysis - Example Notebook

    **Business Question:** What are the revenue trends and top-performing product categories?

    **Objective:** Demonstrate how to use the `olist_utils` module for quick analysis setup.
    """
    )
    return


@app.cell
def __():
    # Import the Olist utilities module
    import sys

    sys.path.append("/home/dhafin/Documents/Projects/EDA")
    from olist_utils import marimo_setup

    # Quick setup - loads all tables and creates common views
    con, dataset_path = marimo_setup()
    return con, dataset_path


@app.cell
def __(mo):
    mo.md(
        """
    ## Available Tables

    The `marimo_setup()` function automatically loaded the following:

    **Base Tables:**
    - `customers` - Customer information
    - `orders` - Order details
    - `order_items` - Line items for each order
    - `payments` - Payment information
    - `reviews` - Customer reviews
    - `products` - Product catalog
    - `sellers` - Seller information
    - `geolocation` - Brazilian zip codes
    - `category_translation` - PT to EN translations

    **Joined Views (automatically created):**
    - `orders_complete` - Orders with customer and payment info
    - `order_items_complete` - Order items with product and seller info
    - `orders_with_reviews` - Orders with review scores
    """
    )
    return


@app.cell
def __(con, mo):
    # Show all available tables
    tables_df = con.execute("SHOW TABLES").df()
    mo.ui.table(tables_df)
    return (tables_df,)


@app.cell
def __(mo):
    mo.md(
        """
    ## Revenue Trends Over Time

    Let's analyze monthly revenue trends.
    """
    )
    return


@app.cell
def __(con):
    revenue_by_month = con.execute(
        """
        SELECT
            DATE_TRUNC('month', CAST(o.order_purchase_timestamp AS TIMESTAMP)) as month,
            COUNT(DISTINCT o.order_id) as total_orders,
            ROUND(SUM(oi.price + oi.freight_value), 2) as total_revenue,
            ROUND(AVG(oi.price), 2) as avg_order_value
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY month
        ORDER BY month
    """
    ).df()
    revenue_by_month
    return (revenue_by_month,)


@app.cell
def __(px, revenue_by_month):
    fig_revenue = px.line(
        revenue_by_month,
        x="month",
        y="total_revenue",
        title="Monthly Revenue Trend",
        labels={"total_revenue": "Revenue (R$)", "month": "Month"},
        markers=True,
    )
    fig_revenue.update_layout(hovermode="x unified")
    fig_revenue
    return (fig_revenue,)


@app.cell
def __(mo):
    mo.md(
        """
    ## Top Product Categories

    Using the pre-joined `order_items_complete` view for easier analysis.
    """
    )
    return


@app.cell
def __(con):
    top_categories = con.execute(
        """
        SELECT
            product_category_name_english as category,
            COUNT(DISTINCT order_id) as order_count,
            ROUND(SUM(price), 2) as total_revenue,
            ROUND(AVG(price), 2) as avg_price
        FROM order_items_complete
        WHERE product_category_name_english IS NOT NULL
        GROUP BY category
        ORDER BY total_revenue DESC
        LIMIT 10
    """
    ).df()
    top_categories
    return (top_categories,)


@app.cell
def __(px, top_categories):
    fig_categories = px.bar(
        top_categories,
        x="category",
        y="total_revenue",
        title="Top 10 Product Categories by Revenue",
        labels={"total_revenue": "Revenue (R$)", "category": "Category"},
        text="total_revenue",
    )
    fig_categories.update_traces(texttemplate="R$ %{text:,.0f}", textposition="outside")
    fig_categories.update_layout(xaxis_tickangle=-45)
    fig_categories
    return (fig_categories,)


@app.cell
def __(mo):
    mo.md(
        """
    ## Customer Satisfaction by State

    Using the `orders_with_reviews` view.
    """
    )
    return


@app.cell
def __(con):
    satisfaction_by_state = con.execute(
        """
        SELECT
            c.customer_state as state,
            COUNT(DISTINCT owr.order_id) as orders_with_reviews,
            ROUND(AVG(owr.review_score), 2) as avg_review_score
        FROM orders_with_reviews owr
        JOIN customers c ON owr.customer_id = c.customer_id
        WHERE owr.review_score IS NOT NULL
        GROUP BY state
        HAVING COUNT(DISTINCT owr.order_id) >= 100
        ORDER BY avg_review_score DESC
    """
    ).df()
    satisfaction_by_state
    return (satisfaction_by_state,)


@app.cell
def __(px, satisfaction_by_state):
    fig_satisfaction = px.bar(
        satisfaction_by_state,
        x="state",
        y="avg_review_score",
        title="Average Review Score by State (min 100 reviews)",
        labels={"avg_review_score": "Avg Review Score", "state": "State"},
        color="avg_review_score",
        color_continuous_scale="RdYlGn",
    )
    fig_satisfaction.update_layout(showlegend=False)
    fig_satisfaction
    return (fig_satisfaction,)


@app.cell
def __(mo):
    mo.md(
        """
    ## Key Insights

    1. **Revenue Growth**: The monthly revenue shows [describe trend]
    2. **Top Categories**: Health & beauty, watches & gifts, and bed/bath/table are top performers
    3. **Customer Satisfaction**: Review scores vary by state, indicating regional differences in service quality

    ## Next Steps

    - Deep dive into seasonal patterns
    - Analyze delivery performance impact on reviews
    - Investigate underperforming categories for improvement opportunities
    """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
    ---

    ## Benefits of Using olist_utils

    **Single import** - No need to copy/paste setup code

    **Automatic table loading** - All 9 tables loaded as views

    **Common joins pre-created** - Use `orders_complete`, `order_items_complete`, etc.

    **Easy maintenance** - Update path in one place (`.env` or `olist_utils.py`)

    **No breaking changes** - All notebooks stay functional when paths change

    ---

    ## Alternative Setup Methods

    If you need more control, you can use individual functions:

    ```python
    from olist_utils import setup_duckdb, load_all_tables, create_common_views

    # Manual setup
    con = setup_duckdb()
    load_all_tables(con)
    create_common_views(con)
    ```
    """
    )
    return


if __name__ == "__main__":
    app.run()
