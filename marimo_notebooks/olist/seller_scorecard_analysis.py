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
    # Seller Performance Scorecard - Olist Marketplace

    **Business Questions Answered:**
    - Which sellers are top performers?
    - What are the seller health indicators?
    - How do sellers specialize in products/categories?
    - What is the geographic distribution of sellers?
    - How do sellers perform on delivery and customer satisfaction?

    **Data Source:** mart_seller_scorecard (3,095 sellers)

    **Analysis Includes:**
    - Comprehensive seller KPIs
    - Performance scoring and rankings
    - Activity status and trends
    - Specialization analysis
    - Geographic reach
    - Health assessments
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
    ## Seller Filters

    Select criteria to analyze seller performance:
    """)
    return


@app.cell
def _(con):
    # Get filter options
    health_options = con.execute("""
        SELECT DISTINCT seller_health
        FROM marts_seller.mart_seller_scorecard
        WHERE seller_health IS NOT NULL
        ORDER BY seller_health
    """).df()['seller_health'].tolist()

    activity_options = con.execute("""
        SELECT DISTINCT activity_status
        FROM marts_seller.mart_seller_scorecard
        ORDER BY activity_status
    """).df()['activity_status'].tolist()

    region_options = con.execute("""
        SELECT DISTINCT region
        FROM marts_seller.mart_seller_scorecard
        WHERE region IS NOT NULL
        ORDER BY region
    """).df()['region'].tolist()
    return activity_options, health_options, region_options


@app.cell
def _(activity_options, health_options, mo, region_options):
    # Filter controls
    health_filter = mo.ui.dropdown(
        options=['All'] + health_options,
        value='All',
        label="Seller Health"
    )

    activity_filter = mo.ui.dropdown(
        options=['All'] + activity_options,
        value='All',
        label="Activity Status"
    )

    region_filter = mo.ui.dropdown(
        options=['All'] + region_options,
        value='All',
        label="Region"
    )

    min_orders = mo.ui.slider(
        start=0,
        stop=50,
        step=5,
        value=10,
        label="Minimum Orders"
    )

    mo.vstack([
        mo.hstack([health_filter, activity_filter]),
        mo.hstack([region_filter, min_orders])
    ])
    return activity_filter, health_filter, min_orders, region_filter


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Marketplace Overview

    Key metrics across all sellers:
    """)
    return


@app.cell
def _(activity_filter, con, health_filter, min_orders, region_filter):
    # Build filter conditions
    filters = []
    if health_filter.value != 'All':
        filters.append(f"seller_health = '{health_filter.value}'")
    if activity_filter.value != 'All':
        filters.append(f"activity_status = '{activity_filter.value}'")
    if region_filter.value != 'All':
        filters.append(f"region = '{region_filter.value}'")
    filters.append(f"total_orders >= {min_orders.value}")

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    # Calculate seller KPIs
    seller_kpis = con.execute(f"""
        SELECT
            COUNT(DISTINCT seller_id) as total_sellers,
            SUM(total_revenue) as total_revenue,
            SUM(total_orders) as total_orders,
            AVG(avg_review_score) as avg_review_score,
            AVG(on_time_delivery_rate) as avg_on_time_rate,
            AVG(overall_performance_score) as avg_performance_score
        FROM marts_seller.mart_seller_scorecard
        {where_clause}
    """).df()

    kpi_data = seller_kpis.iloc[0]
    return filters, kpi_data, seller_kpis, where_clause


