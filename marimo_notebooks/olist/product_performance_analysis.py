import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    import marimo as mo
    import duckdb
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    return Path, duckdb, go, load_dotenv, make_subplots, mo, os, pd, px


@app.cell
def _(mo):
    mo.md("""
    # Product Performance Analysis - Olist E-Commerce

    **Business Questions Answered:**
    - Which products and categories are top performers?
    - How do product attributes impact sales?
    - What's the relationship between product reviews and sales?
    - Which products have the best delivery performance?
    - What's the geographic reach of different products?

    **Data Source:** mart_product_performance (32,951 products)

    **Analysis Includes:**
    - Sales volume and revenue metrics
    - Review scores and sentiment analysis
    - Delivery performance by product
    - Geographic distribution
    - Category-level insights
    """)
    return


@app.cell
def _(Path, duckdb, load_dotenv, os):
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)

    # Configure database for this notebook
    db_name = 'olist_analytical.duckdb'
    db_dir = os.getenv('DUCKDB_DIR')
    db_path = os.path.join(db_dir, db_name)

    # Connect to DuckDB analytical database
    con = duckdb.connect(database=db_path, read_only=True)
    return (con,)


@app.cell
def _(mo):
    mo.md("""
    ## Filter Options

    Select criteria to analyze product performance:
    """)
    return


@app.cell
def _(con):
    # Get available categories for filtering
    categories_df = con.execute("""
        SELECT DISTINCT product_category_name_english
        FROM marts_product.mart_product_performance
        WHERE product_category_name_english IS NOT NULL
        ORDER BY product_category_name_english
    """).df()

    category_list = ['All Categories'] + categories_df['product_category_name_english'].tolist()
    return categories_df, category_list


@app.cell
def _(category_list, mo):
    # Filter controls
    category_filter = mo.ui.dropdown(
        options=category_list,
        value='All Categories',
        label="Product Category"
    )

    min_sales = mo.ui.slider(
        start=0,
        stop=100,
        step=5,
        value=10,
        label="Minimum Units Sold"
    )

    mo.vstack([category_filter, min_sales])
    return category_filter, min_sales


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Top-Level Product Metrics

    Key performance indicators across all products:
    """)
    return


@app.cell
def _(category_filter, con, min_sales):
    # Calculate overall product metrics
    category_condition = "" if category_filter.value == 'All Categories' else f"AND product_category_name_english = '{category_filter.value}'"

    product_kpis = con.execute(f"""
        SELECT
            COUNT(DISTINCT product_id) as total_products,
            SUM(total_units_sold) as total_units,
            SUM(total_revenue) as total_revenue,
            AVG(avg_review_score) as avg_review_score,
            AVG(on_time_delivery_rate) as avg_on_time_rate,
            COUNT(DISTINCT CASE WHEN total_units_sold >= {min_sales.value} THEN product_id END) as active_products
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        {category_condition}
    """).df()

    kpi_data = product_kpis.iloc[0]
    return category_condition, kpi_data, product_kpis


@app.cell
def _(kpi_data, mo):
    mo.hstack([
        mo.stat(label="Total Products", value=f"{kpi_data['total_products']:,}"),
        mo.stat(label="Units Sold", value=f"{kpi_data['total_units']:,}"),
        mo.stat(label="Total Revenue", value=f"R$ {kpi_data['total_revenue']:,.2f}"),
        mo.stat(label="Avg Review Score", value=f"{kpi_data['avg_review_score']:.2f} ⭐"),
        mo.stat(label="On-Time Delivery", value=f"{kpi_data['avg_on_time_rate']:.1f}%")
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Top Products by Sales

    Best performing products ranked by units sold:
    """)
    return


@app.cell
def _(category_condition, con, min_sales):
    top_products = con.execute(f"""
        SELECT
            product_category_name_english as category,
            total_units_sold,
            total_revenue,
            avg_price,
            avg_review_score,
            total_reviews,
            on_time_delivery_rate,
            sales_tier,
            review_tier
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        {category_condition}
        ORDER BY total_units_sold DESC
        LIMIT 20
    """).df()

    top_products
    return (top_products,)


