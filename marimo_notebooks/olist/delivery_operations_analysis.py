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
    return Path, duckdb, go, load_dotenv, make_subplots, mo, os, pd, px


@app.cell
def _(mo):
    mo.md("""
    # Delivery & Operations Performance - Olist E-Commerce

    **Business Questions Answered:**
    - Q21: Average delivery time vs promised delivery time
    - Q22: Percentage of orders delivered late (trend)
    - Q23: States/regions with best and worst delivery performance
    - Q24: Correlation between delivery time and customer satisfaction
    - Q25: Relationship between freight cost and delivery time
    - Q26: Order fulfillment cycle time (purchase to delivery)
    - Q28: Geographical distribution of delivery delays

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
    ## Overall Delivery Performance KPIs

    High-level delivery metrics for the selected period:
    """)
    return


@app.cell
def _(con, date_range):
    # Calculate delivery KPIs
    delivery_kpi_query = f"""
    SELECT
        COUNT(*) as total_orders,
        AVG(days_to_delivery) as avg_delivery_days,
        MEDIAN(days_to_delivery) as median_delivery_days,
        AVG(days_vs_estimated) as avg_days_vs_estimated,

        -- Performance breakdown
        SUM(CASE WHEN delivery_performance = 'Early' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as early_pct,
        SUM(CASE WHEN delivery_performance = 'On Time' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as ontime_pct,
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as late_pct,

        -- Late orders count
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END) as late_orders,

        -- Average satisfaction
        AVG(review_score) as avg_satisfaction,

        -- Freight metrics
        AVG(total_freight) as avg_freight_cost
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND days_to_delivery IS NOT NULL
    """

    delivery_kpis = con.execute(delivery_kpi_query).df()
    return (delivery_kpis,)