@app.cell
def _(kpi_data, mo):
    mo.hstack([
        mo.stat(label="Total Sellers", value=f"{kpi_data['total_sellers']:,}"),
        mo.stat(label="Total Revenue", value=f"R$ {kpi_data['total_revenue']:,.2f}"),
        mo.stat(label="Total Orders", value=f"{kpi_data['total_orders']:,}"),
        mo.stat(label="Avg Review Score", value=f"{kpi_data['avg_review_score']:.2f} ⭐"),
        mo.stat(label="On-Time Delivery", value=f"{kpi_data['avg_on_time_rate']:.1f}%")
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Top Performing Sellers

    Highest ranked sellers by overall performance score:
    """)
    return


@app.cell
def _(con, where_clause):
    top_sellers = con.execute(f"""
        SELECT
            seller_id,
            seller_state,
            region,
            total_orders,
            total_revenue,
            avg_review_score,
            on_time_delivery_rate,
            overall_performance_score,
            seller_health,
            activity_status,
            seller_performance_tier
        FROM marts_seller.mart_seller_scorecard
        {where_clause}
        AND overall_performance_score IS NOT NULL
        ORDER BY overall_performance_score DESC
        LIMIT 20
    """).df()

    top_sellers
    return (top_sellers,)


@app.cell
def _(go, top_sellers):
    # Visualization: Top sellers by performance score
    fig_top_sellers = go.Figure()

    fig_top_sellers.add_trace(go.Bar(
        y=top_sellers['seller_id'][::-1],
        x=top_sellers['overall_performance_score'][::-1],
        orientation='h',
        marker=dict(
            color=top_sellers['overall_performance_score'][::-1],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Performance<br>Score")
        ),
        text=[f"{x:.1f}" for x in top_sellers['overall_performance_score'][::-1]],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}<br>Orders: %{customdata[0]:,}<br>Revenue: R$ %{customdata[1]:,.2f}<extra></extra>',
        customdata=top_sellers[['total_orders', 'total_revenue']][::-1]
    ))

    fig_top_sellers.update_layout(
        title="Top 20 Sellers by Overall Performance Score",
        xaxis_title="Performance Score (0-100)",
        yaxis_title="Seller ID",
        height=600,
        showlegend=False
    )

    fig_top_sellers
    return (fig_top_sellers,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Seller Health Distribution

    How sellers are distributed across health categories:
    """)
    return


@app.cell
def _(con, min_orders):
    health_distribution = con.execute(f"""
        SELECT
            seller_health,
            COUNT(DISTINCT seller_id) as seller_count,
            SUM(total_revenue) as total_revenue,
            AVG(total_orders) as avg_orders,
            AVG(avg_review_score) as avg_review,
            AVG(on_time_delivery_rate) as avg_on_time_rate
        FROM marts_seller.mart_seller_scorecard
        WHERE total_orders >= {min_orders.value}
        GROUP BY seller_health
        ORDER BY
            CASE seller_health
                WHEN 'Excellent' THEN 1
                WHEN 'Good' THEN 2
                WHEN 'Average' THEN 3
                WHEN 'Needs Improvement' THEN 4
                ELSE 5
            END
    """).df()

    health_distribution
    return (health_distribution,)


@app.cell
def _(health_distribution, make_subplots):
    fig_health = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'pie'}, {'type': 'bar'}]],
        subplot_titles=('Seller Count by Health', 'Revenue by Health Status')
    )

    fig_health.add_trace(
        dict(
            type='pie',
            labels=health_distribution['seller_health'],
            values=health_distribution['seller_count'],
            name='Sellers',
            marker=dict(colors=['#27ae60', '#3498db', '#f39c12', '#e74c3c', '#95a5a6'])
        ),
        row=1, col=1
    )

    fig_health.add_trace(
        dict(
            type='bar',
            x=health_distribution['seller_health'],
            y=health_distribution['total_revenue'],
            name='Revenue',
            marker=dict(color=['#27ae60', '#3498db', '#f39c12', '#e74c3c', '#95a5a6'])
        ),
        row=1, col=2
    )

    fig_health.update_layout(
        title="Seller Health Analysis",
        height=500,
        showlegend=False
    )

    fig_health
    return (fig_health,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Activity Status Breakdown

    Current seller activity levels:
    """)
    return


@app.cell
def _(con, min_orders):
    activity_distribution = con.execute(f"""
        SELECT
            activity_status,
            COUNT(DISTINCT seller_id) as seller_count,
            SUM(total_revenue) as total_revenue,
            AVG(orders_last_30_days) as avg_orders_30d,
            AVG(orders_last_90_days) as avg_orders_90d
        FROM marts_seller.mart_seller_scorecard
        WHERE total_orders >= {min_orders.value}
        GROUP BY activity_status
        ORDER BY
            CASE activity_status
                WHEN 'Active (30d)' THEN 1
                WHEN 'Recent (90d)' THEN 2
                WHEN 'Cooling (180d)' THEN 3
                WHEN 'Inactive' THEN 4
                ELSE 5
            END
    """).df()

    activity_distribution
    return (activity_distribution,)


@app.cell
def _(activity_distribution, px):
    fig_activity = px.bar(
        activity_distribution,
        x='activity_status',
        y='seller_count',
        color='total_revenue',
        title='Seller Activity Status Distribution',
        labels={
            'activity_status': 'Activity Status',
            'seller_count': 'Number of Sellers',
            'total_revenue': 'Total Revenue'
        },
        color_continuous_scale='Blues',
        text='seller_count'
    )

    fig_activity.update_traces(textposition='outside')
    fig_activity.update_layout(height=500)
    fig_activity
    return (fig_activity,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Revenue Performance Analysis

    Revenue distribution and efficiency metrics:
    """)
    return


