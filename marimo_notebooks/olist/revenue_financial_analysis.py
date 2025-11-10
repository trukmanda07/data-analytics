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
    # Revenue & Financial Analysis - Olist E-Commerce

    **Business Questions Answered:**
    - Q9: Payment method distribution and cash flow impact
    - Q10: Average payment installment plan and working capital impact
    - Q13: Correlation between price point and conversion rates
    - Q14: Price ranges generating highest volume vs highest revenue
    - Q15: Average freight cost as percentage of order value
    - Q17: Seasonal revenue patterns for planning
    - Q18: Revenue per customer (lifetime value proxy)
    - Q20: Revenue impact of different delivery speeds
    - Q90: Average order value for different payment methods

    **Data Source:** dim_customers & fct_orders

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
    ## Payment Method Distribution

    **Q9:** Payment method distribution and cash flow impact

    **Q90:** Average order value for different payment methods
    """)
    return


@app.cell
def _(con, date_range):
    # Payment method analysis
    payment_method_query = f"""
    SELECT
        primary_payment_method,
        COUNT(*) as order_count,
        COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () * 100 as pct_of_orders,
        SUM(total_payment_value) as total_revenue,
        SUM(total_payment_value)::FLOAT / SUM(SUM(total_payment_value)) OVER () * 100 as pct_of_revenue,
        AVG(total_payment_value) as avg_order_value,
        AVG(max_installments) as avg_installments
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND primary_payment_method IS NOT NULL
    GROUP BY primary_payment_method
    ORDER BY order_count DESC
    """

    payment_methods = con.execute(payment_method_query).df()
    return (payment_methods,)


@app.cell
def _(go, make_subplots, payment_methods):
    # Payment method distribution visualization
    fig_payment = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Orders by Payment Method', 'Revenue by Payment Method'),
        specs=[[{'type': 'pie'}, {'type': 'pie'}]]
    )

    # Orders pie chart
    fig_payment.add_trace(
        go.Pie(
            labels=payment_methods['primary_payment_method'],
            values=payment_methods['order_count'],
            name='Orders',
            textposition='inside',
            textinfo='label+percent'
        ),
        row=1, col=1
    )

    # Revenue pie chart
    fig_payment.add_trace(
        go.Pie(
            labels=payment_methods['primary_payment_method'],
            values=payment_methods['total_revenue'],
            name='Revenue',
            textposition='inside',
            textinfo='label+percent'
        ),
        row=1, col=2
    )

    fig_payment.update_layout(
        height=400,
        showlegend=False,
        title_text="Payment Method Distribution"
    )

    fig_payment
    return


@app.cell
def _(payment_methods, px):
    # Average order value by payment method
    fig_aov_payment = px.bar(
        payment_methods.sort_values('avg_order_value', ascending=False),
        x='primary_payment_method',
        y='avg_order_value',
        title='Average Order Value by Payment Method',
        labels={'avg_order_value': 'AOV (R$)', 'primary_payment_method': 'Payment Method'},
        text='avg_order_value',
        color='avg_order_value',
        color_continuous_scale='Blues'
    )

    fig_aov_payment.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
    fig_aov_payment.update_layout(showlegend=False)
    fig_aov_payment
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Installment Plan Analysis

    **Q10:** Average payment installment plan and working capital impact
    """)
    return


@app.cell
def _(con, date_range):
    # Installment analysis
    installment_query = f"""
    SELECT
        CASE
            WHEN max_installments = 1 THEN '1x (No installment)'
            WHEN max_installments BETWEEN 2 AND 3 THEN '2-3x'
            WHEN max_installments BETWEEN 4 AND 6 THEN '4-6x'
            WHEN max_installments BETWEEN 7 AND 10 THEN '7-10x'
            ELSE '10+x'
        END as installment_range,
        COUNT(*) as order_count,
        SUM(total_payment_value) as total_revenue,
        AVG(total_payment_value) as avg_order_value,
        AVG(max_installments) as avg_installments
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND max_installments IS NOT NULL
    GROUP BY installment_range
    ORDER BY
        CASE installment_range
            WHEN '1x (No installment)' THEN 1
            WHEN '2-3x' THEN 2
            WHEN '4-6x' THEN 3
            WHEN '7-10x' THEN 4
            ELSE 5
        END
    """

    installments = con.execute(installment_query).df()

    # Calculate working capital impact (simple proxy)
    installments['working_capital_impact'] = installments['total_revenue'] * (installments['avg_installments'] - 1) / installments['avg_installments']
    return (installments,)


