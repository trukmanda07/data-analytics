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
    return Path, duckdb, go, load_dotenv, make_subplots, mo, os, px


@app.cell
def _(mo):
    mo.md("""
    # Marketing & Sales Timing Analysis - Olist E-Commerce

    **Business Questions Answered:**
    - Q76: Peak sales periods (day of week, month, season)
    - Q17: Seasonal revenue patterns for campaign planning
    - Q80: Customer segments to target for reactivation

    **Data Source:** fct_orders & dim_customers

    **Dataset Period:** 2016-2018
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
    ## Day of Week Analysis

    **Q76:** Peak sales periods (day of week, month, season)
    """)
    return


@app.cell
def _(con, date_range):
    # Day of week analysis
    dow_query = f"""
    SELECT
        EXTRACT(DAYOFWEEK FROM order_date) as day_of_week_num,
        CASE EXTRACT(DAYOFWEEK FROM order_date)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
        END as day_of_week,
        COUNT(*) as total_orders,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY EXTRACT(DAYOFWEEK FROM order_date), day_of_week
    ORDER BY day_of_week_num
    """

    dow_data = con.execute(dow_query).df()
    return (dow_data,)


@app.cell
def _(dow_data, go, make_subplots):
    # Day of week patterns
    fig_dow = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Orders by Day of Week', 'Revenue by Day of Week'),
        vertical_spacing=0.12
    )

    # Orders
    fig_dow.add_trace(
        go.Bar(
            x=dow_data['day_of_week'],
            y=dow_data['total_orders'],
            marker_color='#636EFA',
            text=dow_data['total_orders'],
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )

    # Revenue
    fig_dow.add_trace(
        go.Bar(
            x=dow_data['day_of_week'],
            y=dow_data['total_revenue'],
            marker_color='#00CC96',
            text=dow_data['total_revenue'].apply(lambda x: f'R$ {x/1000:.0f}K'),
            textposition='outside',
            showlegend=False
        ),
        row=2, col=1
    )

    fig_dow.update_yaxes(title_text="Order Count", row=1, col=1)
    fig_dow.update_yaxes(title_text="Revenue (R$)", row=2, col=1)
    fig_dow.update_xaxes(title_text="Day of Week", row=2, col=1)

    fig_dow.update_layout(
        height=600,
        title_text="Sales Patterns by Day of Week"
    )

    fig_dow
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Monthly and Seasonal Patterns

    **Q17:** Seasonal revenue patterns for campaign planning
    """)
    return


@app.cell
def _(con, date_range):
    # Monthly seasonality
    monthly_query = f"""
    SELECT
        EXTRACT(MONTH FROM order_date) as month_num,
        CASE EXTRACT(MONTH FROM order_date)
            WHEN 1 THEN 'January'
            WHEN 2 THEN 'February'
            WHEN 3 THEN 'March'
            WHEN 4 THEN 'April'
            WHEN 5 THEN 'May'
            WHEN 6 THEN 'June'
            WHEN 7 THEN 'July'
            WHEN 8 THEN 'August'
            WHEN 9 THEN 'September'
            WHEN 10 THEN 'October'
            WHEN 11 THEN 'November'
            WHEN 12 THEN 'December'
        END as month_name,
        COUNT(*) as total_orders,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value,
        COUNT(DISTINCT customer_id) as unique_customers
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY EXTRACT(MONTH FROM order_date), month_name
    ORDER BY month_num
    """

    monthly_data = con.execute(monthly_query).df()
    return (monthly_data,)


@app.cell
def _(monthly_data, px):
    # Monthly revenue pattern
    fig_monthly = px.line(
        monthly_data,
        x='month_name',
        y='total_revenue',
        title='Monthly Revenue Seasonality',
        labels={'total_revenue': 'Revenue (R$)', 'month_name': 'Month'},
        markers=True
    )

    fig_monthly.update_layout(
        hovermode='x unified',
        yaxis_tickformat=',.0f'
    )

    fig_monthly
    return


@app.cell
def _(monthly_data, px):
    # Monthly order volume pattern
    fig_monthly_orders = px.bar(
        monthly_data,
        x='month_name',
        y='total_orders',
        title='Monthly Order Volume Pattern',
        labels={'total_orders': 'Order Count', 'month_name': 'Month'},
        color='total_orders',
        color_continuous_scale='Blues',
        text='total_orders'
    )

    fig_monthly_orders.update_traces(textposition='outside')
    fig_monthly_orders.update_layout(showlegend=False)
    fig_monthly_orders
    return


@app.cell
def _(con, date_range):
    # Quarterly analysis
    quarterly_query = f"""
    SELECT
        EXTRACT(QUARTER FROM order_date) as quarter,
        EXTRACT(YEAR FROM order_date) as year,
        COUNT(*) as total_orders,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY EXTRACT(QUARTER FROM order_date), EXTRACT(YEAR FROM order_date)
    ORDER BY year, quarter
    """

    quarterly_data = con.execute(quarterly_query).df()
    quarterly_data['period'] = quarterly_data['year'].astype(str) + ' Q' + quarterly_data['quarter'].astype(str)
    return (quarterly_data,)


@app.cell
def _(px, quarterly_data):
    # Quarterly revenue trend
    fig_quarterly = px.bar(
        quarterly_data,
        x='period',
        y='total_revenue',
        title='Quarterly Revenue Trend',
        labels={'total_revenue': 'Revenue (R$)', 'period': 'Quarter'},
        color='total_revenue',
        color_continuous_scale='Greens',
        text='total_revenue'
    )

    fig_quarterly.update_traces(
        texttemplate='R$ %{text:,.0f}',
        textposition='outside'
    )
    fig_quarterly.update_layout(showlegend=False)
    fig_quarterly
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Hour of Day Analysis

    Understanding when customers shop during the day
    """)
    return


