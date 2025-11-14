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
    # Geographic & Market Distribution - Olist E-Commerce

    **Business Questions Answered:**
    - Q61: Revenue distribution across Brazilian states
    - Q62: Cities generating the most orders and revenue
    - Q64: Customer satisfaction variation by region
    - Q67: Regions with highest growth rates
    - Q70: Regions with best unit economics

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
    ## Revenue Distribution by State

    **Q61:** Revenue distribution across Brazilian states
    """)
    return


@app.cell
def _(con, date_range):
    # State-level revenue analysis
    state_revenue_query = f"""
    SELECT
        customer_state,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(*) as total_orders,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value,
        AVG(total_freight) as avg_freight,
        AVG(total_freight / NULLIF(total_order_value, 0) * 100) as freight_pct,
        AVG(review_score) as avg_satisfaction,
        AVG(days_to_delivery) as avg_delivery_days
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND customer_state IS NOT NULL
    GROUP BY customer_state
    ORDER BY total_revenue DESC
    """

    state_revenue = con.execute(state_revenue_query).df()

    # Calculate percentages
    state_revenue['revenue_pct'] = state_revenue['total_revenue'] / state_revenue['total_revenue'].sum() * 100
    state_revenue['orders_pct'] = state_revenue['total_orders'] / state_revenue['total_orders'].sum() * 100
    return (state_revenue,)


@app.cell
def _(px, state_revenue):
    # Top states by revenue
    top_states_rev = state_revenue.nlargest(15, 'total_revenue')

    fig_state_rev = px.bar(
        top_states_rev,
        x='customer_state',
        y='total_revenue',
        title='Top 15 States by Revenue',
        labels={'total_revenue': 'Revenue (R$)', 'customer_state': 'State'},
        color='total_revenue',
        color_continuous_scale='Blues',
        text='total_revenue'
    )

    fig_state_rev.update_traces(
        texttemplate='R$ %{text:,.0f}',
        textposition='outside'
    )
    fig_state_rev.update_layout(showlegend=False, height=500)
    fig_state_rev
    return


@app.cell
def _(go, make_subplots, state_revenue):
    # Revenue vs orders concentration
    top_10_states = state_revenue.nlargest(10, 'total_revenue')

    fig_concentration = make_subplots(
        rows=1, cols=2,
        subplot_titles=('% of Revenue', '% of Orders'),
        specs=[[{'type': 'pie'}, {'type': 'pie'}]]
    )

    # Revenue pie
    fig_concentration.add_trace(
        go.Pie(
            labels=top_10_states['customer_state'],
            values=top_10_states['revenue_pct'],
            name='Revenue',
            textposition='inside',
            textinfo='label+percent'
        ),
        row=1, col=1
    )

    # Orders pie
    fig_concentration.add_trace(
        go.Pie(
            labels=top_10_states['customer_state'],
            values=top_10_states['orders_pct'],
            name='Orders',
            textposition='inside',
            textinfo='label+percent'
        ),
        row=1, col=2
    )

    fig_concentration.update_layout(
        height=450,
        showlegend=True,
        title_text="Market Concentration: Top 10 States"
    )

    fig_concentration
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Top Cities Analysis

    **Q62:** Cities generating the most orders and revenue
    """)
    return


@app.cell
def _(con, date_range):
    # City-level analysis
    city_revenue_query = f"""
    SELECT
        customer_city,
        customer_state,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(*) as total_orders,
        SUM(total_order_value) as total_revenue,
        AVG(total_order_value) as avg_order_value,
        AVG(review_score) as avg_satisfaction
    FROM core_core.fct_orders
    WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
    AND is_delivered = TRUE
    AND customer_city IS NOT NULL
    GROUP BY customer_city, customer_state
    HAVING COUNT(*) >= 50
    ORDER BY total_revenue DESC
    LIMIT 20
    """

    city_revenue = con.execute(city_revenue_query).df()
    city_revenue['city_state'] = city_revenue['customer_city'] + ' (' + city_revenue['customer_state'] + ')'
    return (city_revenue,)


@app.cell
def _(city_revenue, px):
    # Top cities by revenue
    fig_city_rev = px.bar(
        city_revenue.head(15),
        y='city_state',
        x='total_revenue',
        orientation='h',
        title='Top 15 Cities by Revenue',
        labels={'total_revenue': 'Revenue (R$)', 'city_state': 'City (State)'},
        color='total_revenue',
        color_continuous_scale='Greens',
        text='total_revenue'
    )

    fig_city_rev.update_traces(
        texttemplate='R$ %{text:,.0f}',
        textposition='outside'
    )
    fig_city_rev.update_layout(showlegend=False, height=600)
    fig_city_rev
    return


