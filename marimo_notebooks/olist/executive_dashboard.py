import marimo

__generated_with = "0.17.7"
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
    return Path, duckdb, load_dotenv, make_subplots, mo, os, px


@app.cell
def _(mo):
    mo.md("""
    # Executive Dashboard - Olist E-Commerce

    **Business Questions Answered:**
    - Q1: Month-over-month and year-over-year revenue growth trend
    - Q2: New customers acquired monthly
    - Q3: Marketplace GMV trajectory
    - Q5: Order volume growth trend
    - Q6: Average order value (AOV) trend
    - Q21: Delivery performance metrics
    - Q31: Customer satisfaction score (NPS proxy)

    **Data Source:** dim_customers (99,441 rows) & fct_orders (99,992 rows)

    **Dataset Period:** 2016-2018
    """)
    return


@app.cell
def _(Path, duckdb, load_dotenv, os):
    # Load environment variables from .env file
    # Path: marimo_notebooks/olist/executive_dashboard.py -> ../../.env
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)

    # Configure database for this notebook
    db_name = 'olist_analytical.duckdb'  # Each notebook can specify its own database
    db_dir = os.getenv('DUCKDB_DIR')
    db_path = os.path.join(db_dir, db_name)

    # Connect to DuckDB analytical database
    con = duckdb.connect(database=db_path, read_only=True)
    return (con,)


@app.cell
def _(mo):
    mo.md("""
    ## Date Range Filter

    Select the time period for your analysis:
    """)
    return