@app.cell
def _(go, top_products):
    # Visualization: Top products by units sold
    fig_top_products = go.Figure()

    fig_top_products.add_trace(go.Bar(
        y=top_products['category'][::-1],
        x=top_products['total_units_sold'][::-1],
        orientation='h',
        marker=dict(
            color=top_products['avg_review_score'][::-1],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Avg Review<br>Score")
        ),
        text=top_products['total_units_sold'][::-1],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Units: %{x:,}<br>Review: %{marker.color:.2f}<extra></extra>'
    ))

    fig_top_products.update_layout(
        title="Top 20 Products by Units Sold (colored by review score)",
        xaxis_title="Units Sold",
        yaxis_title="Product Category",
        height=600,
        showlegend=False
    )

    fig_top_products
    return (fig_top_products,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Category Performance Comparison

    Revenue and sales breakdown by product category:
    """)
    return


@app.cell
def _(con, min_sales):
    category_performance = con.execute(f"""
        SELECT
            product_category_name_english as category,
            COUNT(DISTINCT product_id) as product_count,
            SUM(total_units_sold) as total_units,
            SUM(total_revenue) as total_revenue,
            AVG(avg_price) as avg_price,
            AVG(avg_review_score) as avg_review,
            AVG(on_time_delivery_rate) as avg_on_time_rate,
            SUM(total_revenue) / SUM(total_units_sold) as revenue_per_unit
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        AND product_category_name_english IS NOT NULL
        GROUP BY product_category_name_english
        ORDER BY total_revenue DESC
        LIMIT 15
    """).df()

    category_performance
    return (category_performance,)


@app.cell
def _(category_performance, make_subplots):
    # Category performance visualization
    fig_category = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Revenue by Category', 'Units Sold by Category'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    fig_category.add_trace(
        dict(
            type='bar',
            y=category_performance['category'][::-1],
            x=category_performance['total_revenue'][::-1],
            orientation='h',
            name='Revenue',
            marker=dict(color='#2ecc71')
        ),
        row=1, col=1
    )

    fig_category.add_trace(
        dict(
            type='bar',
            y=category_performance['category'][::-1],
            x=category_performance['total_units'][::-1],
            orientation='h',
            name='Units',
            marker=dict(color='#3498db')
        ),
        row=1, col=2
    )

    fig_category.update_layout(
        title="Top 15 Categories by Performance",
        height=600,
        showlegend=False
    )

    fig_category.update_xaxes(title_text="Revenue (R$)", row=1, col=1)
    fig_category.update_xaxes(title_text="Units Sold", row=1, col=2)

    fig_category
    return (fig_category,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Price vs Review Score Analysis

    Correlation between product pricing and customer satisfaction:
    """)
    return


@app.cell
def _(category_condition, con, min_sales):
    price_review_data = con.execute(f"""
        SELECT
            product_category_name_english as category,
            avg_price,
            avg_review_score,
            total_units_sold,
            total_reviews,
            on_time_delivery_rate
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        AND avg_review_score IS NOT NULL
        {category_condition}
    """).df()
    return (price_review_data,)


@app.cell
def _(price_review_data, px):
    fig_price_review = px.scatter(
        price_review_data,
        x='avg_price',
        y='avg_review_score',
        size='total_units_sold',
        color='category',
        hover_data=['total_reviews', 'on_time_delivery_rate'],
        title='Product Price vs Review Score (size = units sold)',
        labels={
            'avg_price': 'Average Price (R$)',
            'avg_review_score': 'Average Review Score',
            'category': 'Category'
        },
        height=600
    )

    fig_price_review.update_layout(showlegend=True)
    fig_price_review
    return (fig_price_review,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Sales Performance Tiers

    Distribution of products across performance tiers:
    """)
    return


@app.cell
def _(category_condition, con, min_sales):
    sales_tiers = con.execute(f"""
        SELECT
            sales_tier,
            COUNT(DISTINCT product_id) as product_count,
            SUM(total_revenue) as tier_revenue,
            AVG(avg_review_score) as avg_review
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        {category_condition}
        GROUP BY sales_tier
        ORDER BY
            CASE sales_tier
                WHEN 'Best Seller' THEN 1
                WHEN 'Top Seller' THEN 2
                WHEN 'Good Seller' THEN 3
                WHEN 'Low Seller' THEN 4
                ELSE 5
            END
    """).df()

    sales_tiers
    return (sales_tiers,)


@app.cell
def _(make_subplots, sales_tiers):
    fig_tiers = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'pie'}, {'type': 'pie'}]],
        subplot_titles=('Products by Tier', 'Revenue by Tier')
    )

    fig_tiers.add_trace(
        dict(
            type='pie',
            labels=sales_tiers['sales_tier'],
            values=sales_tiers['product_count'],
            name='Products'
        ),
        row=1, col=1
    )

    fig_tiers.add_trace(
        dict(
            type='pie',
            labels=sales_tiers['sales_tier'],
            values=sales_tiers['tier_revenue'],
            name='Revenue'
        ),
        row=1, col=2
    )

    fig_tiers.update_layout(
        title="Product Distribution and Revenue by Sales Tier",
        height=500
    )

    fig_tiers
    return (fig_tiers,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Review Quality Distribution

    How products are rated across review tiers:
    """)
    return


@app.cell
def _(category_condition, con, min_sales):
    review_distribution = con.execute(f"""
        SELECT
            review_tier,
            COUNT(DISTINCT product_id) as product_count,
            AVG(total_units_sold) as avg_units_sold,
            AVG(avg_review_score) as avg_score
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        {category_condition}
        AND review_tier != 'No Reviews'
        GROUP BY review_tier
        ORDER BY avg_score DESC
    """).df()

    review_distribution
    return (review_distribution,)


