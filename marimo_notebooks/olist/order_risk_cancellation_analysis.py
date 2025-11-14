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
    # Order Risk & Cancellation Analysis - Olist E-Commerce

    **Business Questions Answered:**
    - Q81: Order cancellation rate and main reasons
    - Q82: Patterns in cancelled orders (price, region)
    - Q86: Payment failure rate by payment method
    - Q87: Geographic patterns in payment issues
    - Q88: Distribution of installment payments (credit risk)
    - Q89: High-installment orders vs low-installment performance

    **Data Source:** fct_orders

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
    ## Order Cancellation Overview

    **Q81:** Order cancellation rate and main reasons
    """)
    return


@app.cell
def _(con, date_range):
    # Overall cancellation metrics
    cancellation_kpi_query = f"""
    SELECT
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as canceled_orders,
        SUM(CASE WHEN is_delivered THEN 1 ELSE 0 END) as delivered_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as cancellation_rate,

        -- Canceled orders value
        SUM(CASE WHEN is_canceled THEN total_order_value ELSE 0 END) as canceled_revenue,
        AVG(CASE WHEN is_canceled THEN total_order_value END) as avg_canceled_order_value,
        AVG(CASE WHEN is_delivered THEN total_order_value END) as avg_delivered_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    """

    cancellation_kpis = con.execute(cancellation_kpi_query).df()
    return (cancellation_kpis,)


@app.cell
def _(cancellation_kpis, mo):
    # Display cancellation KPI cards
    mo.hstack([
        mo.vstack([
            mo.stat(
                label="Cancellation Rate",
                value=f"{cancellation_kpis['cancellation_rate'].iloc[0]:.2f}%",
                caption=f"{cancellation_kpis['canceled_orders'].iloc[0]:,} orders"
            ),
            mo.stat(
                label="Delivered Orders",
                value=f"{cancellation_kpis['delivered_orders'].iloc[0]:,}",
                caption=f"of {cancellation_kpis['total_orders'].iloc[0]:,} total"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Canceled Revenue",
                value=f"R$ {cancellation_kpis['canceled_revenue'].iloc[0]:,.2f}",
                caption="Potential lost revenue"
            ),
            mo.stat(
                label="Avg Canceled Order",
                value=f"R$ {cancellation_kpis['avg_canceled_order_value'].iloc[0]:.2f}",
                caption=f"vs R$ {cancellation_kpis['avg_delivered_order_value'].iloc[0]:.2f} delivered"
            ),
        ])
    ])
    return


@app.cell
def _(con, date_range):
    # Cancellation trend over time
    cancellation_trend_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as canceled_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as cancellation_rate,
        SUM(CASE WHEN is_canceled THEN total_order_value ELSE 0 END) as canceled_revenue
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    cancellation_trend = con.execute(cancellation_trend_query).df()
    return (cancellation_trend,)


@app.cell
def _(cancellation_trend, go, make_subplots):
    # Cancellation trends
    fig_cancel_trend = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Cancellation Rate', 'Canceled Revenue Over Time'),
        vertical_spacing=0.15
    )

    # Cancellation rate
    fig_cancel_trend.add_trace(
        go.Scatter(
            x=cancellation_trend['month'],
            y=cancellation_trend['cancellation_rate'],
            mode='lines+markers',
            name='Cancellation Rate',
            line=dict(color='#EF553B', width=2),
            fill='tozeroy'
        ),
        row=1, col=1
    )

    # Canceled revenue
    fig_cancel_trend.add_trace(
        go.Bar(
            x=cancellation_trend['month'],
            y=cancellation_trend['canceled_revenue'],
            name='Canceled Revenue',
            marker_color='#AB63FA'
        ),
        row=2, col=1
    )

    fig_cancel_trend.update_yaxes(title_text="Cancellation Rate (%)", row=1, col=1)
    fig_cancel_trend.update_yaxes(title_text="Revenue (R$)", row=2, col=1)
    fig_cancel_trend.update_xaxes(title_text="Month", row=2, col=1)

    fig_cancel_trend.update_layout(
        height=600,
        showlegend=False,
        title_text="Cancellation Trends",
        hovermode='x unified'
    )

    fig_cancel_trend
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Cancellation Patterns Analysis

    **Q82:** Patterns in cancelled orders (price, region)
    """)
    return