@app.cell
def _(mo):
    date_range = mo.ui.date_range(
        start="2016-09-01",
        stop="2018-08-31",
        label="Analysis Period",
        value=("2016-09-01", "2018-08-31")
    )
    date_range
    return (date_range,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Performance Indicators

    High-level metrics for the selected period:
    """)
    return


@app.cell
def _(con, date_range):
    # Calculate overall KPIs for the selected date range
    kpi_query = f"""
    WITH filtered_orders AS (
        SELECT *
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
    ),
    customer_stats AS (
        SELECT
            COUNT(DISTINCT customer_id) as total_customers,
            COUNT(DISTINCT CASE
                WHEN order_date = (
                    SELECT MIN(order_date)
                    FROM core_core.fct_orders f2
                    WHERE f2.customer_id = filtered_orders.customer_id
                ) THEN customer_id
            END) as new_customers
        FROM filtered_orders
    )
    SELECT
        -- Revenue Metrics
        SUM(total_order_value) as total_gmv,
        COUNT(*) as total_orders,
        AVG(total_order_value) as avg_order_value,

        -- Customer Metrics
        (SELECT total_customers FROM customer_stats) as total_customers,
        (SELECT new_customers FROM customer_stats) as new_customers,

        -- Delivery Metrics
        AVG(days_to_delivery) as avg_delivery_days,
        AVG(days_vs_estimated) as avg_days_vs_estimated,
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as late_delivery_pct,

        -- Satisfaction Metrics
        AVG(review_score) as avg_satisfaction_score,
        SUM(CASE WHEN is_positive_review THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_review_pct
    FROM filtered_orders
    """

    kpis = con.execute(kpi_query).df()
    return (kpis,)


@app.cell
def _(kpis, mo):
    # Display KPI cards
    mo.hstack([
        mo.vstack([
            mo.stat(
                label="Total GMV",
                value=f"R$ {kpis['total_gmv'].iloc[0]:,.0f}",
                caption="Gross Merchandise Value"
            ),
            mo.stat(
                label="Total Orders",
                value=f"{kpis['total_orders'].iloc[0]:,.0f}",
                caption="Delivered orders"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Average Order Value",
                value=f"R$ {kpis['avg_order_value'].iloc[0]:,.2f}",
                caption="Per transaction"
            ),
            mo.stat(
                label="New Customers",
                value=f"{kpis['new_customers'].iloc[0]:,.0f}",
                caption=f"of {kpis['total_customers'].iloc[0]:,.0f} total"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Avg Delivery Time",
                value=f"{kpis['avg_delivery_days'].iloc[0]:.1f} days",
                caption=f"{kpis['late_delivery_pct'].iloc[0]:.1f}% delivered late"
            ),
            mo.stat(
                label="Customer Satisfaction",
                value=f"{kpis['avg_satisfaction_score'].iloc[0]:.2f} / 5.0",
                caption=f"{kpis['positive_review_pct'].iloc[0]:.1f}% positive (4-5 stars)"
            ),
        ])
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Revenue Growth Analysis

    **Q1:** Month-over-month and year-over-year revenue growth trend

    **Q3:** Marketplace GMV trajectory
    """)
    return


@app.cell
def _(con, date_range):
    # Monthly revenue trend
    revenue_trend_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        COUNT(*) as total_orders,
        SUM(total_order_value) as monthly_revenue,
        AVG(total_order_value) as avg_order_value,
        COUNT(DISTINCT customer_id) as active_customers
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    revenue_trend = con.execute(revenue_trend_query).df()

    # Calculate growth rates
    revenue_trend['mom_growth'] = revenue_trend['monthly_revenue'].pct_change() * 100
    revenue_trend['yoy_growth'] = revenue_trend['monthly_revenue'].pct_change(periods=12) * 100
    return (revenue_trend,)


@app.cell
def _(px, revenue_trend):
    # Revenue trend visualization
    fig_revenue = px.line(
        revenue_trend,
        x='month',
        y='monthly_revenue',
        title='Monthly Revenue Trend (GMV)',
        labels={'monthly_revenue': 'Revenue (R$)', 'month': 'Month'},
        markers=True
    )

    fig_revenue.update_layout(
        hovermode='x unified',
        yaxis_tickformat=',.0f'
    )

    fig_revenue
    return


@app.cell
def _(px, revenue_trend):
    # Growth rates visualization
    fig_growth = px.line(
        revenue_trend[revenue_trend['mom_growth'].notna()],
        x='month',
        y=['mom_growth', 'yoy_growth'],
        title='Revenue Growth Rates',
        labels={'value': 'Growth Rate (%)', 'month': 'Month', 'variable': 'Metric'},
        markers=True
    )

    fig_growth.update_layout(
        hovermode='x unified',
        legend_title_text='Growth Type'
    )

    # Rename legend items
    fig_growth.for_each_trace(lambda t: t.update(
        name='Month-over-Month' if t.name == 'mom_growth' else 'Year-over-Year'
    ))

    fig_growth
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Acquisition & Activity

    **Q2:** New customers acquired monthly

    **Q5:** Order volume growth trend
    """)
    return


@app.cell
def _(con, date_range):
    # Customer acquisition trend
    customer_acquisition_query = f"""
    WITH customer_first_order AS (
        SELECT
            customer_id,
            MIN(order_date) as first_order_date
        FROM core_core.fct_orders
        WHERE is_delivered = TRUE
        GROUP BY customer_id
    )
    SELECT
        DATE_TRUNC('month', first_order_date) as month,
        COUNT(*) as new_customers
    FROM customer_first_order
    WHERE first_order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    GROUP BY DATE_TRUNC('month', first_order_date)
    ORDER BY month
    """

    customer_acquisition = con.execute(customer_acquisition_query).df()
    return (customer_acquisition,)


@app.cell
def _(con, date_range):
    # Order volume trend
    order_volume_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        COUNT(*) as total_orders,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(*)::FLOAT / COUNT(DISTINCT customer_id) as orders_per_customer
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    order_volume = con.execute(order_volume_query).df()
    return (order_volume,)


@app.cell
def _(customer_acquisition, make_subplots, order_volume):
    # Combined customer and order metrics
    fig_customer_orders = make_subplots(
        rows=2, cols=1,
        subplot_titles=('New Customer Acquisition', 'Order Volume'),
        vertical_spacing=0.12
    )

    # New customers
    fig_customer_orders.add_trace(
        {
            'type': 'bar',
            'x': customer_acquisition['month'],
            'y': customer_acquisition['new_customers'],
            'name': 'New Customers',
            'marker': {'color': '#636EFA'}
        },
        row=1, col=1
    )

    # Order volume
    fig_customer_orders.add_trace(
        {
            'type': 'scatter',
            'mode': 'lines+markers',
            'x': order_volume['month'],
            'y': order_volume['total_orders'],
            'name': 'Total Orders',
            'marker': {'color': '#EF553B'}
        },
        row=2, col=1
    )

    fig_customer_orders.update_xaxes(title_text="Month", row=2, col=1)
    fig_customer_orders.update_yaxes(title_text="New Customers", row=1, col=1)
    fig_customer_orders.update_yaxes(title_text="Orders", row=2, col=1)

    fig_customer_orders.update_layout(
        height=600,
        showlegend=False,
        title_text="Customer Acquisition & Order Volume Trends"
    )

    fig_customer_orders
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Average Order Value Analysis

    **Q6:** Average order value (AOV) and trend over time
    """)
    return