@app.cell
def _(delivery_kpis, mo):
    # Display delivery KPI cards
    mo.hstack([
        mo.vstack([
            mo.stat(
                label="Avg Delivery Time",
                value=f"{delivery_kpis['avg_delivery_days'].iloc[0]:.1f} days",
                caption=f"Median: {delivery_kpis['median_delivery_days'].iloc[0]:.1f} days"
            ),
            mo.stat(
                label="On-Time Performance",
                value=f"{delivery_kpis['ontime_pct'].iloc[0]:.1f}%",
                caption="Delivered on time"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Late Delivery Rate",
                value=f"{delivery_kpis['late_pct'].iloc[0]:.1f}%",
                caption=f"{delivery_kpis['late_orders'].iloc[0]:,.0f} orders"
            ),
            mo.stat(
                label="Avg vs Estimated",
                value=f"{delivery_kpis['avg_days_vs_estimated'].iloc[0]:.1f} days",
                caption="Difference from promised date"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Customer Satisfaction",
                value=f"{delivery_kpis['avg_satisfaction'].iloc[0]:.2f} / 5.0",
                caption="Average review score"
            ),
            mo.stat(
                label="Avg Freight Cost",
                value=f"R$ {delivery_kpis['avg_freight_cost'].iloc[0]:.2f}",
                caption="Per order"
            ),
        ])
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Delivery Time vs Promised Time

    **Q21:** Average delivery time vs promised delivery time

    **Q22:** Percentage of orders delivered late (trend)
    """)
    return


@app.cell
def _(con, date_range):
    # Monthly delivery performance trend
    delivery_trend_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        COUNT(*) as total_orders,
        AVG(days_to_delivery) as avg_delivery_days,
        AVG(days_vs_estimated) as avg_days_vs_estimated,

        -- Performance categories
        SUM(CASE WHEN delivery_performance = 'Early' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as early_pct,
        SUM(CASE WHEN delivery_performance = 'On Time' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as ontime_pct,
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as late_pct,

        AVG(review_score) as avg_satisfaction
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND days_to_delivery IS NOT NULL
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    delivery_trend = con.execute(delivery_trend_query).df()
    return (delivery_trend,)


@app.cell
def _(delivery_trend, px):
    # Delivery time trend
    fig_delivery_time = px.line(
        delivery_trend,
        x='month',
        y='avg_delivery_days',
        title='Average Delivery Time Trend',
        labels={'avg_delivery_days': 'Days to Delivery', 'month': 'Month'},
        markers=True
    )

    fig_delivery_time.update_layout(
        hovermode='x unified',
        yaxis_title='Days'
    )

    fig_delivery_time
    return


@app.cell
def _(delivery_trend, px):
    # Late delivery percentage trend
    fig_late_trend = px.line(
        delivery_trend,
        x='month',
        y='late_pct',
        title='Late Delivery Rate Over Time',
        labels={'late_pct': 'Late Delivery %', 'month': 'Month'},
        markers=True,
        color_discrete_sequence=['#EF553B']
    )

    fig_late_trend.update_layout(
        hovermode='x unified',
        yaxis_title='Percentage (%)'
    )

    fig_late_trend
    return


@app.cell
def _(delivery_trend, px):
    # Performance distribution over time (stacked area)
    delivery_perf_melt = delivery_trend.melt(
        id_vars=['month'],
        value_vars=['early_pct', 'ontime_pct', 'late_pct'],
        var_name='performance',
        value_name='percentage'
    )

    fig_perf_stack = px.area(
        delivery_perf_melt,
        x='month',
        y='percentage',
        color='performance',
        title='Delivery Performance Distribution Over Time',
        labels={'percentage': 'Percentage (%)', 'month': 'Month'},
        color_discrete_map={
            'early_pct': '#00CC96',
            'ontime_pct': '#636EFA',
            'late_pct': '#EF553B'
        }
    )

    # Update legend labels
    fig_perf_stack.for_each_trace(lambda t: t.update(
        name={'early_pct': 'Early', 'ontime_pct': 'On Time', 'late_pct': 'Late'}[t.name]
    ))

    fig_perf_stack.update_layout(hovermode='x unified')
    fig_perf_stack
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Regional Delivery Performance

    **Q23:** States/regions with best and worst delivery performance

    **Q28:** Geographical distribution of delivery delays
    """)
    return


@app.cell
def _(con, date_range):
    # Delivery performance by state
    state_delivery_query = f"""
    SELECT
        customer_state,
        COUNT(*) as total_orders,
        AVG(days_to_delivery) as avg_delivery_days,
        AVG(days_vs_estimated) as avg_days_vs_estimated,
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as late_pct,
        AVG(review_score) as avg_satisfaction,
        AVG(total_freight) as avg_freight_cost
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND days_to_delivery IS NOT NULL
    AND customer_state IS NOT NULL
    GROUP BY customer_state
    HAVING COUNT(*) >= 100  -- Only include states with significant volume
    ORDER BY avg_delivery_days
    """

    state_delivery = con.execute(state_delivery_query).df()
    return (state_delivery,)


@app.cell
def _(pd, px, state_delivery):
    # Best and worst performing states by delivery time
    top_states = state_delivery.nsmallest(10, 'avg_delivery_days')
    bottom_states = state_delivery.nlargest(10, 'avg_delivery_days')

    fig_states = px.bar(
        pd.concat([top_states, bottom_states]),
        x='customer_state',
        y='avg_delivery_days',
        title='Top 10 Best & Worst States by Delivery Time',
        labels={'avg_delivery_days': 'Avg Delivery Days', 'customer_state': 'State'},
        color='avg_delivery_days',
        color_continuous_scale='RdYlGn_r',
        text='avg_delivery_days'
    )

    fig_states.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_states.update_layout(showlegend=False, height=500)
    fig_states
    return


@app.cell
def _(px, state_delivery):
    # Late delivery rate by state
    fig_late_by_state = px.bar(
        state_delivery.nlargest(15, 'late_pct'),
        x='customer_state',
        y='late_pct',
        title='Top 15 States with Highest Late Delivery Rates',
        labels={'late_pct': 'Late Delivery %', 'customer_state': 'State'},
        color='late_pct',
        color_continuous_scale='Reds',
        text='late_pct'
    )

    fig_late_by_state.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_late_by_state.update_layout(showlegend=False)
    fig_late_by_state
    return


@app.cell
def _(px, state_delivery):
    # Geographic heatmap - delivery days vs late %
    fig_geo_scatter = px.scatter(
        state_delivery,
        x='avg_delivery_days',
        y='late_pct',
        size='total_orders',
        color='avg_satisfaction',
        hover_name='customer_state',
        title='State Delivery Performance Map',
        labels={
            'avg_delivery_days': 'Avg Delivery Days',
            'late_pct': 'Late Delivery %',
            'total_orders': 'Order Volume',
            'avg_satisfaction': 'Satisfaction'
        },
        color_continuous_scale='RdYlGn'
    )

    fig_geo_scatter.update_layout(height=500)
    fig_geo_scatter
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Delivery Time vs Customer Satisfaction

    **Q24:** Correlation between delivery time and customer satisfaction
    """)
    return


@app.cell
def _(con, date_range):
    # Satisfaction by delivery time buckets
    satisfaction_by_delivery_query = f"""
    SELECT
        CASE
            WHEN days_to_delivery < 7 THEN '< 7 days'
            WHEN days_to_delivery < 14 THEN '7-14 days'
            WHEN days_to_delivery < 21 THEN '14-21 days'
            WHEN days_to_delivery < 30 THEN '21-30 days'
            ELSE '30+ days'
        END as delivery_time_bucket,
        COUNT(*) as order_count,
        AVG(review_score) as avg_satisfaction,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_review_pct,
        AVG(days_to_delivery) as avg_delivery_days
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND days_to_delivery IS NOT NULL
    AND review_score IS NOT NULL
    GROUP BY delivery_time_bucket
    ORDER BY
        CASE delivery_time_bucket
            WHEN '< 7 days' THEN 1
            WHEN '7-14 days' THEN 2
            WHEN '14-21 days' THEN 3
            WHEN '21-30 days' THEN 4
            ELSE 5
        END
    """

    satisfaction_delivery = con.execute(satisfaction_by_delivery_query).df()
    return (satisfaction_delivery,)


@app.cell
def _(go, make_subplots, satisfaction_delivery):
    # Satisfaction vs delivery time
    fig_sat_del = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Average Satisfaction by Delivery Speed', 'Positive Review % by Delivery Speed')
    )

    # Average satisfaction
    fig_sat_del.add_trace(
        go.Bar(
            x=satisfaction_delivery['delivery_time_bucket'],
            y=satisfaction_delivery['avg_satisfaction'],
            name='Avg Satisfaction',
            marker_color='#636EFA',
            text=satisfaction_delivery['avg_satisfaction'].apply(lambda x: f'{x:.2f}'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Positive review percentage
    fig_sat_del.add_trace(
        go.Bar(
            x=satisfaction_delivery['delivery_time_bucket'],
            y=satisfaction_delivery['positive_review_pct'],
            name='Positive %',
            marker_color='#00CC96',
            text=satisfaction_delivery['positive_review_pct'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ),
        row=1, col=2
    )

    fig_sat_del.update_yaxes(title_text="Satisfaction Score", row=1, col=1, range=[0, 5])
    fig_sat_del.update_yaxes(title_text="Positive Review %", row=1, col=2)
    fig_sat_del.update_xaxes(tickangle=45)

    fig_sat_del.update_layout(
        height=500,
        showlegend=False,
        title_text="Impact of Delivery Time on Customer Satisfaction"
    )

    fig_sat_del
    return


@app.cell
def _(con, date_range):
    # Correlation analysis - delivery performance vs satisfaction
    correlation_query = f"""
    SELECT
        delivery_performance,
        COUNT(*) as order_count,
        AVG(review_score) as avg_satisfaction,
        AVG(days_to_delivery) as avg_delivery_days,
        AVG(days_vs_estimated) as avg_days_vs_estimated
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    AND delivery_performance IS NOT NULL
    GROUP BY delivery_performance
    ORDER BY
        CASE delivery_performance
            WHEN 'Early' THEN 1
            WHEN 'On Time' THEN 2
            ELSE 3
        END
    """

    perf_satisfaction = con.execute(correlation_query).df()
    return (perf_satisfaction,)


@app.cell
def _(perf_satisfaction, px):
    # Satisfaction by delivery performance category
    fig_perf_sat = px.bar(
        perf_satisfaction,
        x='delivery_performance',
        y='avg_satisfaction',
        title='Customer Satisfaction by Delivery Performance',
        labels={'avg_satisfaction': 'Avg Satisfaction Score', 'delivery_performance': 'Delivery Performance'},
        color='avg_satisfaction',
        color_continuous_scale='RdYlGn',
        text='avg_satisfaction'
    )

    fig_perf_sat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_perf_sat.update_layout(showlegend=False, yaxis_range=[0, 5])
    fig_perf_sat
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Freight Cost vs Delivery Time

    **Q25:** Relationship between freight cost and delivery time
    """)
    return