@app.cell
def _(con, date_range):
    # Cancellation by order value
    cancel_by_value_query = f"""
    SELECT
        CASE
            WHEN total_order_value < 50 THEN '< R$ 50'
            WHEN total_order_value < 100 THEN 'R$ 50-100'
            WHEN total_order_value < 200 THEN 'R$ 100-200'
            WHEN total_order_value < 500 THEN 'R$ 200-500'
            ELSE 'R$ 500+'
        END as order_value_range,
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as canceled_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as cancellation_rate,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
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

    cancel_by_value = con.execute(cancel_by_value_query).df()
    return (cancel_by_value,)


@app.cell
def _(cancel_by_value, px):
    # Cancellation rate by order value
    fig_cancel_value = px.bar(
        cancel_by_value,
        x='order_value_range',
        y='cancellation_rate',
        title='Cancellation Rate by Order Value',
        labels={'cancellation_rate': 'Cancellation Rate (%)', 'order_value_range': 'Order Value Range'},
        color='cancellation_rate',
        color_continuous_scale='Reds',
        text='cancellation_rate'
    )

    fig_cancel_value.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_cancel_value.update_layout(showlegend=False)
    fig_cancel_value
    return


@app.cell
def _(con, date_range):
    # Cancellation by state
    cancel_by_state_query = f"""
    SELECT
        customer_state,
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as canceled_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as cancellation_rate,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND customer_state IS NOT NULL
    GROUP BY customer_state
    HAVING COUNT(*) >= 100
    ORDER BY cancellation_rate DESC
    """

    cancel_by_state = con.execute(cancel_by_state_query).df()
    return (cancel_by_state,)


@app.cell
def _(cancel_by_state, px):
    # Top states with highest cancellation rates
    top_cancel_states = cancel_by_state.nlargest(15, 'cancellation_rate')

    fig_cancel_state = px.bar(
        top_cancel_states,
        x='customer_state',
        y='cancellation_rate',
        title='Top 15 States with Highest Cancellation Rates',
        labels={'cancellation_rate': 'Cancellation Rate (%)', 'customer_state': 'State'},
        color='cancellation_rate',
        color_continuous_scale='Reds',
        text='cancellation_rate'
    )

    fig_cancel_state.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_cancel_state.update_layout(showlegend=False)
    fig_cancel_state
    return


@app.cell
def _(con, date_range):
    # Cancellation by payment method
    cancel_by_payment_query = f"""
    SELECT
        primary_payment_method,
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as canceled_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as cancellation_rate
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND primary_payment_method IS NOT NULL
    GROUP BY primary_payment_method
    ORDER BY cancellation_rate DESC
    """

    cancel_by_payment = con.execute(cancel_by_payment_query).df()
    return (cancel_by_payment,)


@app.cell
def _(cancel_by_payment, px):
    # Cancellation by payment method
    fig_cancel_payment = px.bar(
        cancel_by_payment,
        x='primary_payment_method',
        y='cancellation_rate',
        title='Cancellation Rate by Payment Method',
        labels={'cancellation_rate': 'Cancellation Rate (%)', 'primary_payment_method': 'Payment Method'},
        color='cancellation_rate',
        color_continuous_scale='Oranges',
        text='cancellation_rate'
    )

    fig_cancel_payment.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig_cancel_payment.update_layout(showlegend=False)
    fig_cancel_payment
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Installment Payment Distribution

    **Q88:** Distribution of installment payments (credit risk)

    **Q89:** High-installment orders vs low-installment performance
    """)
    return


@app.cell
def _(con, date_range):
    # Installment distribution analysis
    installment_dist_query = f"""
    SELECT
        max_installments,
        COUNT(*) as order_count,
        COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () * 100 as order_pct,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as cancellation_rate,
        AVG(CASE WHEN is_delivered THEN review_score END) as avg_satisfaction
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND max_installments IS NOT NULL
    GROUP BY max_installments
    ORDER BY max_installments
    """

    installment_dist = con.execute(installment_dist_query).df()
    return (installment_dist,)


