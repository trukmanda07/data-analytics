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
    # Customer RFM Analysis Dashboard - Olist E-Commerce

    **Business Questions Answered:**
    - Which customers are most valuable (RFM segmentation)?
    - Who are our champions vs at-risk customers?
    - What are customer lifecycle stages?
    - Which customers should we target for reactivation?
    - How do customer segments differ in behavior?

    **Data Source:** mart_customer_analytics (99,441 customers)

    **RFM Framework:**
    - **Recency** - Days since last purchase (lower is better)
    - **Frequency** - Number of orders (higher is better)
    - **Monetary** - Total lifetime value (higher is better)

    **Customer Segments:**
    - Champions, Loyal Customers, Big Spenders
    - New Customers, At Risk, Lost
    - Regular customers
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
    ## Segment Filter

    Select RFM segments to analyze:
    """)
    return


@app.cell
def _(con):
    # Get available segments
    segments_df = con.execute("""
        SELECT DISTINCT rfm_segment
        FROM marts_customer.mart_customer_analytics
        WHERE rfm_segment IS NOT NULL
        ORDER BY rfm_segment
    """).df()

    segment_list = ['All Segments'] + segments_df['rfm_segment'].tolist()
    return segment_list, segments_df


@app.cell
def _(mo, segment_list):
    segment_filter = mo.ui.dropdown(
        options=segment_list,
        value='All Segments',
        label="RFM Segment"
    )

    lifecycle_filter = mo.ui.dropdown(
        options=['All', 'Active Repeat', 'Active New', 'Cooling Down', 'At Risk', 'Dormant', 'Never Purchased'],
        value='All',
        label="Lifecycle Stage"
    )

    mo.vstack([segment_filter, lifecycle_filter])
    return lifecycle_filter, segment_filter


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Base Overview

    High-level metrics for the customer base:
    """)
    return


@app.cell
def _(con, lifecycle_filter, segment_filter):
    # Build filter conditions
    filters = []
    if segment_filter.value != 'All Segments':
        filters.append(f"rfm_segment = '{segment_filter.value}'")
    if lifecycle_filter.value != 'All':
        filters.append(f"lifecycle_stage = '{lifecycle_filter.value}'")

    where_clause = "WHERE " + " AND ".join(filters) if filters else ""

    # Calculate customer KPIs
    customer_kpis = con.execute(f"""
        SELECT
            COUNT(DISTINCT customer_id) as total_customers,
            SUM(lifetime_value) as total_ltv,
            AVG(lifetime_value) as avg_ltv,
            AVG(total_orders) as avg_orders,
            AVG(recency_days) as avg_recency,
            AVG(avg_review_score) as avg_satisfaction
        FROM marts_customer.mart_customer_analytics
        {where_clause}
    """).df()

    kpi_data = customer_kpis.iloc[0]
    return customer_kpis, filters, kpi_data, where_clause


