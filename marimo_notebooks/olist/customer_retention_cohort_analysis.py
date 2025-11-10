import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import duckdb
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    import numpy as np
    return mo, duckdb, pd, px, go, make_subplots, os, Path, load_dotenv, np


@app.cell
def __(mo):
    mo.md("""
    # Customer Retention & Cohort Analysis - Olist E-Commerce

    **Business Questions Answered:**
    - Q36: Customer repeat purchase rate
    - Q37: Average time between first and second purchase
    - Q39: Customer churn rate month-over-month
    - Q40: Do customers who write reviews have different purchasing patterns?
    - Q72: Customer cohort retention analysis (monthly cohorts)
    - Q75: First-time buyer behaviors vs repeat customers

    **Data Source:** dim_customers & fct_orders

    **Dataset Period:** 2016-2018
    """)
    return


@app.cell
def __(duckdb, load_dotenv, os, Path):
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)

    # Configure database for this notebook
    db_name = 'olist_analytical.duckdb'
    db_dir = os.getenv('DUCKDB_DIR')
    db_path = os.path.join(db_dir, db_name)

    # Connect to DuckDB analytical database
    con = duckdb.connect(database=db_path, read_only=True)

    return con, db_path, db_name, env_path


@app.cell
def __(mo):
    mo.md("""
    ## Date Range Filter

    Select the time period for your analysis:
    """)
    return


@app.cell
def __(mo):
    date_range = mo.ui.date_range(
        start="2016-09-01",
        stop="2018-08-31",
        label="Analysis Period",
        value=("2016-09-01", "2018-08-31")
    )
    date_range
    return (date_range,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Customer Retention KPIs

    High-level retention metrics for the selected period:
    """)
    return


@app.cell
def __(con, date_range):
    # Calculate retention KPIs
    retention_kpi_query = f"""
    WITH customer_orders AS (
        SELECT
            customer_id,
            COUNT(*) as order_count,
            MIN(order_date) as first_order_date,
            MAX(order_date) as last_order_date
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
        GROUP BY customer_id
    )
    SELECT
        COUNT(DISTINCT customer_id) as total_customers,
        SUM(CASE WHEN order_count = 1 THEN 1 ELSE 0 END) as one_time_customers,
        SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) as repeat_customers,
        SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as repeat_rate,
        AVG(order_count) as avg_orders_per_customer,
        AVG(CASE WHEN order_count >= 2 THEN DATE_DIFF('day', first_order_date, last_order_date) END) as avg_customer_lifetime_days
    FROM customer_orders
    """

    retention_kpis = con.execute(retention_kpi_query).df()
    return retention_kpi_query, retention_kpis


@app.cell
def __(mo, retention_kpis):
    # Display retention KPI cards
    mo.hstack([
        mo.vstack([
            mo.stat(
                label="Total Customers",
                value=f"{retention_kpis['total_customers'].iloc[0]:,}",
                caption="In selected period"
            ),
            mo.stat(
                label="Repeat Customer Rate",
                value=f"{retention_kpis['repeat_rate'].iloc[0]:.1f}%",
                caption=f"{retention_kpis['repeat_customers'].iloc[0]:,} repeat customers"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="One-Time Customers",
                value=f"{retention_kpis['one_time_customers'].iloc[0]:,}",
                caption="Never returned"
            ),
            mo.stat(
                label="Avg Orders per Customer",
                value=f"{retention_kpis['avg_orders_per_customer'].iloc[0]:.2f}",
                caption="Across all customers"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Avg Customer Lifetime",
                value=f"{retention_kpis['avg_customer_lifetime_days'].iloc[0]:.0f} days",
                caption="For repeat customers"
            ),
        ])
    ])
    return


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Customer Segmentation

    **Q36:** Customer repeat purchase rate

    **Q75:** First-time buyer behaviors vs repeat customers
    """)
    return