@app.cell
def _(go, installments, make_subplots):
    # Installment distribution
    fig_installment = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Orders by Installment Range', 'Working Capital Impact (Revenue Delayed)'),
        vertical_spacing=0.15
    )

    # Order count bar chart
    fig_installment.add_trace(
        go.Bar(
            x=installments['installment_range'],
            y=installments['order_count'],
            name='Order Count',
            marker_color='#636EFA',
            text=installments['order_count'],
            textposition='outside'
        ),
        row=1, col=1
    )

    # Working capital impact
    fig_installment.add_trace(
        go.Bar(
            x=installments['installment_range'],
            y=installments['working_capital_impact'],
            name='WC Impact',
            marker_color='#EF553B',
            text=installments['working_capital_impact'].apply(lambda x: f'R$ {x:,.0f}'),
            textposition='outside'
        ),
        row=2, col=1
    )

    fig_installment.update_yaxes(title_text="Order Count", row=1, col=1)
    fig_installment.update_yaxes(title_text="Revenue Delayed (R$)", row=2, col=1)
    fig_installment.update_xaxes(title_text="Installment Range", row=2, col=1)

    fig_installment.update_layout(
        height=600,
        showlegend=False,
        title_text="Payment Installment Analysis"
    )

    fig_installment
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Order Value Distribution Analysis

    **Q14:** Price ranges generating highest volume vs highest revenue
    """)
    return


@app.cell
def _(con, date_range):
    # Order value distribution
    order_value_dist_query = f"""
    SELECT
        CASE
            WHEN total_order_value < 50 THEN '< R$ 50'
            WHEN total_order_value < 100 THEN 'R$ 50-100'
            WHEN total_order_value < 150 THEN 'R$ 100-150'
            WHEN total_order_value < 200 THEN 'R$ 150-200'
            WHEN total_order_value < 300 THEN 'R$ 200-300'
            WHEN total_order_value < 500 THEN 'R$ 300-500'
            ELSE 'R$ 500+'
        END as value_range,
        COUNT(*) as order_count,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value,
        COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () * 100 as pct_orders,
        SUM(total_order_value)::FLOAT / SUM(SUM(total_order_value)) OVER () * 100 as pct_revenue
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY value_range
    ORDER BY
        CASE value_range
            WHEN '< R$ 50' THEN 1
            WHEN 'R$ 50-100' THEN 2
            WHEN 'R$ 100-150' THEN 3
            WHEN 'R$ 150-200' THEN 4
            WHEN 'R$ 200-300' THEN 5
            WHEN 'R$ 300-500' THEN 6
            ELSE 7
        END
    """

    order_value_dist = con.execute(order_value_dist_query).df()
    return (order_value_dist,)


@app.cell
def _(go, make_subplots, order_value_dist):
    # Volume vs Revenue comparison
    fig_vol_rev = make_subplots(
        rows=1, cols=2,
        subplot_titles=('% of Orders', '% of Revenue'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Orders percentage
    fig_vol_rev.add_trace(
        go.Bar(
            x=order_value_dist['value_range'],
            y=order_value_dist['pct_orders'],
            name='% Orders',
            marker_color='#00CC96',
            text=order_value_dist['pct_orders'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Revenue percentage
    fig_vol_rev.add_trace(
        go.Bar(
            x=order_value_dist['value_range'],
            y=order_value_dist['pct_revenue'],
            name='% Revenue',
            marker_color='#AB63FA',
            text=order_value_dist['pct_revenue'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ),
        row=1, col=2
    )

    fig_vol_rev.update_yaxes(title_text="% of Orders", row=1, col=1)
    fig_vol_rev.update_yaxes(title_text="% of Revenue", row=1, col=2)
    fig_vol_rev.update_xaxes(tickangle=45)

    fig_vol_rev.update_layout(
        height=500,
        showlegend=False,
        title_text="Order Volume vs Revenue by Price Range"
    )

    fig_vol_rev
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Freight Cost Analysis

    **Q15:** Average freight cost as percentage of order value
    """)
    return