@app.cell
def _(kpi_data, mo):
    mo.hstack([
        mo.stat(label="Total Customers", value=f"{kpi_data['total_customers']:,}"),
        mo.stat(label="Total LTV", value=f"R$ {kpi_data['total_ltv']:,.2f}"),
        mo.stat(label="Avg LTV", value=f"R$ {kpi_data['avg_ltv']:,.2f}"),
        mo.stat(label="Avg Orders", value=f"{kpi_data['avg_orders']:.1f}"),
        mo.stat(label="Avg Satisfaction", value=f"{kpi_data['avg_satisfaction']:.2f} ⭐")
    ])
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## RFM Segmentation Overview

    Customer distribution across RFM segments:
    """)
    return


@app.cell
def _(con):
    rfm_segments = con.execute("""
        SELECT
            rfm_segment,
            COUNT(DISTINCT customer_id) as customer_count,
            SUM(lifetime_value) as total_ltv,
            AVG(lifetime_value) as avg_ltv,
            AVG(total_orders) as avg_orders,
            AVG(recency_days) as avg_recency,
            AVG(rfm_total_score) as avg_rfm_score,
            AVG(avg_review_score) as avg_satisfaction
        FROM marts_customer.mart_customer_analytics
        WHERE rfm_segment IS NOT NULL
        GROUP BY rfm_segment
        ORDER BY avg_rfm_score DESC
    """).df()

    rfm_segments
    return (rfm_segments,)


@app.cell
def _(make_subplots, rfm_segments):
    fig_rfm_overview = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'pie'}, {'type': 'pie'}]],
        subplot_titles=('Customer Count by Segment', 'Lifetime Value by Segment')
    )

    colors = {
        'Champions': '#27ae60',
        'Loyal Customers': '#2ecc71',
        'Big Spenders': '#f39c12',
        'New Customers': '#3498db',
        'At Risk': '#e67e22',
        'Lost': '#e74c3c',
        'Regular': '#95a5a6'
    }

    segment_colors = [colors.get(seg, '#95a5a6') for seg in rfm_segments['rfm_segment']]

    fig_rfm_overview.add_trace(
        dict(
            type='pie',
            labels=rfm_segments['rfm_segment'],
            values=rfm_segments['customer_count'],
            marker=dict(colors=segment_colors),
            name='Customers'
        ),
        row=1, col=1
    )

    fig_rfm_overview.add_trace(
        dict(
            type='pie',
            labels=rfm_segments['rfm_segment'],
            values=rfm_segments['total_ltv'],
            marker=dict(colors=segment_colors),
            name='LTV'
        ),
        row=1, col=2
    )

    fig_rfm_overview.update_layout(
        title="RFM Segment Distribution",
        height=500
    )

    fig_rfm_overview
    return colors, fig_rfm_overview, segment_colors


@app.cell
def _(mo):
    mo.md("""
    ---
    ## RFM Score Distribution

    Individual R, F, M scores across the customer base:
    """)
    return


@app.cell
def _(con, where_clause):
    rfm_score_dist = con.execute(f"""
        SELECT
            recency_score,
            frequency_score,
            monetary_score,
            COUNT(DISTINCT customer_id) as customer_count
        FROM marts_customer.mart_customer_analytics
        {where_clause}
        GROUP BY recency_score, frequency_score, monetary_score
        ORDER BY recency_score, frequency_score, monetary_score
    """).df()
    return (rfm_score_dist,)


@app.cell
def _(con, where_clause):
    # Get score averages by segment
    score_by_segment = con.execute(f"""
        SELECT
            rfm_segment,
            AVG(recency_score) as avg_r,
            AVG(frequency_score) as avg_f,
            AVG(monetary_score) as avg_m
        FROM marts_customer.mart_customer_analytics
        {where_clause}
        AND rfm_segment IS NOT NULL
        GROUP BY rfm_segment
        ORDER BY (avg_r + avg_f + avg_m) DESC
    """).df()
    return (score_by_segment,)


@app.cell
def _(go, score_by_segment):
    fig_rfm_scores = go.Figure()

    fig_rfm_scores.add_trace(go.Bar(
        name='Recency Score',
        x=score_by_segment['rfm_segment'],
        y=score_by_segment['avg_r'],
        marker_color='#3498db'
    ))

    fig_rfm_scores.add_trace(go.Bar(
        name='Frequency Score',
        x=score_by_segment['rfm_segment'],
        y=score_by_segment['avg_f'],
        marker_color='#2ecc71'
    ))

    fig_rfm_scores.add_trace(go.Bar(
        name='Monetary Score',
        x=score_by_segment['rfm_segment'],
        y=score_by_segment['avg_m'],
        marker_color='#f39c12'
    ))

    fig_rfm_scores.update_layout(
        title='Average RFM Scores by Segment',
        xaxis_title='RFM Segment',
        yaxis_title='Score (1-5)',
        barmode='group',
        height=500
    )

    fig_rfm_scores
    return (fig_rfm_scores,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Lifecycle Analysis

    Distribution across lifecycle stages:
    """)
    return