@app.cell
def _(con, where_clause):
    revenue_metrics = con.execute(f"""
        SELECT
            seller_performance_tier,
            COUNT(DISTINCT seller_id) as seller_count,
            SUM(total_revenue) as total_revenue,
            AVG(revenue_per_order) as avg_revenue_per_order,
            AVG(revenue_per_day_active) as avg_revenue_per_day,
            AVG(total_orders) as avg_orders
        FROM marts_seller.mart_seller_scorecard
        {where_clause}
        AND seller_performance_tier IS NOT NULL
        GROUP BY seller_performance_tier
        ORDER BY seller_performance_tier
    """).df()

    revenue_metrics
    return (revenue_metrics,)


@app.cell
def _(con, where_clause):
    # Revenue percentile analysis
    revenue_analysis = con.execute(f"""
        SELECT
            seller_id,
            seller_state,
            total_revenue,
            revenue_per_order,
            revenue_per_month,
            revenue_percentile,
            seller_performance_tier
        FROM marts_seller.mart_seller_scorecard
        {where_clause}
        AND revenue_percentile IS NOT NULL
        ORDER BY revenue_percentile DESC
        LIMIT 100
    """).df()
    return (revenue_analysis,)


@app.cell
def _(px, revenue_analysis):
    fig_revenue_dist = px.histogram(
        revenue_analysis,
        x='revenue_percentile',
        nbins=20,
        title='Seller Revenue Percentile Distribution',
        labels={'revenue_percentile': 'Revenue Percentile', 'count': 'Number of Sellers'},
        color_discrete_sequence=['#3498db']
    )

    fig_revenue_dist.update_layout(height=500)
    fig_revenue_dist
    return (fig_revenue_dist,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Seller Specialization

    Product diversity and category focus:
    """)
    return


@app.cell
def _(con, min_orders):
    specialization_data = con.execute(f"""
        SELECT
            product_diversity_type,
            COUNT(DISTINCT seller_id) as seller_count,
            AVG(unique_products_sold) as avg_products,
            AVG(unique_categories) as avg_categories,
            AVG(total_revenue) as avg_revenue,
            AVG(avg_review_score) as avg_review
        FROM marts_seller.mart_seller_scorecard
        WHERE total_orders >= {min_orders.value}
        AND product_diversity_type IS NOT NULL
        GROUP BY product_diversity_type
        ORDER BY
            CASE product_diversity_type
                WHEN 'Specialist' THEN 1
                WHEN 'Focused' THEN 2
                WHEN 'Diverse' THEN 3
                WHEN 'Generalist' THEN 4
            END
    """).df()

    specialization_data
    return (specialization_data,)


@app.cell
def _(make_subplots, specialization_data):
    fig_spec = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Seller Count', 'Avg Products per Seller',
            'Avg Categories', 'Avg Revenue'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )

    fig_spec.add_trace(
        dict(
            type='bar',
            x=specialization_data['product_diversity_type'],
            y=specialization_data['seller_count'],
            marker=dict(color='#9b59b6')
        ),
        row=1, col=1
    )

    fig_spec.add_trace(
        dict(
            type='bar',
            x=specialization_data['product_diversity_type'],
            y=specialization_data['avg_products'],
            marker=dict(color='#e74c3c')
        ),
        row=1, col=2
    )

    fig_spec.add_trace(
        dict(
            type='bar',
            x=specialization_data['product_diversity_type'],
            y=specialization_data['avg_categories'],
            marker=dict(color='#f39c12')
        ),
        row=2, col=1
    )

    fig_spec.add_trace(
        dict(
            type='bar',
            x=specialization_data['product_diversity_type'],
            y=specialization_data['avg_revenue'],
            marker=dict(color='#27ae60')
        ),
        row=2, col=2
    )

    fig_spec.update_layout(
        title="Seller Specialization Analysis",
        height=700,
        showlegend=False
    )

    fig_spec
    return (fig_spec,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Geographic Distribution

    Seller presence and focus across Brazil:
    """)
    return


@app.cell
def _(con, min_orders):
    geographic_data = con.execute(f"""
        SELECT
            region,
            COUNT(DISTINCT seller_id) as seller_count,
            SUM(total_revenue) as total_revenue,
            AVG(unique_customer_states) as avg_states_reached,
            AVG(same_state_order_rate) as avg_same_state_rate
        FROM marts_seller.mart_seller_scorecard
        WHERE total_orders >= {min_orders.value}
        AND region IS NOT NULL
        GROUP BY region
        ORDER BY total_revenue DESC
    """).df()

    geographic_data
    return (geographic_data,)