@app.cell
def __(con, date_range):
    # Customer segmentation analysis
    segment_query = f"""
    WITH customer_orders AS (
        SELECT
            customer_id,
            COUNT(*) as order_count,
            SUM(total_order_value) as lifetime_value,
            AVG(total_order_value) as avg_order_value,
            MIN(order_date) as first_order_date,
            MAX(order_date) as last_order_date
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
        GROUP BY customer_id
    )
    SELECT
        CASE
            WHEN order_count = 1 THEN '1 Order (One-time)'
            WHEN order_count = 2 THEN '2 Orders'
            WHEN order_count = 3 THEN '3 Orders'
            WHEN order_count BETWEEN 4 AND 5 THEN '4-5 Orders'
            ELSE '6+ Orders'
        END as customer_segment,
        COUNT(*) as customer_count,
        SUM(lifetime_value) as total_revenue,
        AVG(lifetime_value) as avg_ltv,
        AVG(avg_order_value) as avg_aov
    FROM customer_orders
    GROUP BY customer_segment
    ORDER BY
        CASE customer_segment
            WHEN '1 Order (One-time)' THEN 1
            WHEN '2 Orders' THEN 2
            WHEN '3 Orders' THEN 3
            WHEN '4-5 Orders' THEN 4
            ELSE 5
        END
    """

    segments = con.execute(segment_query).df()

    # Calculate percentages
    segments['customer_pct'] = segments['customer_count'] / segments['customer_count'].sum() * 100
    segments['revenue_pct'] = segments['total_revenue'] / segments['total_revenue'].sum() * 100

    return segment_query, segments


@app.cell
def __(make_subplots, go, segments):
    # Customer and revenue distribution
    fig_segments = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Customer Distribution', 'Revenue Distribution'),
        specs=[[{'type': 'pie'}, {'type': 'pie'}]]
    )

    # Customer count
    fig_segments.add_trace(
        go.Pie(
            labels=segments['customer_segment'],
            values=segments['customer_count'],
            name='Customers',
            textposition='inside',
            textinfo='label+percent',
            hole=0.3
        ),
        row=1, col=1
    )

    # Revenue
    fig_segments.add_trace(
        go.Pie(
            labels=segments['customer_segment'],
            values=segments['total_revenue'],
            name='Revenue',
            textposition='inside',
            textinfo='label+percent',
            hole=0.3
        ),
        row=1, col=2
    )

    fig_segments.update_layout(
        height=450,
        showlegend=True,
        title_text="Customer Segmentation by Order Frequency"
    )

    fig_segments
    return (fig_segments,)