@app.cell
def _(px, revenue_trend):
    # AOV trend
    fig_aov = px.line(
        revenue_trend,
        x='month',
        y='avg_order_value',
        title='Average Order Value (AOV) Trend',
        labels={'avg_order_value': 'AOV (R$)', 'month': 'Month'},
        markers=True
    )

    fig_aov.update_layout(
        hovermode='x unified',
        yaxis_tickformat=',.2f'
    )

    fig_aov
    return


@app.cell
def _(con, date_range):
    # AOV distribution by order size
    aov_distribution_query = f"""
    SELECT
        CASE
            WHEN total_order_value < 50 THEN '< R$ 50'
            WHEN total_order_value < 100 THEN 'R$ 50-100'
            WHEN total_order_value < 200 THEN 'R$ 100-200'
            WHEN total_order_value < 500 THEN 'R$ 200-500'
            ELSE 'R$ 500+'
        END as order_value_range,
        COUNT(*) as order_count,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY order_value_range
    ORDER BY
        CASE order_value_range
            WHEN '< R$ 50' THEN 1
            WHEN 'R$ 50-100' THEN 2
            WHEN 'R$ 100-200' THEN 3
            WHEN 'R$ 200-500' THEN 4
            ELSE 5
        END
    """

    aov_distribution = con.execute(aov_distribution_query).df()
    return (aov_distribution,)


@app.cell
def _(aov_distribution, make_subplots):
    # AOV distribution visualization
    fig_aov_dist = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Orders by Value Range', 'Revenue by Value Range'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Order count
    fig_aov_dist.add_trace(
        {
            'type': 'bar',
            'x': aov_distribution['order_value_range'],
            'y': aov_distribution['order_count'],
            'name': 'Order Count',
            'marker': {'color': '#00CC96'}
        },
        row=1, col=1
    )

    # Revenue
    fig_aov_dist.add_trace(
        {
            'type': 'bar',
            'x': aov_distribution['order_value_range'],
            'y': aov_distribution['total_revenue'],
            'name': 'Total Revenue',
            'marker': {'color': '#AB63FA'}
        },
        row=1, col=2
    )

    fig_aov_dist.update_yaxes(title_text="Order Count", row=1, col=1)
    fig_aov_dist.update_yaxes(title_text="Revenue (R$)", row=1, col=2)

    fig_aov_dist.update_layout(
        height=400,
        showlegend=False,
        title_text="Order Value Distribution"
    )

    fig_aov_dist
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Delivery Performance

    **Q21:** Average delivery time vs promised delivery time
    """)
    return


@app.cell
def _(con, date_range):
    # Delivery performance metrics
    delivery_performance_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        AVG(days_to_delivery) as avg_delivery_days,
        AVG(days_vs_estimated) as avg_days_vs_estimated,
        SUM(CASE WHEN delivery_performance = 'Early' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as early_pct,
        SUM(CASE WHEN delivery_performance = 'On Time' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as ontime_pct,
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as late_pct
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    delivery_performance = con.execute(delivery_performance_query).df()
    return (delivery_performance,)


@app.cell
def _(delivery_performance, px):
    # Delivery time trend
    fig_delivery = px.line(
        delivery_performance,
        x='month',
        y='avg_delivery_days',
        title='Average Delivery Time Trend',
        labels={'avg_delivery_days': 'Avg Days to Delivery', 'month': 'Month'},
        markers=True
    )

    fig_delivery.update_layout(hovermode='x unified')
    fig_delivery
    return


@app.cell
def _(delivery_performance, px):
    # Delivery performance breakdown
    delivery_perf_melt = delivery_performance.melt(
        id_vars=['month'],
        value_vars=['early_pct', 'ontime_pct', 'late_pct'],
        var_name='performance',
        value_name='percentage'
    )

    fig_delivery_perf = px.area(
        delivery_perf_melt,
        x='month',
        y='percentage',
        color='performance',
        title='Delivery Performance Distribution Over Time',
        labels={'percentage': 'Percentage (%)', 'month': 'Month', 'performance': 'Performance'},
        color_discrete_map={
            'early_pct': '#00CC96',
            'ontime_pct': '#636EFA',
            'late_pct': '#EF553B'
        }
    )

    # Update legend labels
    fig_delivery_perf.for_each_trace(lambda t: t.update(
        name={'early_pct': 'Early', 'ontime_pct': 'On Time', 'late_pct': 'Late'}[t.name]
    ))

    fig_delivery_perf.update_layout(hovermode='x unified')
    fig_delivery_perf
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Satisfaction

    **Q31:** Overall customer satisfaction score (NPS proxy from review ratings)
    """)
    return