@app.cell
def _(con, date_range):
    # Hour of day analysis
    hour_query = f"""
    SELECT
        EXTRACT(HOUR FROM order_purchase_timestamp) as hour,
        COUNT(*) as total_orders,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND order_purchase_timestamp IS NOT NULL
    GROUP BY EXTRACT(HOUR FROM order_purchase_timestamp)
    ORDER BY hour
    """

    hour_data = con.execute(hour_query).df()
    return (hour_data,)


@app.cell
def _(hour_data, px):
    # Hourly pattern
    fig_hourly = px.line(
        hour_data,
        x='hour',
        y='total_orders',
        title='Order Volume by Hour of Day',
        labels={'total_orders': 'Order Count', 'hour': 'Hour (24h format)'},
        markers=True
    )

    fig_hourly.update_layout(
        hovermode='x unified',
        xaxis_tickvals=list(range(0, 24, 2))
    )

    fig_hourly
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Reactivation Opportunities

    **Q80:** Customer segments to target for reactivation
    """)
    return


@app.cell
def _(con, date_range):
    # Customer reactivation analysis
    reactivation_query = f"""
    WITH customer_activity AS (
        SELECT
            c.customer_id,
            c.customer_segment,
            c.lifetime_orders,
            c.first_order_date,
            c.last_order_date,
            c.days_since_last_order,
            c.avg_review_score
        FROM core_core.dim_customers c
        WHERE c.first_order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    )
    SELECT
        CASE
            WHEN days_since_last_order <= 30 THEN 'Active (0-30 days)'
            WHEN days_since_last_order <= 90 THEN 'At Risk (31-90 days)'
            WHEN days_since_last_order <= 180 THEN 'Dormant (91-180 days)'
            WHEN days_since_last_order <= 365 THEN 'Lapsed (181-365 days)'
            ELSE 'Churned (365+ days)'
        END as reactivation_segment,
        COUNT(*) as customer_count,
        AVG(lifetime_orders) as avg_orders,
        AVG(avg_review_score) as avg_satisfaction
    FROM customer_activity
    WHERE days_since_last_order IS NOT NULL
    GROUP BY reactivation_segment
    ORDER BY
        CASE reactivation_segment
            WHEN 'Active (0-30 days)' THEN 1
            WHEN 'At Risk (31-90 days)' THEN 2
            WHEN 'Dormant (91-180 days)' THEN 3
            WHEN 'Lapsed (181-365 days)' THEN 4
            ELSE 5
        END
    """

    reactivation_data = con.execute(reactivation_query).df()
    return (reactivation_data,)


@app.cell
def _(px, reactivation_data):
    # Customer reactivation segments
    fig_reactivation = px.bar(
        reactivation_data,
        x='reactivation_segment',
        y='customer_count',
        title='Customer Reactivation Segments',
        labels={'customer_count': 'Customer Count', 'reactivation_segment': 'Segment'},
        color='customer_count',
        color_continuous_scale='Reds',
        text='customer_count'
    )

    fig_reactivation.update_traces(textposition='outside')
    fig_reactivation.update_layout(showlegend=False)
    fig_reactivation.update_xaxes(tickangle=45)
    fig_reactivation
    return


@app.cell
def _(con, date_range):
    # High-value dormant customers
    dormant_value_query = f"""
    WITH customer_activity AS (
        SELECT
            c.customer_id,
            c.lifetime_orders,
            c.days_since_last_order,
            SUM(o.total_order_value) as lifetime_value
        FROM core_core.dim_customers c
        JOIN core_core.fct_orders o ON c.customer_id = o.customer_id
        WHERE o.is_delivered = TRUE
        AND c.first_order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        GROUP BY c.customer_id, c.lifetime_orders, c.days_since_last_order
    )
    SELECT
        CASE
            WHEN days_since_last_order BETWEEN 90 AND 180 THEN 'Dormant'
            WHEN days_since_last_order BETWEEN 181 AND 365 THEN 'Lapsed'
            ELSE 'Churned'
        END as segment,
        CASE
            WHEN lifetime_value < 200 THEN 'Low Value'
            WHEN lifetime_value < 500 THEN 'Medium Value'
            ELSE 'High Value'
        END as value_segment,
        COUNT(*) as customer_count,
        AVG(lifetime_value) as avg_ltv
    FROM customer_activity
    WHERE days_since_last_order >= 90
    AND lifetime_orders >= 2
    GROUP BY segment, value_segment
    ORDER BY segment, avg_ltv DESC
    """

    dormant_value = con.execute(dormant_value_query).df()
    return (dormant_value,)


@app.cell
def _(dormant_value, px):
    # Dormant customer value distribution
    fig_dormant_value = px.bar(
        dormant_value,
        x='segment',
        y='customer_count',
        color='value_segment',
        title='Dormant/Lapsed Customers by Value Segment',
        labels={'customer_count': 'Customer Count', 'segment': 'Activity Segment'},
        barmode='group',
        text='customer_count'
    )

    fig_dormant_value.update_traces(textposition='outside')
    fig_dormant_value.update_layout(height=500)
    fig_dormant_value
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Campaign Timing Recommendations

    Based on the analysis above
    """)
    return