@app.cell
def _(con):
    lifecycle_data = con.execute("""
        SELECT
            lifecycle_stage,
            COUNT(DISTINCT customer_id) as customer_count,
            SUM(lifetime_value) as total_ltv,
            AVG(lifetime_value) as avg_ltv,
            AVG(recency_days) as avg_recency,
            AVG(total_orders) as avg_orders,
            AVG(avg_review_score) as avg_satisfaction
        FROM marts_customer.mart_customer_analytics
        GROUP BY lifecycle_stage
        ORDER BY
            CASE lifecycle_stage
                WHEN 'Active Repeat' THEN 1
                WHEN 'Active New' THEN 2
                WHEN 'Cooling Down' THEN 3
                WHEN 'At Risk' THEN 4
                WHEN 'Dormant' THEN 5
                WHEN 'Never Purchased' THEN 6
            END
    """).df()

    lifecycle_data
    return (lifecycle_data,)


@app.cell
def _(lifecycle_data, make_subplots):
    fig_lifecycle = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Customer Count', 'Total Lifetime Value',
            'Avg Orders per Customer', 'Avg Recency (days)'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )

    lifecycle_colors = {
        'Active Repeat': '#27ae60',
        'Active New': '#2ecc71',
        'Cooling Down': '#f39c12',
        'At Risk': '#e67e22',
        'Dormant': '#e74c3c',
        'Never Purchased': '#95a5a6'
    }

    bar_colors = [lifecycle_colors.get(stage, '#95a5a6') for stage in lifecycle_data['lifecycle_stage']]

    fig_lifecycle.add_trace(
        dict(
            type='bar',
            x=lifecycle_data['lifecycle_stage'],
            y=lifecycle_data['customer_count'],
            marker=dict(color=bar_colors)
        ),
        row=1, col=1
    )

    fig_lifecycle.add_trace(
        dict(
            type='bar',
            x=lifecycle_data['lifecycle_stage'],
            y=lifecycle_data['total_ltv'],
            marker=dict(color=bar_colors)
        ),
        row=1, col=2
    )

    fig_lifecycle.add_trace(
        dict(
            type='bar',
            x=lifecycle_data['lifecycle_stage'],
            y=lifecycle_data['avg_orders'],
            marker=dict(color=bar_colors)
        ),
        row=2, col=1
    )

    fig_lifecycle.add_trace(
        dict(
            type='bar',
            x=lifecycle_data['lifecycle_stage'],
            y=lifecycle_data['avg_recency'],
            marker=dict(color=bar_colors)
        ),
        row=2, col=2
    )

    fig_lifecycle.update_layout(
        title="Customer Lifecycle Analysis",
        height=700,
        showlegend=False
    )

    fig_lifecycle
    return bar_colors, fig_lifecycle, lifecycle_colors


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Value Tier Analysis

    Customer segmentation by lifetime value:
    """)
    return


@app.cell
def _(con):
    value_tiers = con.execute("""
        SELECT
            value_tier,
            COUNT(DISTINCT customer_id) as customer_count,
            SUM(lifetime_value) as total_ltv,
            AVG(lifetime_value) as avg_ltv,
            AVG(total_orders) as avg_orders,
            MIN(lifetime_value) as min_ltv,
            MAX(lifetime_value) as max_ltv
        FROM marts_customer.mart_customer_analytics
        GROUP BY value_tier
        ORDER BY
            CASE value_tier
                WHEN 'VIP' THEN 1
                WHEN 'High Value' THEN 2
                WHEN 'Medium Value' THEN 3
                WHEN 'Low Value' THEN 4
                WHEN 'No Orders' THEN 5
            END
    """).df()

    value_tiers
    return (value_tiers,)


@app.cell
def _(px, value_tiers):
    # Value tier contribution
    fig_value_tiers = px.sunburst(
        value_tiers,
        path=['value_tier'],
        values='total_ltv',
        color='avg_ltv',
        color_continuous_scale='Greens',
        title='Revenue Contribution by Value Tier'
    )

    fig_value_tiers.update_layout(height=600)
    fig_value_tiers
    return (fig_value_tiers,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## RFM Segment Deep Dive

    Detailed characteristics of each segment:
    """)
    return