@app.cell
def _(installment_dist, px):
    # Installment distribution
    fig_install_dist = px.bar(
        installment_dist[installment_dist['max_installments'] <= 12],
        x='max_installments',
        y='order_count',
        title='Order Distribution by Number of Installments',
        labels={'order_count': 'Order Count', 'max_installments': 'Number of Installments'},
        color='order_count',
        color_continuous_scale='Blues',
        text='order_count'
    )

    fig_install_dist.update_traces(textposition='outside')
    fig_install_dist.update_layout(showlegend=False, xaxis_type='category')
    fig_install_dist
    return


@app.cell
def _(installment_dist):
    # Group installments for analysis
    installment_grouped = installment_dist.copy()
    installment_grouped['installment_group'] = installment_grouped['max_installments'].apply(
        lambda x: '1x' if x == 1 else '2-3x' if x <= 3 else '4-6x' if x <= 6 else '7-10x' if x <= 10 else '10+x'
    )

    installment_analysis = installment_grouped.groupby('installment_group').agg({
        'order_count': 'sum',
        'total_revenue': 'sum',
        'avg_order_value': 'mean',
        'cancellation_rate': 'mean',
        'avg_satisfaction': 'mean'
    }).reset_index()

    # Sort by installment group
    group_order = ['1x', '2-3x', '4-6x', '7-10x', '10+x']
    installment_analysis['order'] = installment_analysis['installment_group'].apply(
        lambda x: group_order.index(x) if x in group_order else 999
    )
    installment_analysis = installment_analysis.sort_values('order')
    return (installment_analysis,)