@app.cell
def _(dow_data, hour_data, mo, monthly_data):
    # Calculate key insights
    peak_dow = dow_data.loc[dow_data['total_orders'].idxmax(), 'day_of_week']
    peak_month = monthly_data.loc[monthly_data['total_revenue'].idxmax(), 'month_name']
    peak_hour = hour_data.loc[hour_data['total_orders'].idxmax(), 'hour']

    mo.md(f"""
    ## Key Timing Insights

    **Peak Sales Day:** {peak_dow}
    - Highest order volume consistently occurs on {peak_dow}
    - Schedule major promotions and campaigns for this day

    **Peak Sales Month:** {peak_month}
    - {peak_month} shows the highest revenue
    - Plan inventory and marketing budgets accordingly
    - Seasonal campaigns should target this period

    **Peak Shopping Hour:** {int(peak_hour)}:00
    - Most orders placed around {int(peak_hour)}:00 (24h format)
    - Schedule email campaigns and flash sales for this time
    - Optimize website performance during peak hours

    **Reactivation Opportunities:**
    - Target "At Risk" customers (31-90 days inactive)
    - Focus on dormant high-value customers
    - Create win-back campaigns for lapsed customers
    - Offer incentives to prevent churn

    **Campaign Recommendations:**
    - **Weekly:** Launch promotions on {peak_dow}
    - **Monthly:** Focus budgets on {peak_month} and surrounding months
    - **Daily:** Send marketing emails around {int(peak_hour)-2}:00 - {int(peak_hour)}:00
    - **Retention:** Reach out to customers at 60-day mark to prevent dormancy
    - **Seasonal:** Prepare for Q4 holiday season with increased inventory
    - **Reactivation:** Create targeted campaigns for dormant high-value customers
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    **Day of Week Patterns:**
    - Identify peak days for sales
    - Schedule promotions on high-traffic days
    - Optimize customer support staffing

    **Seasonal Trends:**
    - Plan inventory based on monthly patterns
    - Allocate marketing budgets to peak seasons
    - Prepare for seasonal demand fluctuations

    **Hourly Patterns:**
    - Send email campaigns at optimal times
    - Schedule flash sales during peak hours
    - Ensure website performance during busy periods

    **Customer Reactivation:**
    - Large pool of at-risk and dormant customers
    - High-value dormant customers represent revenue opportunity
    - Implement retention campaigns before 90-day mark
    - Create win-back offers for lapsed customers

    **Strategic Recommendations:**
    - Develop calendar of promotional events aligned with peak periods
    - Create automated reactivation campaigns
    - Optimize ad spend timing based on hourly and daily patterns
    - Implement early warning system for customer churn
    - Target high-value customers with personalized retention offers
    """)
    return


if __name__ == "__main__":
    app.run()
