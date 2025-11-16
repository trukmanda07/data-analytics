#!/bin/bash
# Wrapper script to run dbt and automatically log results to monitoring tables
# Usage: ./dbt_run.sh [dbt run arguments]

set -e

# Activate virtual environment
source ../../.venv/bin/activate

# Run dbt with all provided arguments
dbt run "$@"

# Log the results
echo ""
echo "📊 Logging run results to monitoring tables..."
python3 monitoring/log_run_results.py

echo ""
echo "✅ Complete! Run results logged to core_monitoring.dbt_run_history and core_monitoring.dbt_model_history"