@app.cell
def __(px, segments):
    # LTV by segment
    fig_ltv = px.bar(
        segments,
        x='customer_segment',
        y='avg_ltv',
        title='Average Lifetime Value by Customer Segment',
        labels={'avg_ltv': 'Avg LTV (R$)', 'customer_segment': 'Segment'},
        color='avg_ltv',
        color_continuous_scale='Greens',
        text='avg_ltv'
    )

    fig_ltv.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
    fig_ltv.update_layout(showlegend=False)
    fig_ltv
    return (fig_ltv,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Time to Second Purchase

    **Q37:** Average time between first and second purchase
    """)
    return


@app.cell
def __(con, date_range):
    # Time between first and second purchase
    time_to_second_query = f"""
    WITH customer_orders AS (
        SELECT
            customer_id,
            order_date,
            ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) as order_number
        FROM core_core.fct_orders
        WHERE is_delivered = TRUE
    ),
    first_second_orders AS (
        SELECT
            customer_id,
            MAX(CASE WHEN order_number = 1 THEN order_date END) as first_order_date,
            MAX(CASE WHEN order_number = 2 THEN order_date END) as second_order_date
        FROM customer_orders
        WHERE order_number <= 2
        GROUP BY customer_id
        HAVING MAX(CASE WHEN order_number = 2 THEN order_date END) IS NOT NULL
    )
    SELECT
        DATE_DIFF('day', first_order_date, second_order_date) as days_to_second_purchase
    FROM first_second_orders
    WHERE first_order_date >= '{date_range.value[0]}'
    AND second_order_date <= '{date_range.value[1]}'
    """

    time_to_second = con.execute(time_to_second_query).df()
    return time_to_second, time_to_second_query


@app.cell
def __(time_to_second, np):
    # Calculate statistics
    avg_days = time_to_second['days_to_second_purchase'].mean()
    median_days = time_to_second['days_to_second_purchase'].median()

    # Create bins for distribution
    time_to_second['days_bucket'] = pd.cut(
        time_to_second['days_to_second_purchase'],
        bins=[0, 30, 60, 90, 120, 180, 365, np.inf],
        labels=['0-30 days', '31-60 days', '61-90 days', '91-120 days', '121-180 days', '181-365 days', '365+ days']
    )

    time_distribution = time_to_second.groupby('days_bucket', observed=True).size().reset_index(name='customer_count')

    return avg_days, median_days, time_distribution


@app.cell
def __(mo, avg_days, median_days):
    mo.md(f"""
    **Average time to 2nd purchase:** {avg_days:.1f} days

    **Median time to 2nd purchase:** {median_days:.1f} days
    """)
    return


@app.cell
def __(px, time_distribution):
    # Distribution of time to second purchase
    fig_time_second = px.bar(
        time_distribution,
        x='days_bucket',
        y='customer_count',
        title='Distribution of Time Between 1st and 2nd Purchase',
        labels={'customer_count': 'Number of Customers', 'days_bucket': 'Time Period'},
        color='customer_count',
        color_continuous_scale='Blues',
        text='customer_count'
    )

    fig_time_second.update_traces(textposition='outside')
    fig_time_second.update_layout(showlegend=False)
    fig_time_second
    return (fig_time_second,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Monthly Cohort Retention Analysis

    **Q72:** Customer cohort retention analysis (monthly cohorts)
    """)
    return


@app.cell
def __(con, date_range):
    # Cohort retention analysis
    cohort_query = f"""
    WITH customer_cohorts AS (
        SELECT
            customer_id,
            DATE_TRUNC('month', MIN(order_date)) as cohort_month,
            MIN(order_date) as first_order_date
        FROM core_core.fct_orders
        WHERE is_delivered = TRUE
        GROUP BY customer_id
    ),
    customer_activities AS (
        SELECT
            f.customer_id,
            c.cohort_month,
            DATE_TRUNC('month', f.order_date) as activity_month,
            DATE_DIFF('month', c.cohort_month, DATE_TRUNC('month', f.order_date)) as months_since_first
        FROM core_core.fct_orders f
        JOIN customer_cohorts c ON f.customer_id = c.customer_id
        WHERE f.is_delivered = TRUE
        AND f.order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    )
    SELECT
        cohort_month,
        months_since_first,
        COUNT(DISTINCT customer_id) as active_customers
    FROM customer_activities
    WHERE cohort_month >= '{date_range.value[0]}'
    GROUP BY cohort_month, months_since_first
    ORDER BY cohort_month, months_since_first
    """

    cohort_data = con.execute(cohort_query).df()
    return cohort_data, cohort_query


@app.cell
def __(cohort_data, pd):
    # Create cohort retention matrix
    cohort_pivot = cohort_data.pivot(
        index='cohort_month',
        columns='months_since_first',
        values='active_customers'
    ).fillna(0)

    # Calculate retention percentages
    cohort_sizes = cohort_pivot[0]
    cohort_retention = cohort_pivot.divide(cohort_sizes, axis=0) * 100

    return cohort_pivot, cohort_retention, cohort_sizes


@app.cell
def __(px, cohort_retention):
    # Cohort retention heatmap
    fig_cohort = px.imshow(
        cohort_retention,
        labels=dict(x="Months Since First Purchase", y="Cohort Month", color="Retention %"),
        x=[f"Month {i}" for i in cohort_retention.columns],
        y=cohort_retention.index.astype(str),
        color_continuous_scale='RdYlGn',
        title='Monthly Cohort Retention Heatmap (%)',
        aspect='auto'
    )

    fig_cohort.update_layout(height=600)
    fig_cohort
    return (fig_cohort,)


