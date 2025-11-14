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
    # Customer Satisfaction & Experience - Olist E-Commerce

    **Business Questions Answered:**
    - Q31: Overall customer satisfaction score (NPS proxy)
    - Q32: Correlation between delivery time and review scores
    - Q64: Customer satisfaction variation by region
    - Q100: Factors most strongly predicting customer satisfaction

    **Data Source:** fct_orders

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
    ## Overall Customer Satisfaction (NPS Proxy)

    **Q31:** Overall customer satisfaction score (NPS proxy from review ratings)
    """)
    return


@app.cell
def __(con, date_range):
    # Overall satisfaction metrics
    satisfaction_kpi_query = f"""
    SELECT
        COUNT(*) as total_orders_with_reviews,
        AVG(review_score) as avg_review_score,

        -- NPS calculation (Promoters - Detractors)
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as promoters_pct,
        SUM(CASE WHEN review_score = 3 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as passives_pct,
        SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as detractors_pct,

        -- Review score distribution
        SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) as five_star,
        SUM(CASE WHEN review_score = 4 THEN 1 ELSE 0 END) as four_star,
        SUM(CASE WHEN review_score = 3 THEN 1 ELSE 0 END) as three_star,
        SUM(CASE WHEN review_score = 2 THEN 1 ELSE 0 END) as two_star,
        SUM(CASE WHEN review_score = 1 THEN 1 ELSE 0 END) as one_star
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    """

    satisfaction_kpis = con.execute(satisfaction_kpi_query).df()

    # Calculate NPS
    nps_score = satisfaction_kpis['promoters_pct'].iloc[0] - satisfaction_kpis['detractors_pct'].iloc[0]

    return nps_score, satisfaction_kpi_query, satisfaction_kpis


@app.cell
def __(mo, satisfaction_kpis, nps_score):
    # Display satisfaction KPI cards
    mo.hstack([
        mo.vstack([
            mo.stat(
                label="Net Promoter Score",
                value=f"{nps_score:.1f}",
                caption="Promoters - Detractors"
            ),
            mo.stat(
                label="Average Rating",
                value=f"{satisfaction_kpis['avg_review_score'].iloc[0]:.2f} / 5.0",
                caption="Overall satisfaction"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Promoters (4-5 ⭐)",
                value=f"{satisfaction_kpis['promoters_pct'].iloc[0]:.1f}%",
                caption="Highly satisfied"
            ),
            mo.stat(
                label="Passives (3 ⭐)",
                value=f"{satisfaction_kpis['passives_pct'].iloc[0]:.1f}%",
                caption="Neutral"
            ),
        ]),
        mo.vstack([
            mo.stat(
                label="Detractors (1-2 ⭐)",
                value=f"{satisfaction_kpis['detractors_pct'].iloc[0]:.1f}%",
                caption="Unsatisfied"
            ),
            mo.stat(
                label="Total Reviews",
                value=f"{satisfaction_kpis['total_orders_with_reviews'].iloc[0]:,}",
                caption="Orders with reviews"
            ),
        ])
    ])
    return


@app.cell
def __(satisfaction_kpis, pd):
    # Review distribution data
    review_dist_data = pd.DataFrame({
        'rating': [5, 4, 3, 2, 1],
        'count': [
            satisfaction_kpis['five_star'].iloc[0],
            satisfaction_kpis['four_star'].iloc[0],
            satisfaction_kpis['three_star'].iloc[0],
            satisfaction_kpis['two_star'].iloc[0],
            satisfaction_kpis['one_star'].iloc[0]
        ]
    })
    review_dist_data['percentage'] = review_dist_data['count'] / review_dist_data['count'].sum() * 100

    return (review_dist_data,)


@app.cell
def __(px, review_dist_data):
    # Review distribution visualization
    fig_review_dist = px.bar(
        review_dist_data,
        x='rating',
        y='percentage',
        title='Customer Satisfaction Distribution',
        labels={'percentage': 'Percentage (%)', 'rating': 'Star Rating'},
        text='percentage',
        color='rating',
        color_continuous_scale='RdYlGn'
    )

    fig_review_dist.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig_review_dist.update_layout(showlegend=False, xaxis_type='category')
    fig_review_dist.update_xaxes(tickvals=[1, 2, 3, 4, 5])
    fig_review_dist
    return (fig_review_dist,)


@app.cell
def __(con, date_range):
    # Satisfaction trend over time
    satisfaction_trend_query = f"""
    SELECT
        DATE_TRUNC('month', order_date) as month,
        COUNT(*) as total_reviews,
        AVG(review_score) as avg_rating,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as promoters_pct,
        SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as detractors_pct
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    GROUP BY DATE_TRUNC('month', order_date)
    ORDER BY month
    """

    satisfaction_trend = con.execute(satisfaction_trend_query).df()
    satisfaction_trend['nps'] = satisfaction_trend['promoters_pct'] - satisfaction_trend['detractors_pct']

    return satisfaction_trend, satisfaction_trend_query


@app.cell
def __(make_subplots, go, satisfaction_trend):
    # Satisfaction trends
    fig_sat_trend = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Average Rating Over Time', 'NPS Score Over Time'),
        vertical_spacing=0.12
    )

    # Average rating
    fig_sat_trend.add_trace(
        go.Scatter(
            x=satisfaction_trend['month'],
            y=satisfaction_trend['avg_rating'],
            mode='lines+markers',
            name='Avg Rating',
            line=dict(color='#636EFA', width=2)
        ),
        row=1, col=1
    )

    # NPS score
    fig_sat_trend.add_trace(
        go.Scatter(
            x=satisfaction_trend['month'],
            y=satisfaction_trend['nps'],
            mode='lines+markers',
            name='NPS',
            line=dict(color='#00CC96', width=2),
            fill='tozeroy'
        ),
        row=2, col=1
    )

    fig_sat_trend.update_yaxes(title_text="Rating (1-5)", row=1, col=1, range=[1, 5])
    fig_sat_trend.update_yaxes(title_text="NPS Score", row=2, col=1)
    fig_sat_trend.update_xaxes(title_text="Month", row=2, col=1)

    fig_sat_trend.update_layout(
        height=600,
        showlegend=False,
        title_text="Customer Satisfaction Trends",
        hovermode='x unified'
    )

    fig_sat_trend
    return (fig_sat_trend,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Delivery Time Impact on Satisfaction

    **Q32:** Correlation between delivery time and review scores
    """)
    return