@app.cell
def _(geographic_data, make_subplots):
    fig_geo = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'bar'}, {'type': 'bar'}]],
        subplot_titles=('Sellers by Region', 'Revenue by Region')
    )

    fig_geo.add_trace(
        dict(
            type='bar',
            x=geographic_data['region'],
            y=geographic_data['seller_count'],
            marker=dict(color='#3498db'),
            name='Sellers'
        ),
        row=1, col=1
    )

    fig_geo.add_trace(
        dict(
            type='bar',
            x=geographic_data['region'],
            y=geographic_data['total_revenue'],
            marker=dict(color='#2ecc71'),
            name='Revenue'
        ),
        row=1, col=2
    )

    fig_geo.update_layout(
        title="Geographic Distribution of Sellers",
        height=500,
        showlegend=False
    )

    fig_geo
    return (fig_geo,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Geographic Focus Analysis

    Local vs national seller strategies:
    """)
    return


@app.cell
def _(con, min_orders):
    geo_focus_data = con.execute(f"""
        SELECT
            geographic_focus,
            COUNT(DISTINCT seller_id) as seller_count,
            AVG(total_revenue) as avg_revenue,
            AVG(same_state_order_rate) as avg_same_state_rate,
            AVG(unique_customer_states) as avg_states_reached
        FROM marts_seller.mart_seller_scorecard
        WHERE total_orders >= {min_orders.value}
        AND geographic_focus IS NOT NULL
        GROUP BY geographic_focus
        ORDER BY avg_revenue DESC
    """).df()

    geo_focus_data
    return (geo_focus_data,)


@app.cell
def _(geo_focus_data, px):
    fig_focus = px.bar(
        geo_focus_data,
        x='geographic_focus',
        y='seller_count',
        color='avg_revenue',
        title='Seller Count by Geographic Focus Strategy',
        labels={
            'geographic_focus': 'Geographic Focus',
            'seller_count': 'Number of Sellers',
            'avg_revenue': 'Avg Revenue'
        },
        color_continuous_scale='Greens',
        text='seller_count'
    )

    fig_focus.update_traces(textposition='outside')
    fig_focus.update_layout(height=500)
    fig_focus
    return (fig_focus,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Delivery & Review Performance

    Customer satisfaction and fulfillment metrics:
    """)
    return


@app.cell
def _(con, where_clause):
    performance_scatter = con.execute(f"""
        SELECT
            seller_id,
            on_time_delivery_rate,
            avg_review_score,
            total_revenue,
            total_orders,
            seller_health,
            positive_review_rate
        FROM marts_seller.mart_seller_scorecard
        {where_clause}
        AND on_time_delivery_rate IS NOT NULL
        AND avg_review_score IS NOT NULL
    """).df()
    return (performance_scatter,)


@app.cell
def _(performance_scatter, px):
    fig_perf_scatter = px.scatter(
        performance_scatter,
        x='on_time_delivery_rate',
        y='avg_review_score',
        size='total_revenue',
        color='seller_health',
        hover_data=['total_orders', 'positive_review_rate'],
        title='Delivery Performance vs Customer Satisfaction (size = revenue)',
        labels={
            'on_time_delivery_rate': 'On-Time Delivery Rate (%)',
            'avg_review_score': 'Average Review Score',
            'seller_health': 'Seller Health'
        },
        height=600,
        color_discrete_map={
            'Excellent': '#27ae60',
            'Good': '#3498db',
            'Average': '#f39c12',
            'Needs Improvement': '#e74c3c',
            'New/Unknown': '#95a5a6'
        }
    )

    fig_perf_scatter
    return (fig_perf_scatter,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    **Top Findings:**

    1. **Health Distribution** - Majority of active sellers fall into Good/Average health categories

    2. **Activity Trends** - Identify sellers at risk of churning (Cooling/Inactive status)

    3. **Specialization Patterns** - Specialist sellers often have higher customer satisfaction despite lower volumes

    4. **Geographic Concentration** - Most sellers are concentrated in Southeast region

    5. **Performance Drivers** - Strong correlation between on-time delivery and review scores

    **Actionable Recommendations:**

    - Engage with "Needs Improvement" sellers for training/support
    - Reactivate "Cooling" sellers with targeted incentives
    - Encourage successful local sellers to expand geographically
    - Share best practices from "Excellent" health sellers
    - Monitor new sellers for early performance issues
    """)
    return


if __name__ == "__main__":
    app.run()