@app.cell
def __(cohort_retention):
    # Average retention curve across all cohorts
    avg_retention_curve = cohort_retention.mean(axis=0).reset_index()
    avg_retention_curve.columns = ['months_since_first', 'avg_retention_pct']

    return (avg_retention_curve,)


@app.cell
def __(px, avg_retention_curve):
    # Average retention curve
    fig_retention_curve = px.line(
        avg_retention_curve,
        x='months_since_first',
        y='avg_retention_pct',
        title='Average Customer Retention Curve',
        labels={'avg_retention_pct': 'Retention %', 'months_since_first': 'Months Since First Purchase'},
        markers=True
    )

    fig_retention_curve.update_layout(
        hovermode='x unified',
        yaxis_range=[0, 100]
    )

    fig_retention_curve
    return (fig_retention_curve,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Monthly Churn Analysis

    **Q39:** Customer churn rate month-over-month
    """)
    return


@app.cell
def __(con, date_range):
    # Monthly churn analysis
    churn_query = f"""
    WITH monthly_active_customers AS (
        SELECT
            DATE_TRUNC('month', order_date) as activity_month,
            customer_id
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
        GROUP BY DATE_TRUNC('month', order_date), customer_id
    ),
    monthly_metrics AS (
        SELECT
            activity_month,
            COUNT(DISTINCT customer_id) as active_customers,
            LAG(COUNT(DISTINCT customer_id)) OVER (ORDER BY activity_month) as prev_active_customers
        FROM monthly_active_customers
        GROUP BY activity_month
        ORDER BY activity_month
    )
    SELECT
        activity_month as month,
        active_customers,
        prev_active_customers,
        CASE
            WHEN prev_active_customers > 0
            THEN ((prev_active_customers - active_customers)::FLOAT / prev_active_customers * 100)
            ELSE NULL
        END as churn_rate
    FROM monthly_metrics
    WHERE prev_active_customers IS NOT NULL
    """

    churn_data = con.execute(churn_query).df()
    return churn_data, churn_query


@app.cell
def __(make_subplots, go, churn_data):
    # Churn rate visualization
    fig_churn = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Active Customers', 'Month-over-Month Churn Rate'),
        vertical_spacing=0.15
    )

    # Active customers
    fig_churn.add_trace(
        go.Scatter(
            x=churn_data['month'],
            y=churn_data['active_customers'],
            mode='lines+markers',
            name='Active Customers',
            line=dict(color='#636EFA', width=2)
        ),
        row=1, col=1
    )

    # Churn rate
    fig_churn.add_trace(
        go.Scatter(
            x=churn_data['month'],
            y=churn_data['churn_rate'],
            mode='lines+markers',
            name='Churn Rate',
            line=dict(color='#EF553B', width=2),
            fill='tozeroy'
        ),
        row=2, col=1
    )

    fig_churn.update_yaxes(title_text="Active Customers", row=1, col=1)
    fig_churn.update_yaxes(title_text="Churn Rate (%)", row=2, col=1)
    fig_churn.update_xaxes(title_text="Month", row=2, col=1)

    fig_churn.update_layout(
        height=600,
        showlegend=False,
        title_text="Customer Churn Analysis",
        hovermode='x unified'
    )

    fig_churn
    return (fig_churn,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Review Writers vs Non-Review Writers

    **Q40:** Do customers who write reviews have different purchasing patterns?
    """)
    return


@app.cell
def __(con, date_range):
    # Compare review writers vs non-writers
    review_comparison_query = f"""
    WITH customer_review_behavior AS (
        SELECT
            customer_id,
            COUNT(DISTINCT order_id) as total_orders,
            SUM(total_order_value) as lifetime_value,
            AVG(total_order_value) as avg_order_value,
            SUM(CASE WHEN review_score IS NOT NULL THEN 1 ELSE 0 END) as orders_with_review,
            MIN(order_date) as first_order_date,
            MAX(order_date) as last_order_date
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
        GROUP BY customer_id
    )
    SELECT
        CASE
            WHEN orders_with_review > 0 THEN 'Review Writers'
            ELSE 'Non-Review Writers'
        END as customer_type,
        COUNT(*) as customer_count,
        AVG(total_orders) as avg_orders,
        AVG(lifetime_value) as avg_ltv,
        AVG(avg_order_value) as avg_aov,
        SUM(CASE WHEN total_orders >= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as repeat_rate,
        AVG(DATE_DIFF('day', first_order_date, last_order_date)) as avg_lifetime_days
    FROM customer_review_behavior
    GROUP BY customer_type
    """

    review_comparison = con.execute(review_comparison_query).df()
    return review_comparison, review_comparison_query