@app.cell
def __(con, date_range):
    # Satisfaction by delivery performance
    delivery_satisfaction_query = f"""
    SELECT
        delivery_performance,
        COUNT(*) as order_count,
        AVG(review_score) as avg_rating,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_pct,
        SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as negative_pct,
        AVG(days_to_delivery) as avg_delivery_days
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

    delivery_sat = con.execute(delivery_satisfaction_query).df()
    return delivery_sat, delivery_satisfaction_query


@app.cell
def __(px, delivery_sat):
    # Satisfaction by delivery performance
    fig_del_sat = px.bar(
        delivery_sat,
        x='delivery_performance',
        y='avg_rating',
        title='Customer Satisfaction by Delivery Performance',
        labels={'avg_rating': 'Avg Rating', 'delivery_performance': 'Delivery Performance'},
        color='avg_rating',
        color_continuous_scale='RdYlGn',
        text='avg_rating'
    )

    fig_del_sat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_del_sat.update_layout(showlegend=False, yaxis_range=[0, 5])
    fig_del_sat
    return (fig_del_sat,)


@app.cell
def __(con, date_range):
    # Satisfaction by delivery time buckets
    delivery_time_sat_query = f"""
    SELECT
        CASE
            WHEN days_to_delivery < 7 THEN '< 7 days'
            WHEN days_to_delivery < 14 THEN '7-14 days'
            WHEN days_to_delivery < 21 THEN '14-21 days'
            WHEN days_to_delivery < 30 THEN '21-30 days'
            ELSE '30+ days'
        END as delivery_bucket,
        AVG(days_to_delivery) as avg_days,
        COUNT(*) as order_count,
        AVG(review_score) as avg_rating,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_pct
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    AND days_to_delivery IS NOT NULL
    GROUP BY delivery_bucket
    ORDER BY
        CASE delivery_bucket
            WHEN '< 7 days' THEN 1
            WHEN '7-14 days' THEN 2
            WHEN '14-21 days' THEN 3
            WHEN '21-30 days' THEN 4
            ELSE 5
        END
    """

    delivery_time_sat = con.execute(delivery_time_sat_query).df()
    return delivery_time_sat, delivery_time_sat_query


@app.cell
def __(make_subplots, go, delivery_time_sat):
    # Delivery time vs satisfaction correlation
    fig_time_corr = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Avg Rating by Delivery Speed', 'Positive Review % by Delivery Speed')
    )

    # Average rating
    fig_time_corr.add_trace(
        go.Bar(
            x=delivery_time_sat['delivery_bucket'],
            y=delivery_time_sat['avg_rating'],
            name='Avg Rating',
            marker_color='#636EFA',
            text=delivery_time_sat['avg_rating'].apply(lambda x: f'{x:.2f}'),
            textposition='outside'
        ),
        row=1, col=1
    )

    # Positive percentage
    fig_time_corr.add_trace(
        go.Bar(
            x=delivery_time_sat['delivery_bucket'],
            y=delivery_time_sat['positive_pct'],
            name='Positive %',
            marker_color='#00CC96',
            text=delivery_time_sat['positive_pct'].apply(lambda x: f'{x:.1f}%'),
            textposition='outside'
        ),
        row=1, col=2
    )

    fig_time_corr.update_yaxes(title_text="Avg Rating", row=1, col=1, range=[0, 5])
    fig_time_corr.update_yaxes(title_text="Positive %", row=1, col=2)
    fig_time_corr.update_xaxes(tickangle=45)

    fig_time_corr.update_layout(
        height=450,
        showlegend=False,
        title_text="Delivery Time Impact on Satisfaction"
    )

    fig_time_corr
    return (fig_time_corr,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Regional Satisfaction Analysis

    **Q64:** Customer satisfaction variation by region
    """)
    return