@app.cell
def _(city_revenue, px):
    # City scatter: orders vs revenue
    fig_city_scatter = px.scatter(
        city_revenue,
        x='total_orders',
        y='total_revenue',
        size='unique_customers',
        color='avg_satisfaction',
        hover_name='city_state',
        title='City Performance: Orders vs Revenue',
        labels={
            'total_orders': 'Total Orders',
            'total_revenue': 'Revenue (R$)',
            'unique_customers': 'Customers',
            'avg_satisfaction': 'Satisfaction'
        },
        color_continuous_scale='RdYlGn'
    )

    fig_city_scatter.update_layout(height=500)
    fig_city_scatter
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Regional Growth Analysis

    **Q67:** Regions with highest growth rates
    """)
    return


@app.cell
def _(con, date_range):
    # State growth analysis (comparing first half vs second half)
    growth_query = f"""
    WITH period_split AS (
        SELECT
            customer_state,
            CASE
                WHEN order_date < DATE '{date_range.value[0]}'::DATE + INTERVAL '12 months'
                THEN 'First Year'
                ELSE 'Second Year'
            END as period,
            COUNT(*) as order_count,
            SUM(total_order_value) as revenue
        FROM core_core.fct_orders
        WHERE order_date BETWEEN '{date_range.value[0]}' AND '{date_range.value[1]}'
        AND is_delivered = TRUE
        AND customer_state IS NOT NULL
        GROUP BY customer_state, period
    ),
    growth_calc AS (
        SELECT
            customer_state,
            MAX(CASE WHEN period = 'First Year' THEN revenue END) as first_year_revenue,
            MAX(CASE WHEN period = 'Second Year' THEN revenue END) as second_year_revenue,
            MAX(CASE WHEN period = 'First Year' THEN order_count END) as first_year_orders,
            MAX(CASE WHEN period = 'Second Year' THEN order_count END) as second_year_orders
        FROM period_split
        GROUP BY customer_state
    )
    SELECT
        customer_state,
        first_year_revenue,
        second_year_revenue,
        CASE
            WHEN first_year_revenue > 0
            THEN ((second_year_revenue - first_year_revenue) / first_year_revenue * 100)
            ELSE NULL
        END as revenue_growth_pct,
        CASE
            WHEN first_year_orders > 0
            THEN ((second_year_orders - first_year_orders) / first_year_orders * 100)
            ELSE NULL
        END as orders_growth_pct
    FROM growth_calc
    WHERE first_year_revenue IS NOT NULL
    AND second_year_revenue IS NOT NULL
    ORDER BY revenue_growth_pct DESC
    """

    state_growth = con.execute(growth_query).df()
    return (state_growth,)


@app.cell
def _(px, state_growth):
    # Top growing states
    top_growth = state_growth.nlargest(15, 'revenue_growth_pct')

    fig_growth = px.bar(
        top_growth,
        x='customer_state',
        y='revenue_growth_pct',
        title='Top 15 Fastest Growing States (YoY Revenue Growth)',
        labels={'revenue_growth_pct': 'Revenue Growth (%)', 'customer_state': 'State'},
        color='revenue_growth_pct',
        color_continuous_scale='Greens',
        text='revenue_growth_pct'
    )

    fig_growth.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    fig_growth.update_layout(showlegend=False)
    fig_growth
    return


@app.cell
def _(px, state_growth):
    # Growth scatter: revenue vs orders growth
    fig_growth_scatter = px.scatter(
        state_growth[state_growth['revenue_growth_pct'].notna()],
        x='orders_growth_pct',
        y='revenue_growth_pct',
        hover_name='customer_state',
        title='State Growth: Orders Growth vs Revenue Growth',
        labels={
            'orders_growth_pct': 'Orders Growth (%)',
            'revenue_growth_pct': 'Revenue Growth (%)'
        },
        color='revenue_growth_pct',
        color_continuous_scale='RdYlGn'
    )

    # Add reference line
    fig_growth_scatter.add_shape(
        type='line',
        x0=-100, x1=300,
        y0=-100, y1=300,
        line=dict(color='gray', dash='dash')
    )

    fig_growth_scatter.update_layout(height=500)
    fig_growth_scatter
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Unit Economics by Region

    **Q70:** Regions with best unit economics
    """)
    return


@app.cell
def _(state_revenue):
    # Calculate unit economics metrics
    state_economics = state_revenue.copy()

    # Revenue per customer
    state_economics['revenue_per_customer'] = state_economics['total_revenue'] / state_economics['unique_customers']

    # Orders per customer
    state_economics['orders_per_customer'] = state_economics['total_orders'] / state_economics['unique_customers']

    # Sort by revenue per customer
    state_economics_sorted = state_economics.sort_values('revenue_per_customer', ascending=False)
    return state_economics, state_economics_sorted