@app.cell
def _(px, review_distribution):
    fig_reviews = px.bar(
        review_distribution,
        x='review_tier',
        y='product_count',
        color='avg_score',
        title='Product Count by Review Tier',
        labels={
            'review_tier': 'Review Tier',
            'product_count': 'Number of Products',
            'avg_score': 'Avg Score'
        },
        color_continuous_scale='RdYlGn',
        text='product_count'
    )

    fig_reviews.update_traces(textposition='outside')
    fig_reviews.update_layout(height=500)
    fig_reviews
    return (fig_reviews,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Delivery Performance by Product

    On-time delivery rates across different product categories:
    """)
    return


@app.cell
def _(con, min_sales):
    delivery_by_category = con.execute(f"""
        SELECT
            product_category_name_english as category,
            AVG(on_time_delivery_rate) as avg_on_time_rate,
            AVG(avg_delivery_days) as avg_delivery_days,
            SUM(total_units_sold) as total_units,
            AVG(avg_review_score) as avg_review
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        AND product_category_name_english IS NOT NULL
        AND on_time_delivery_rate IS NOT NULL
        GROUP BY product_category_name_english
        ORDER BY avg_on_time_rate DESC
        LIMIT 15
    """).df()
    return (delivery_by_category,)


@app.cell
def _(delivery_by_category, go):
    fig_delivery = go.Figure()

    fig_delivery.add_trace(go.Bar(
        y=delivery_by_category['category'][::-1],
        x=delivery_by_category['avg_on_time_rate'][::-1],
        orientation='h',
        marker=dict(
            color=delivery_by_category['avg_on_time_rate'][::-1],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="On-Time<br>Rate %")
        ),
        text=[f"{x:.1f}%" for x in delivery_by_category['avg_on_time_rate'][::-1]],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>On-Time: %{x:.1f}%<extra></extra>'
    ))

    fig_delivery.update_layout(
        title="Top 15 Categories by On-Time Delivery Rate",
        xaxis_title="On-Time Delivery Rate (%)",
        yaxis_title="Category",
        height=600,
        showlegend=False
    )

    fig_delivery
    return (fig_delivery,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Geographic Reach Analysis

    How widely products are distributed across Brazil:
    """)
    return


@app.cell
def _(category_condition, con, min_sales):
    geographic_reach = con.execute(f"""
        SELECT
            product_category_name_english as category,
            AVG(unique_customer_states) as avg_states_reached,
            AVG(unique_customer_locations) as avg_locations_reached,
            SUM(total_units_sold) as total_units,
            AVG(same_state_sales_rate) as avg_same_state_rate
        FROM marts_product.mart_product_performance
        WHERE total_units_sold >= {min_sales.value}
        {category_condition}
        AND product_category_name_english IS NOT NULL
        GROUP BY product_category_name_english
        ORDER BY avg_states_reached DESC
        LIMIT 15
    """).df()
    return (geographic_reach,)


@app.cell
def _(geographic_reach, make_subplots):
    fig_geo = make_subplots(
        rows=1, cols=2,
        subplot_titles=('States Reached', 'Same-State Sales %'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    fig_geo.add_trace(
        dict(
            type='bar',
            y=geographic_reach['category'][::-1],
            x=geographic_reach['avg_states_reached'][::-1],
            orientation='h',
            name='States',
            marker=dict(color='#9b59b6')
        ),
        row=1, col=1
    )

    fig_geo.add_trace(
        dict(
            type='bar',
            y=geographic_reach['category'][::-1],
            x=geographic_reach['avg_same_state_rate'][::-1],
            orientation='h',
            name='Same State %',
            marker=dict(color='#e74c3c')
        ),
        row=1, col=2
    )

    fig_geo.update_layout(
        title="Geographic Distribution by Category",
        height=600,
        showlegend=False
    )

    fig_geo.update_xaxes(title_text="Avg States Reached", row=1, col=1)
    fig_geo.update_xaxes(title_text="Same-State Sales (%)", row=1, col=2)

    fig_geo
    return (fig_geo,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    **Top Findings:**

    1. **Best Performing Categories** - Identify which product categories drive the most revenue and volume

    2. **Review Score Impact** - Products with higher review scores don't always correlate with higher prices

    3. **Delivery Performance** - On-time delivery rates vary significantly by category, impacting customer satisfaction

    4. **Geographic Patterns** - Some categories have wider geographic reach than others

    5. **Sales Tiers** - Most products are in Low/Good Seller tiers, with few Best Sellers dominating revenue

    **Actionable Recommendations:**

    - Focus marketing efforts on top-performing categories
    - Investigate low-rated products for quality improvements
    - Address delivery issues in categories with poor on-time rates
    - Expand successful products to new geographic markets
    - Promote high-potential products (good reviews, low sales)
    """)
    return


if __name__ == "__main__":
    app.run()