@app.cell
def _(con, date_range):
    # Freight cost analysis
    freight_analysis_query = f"""
    SELECT
        CASE
            WHEN total_order_value < 100 THEN '< R$ 100'
            WHEN total_order_value < 200 THEN 'R$ 100-200'
            WHEN total_order_value < 500 THEN 'R$ 200-500'
            ELSE 'R$ 500+'
        END as order_value_range,
        COUNT(*) as order_count,
        AVG(total_freight) as avg_freight,
        AVG(total_order_value) as avg_order_value,
        AVG(total_freight::FLOAT / NULLIF(total_order_value, 0) * 100) as avg_freight_pct
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND total_order_value > 0
    GROUP BY order_value_range
    ORDER BY
        CASE order_value_range
            WHEN '< R$ 100' THEN 1
            WHEN 'R$ 100-200' THEN 2
            WHEN 'R$ 200-500' THEN 3
            ELSE 4
        END
    """

    freight_analysis = con.execute(freight_analysis_query).df()
    return (freight_analysis,)


@app.cell
def _(freight_analysis, go, make_subplots):
    # Freight cost visualization
    fig_freight = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Average Freight Cost (R$)', 'Freight as % of Order Value'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Freight cost in R$
    fig_freight.add_trace(
        go.Bar(
            x=freight_analysis['order_value_range'],
            y=freight_analysis['avg_freight'],
            name='Avg Freight',
            marker_color='#FFA15A',
            text=freight_analysis['avg_freight'].apply(lambda x: f'R$ {x:.2f}'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Freight percentage
    fig_freight.add_trace(
        go.Bar(
            x=freight_analysis['order_value_range'],
            y=freight_analysis['avg_freight_pct'],
            name='Freight %',
            marker_color='#19D3F3',
            text=freight_analysis['avg_freight_pct'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ),
        row=1, col=2
    )

    fig_freight.update_yaxes(title_text="Freight Cost (R$)", row=1, col=1)
    fig_freight.update_yaxes(title_text="% of Order Value", row=1, col=2)

    fig_freight.update_layout(
        height=400,
        showlegend=False,
        title_text="Freight Cost Economics"
    )

    fig_freight
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Seasonal Revenue Patterns

    **Q17:** Seasonal revenue patterns for campaign planning
    """)
    return


@app.cell
def _(con, date_range):
    # Monthly seasonality
    seasonality_query = f"""
    SELECT
        EXTRACT(MONTH FROM order_date) as month_num,
        TO_CHAR(order_date, 'Mon') as month_name,
        COUNT(*) as order_count,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    GROUP BY EXTRACT(MONTH FROM order_date), TO_CHAR(order_date, 'Mon')
    ORDER BY month_num
    """

    seasonality = con.execute(seasonality_query).df()
    return (seasonality,)


@app.cell
def _(go, make_subplots, seasonality):
    # Seasonality visualization
    fig_season = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Revenue Pattern', 'Monthly Order Volume'),
        vertical_spacing=0.12
    )

    # Revenue
    fig_season.add_trace(
        go.Bar(
            x=seasonality['month_name'],
            y=seasonality['total_revenue'],
            name='Revenue',
            marker_color='#636EFA',
            text=seasonality['total_revenue'].apply(lambda x: f'R$ {x/1000:.0f}K'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Order volume
    fig_season.add_trace(
        go.Bar(
            x=seasonality['month_name'],
            y=seasonality['order_count'],
            name='Orders',
            marker_color='#EF553B',
            text=seasonality['order_count'],
            textposition='outside'
        ),
        row=2, col=1
    )

    fig_season.update_yaxes(title_text="Revenue (R$)", row=1, col=1)
    fig_season.update_yaxes(title_text="Order Count", row=2, col=1)
    fig_season.update_xaxes(title_text="Month", row=2, col=1)

    fig_season.update_layout(
        height=600,
        showlegend=False,
        title_text="Seasonal Revenue Patterns"
    )

    fig_season
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Lifetime Value Analysis

    **Q18:** Revenue per customer (lifetime value proxy)
    """)
    return


@app.cell
def _(con, date_range):
    # Customer LTV analysis
    ltv_query = f"""
    WITH customer_orders AS (
        SELECT
            customer_id,
            COUNT(*) as order_count,
            SUM(total_order_value) as lifetime_revenue,
            AVG(total_order_value) as avg_order_value,
            MIN(order_date) as first_order_date,
            MAX(order_date) as last_order_date,
            DATE_DIFF('day', MIN(order_date), MAX(order_date)) as customer_tenure_days
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
        GROUP BY customer_id
    )
    SELECT
        CASE
            WHEN order_count = 1 THEN '1 Order'
            WHEN order_count = 2 THEN '2 Orders'
            WHEN order_count = 3 THEN '3 Orders'
            WHEN order_count BETWEEN 4 AND 5 THEN '4-5 Orders'
            ELSE '6+ Orders'
        END as customer_segment,
        COUNT(*) as customer_count,
        AVG(lifetime_revenue) as avg_ltv,
        SUM(lifetime_revenue) as total_revenue,
        AVG(avg_order_value) as avg_order_value,
        AVG(customer_tenure_days) as avg_tenure_days
    FROM customer_orders
    GROUP BY customer_segment
    ORDER BY
        CASE customer_segment
            WHEN '1 Order' THEN 1
            WHEN '2 Orders' THEN 2
            WHEN '3 Orders' THEN 3
            WHEN '4-5 Orders' THEN 4
            ELSE 5
        END
    """

    ltv_analysis = con.execute(ltv_query).df()
    return (ltv_analysis,)


@app.cell
def _(go, ltv_analysis, make_subplots):
    # LTV visualization
    fig_ltv = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Customer Count by Segment', 'Average LTV by Segment'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}]]
    )

    # Customer count
    fig_ltv.add_trace(
        go.Bar(
            x=ltv_analysis['customer_segment'],
            y=ltv_analysis['customer_count'],
            name='Customers',
            marker_color='#00CC96',
            text=ltv_analysis['customer_count'],
            textposition='outside'
        ),
        row=1, col=1
    )

    # Average LTV
    fig_ltv.add_trace(
        go.Bar(
            x=ltv_analysis['customer_segment'],
            y=ltv_analysis['avg_ltv'],
            name='Avg LTV',
            marker_color='#AB63FA',
            text=ltv_analysis['avg_ltv'].apply(lambda x: f'R$ {x:.2f}'),
            textposition='outside'
        ),
        row=1, col=2
    )

    fig_ltv.update_yaxes(title_text="Customer Count", row=1, col=1)
    fig_ltv.update_yaxes(title_text="Avg LTV (R$)", row=1, col=2)

    fig_ltv.update_layout(
        height=400,
        showlegend=False,
        title_text="Customer Lifetime Value Analysis"
    )

    fig_ltv
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Delivery Speed vs Revenue

    **Q20:** Revenue impact of different delivery speeds
    """)
    return


@app.cell
def _(con, date_range):
    # Delivery speed revenue impact
    delivery_revenue_query = f"""
    SELECT
        CASE
            WHEN days_to_delivery < 7 THEN '< 7 days (Fast)'
            WHEN days_to_delivery < 14 THEN '7-14 days'
            WHEN days_to_delivery < 21 THEN '14-21 days'
            WHEN days_to_delivery < 30 THEN '21-30 days'
            ELSE '30+ days (Slow)'
        END as delivery_speed,
        COUNT(*) as order_count,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value,
        AVG(review_score) as avg_review_score,
        AVG(total_freight) as avg_freight
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND days_to_delivery IS NOT NULL
    GROUP BY delivery_speed
    ORDER BY
        CASE delivery_speed
            WHEN '< 7 days (Fast)' THEN 1
            WHEN '7-14 days' THEN 2
            WHEN '14-21 days' THEN 3
            WHEN '21-30 days' THEN 4
            ELSE 5
        END
    """

    delivery_revenue = con.execute(delivery_revenue_query).df()
    return (delivery_revenue,)


@app.cell
def _(delivery_revenue, go, make_subplots):
    # Delivery speed impact
    fig_delivery_rev = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Revenue by Delivery Speed', 'AOV & Satisfaction vs Speed'),
        specs=[[{'type': 'bar'}, {'type': 'scatter'}]]
    )

    # Total revenue
    fig_delivery_rev.add_trace(
        go.Bar(
            x=delivery_revenue['delivery_speed'],
            y=delivery_revenue['total_revenue'],
            name='Revenue',
            marker_color='#636EFA',
            text=delivery_revenue['total_revenue'].apply(lambda x: f'R$ {x/1000:.0f}K'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # AOV trend
    fig_delivery_rev.add_trace(
        go.Scatter(
            x=delivery_revenue['delivery_speed'],
            y=delivery_revenue['avg_order_value'],
            mode='lines+markers',
            name='AOV',
            marker_color='#00CC96',
            yaxis='y2'
        ),
        row=1, col=2
    )

    # Satisfaction trend
    fig_delivery_rev.add_trace(
        go.Scatter(
            x=delivery_revenue['delivery_speed'],
            y=delivery_revenue['avg_review_score'],
            mode='lines+markers',
            name='Satisfaction',
            marker_color='#EF553B',
            yaxis='y3'
        ),
        row=1, col=2
    )

    fig_delivery_rev.update_yaxes(title_text="Revenue (R$)", row=1, col=1)
    fig_delivery_rev.update_yaxes(title_text="AOV (R$) / Review Score", row=1, col=2)
    fig_delivery_rev.update_xaxes(tickangle=45)

    fig_delivery_rev.update_layout(
        height=400,
        title_text="Delivery Speed Impact on Revenue & Satisfaction"
    )

    fig_delivery_rev
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the revenue and financial analysis:

    **Payment Methods:**
    - Identify dominant payment methods and their revenue contribution
    - Compare AOV across payment methods
    - Understand customer payment preferences

    **Installment Plans:**
    - Most common installment ranges
    - Working capital impact of installment plans
    - Higher installments may indicate price sensitivity

    **Order Value Distribution:**
    - Identify sweet spots: price ranges with high volume AND high revenue
    - Optimize pricing strategy based on volume vs revenue trade-offs
    - Target high-value segments for retention

    **Freight Economics:**
    - Freight as % of order value decreases with order size
    - Opportunity to optimize shipping costs for low-value orders
    - Consider free shipping thresholds

    **Seasonality:**
    - Identify peak revenue months for inventory planning
    - Plan marketing campaigns around seasonal trends
    - Prepare for demand fluctuations

    **Customer LTV:**
    - One-time customers dominate but have lowest LTV
    - Focus on converting one-time to repeat customers
    - High-value repeat customers drive significant revenue

    **Delivery Speed:**
    - Faster delivery correlates with higher satisfaction
    - Revenue concentration in specific delivery windows
    - Balance speed vs cost for optimal customer experience
    """)
    return


if __name__ == "__main__":
    app.run()