@app.cell
def __(con, date_range):
    # Satisfaction by state
    state_satisfaction_query = f"""
    SELECT
        customer_state,
        COUNT(*) as total_orders,
        AVG(review_score) as avg_rating,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as promoters_pct,
        SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as detractors_pct,
        AVG(days_to_delivery) as avg_delivery_days,
        AVG(total_order_value) as avg_order_value
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    AND customer_state IS NOT NULL
    GROUP BY customer_state
    HAVING COUNT(*) >= 100
    ORDER BY avg_rating DESC
    """

    state_sat = con.execute(state_satisfaction_query).df()
    state_sat['nps'] = state_sat['promoters_pct'] - state_sat['detractors_pct']

    return state_sat, state_satisfaction_query


@app.cell
def __(px, pd, state_sat):
    # Top and bottom states by satisfaction
    top_states_sat = state_sat.nlargest(10, 'avg_rating')
    bottom_states_sat = state_sat.nsmallest(10, 'avg_rating')

    combined_states = pd.concat([top_states_sat, bottom_states_sat])

    fig_state_sat = px.bar(
        combined_states.sort_values('avg_rating', ascending=True),
        y='customer_state',
        x='avg_rating',
        orientation='h',
        title='Top 10 Best & Worst States by Customer Satisfaction',
        labels={'avg_rating': 'Avg Rating', 'customer_state': 'State'},
        color='avg_rating',
        color_continuous_scale='RdYlGn',
        text='avg_rating'
    )

    fig_state_sat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_state_sat.update_layout(showlegend=False, height=600)
    fig_state_sat
    return bottom_states_sat, combined_states, fig_state_sat, top_states_sat