@app.cell
def _(go, installment_analysis, make_subplots):
    # Installment performance analysis
    fig_install_perf = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Avg Order Value', 'Cancellation Rate', 'Satisfaction Score', 'Total Revenue'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}], [{'type': 'bar'}, {'type': 'bar'}]]
    )

    # AOV
    fig_install_perf.add_trace(
        go.Bar(
            x=installment_analysis['installment_group'],
            y=installment_analysis['avg_order_value'],
            marker_color='#636EFA',
            showlegend=False,
            text=installment_analysis['avg_order_value'].apply(lambda x: f'R$ {x:.2f}'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Cancellation rate
    fig_install_perf.add_trace(
        go.Bar(
            x=installment_analysis['installment_group'],
            y=installment_analysis['cancellation_rate'],
            marker_color='#EF553B',
            showlegend=False,
            text=installment_analysis['cancellation_rate'].apply(lambda x: f'{x:.2f}%'),
            textposition='outside'
        ),
        row=1, col=2
    )

    # Satisfaction
    fig_install_perf.add_trace(
        go.Bar(
            x=installment_analysis['installment_group'],
            y=installment_analysis['avg_satisfaction'],
            marker_color='#00CC96',
            showlegend=False,
            text=installment_analysis['avg_satisfaction'].apply(lambda x: f'{x:.2f}'),
            textposition='outside'
        ),
        row=2, col=1
    )

    # Revenue
    fig_install_perf.add_trace(
        go.Bar(
            x=installment_analysis['installment_group'],
            y=installment_analysis['total_revenue'],
            marker_color='#AB63FA',
            showlegend=False,
            text=installment_analysis['total_revenue'].apply(lambda x: f'R$ {x/1000:.0f}K'),
            textposition='outside'
        ),
        row=2, col=2
    )

    fig_install_perf.update_yaxes(title_text="AOV (R$)", row=1, col=1)
    fig_install_perf.update_yaxes(title_text="Cancellation %", row=1, col=2)
    fig_install_perf.update_yaxes(title_text="Rating", row=2, col=1, range=[0, 5])
    fig_install_perf.update_yaxes(title_text="Revenue (R$)", row=2, col=2)

    fig_install_perf.update_layout(
        height=600,
        title_text="Performance by Installment Range"
    )

    fig_install_perf
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Payment Method Risk Profile

    **Q86:** Payment failure rate by payment method

    **Q87:** Geographic patterns in payment issues
    """)
    return


@app.cell
def _(con, date_range):
    # Payment method risk analysis
    payment_risk_query = f"""
    SELECT
        primary_payment_method,
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as failed_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as failure_rate,
        AVG(max_installments) as avg_installments,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND primary_payment_method IS NOT NULL
    GROUP BY primary_payment_method
    ORDER BY failure_rate DESC
    """

    payment_risk = con.execute(payment_risk_query).df()
    return (payment_risk,)


@app.cell
def _(go, make_subplots, payment_risk):
    # Payment method risk comparison
    fig_payment_risk = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Failure Rate by Payment Method', 'Avg Installments by Payment Method')
    )

    # Failure rate
    fig_payment_risk.add_trace(
        go.Bar(
            x=payment_risk['primary_payment_method'],
            y=payment_risk['failure_rate'],
            marker_color='#EF553B',
            text=payment_risk['failure_rate'].apply(lambda x: f'{x:.2f}%'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=1
    )

    # Avg installments
    fig_payment_risk.add_trace(
        go.Bar(
            x=payment_risk['primary_payment_method'],
            y=payment_risk['avg_installments'],
            marker_color='#636EFA',
            text=payment_risk['avg_installments'].apply(lambda x: f'{x:.1f}x'),
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )

    fig_payment_risk.update_yaxes(title_text="Failure Rate (%)", row=1, col=1)
    fig_payment_risk.update_yaxes(title_text="Avg Installments", row=1, col=2)

    fig_payment_risk.update_layout(
        height=450,
        title_text="Payment Method Risk Analysis"
    )

    fig_payment_risk
    return


@app.cell
def _(con, date_range):
    # Geographic payment issues
    geo_payment_query = f"""
    SELECT
        customer_state,
        primary_payment_method,
        COUNT(*) as total_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END) as failed_orders,
        SUM(CASE WHEN is_canceled THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as failure_rate
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND customer_state IS NOT NULL
    AND primary_payment_method IS NOT NULL
    GROUP BY customer_state, primary_payment_method
    HAVING COUNT(*) >= 50
    ORDER BY failure_rate DESC
    LIMIT 30
    """

    geo_payment = con.execute(geo_payment_query).df()
    return (geo_payment,)


@app.cell
def _(geo_payment, px):
    # Top state-payment combinations with highest failure rates
    fig_geo_payment = px.bar(
        geo_payment.head(15),
        x='customer_state',
        y='failure_rate',
        color='primary_payment_method',
        title='Top State-Payment Combinations with Highest Failure Rates',
        labels={'failure_rate': 'Failure Rate (%)', 'customer_state': 'State'},
        barmode='group'
    )

    fig_geo_payment.update_layout(height=500)
    fig_geo_payment
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the order risk and cancellation analysis:

    **Cancellation Patterns:**
    - Overall cancellation rate indicates operational efficiency
    - Monitor trends for early warning signals
    - Seasonal patterns in cancellations
    - Revenue impact of cancellations

    **Order Value Impact:**
    - Relationship between order value and cancellation risk
    - Higher-value orders may have different risk profiles
    - Price sensitivity varies by segment

    **Geographic Risk:**
    - States with highest cancellation rates
    - Regional patterns in payment failures
    - Logistics issues may drive cancellations in remote areas

    **Payment Method Risk:**
    - Different payment methods have varying failure rates
    - Credit card transactions show different risk than boleto
    - Payment method preferences by region

    **Installment Analysis:**
    - Distribution of payment plans indicates customer preferences
    - Higher installments correlate with larger order values
    - Monitor high-installment orders for credit risk
    - Cancellation rates vary by installment count

    **Recommendations:**
    - Implement fraud detection for high-risk segments
    - Optimize payment flows to reduce failures
    - Target regions with high cancellation rates for improvement
    - Monitor installment payment performance
    - Set credit limits based on risk profiles
    - Improve logistics in high-cancellation states
    - Offer payment method education to reduce failures
    """)
    return


if __name__ == "__main__":
    app.run()