@app.cell
def __(review_comparison):
    # Display comparison table
    review_comparison
    return


@app.cell
def __(make_subplots, go, review_comparison):
    # Comparison visualization
    fig_review_comp = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Average Orders', 'Average LTV', 'Repeat Rate', 'Avg AOV'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}], [{'type': 'bar'}, {'type': 'bar'}]]
    )

    colors = ['#636EFA', '#EF553B']

    # Avg orders
    fig_review_comp.add_trace(
        go.Bar(
            x=review_comparison['customer_type'],
            y=review_comparison['avg_orders'],
            marker_color=colors,
            text=review_comparison['avg_orders'].apply(lambda x: f'{x:.2f}'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )

    # Avg LTV
    fig_review_comp.add_trace(
        go.Bar(
            x=review_comparison['customer_type'],
            y=review_comparison['avg_ltv'],
            marker_color=colors,
            text=review_comparison['avg_ltv'].apply(lambda x: f'R$ {x:.2f}'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )

    # Repeat rate
    fig_review_comp.add_trace(
        go.Bar(
            x=review_comparison['customer_type'],
            y=review_comparison['repeat_rate'],
            marker_color=colors,
            text=review_comparison['repeat_rate'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside',
            showlegend=False
        ),
        row=2, col=1
    )

    # Avg AOV
    fig_review_comp.add_trace(
        go.Bar(
            x=review_comparison['customer_type'],
            y=review_comparison['avg_aov'],
            marker_color=colors,
            text=review_comparison['avg_aov'].apply(lambda x: f'R$ {x:.2f}'),
            textposition='outside',
            showlegend=False
        ),
        row=2, col=2
    )

    fig_review_comp.update_yaxes(title_text="Orders", row=1, col=1)
    fig_review_comp.update_yaxes(title_text="LTV (R$)", row=1, col=2)
    fig_review_comp.update_yaxes(title_text="Repeat Rate (%)", row=2, col=1)
    fig_review_comp.update_yaxes(title_text="AOV (R$)", row=2, col=2)

    fig_review_comp.update_layout(
        height=600,
        title_text="Review Writers vs Non-Review Writers Comparison"
    )

    fig_review_comp
    return colors, fig_review_comp


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the customer retention and cohort analysis:

    **Customer Segmentation:**
    - Majority are one-time customers (low repeat rate)
    - Small percentage of repeat customers drive significant revenue
    - Focus on converting one-time to repeat customers

    **Time to Second Purchase:**
    - Average time between purchases reveals engagement window
    - Most repeat purchases happen within first 60 days
    - Target reactivation campaigns based on typical conversion time

    **Cohort Retention:**
    - Retention drops sharply after first month
    - Different cohorts show varying retention patterns
    - Seasonal effects visible in cohort performance

    **Churn Analysis:**
    - Month-over-month churn reveals customer activity trends
    - High churn indicates need for retention strategies
    - Active customer base fluctuates with seasonality

    **Review Writers:**
    - Review writers show higher engagement and LTV
    - Writing reviews correlates with repeat purchase behavior
    - Encourage reviews as part of retention strategy

    **Recommendations:**
    - Implement win-back campaigns for churned customers
    - Target customers 30-60 days after first purchase
    - Incentivize review writing to improve engagement
    - Focus on first 90 days for retention efforts
    - Segment marketing by customer purchase frequency
    - Monitor cohort performance for early warning signals
    """)
    return


if __name__ == "__main__":
    app.run()