@app.cell
def _(con, where_clause):
    segment_characteristics = con.execute(f"""
        SELECT
            rfm_segment,
            COUNT(DISTINCT customer_id) as customers,
            AVG(recency_days) as avg_recency_days,
            AVG(frequency) as avg_frequency,
            AVG(monetary_value) as avg_monetary,
            AVG(lifetime_value) as avg_ltv,
            AVG(total_orders) as avg_orders,
            AVG(avg_order_value) as avg_order_value,
            AVG(avg_review_score) as avg_satisfaction,
            AVG(on_time_delivery_rate) as avg_on_time_rate,
            SUM(lifetime_value) / SUM(SUM(lifetime_value)) OVER () * 100 as ltv_contribution_pct
        FROM marts_customer.mart_customer_analytics
        {where_clause}
        AND rfm_segment IS NOT NULL
        GROUP BY rfm_segment
        ORDER BY ltv_contribution_pct DESC
    """).df()

    segment_characteristics
    return (segment_characteristics,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Reactivation Opportunities

    Customers at risk or dormant that could be targeted:
    """)
    return


@app.cell
def _(con):
    reactivation_targets = con.execute("""
        SELECT
            rfm_segment,
            lifecycle_stage,
            COUNT(DISTINCT customer_id) as customer_count,
            SUM(lifetime_value) as historical_ltv,
            AVG(total_orders) as avg_past_orders,
            AVG(recency_days) as avg_days_since_purchase,
            AVG(avg_review_score) as avg_past_satisfaction
        FROM marts_customer.mart_customer_analytics
        WHERE rfm_segment IN ('At Risk', 'Lost')
           OR lifecycle_stage IN ('Cooling Down', 'At Risk', 'Dormant')
        GROUP BY rfm_segment, lifecycle_stage
        ORDER BY historical_ltv DESC
    """).df()

    reactivation_targets
    return (reactivation_targets,)


@app.cell
def _(go, reactivation_targets):
    fig_reactivation = go.Figure()

    fig_reactivation.add_trace(go.Bar(
        x=reactivation_targets['rfm_segment'] + ' - ' + reactivation_targets['lifecycle_stage'],
        y=reactivation_targets['customer_count'],
        marker=dict(
            color=reactivation_targets['historical_ltv'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Historical<br>LTV")
        ),
        text=reactivation_targets['customer_count'],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Customers: %{y}<br>Historical LTV: R$ %{marker.color:,.2f}<extra></extra>'
    ))

    fig_reactivation.update_layout(
        title="Reactivation Opportunities (At Risk & Lost Customers)",
        xaxis_title="Segment - Lifecycle Stage",
        yaxis_title="Customer Count",
        height=600,
        showlegend=False
    )

    fig_reactivation.update_xaxes(tickangle=45)
    fig_reactivation
    return (fig_reactivation,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Geographic Distribution by Segment

    Regional presence of different customer segments:
    """)
    return


@app.cell
def _(con):
    segment_by_region = con.execute("""
        SELECT
            region,
            rfm_segment,
            COUNT(DISTINCT customer_id) as customer_count,
            SUM(lifetime_value) as total_ltv
        FROM marts_customer.mart_customer_analytics
        WHERE region IS NOT NULL
        AND rfm_segment IS NOT NULL
        GROUP BY region, rfm_segment
        ORDER BY region, total_ltv DESC
    """).df()
    return (segment_by_region,)