@app.cell
def _(con, date_range):
    # Customer satisfaction trend
    satisfaction_trend_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        AVG(review_score) as avg_review_score,
        SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as five_star_pct,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_pct,
        SUM(CASE WHEN review_score = 3 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as neutral_pct,
        SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as negative_pct
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    satisfaction_trend = con.execute(satisfaction_trend_query).df()
    return (satisfaction_trend,)


@app.cell
def _(px, satisfaction_trend):
    # Satisfaction score trend
    fig_satisfaction = px.line(
        satisfaction_trend,
        x='month',
        y='avg_review_score',
        title='Average Customer Satisfaction Score (1-5 scale)',
        labels={'avg_review_score': 'Avg Review Score', 'month': 'Month'},
        markers=True
    )

    fig_satisfaction.update_layout(
        hovermode='x unified',
        yaxis_range=[1, 5]
    )

    fig_satisfaction
    return


@app.cell
def _(con, date_range):
    # Review score distribution
    review_distribution_query = f"""
    SELECT
        review_score,
        COUNT(*) as review_count,
        COUNT(*)::FLOAT / (SELECT COUNT(*) FROM core_core.fct_orders
                           WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
                           AND is_delivered = TRUE
                           AND review_score IS NOT NULL) * 100 as percentage
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    GROUP BY review_score
    ORDER BY review_score
    """

    review_distribution = con.execute(review_distribution_query).df()
    return (review_distribution,)


@app.cell
def _(px, review_distribution):
    # Review distribution bar chart
    fig_review_dist = px.bar(
        review_distribution,
        x='review_score',
        y='percentage',
        title='Review Score Distribution',
        labels={'percentage': 'Percentage (%)', 'review_score': 'Review Score'},
        text='percentage',
        color='review_score',
        color_continuous_scale='RdYlGn'
    )

    fig_review_dist.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_review_dist.update_layout(showlegend=False, xaxis_type='category')
    fig_review_dist
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the data analysis above, here are the key takeaways:

    **Revenue & Growth:**
    - Track month-over-month and year-over-year revenue trends
    - Monitor GMV trajectory and identify growth patterns
    - Analyze AOV trends and order value distribution

    **Customer Acquisition:**
    - Monitor new customer acquisition rates
    - Track active customer base growth
    - Identify seasonal patterns in customer acquisition

    **Operational Excellence:**
    - Average delivery time performance vs. estimates
    - Late delivery percentage and trends
    - Correlation between delivery performance and satisfaction

    **Customer Satisfaction:**
    - Overall satisfaction score (NPS proxy)
    - Review score distribution and trends
    - Identify periods of declining satisfaction for investigation

    **Recommendations:**
    - Focus on reducing late deliveries to improve satisfaction
    - Investigate months with declining growth rates
    - Monitor AOV trends for pricing strategy insights
    - Target customer segments with high satisfaction for retention
    """)
    return


if __name__ == "__main__":
    app.run()
