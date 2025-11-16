import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def __():
    from datetime import datetime, timedelta

    import duckdb
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    return mo, duckdb, pd, px, go, datetime, timedelta


@app.cell
def __(mo):
    mo.md(
        """
    # dbt Pipeline Performance Dashboard

    Monitor your dbt pipeline execution metrics, test results, and model performance.

    This dashboard uses **custom monitoring tables** to track:
    - Model execution times and trends
    - Pipeline run history
    - Slowest models identification
    - Performance over time

    **Data Source:** `core_monitoring.dbt_run_history` and `core_monitoring.dbt_model_history`

    **To populate data:** After running dbt, execute `python3 monitoring/log_run_results.py`
    or use the wrapper script `./dbt_run.sh` which does this automatically.
    """
    )
    return


@app.cell
def __():
    # Connect to DuckDB database (where dbt writes artifacts)
    con = duckdb.connect(
        "/home/dhafin/Documents/Projects/EDA/data/duckdb/olist_analytical.duckdb"
    )
    return (con,)


@app.cell
def __(mo):
    mo.md(
        """
    ## Monitoring Data Status

    Checking custom monitoring tables:
    """
    )
    return


@app.cell
def __(con):
    # Check monitoring table row counts
    monitoring_status = con.execute(
        """
        SELECT
            'dbt_run_history' as table_name,
            COUNT(*) as row_count,
            MAX(run_started_at) as latest_record
        FROM core_monitoring.dbt_run_history
        UNION ALL
        SELECT
            'dbt_model_history' as table_name,
            COUNT(*) as row_count,
            MAX(executed_at) as latest_record
        FROM core_monitoring.dbt_model_history
    """
    ).df()
    monitoring_status
    return (monitoring_status,)


@app.cell
def __(mo):
    mo.md(
        """
    ---
    ## Pipeline Performance Metrics
    """
    )
    return


@app.cell
def __(con, mo):
    # Latest pipeline stats
    latest_stats = con.execute(
        """
        SELECT
            SUM(total_models) AS models_run,
            ROUND(SUM(total_runtime_seconds), 2) AS total_runtime_seconds,
            SUM(CASE WHEN success = false THEN 1 ELSE 0 END) AS failed_runs,
            MAX(run_started_at) AS last_run
        FROM core_monitoring.dbt_run_history
        WHERE run_started_at >= CURRENT_DATE - INTERVAL '7 days'
    """
    ).df()

    mo.hstack(
        [
            mo.stat(
                label="Models Run (7 days)",
                value=f"{latest_stats['models_run'][0] or 0:,}",
            ),
            mo.stat(
                label="Total Runtime (sec)",
                value=f"{latest_stats['total_runtime_seconds'][0] or 0:,.1f}",
            ),
            mo.stat(
                label="Failed Runs", value=f"{latest_stats['failed_runs'][0] or 0:,}"
            ),
        ]
    )
    return (latest_stats,)


@app.cell
def __(con, px):
    # Model execution trend
    trend_data = con.execute(
        """
        SELECT
            DATE_TRUNC('day', run_started_at) AS run_date,
            SUM(total_models) AS models_executed,
            ROUND(SUM(total_runtime_seconds), 2) AS runtime_seconds
        FROM core_monitoring.dbt_run_history
        WHERE run_started_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', run_started_at)
        ORDER BY run_date
    """
    ).df()

    if len(trend_data) > 0:
        fig_trend = px.line(
            trend_data,
            x="run_date",
            y="runtime_seconds",
            title="Daily Pipeline Runtime (Last 30 Days)",
            labels={"run_date": "Date", "runtime_seconds": "Runtime (seconds)"},
            markers=True,
        )
        fig_trend.update_layout(hovermode="x unified")
        fig_trend
    else:
        mo.md(
            "**No run data yet.** Run dbt and execute `python3 monitoring/log_run_results.py` to populate."
        )
    return (trend_data,) if len(trend_data) > 0 else tuple()


@app.cell
def __(con, px, mo):
    # Slowest models (7 day average)
    slow_models = con.execute(
        """
        SELECT
            model_name,
            materialization,
            ROUND(AVG(execution_time_seconds), 2) AS avg_seconds,
            COUNT(*) AS run_count
        FROM core_monitoring.dbt_model_history
        WHERE status = 'success'
            AND executed_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY model_name, materialization
        HAVING COUNT(*) > 0
        ORDER BY avg_seconds DESC
        LIMIT 15
    """
    ).df()

    if len(slow_models) > 0:
        fig_slow = px.bar(
            slow_models,
            x="avg_seconds",
            y="model_name",
            color="materialization",
            orientation="h",
            title="Top 15 Slowest Models (7 Day Average)",
            labels={
                "avg_seconds": "Avg Execution Time (seconds)",
                "model_name": "Model",
            },
            hover_data=["run_count"],
        )
        fig_slow.update_layout(height=500)
        fig_slow
    else:
        mo.md("**No model execution data yet.**")
    return (slow_models,) if len(slow_models) > 0 else tuple()