@app.cell
def _(px, segment_by_region):
    fig_region_segment = px.bar(
        segment_by_region,
        x='region',
        y='customer_count',
        color='rfm_segment',
        title='Customer Segments by Region',
        labels={
            'region': 'Region',
            'customer_count': 'Customer Count',
            'rfm_segment': 'RFM Segment'
        },
        height=600,
        barmode='stack'
    )

    fig_region_segment
    return (fig_region_segment,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Customer Behavior Patterns

    Purchase and review behavior by segment:
    """)
    return


@app.cell
def _(con, where_clause):
    behavior_patterns = con.execute(f"""
        SELECT
            rfm_segment,
            AVG(avg_days_between_orders) as avg_repurchase_cycle,
            AVG(avg_items_per_order) as avg_basket_size,
            AVG(installment_orders) / NULLIF(AVG(total_orders), 0) * 100 as installment_rate,
            AVG(orders_with_comments) / NULLIF(AVG(total_orders), 0) * 100 as comment_rate,
            AVG(unique_categories_purchased) as avg_categories
        FROM marts_customer.mart_customer_analytics
        {where_clause}
        AND rfm_segment IS NOT NULL
        GROUP BY rfm_segment
        ORDER BY avg_repurchase_cycle
    """).df()
    return (behavior_patterns,)


@app.cell
def _(behavior_patterns, make_subplots):
    fig_behavior = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Avg Repurchase Cycle (days)', 'Avg Basket Size (items)',
            'Installment Usage Rate (%)', 'Avg Categories Purchased'
        ),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )

    fig_behavior.add_trace(
        dict(
            type='bar',
            x=behavior_patterns['rfm_segment'],
            y=behavior_patterns['avg_repurchase_cycle'],
            marker=dict(color='#3498db')
        ),
        row=1, col=1
    )

    fig_behavior.add_trace(
        dict(
            type='bar',
            x=behavior_patterns['rfm_segment'],
            y=behavior_patterns['avg_basket_size'],
            marker=dict(color='#2ecc71')
        ),
        row=1, col=2
    )

    fig_behavior.add_trace(
        dict(
            type='bar',
            x=behavior_patterns['rfm_segment'],
            y=behavior_patterns['installment_rate'],
            marker=dict(color='#f39c12')
        ),
        row=2, col=1
    )

    fig_behavior.add_trace(
        dict(
            type='bar',
            x=behavior_patterns['rfm_segment'],
            y=behavior_patterns['avg_categories'],
            marker=dict(color='#9b59b6')
        ),
        row=2, col=2
    )

    fig_behavior.update_layout(
        title="Customer Behavior Patterns by RFM Segment",
        height=700,
        showlegend=False
    )

    fig_behavior.update_xaxes(tickangle=45)
    fig_behavior
    return (fig_behavior,)


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights & Recommendations

    **Segment Strategies:**

    **Champions** (High R, F, M)
    - Reward with exclusive perks and early access
    - Use as brand ambassadors
    - Maintain high service quality

    **Loyal Customers** (Good R, F, M)
    - Upsell and cross-sell opportunities
    - Encourage referrals
    - Build long-term relationships

    **Big Spenders** (High M, varying R, F)
    - VIP treatment and personalized service
    - Premium product recommendations
    - Special pricing or bundles

    **New Customers** (High R, low F)
    - Welcome programs and onboarding
    - Product education
    - Incentivize second purchase

    **At Risk** (Low R, high F)
    - Win-back campaigns with special offers
    - Survey for feedback
    - Remind of past positive experiences

    **Lost** (Very low R)
    - Aggressive reactivation campaigns
    - Significant discounts or promotions
    - Understand reasons for churn

    **Regular** (Average scores)
    - Nurture with consistent engagement
    - Move up to Loyal or Champions
    - Prevent downgrade to At Risk
    """)
    return


if __name__ == "__main__":
    app.run()