@app.cell
def _(con, date_range):
    # Freight vs delivery time analysis
    freight_delivery_query = f"""
    SELECT
        CASE
            WHEN total_freight < 10 THEN '< R$ 10'
            WHEN total_freight < 20 THEN 'R$ 10-20'
            WHEN total_freight < 30 THEN 'R$ 20-30'
            WHEN total_freight < 50 THEN 'R$ 30-50'
            ELSE 'R$ 50+'
        END as freight_range,
        COUNT(*) as order_count,
        AVG(total_freight) as avg_freight,
        AVG(days_to_delivery) as avg_delivery_days,
        SUM(CASE WHEN delivery_performance = 'Late' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as late_pct,
        AVG(review_score) as avg_satisfaction
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND total_freight IS NOT NULL
    AND days_to_delivery IS NOT NULL
    GROUP BY freight_range
    ORDER BY
        CASE freight_range
            WHEN '< R$ 10' THEN 1
            WHEN 'R$ 10-20' THEN 2
            WHEN 'R$ 20-30' THEN 3
            WHEN 'R$ 30-50' THEN 4
            ELSE 5
        END
    """

    freight_delivery = con.execute(freight_delivery_query).df()
    return (freight_delivery,)


@app.cell
def _(freight_delivery, go, make_subplots):
    # Freight vs delivery time visualization
    fig_freight_del = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Delivery Time by Freight Cost', 'Late Delivery % by Freight Cost'),
        vertical_spacing=0.15
    )

    # Delivery time
    fig_freight_del.add_trace(
        go.Bar(
            x=freight_delivery['freight_range'],
            y=freight_delivery['avg_delivery_days'],
            name='Delivery Days',
            marker_color='#636EFA',
            text=freight_delivery['avg_delivery_days'].apply(lambda x: f'{x:.1f}'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Late delivery percentage
    fig_freight_del.add_trace(
        go.Bar(
            x=freight_delivery['freight_range'],
            y=freight_delivery['late_pct'],
            name='Late %',
            marker_color='#EF553B',
            text=freight_delivery['late_pct'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ),
        row=2, col=1
    )

    fig_freight_del.update_yaxes(title_text="Avg Delivery Days", row=1, col=1)
    fig_freight_del.update_yaxes(title_text="Late Delivery %", row=2, col=1)
    fig_freight_del.update_xaxes(title_text="Freight Cost Range", row=2, col=1)

    fig_freight_del.update_layout(
        height=600,
        showlegend=False,
        title_text="Freight Cost vs Delivery Performance"
    )

    fig_freight_del
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Order Fulfillment Cycle Time

    **Q26:** Order fulfillment cycle time (purchase to delivery)
    """)
    return


@app.cell
def _(con, date_range):
    # Fulfillment cycle time breakdown
    fulfillment_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        AVG(hours_to_approval) / 24.0 as avg_days_to_approval,
        AVG(days_to_delivery) as avg_days_to_delivery,
        AVG(hours_to_approval / 24.0 + days_to_delivery) as total_cycle_time,
        COUNT(*) as order_count
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND hours_to_approval IS NOT NULL
    AND days_to_delivery IS NOT NULL
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    fulfillment = con.execute(fulfillment_query).df()
    return (fulfillment,)


@app.cell
def _(fulfillment, px):
    # Cycle time breakdown
    fulfillment_melt = fulfillment.melt(
        id_vars=['month'],
        value_vars=['avg_days_to_approval', 'avg_days_to_delivery'],
        var_name='stage',
        value_name='days'
    )

    fig_cycle = px.bar(
        fulfillment_melt,
        x='month',
        y='days',
        color='stage',
        title='Order Fulfillment Cycle Time Breakdown',
        labels={'days': 'Days', 'month': 'Month'},
        color_discrete_map={
            'avg_days_to_approval': '#636EFA',
            'avg_days_to_delivery': '#EF553B'
        }
    )

    # Update legend
    fig_cycle.for_each_trace(lambda t: t.update(
        name={'avg_days_to_approval': 'Approval Time', 'avg_days_to_delivery': 'Delivery Time'}[t.name]
    ))

    fig_cycle.update_layout(hovermode='x unified')
    fig_cycle
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the delivery and operations analysis:

    **Overall Performance:**
    - Track on-time delivery percentage
    - Monitor late delivery trends
    - Identify improvement opportunities

    **Regional Variations:**
    - Significant differences in delivery times by state
    - Remote states have longer delivery times and higher late rates
    - Urban centers (SP, RJ) perform better

    **Satisfaction Impact:**
    - Strong correlation between delivery speed and satisfaction
    - Early/on-time deliveries have significantly higher ratings
    - Late deliveries drive negative reviews

    **Freight Economics:**
    - Higher freight costs don't guarantee faster delivery
    - Optimize shipping methods by region
    - Balance cost vs speed

    **Operational Improvements:**
    - Reduce approval time for faster fulfillment
    - Focus on high-volume states with poor performance
    - Implement regional logistics strategies
    - Set realistic delivery estimates to manage expectations

    **Priority Actions:**
    - Address top 10 worst-performing states
    - Reduce late delivery rate to improve satisfaction
    - Optimize freight costs without compromising speed
    - Improve fulfillment cycle time efficiency
    """)
    return


if __name__ == "__main__":
    app.run()