@app.cell
def __(con, px, mo):
    # Performance by model layer
    layer_performance = con.execute(
        """
        SELECT
            CASE
                WHEN model_name LIKE 'stg_%' THEN 'staging'
                WHEN model_name LIKE 'int_%' THEN 'intermediate'
                WHEN model_name LIKE 'dim_%' THEN 'dimension'
                WHEN model_name LIKE 'fct_%' THEN 'fact'
                WHEN model_name LIKE 'mart_%' THEN 'mart'
                ELSE 'other'
            END AS model_layer,
            COUNT(DISTINCT model_name) AS model_count,
            ROUND(AVG(execution_time_seconds), 2) AS avg_execution_seconds,
            ROUND(SUM(execution_time_seconds), 2) AS total_execution_seconds
        FROM core_monitoring.dbt_model_history
        WHERE status = 'success'
            AND executed_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY model_layer
        ORDER BY total_execution_seconds DESC
    """
    ).df()

    if len(layer_performance) > 0:
        fig_layer = px.bar(
            layer_performance,
            x="model_layer",
            y="total_execution_seconds",
            title="Total Execution Time by Model Layer (7 Days)",
            labels={"model_layer": "Layer", "total_execution_seconds": "Total Seconds"},
            text="model_count",
            color="avg_execution_seconds",
            color_continuous_scale="Viridis",
        )
        fig_layer.update_traces(texttemplate="%{text} models", textposition="outside")
        fig_layer
    else:
        mo.md("**No layer performance data yet.**")
    return (layer_performance,) if len(layer_performance) > 0 else tuple()


@app.cell
def __(mo):
    mo.md(
        """
    ## Recent Pipeline Runs
    """
    )
    return


@app.cell
def __(con):
    # Recent pipeline runs
    recent_runs = con.execute(
        """
        SELECT
            invocation_id,
            dbt_command,
            run_started_at::TIMESTAMP AS run_time,
            ROUND(total_runtime_seconds, 2) AS runtime_sec,
            total_models,
            success
        FROM core_monitoring.dbt_run_history
        ORDER BY run_started_at DESC
        LIMIT 10
    """
    ).df()

    recent_runs
    return (recent_runs,)


@app.cell
def __(con):
    # Most recent model executions
    recent_executions = con.execute(
        """
        SELECT
            model_name,
            materialization,
            status,
            ROUND(execution_time_seconds, 2) AS execution_seconds,
            executed_at::TIMESTAMP AS executed_at
        FROM core_monitoring.dbt_model_history
        ORDER BY executed_at DESC
        LIMIT 20
    """
    ).df()

    recent_executions
    return (recent_executions,)


@app.cell
def __(mo):
    mo.md(
        """
    ## Query Examples

    Use these queries to dig deeper into your dbt pipeline performance:

    **Find models that take longer than 1 second:**
    ```sql
    SELECT
        model_name,
        materialization,
        ROUND(AVG(execution_time_seconds), 2) AS avg_seconds,
        COUNT(*) AS run_count
    FROM core_monitoring.dbt_model_history
    WHERE execution_time_seconds > 1
        AND status = 'success'
    GROUP BY model_name, materialization
    ORDER BY avg_seconds DESC;
    ```

    **Model performance over time:**
    ```sql
    SELECT
        model_name,
        DATE_TRUNC('day', executed_at) AS execution_date,
        ROUND(AVG(execution_time_seconds), 2) AS avg_runtime,
        COUNT(*) AS executions
    FROM core_monitoring.dbt_model_history
    WHERE model_name = 'fct_orders'
        AND executed_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY model_name, DATE_TRUNC('day', executed_at)
    ORDER BY execution_date;
    ```

    **Run history summary:**
    ```sql
    SELECT
        dbt_command,
        COUNT(*) AS runs,
        ROUND(AVG(total_runtime_seconds), 2) AS avg_runtime,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_runs
    FROM core_monitoring.dbt_run_history
    GROUP BY dbt_command
    ORDER BY runs DESC;
    ```
    """
    )
    return


if __name__ == "__main__":
    app.run()