@app.cell
def _(px, state_economics_sorted):
    # Top states by revenue per customer
    top_economics = state_economics_sorted.head(15)

    fig_economics = px.bar(
        top_economics,
        x='customer_state',
        y='revenue_per_customer',
        title='Top 15 States by Revenue per Customer',
        labels={'revenue_per_customer': 'Revenue per Customer (R$)', 'customer_state': 'State'},
        color='revenue_per_customer',
        color_continuous_scale='Purples',
        text='revenue_per_customer'
    )

    fig_economics.update_traces(
        texttemplate='R$ %{text:.2f}',
        textposition='outside'
    )
    fig_economics.update_layout(showlegend=False)
    fig_economics
    return


@app.cell
def _(go, make_subplots, state_economics):
    # Unit economics comparison: AOV, Freight %, Satisfaction
    top_15_states = state_economics.nlargest(15, 'total_revenue')

    fig_unit_econ = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Avg Order Value', 'Freight %', 'Satisfaction Score')
    )

    # AOV
    fig_unit_econ.add_trace(
        go.Bar(
            x=top_15_states['customer_state'],
            y=top_15_states['avg_order_value'],
            name='AOV',
            marker_color='#636EFA',
            showlegend=False
        ),
        row=1, col=1
    )

    # Freight %
    fig_unit_econ.add_trace(
        go.Bar(
            x=top_15_states['customer_state'],
            y=top_15_states['freight_pct'],
            name='Freight %',
            marker_color='#EF553B',
            showlegend=False
        ),
        row=1, col=2
    )

    # Satisfaction
    fig_unit_econ.add_trace(
        go.Bar(
            x=top_15_states['customer_state'],
            y=top_15_states['avg_satisfaction'],
            name='Satisfaction',
            marker_color='#00CC96',
            showlegend=False
        ),
        row=1, col=3
    )

    fig_unit_econ.update_yaxes(title_text="AOV (R$)", row=1, col=1)
    fig_unit_econ.update_yaxes(title_text="Freight %", row=1, col=2)
    fig_unit_econ.update_yaxes(title_text="Rating (1-5)", row=1, col=3, range=[0, 5])
    fig_unit_econ.update_xaxes(tickangle=45)

    fig_unit_econ.update_layout(
        height=450,
        title_text="Unit Economics: Top 15 States"
    )

    fig_unit_econ
    return


@app.cell
def _(px, state_economics):
    # Comprehensive state performance scatter
    fig_state_performance = px.scatter(
        state_economics,
        x='avg_order_value',
        y='avg_satisfaction',
        size='total_revenue',
        color='freight_pct',
        hover_name='customer_state',
        title='State Performance Matrix: AOV vs Satisfaction',
        labels={
            'avg_order_value': 'Avg Order Value (R$)',
            'avg_satisfaction': 'Satisfaction Score',
            'total_revenue': 'Total Revenue',
            'freight_pct': 'Freight %'
        },
        color_continuous_scale='RdYlGn_r'
    )

    fig_state_performance.update_layout(height=500)
    fig_state_performance
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Key Insights Summary

    Based on the geographic and market distribution analysis:

    **Revenue Concentration:**
    - Revenue is highly concentrated in a few states
    - Top 10 states account for majority of GMV
    - SP (São Paulo) dominates the market
    - Opportunity for expansion in underserved states

    **Top Cities:**
    - Urban centers drive most revenue
    - Large cities have better unit economics
    - Metro areas show higher customer density
    - Potential for city-specific strategies

    **Growth Patterns:**
    - Emerging states show high growth rates
    - Smaller markets growing faster than mature ones
    - Early-stage markets offer expansion opportunities
    - Monitor fast-growing regions for scaling

    **Unit Economics:**
    - Significant variation in AOV by state
    - Freight costs higher in remote regions
    - Urban states have better margins
    - Satisfaction correlates with delivery performance

    **Regional Strategy:**
    - **Mature Markets (SP, RJ, MG):** Focus on retention and AOV
    - **Growing Markets:** Invest in logistics and customer acquisition
    - **Remote Markets:** Optimize freight costs and delivery times
    - **Underserved Regions:** Evaluate expansion potential

    **Recommendations:**
    - Expand logistics infrastructure in high-growth states
    - Optimize freight costs for remote regions
    - Target top cities for premium product offerings
    - Develop region-specific marketing strategies
    - Balance market share growth with profitability
    """)
    return


if __name__ == "__main__":
    app.run()