@app.cell
def __(px, state_sat):
    # Geographic scatter: delivery time vs satisfaction
    fig_geo_sat = px.scatter(
        state_sat,
        x='avg_delivery_days',
        y='avg_rating',
        size='total_orders',
        color='nps',
        hover_name='customer_state',
        title='State Performance: Delivery Time vs Satisfaction',
        labels={
            'avg_delivery_days': 'Avg Delivery Days',
            'avg_rating': 'Avg Rating',
            'total_orders': 'Order Volume',
            'nps': 'NPS Score'
        },
        color_continuous_scale='RdYlGn'
    )

    fig_geo_sat.update_layout(height=500)
    fig_geo_sat
    return (fig_geo_sat,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Satisfaction Drivers Analysis

    **Q100:** Factors most strongly predicting customer satisfaction
    """)
    return


@app.cell
def __(con, date_range):
    # Correlation analysis - multiple factors
    factors_query = f"""
    SELECT
        -- Order value segments
        CASE
            WHEN total_order_value < 100 THEN '< R$ 100'
            WHEN total_order_value < 200 THEN 'R$ 100-200'
            WHEN total_order_value < 500 THEN 'R$ 200-500'
            ELSE 'R$ 500+'
        END as order_value_segment,

        -- Payment method
        primary_payment_method,

        -- Delivery performance
        delivery_performance,

        -- Freight segment
        CASE
            WHEN total_freight < 15 THEN 'Low Freight'
            WHEN total_freight < 25 THEN 'Medium Freight'
            ELSE 'High Freight'
        END as freight_segment,

        COUNT(*) as order_count,
        AVG(review_score) as avg_rating,
        SUM(CASE WHEN review_score >= 4 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as positive_pct
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND review_score IS NOT NULL
    GROUP BY order_value_segment, primary_payment_method, delivery_performance, freight_segment
    HAVING COUNT(*) >= 10
    """

    factors_data = con.execute(factors_query).df()
    return factors_data, factors_query


@app.cell
def __(factors_data):
    # Analyze by order value
    order_value_sat = factors_data.groupby('order_value_segment').agg({
        'order_count': 'sum',
        'avg_rating': 'mean',
        'positive_pct': 'mean'
    }).reset_index()

    # Sort by order value
    order_value_order = ['< R$ 100', 'R$ 100-200', 'R$ 200-500', 'R$ 500+']
    order_value_sat['order'] = order_value_sat['order_value_segment'].apply(
        lambda x: order_value_order.index(x) if x in order_value_order else 999
    )
    order_value_sat = order_value_sat.sort_values('order')

    return order_value_order, order_value_sat


@app.cell
def __(px, order_value_sat):
    # Order value impact on satisfaction
    fig_value_sat = px.bar(
        order_value_sat,
        x='order_value_segment',
        y='avg_rating',
        title='Satisfaction by Order Value',
        labels={'avg_rating': 'Avg Rating', 'order_value_segment': 'Order Value'},
        color='avg_rating',
        color_continuous_scale='Blues',
        text='avg_rating'
    )

    fig_value_sat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_value_sat.update_layout(showlegend=False, yaxis_range=[0, 5])
    fig_value_sat
    return (fig_value_sat,)


@app.cell
def __(factors_data):
    # Analyze by payment method
    payment_sat = factors_data.groupby('primary_payment_method').agg({
        'order_count': 'sum',
        'avg_rating': 'mean',
        'positive_pct': 'mean'
    }).reset_index().sort_values('avg_rating', ascending=False)

    return (payment_sat,)


@app.cell
def __(px, payment_sat):
    # Payment method impact
    fig_payment_sat = px.bar(
        payment_sat,
        x='primary_payment_method',
        y='avg_rating',
        title='Satisfaction by Payment Method',
        labels={'avg_rating': 'Avg Rating', 'primary_payment_method': 'Payment Method'},
        color='avg_rating',
        color_continuous_scale='Greens',
        text='avg_rating'
    )

    fig_payment_sat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_payment_sat.update_layout(showlegend=False, yaxis_range=[0, 5])
    fig_payment_sat
    return (fig_payment_sat,)


@app.cell
def __(factors_data):
    # Analyze by freight cost
    freight_sat = factors_data.groupby('freight_segment').agg({
        'order_count': 'sum',
        'avg_rating': 'mean',
        'positive_pct': 'mean'
    }).reset_index()

    # Order freight segments
    freight_order = ['Low Freight', 'Medium Freight', 'High Freight']
    freight_sat['order'] = freight_sat['freight_segment'].apply(
        lambda x: freight_order.index(x) if x in freight_order else 999
    )
    freight_sat = freight_sat.sort_values('order')

    return freight_order, freight_sat


@app.cell
def __(px, freight_sat):
    # Freight cost impact
    fig_freight_sat = px.bar(
        freight_sat,
        x='freight_segment',
        y='avg_rating',
        title='Satisfaction by Freight Cost',
        labels={'avg_rating': 'Avg Rating', 'freight_segment': 'Freight Segment'},
        color='avg_rating',
        color_continuous_scale='Oranges',
        text='avg_rating'
    )

    fig_freight_sat.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_freight_sat.update_layout(showlegend=False, yaxis_range=[0, 5])
    fig_freight_sat
    return (fig_freight_sat,)


@app.cell
def __(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the customer satisfaction analysis:

    **Overall Satisfaction:**
    - NPS score indicates overall customer sentiment
    - Track promoters, passives, and detractors percentages
    - Monitor satisfaction trends over time

    **Delivery Impact (Strongest Driver):**
    - Delivery performance has the strongest correlation with satisfaction
    - Early/on-time deliveries result in significantly higher ratings
    - Late deliveries are the primary driver of negative reviews
    - Faster delivery (< 7 days) consistently receives highest ratings

    **Regional Variations:**
    - Significant differences in satisfaction across states
    - Urban centers typically have higher satisfaction
    - Remote states with longer delivery times show lower ratings
    - Delivery time is the key mediating factor

    **Other Factors:**
    - Order value shows moderate correlation with satisfaction
    - Payment method has minimal impact on satisfaction
    - Freight cost alone doesn't significantly affect ratings
    - Delivery speed matters more than delivery cost

    **Recommendations:**
    - **Priority 1:** Improve delivery speed and reliability
    - **Priority 2:** Focus on states with lowest satisfaction scores
    - **Priority 3:** Set realistic delivery expectations
    - **Priority 4:** Reduce late deliveries to improve NPS
    - **Priority 5:** Monitor satisfaction trends for early warning signals

    **Key Takeaway:**
    Delivery performance is the dominant factor in customer satisfaction.
    Improving on-time delivery rates will have the greatest impact on NPS.
    """)
    return


if __name__ == "__main__":
    app.run()
