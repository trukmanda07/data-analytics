#!/usr/bin/env python3
"""
Custom dbt monitoring script for DuckDB.
Parses run_results.json and manifest.json to populate monitoring tables.

Usage:
    python monitoring/log_run_results.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

# Paths
DBT_PROJECT_DIR = Path(__file__).parent.parent
RUN_RESULTS_PATH = DBT_PROJECT_DIR / "target" / "run_results.json"
MANIFEST_PATH = DBT_PROJECT_DIR / "target" / "manifest.json"
DB_PATH = Path(
    "/home/dhafin/Documents/Projects/EDA/data/duckdb/olist_analytical.duckdb"
)


def load_json_file(filepath):
    """Load and parse a JSON file."""
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return None

    with open(filepath, "r") as f:
        return json.load(f)


def get_invocation_id(run_results):
    """Extract invocation ID from run_results."""
    metadata = run_results.get("metadata", {})
    return metadata.get("invocation_id", "unknown")


def parse_run_summary(run_results, manifest):
    """Parse run-level summary information."""
    metadata = run_results.get("metadata", {})
    args = run_results.get("args", {})

    # Calculate timestamps
    run_started_at = metadata.get("generated_at")
    elapsed_time = run_results.get("elapsed_time", 0)

    # Count results
    results = run_results.get("results", [])
    model_results = [r for r in results if r.get("unique_id", "").startswith("model.")]
    test_results = [r for r in results if r.get("unique_id", "").startswith("test.")]

    success = all(r.get("status") in ["success", "pass"] for r in results)

    return {
        "invocation_id": get_invocation_id(run_results),
        "run_started_at": run_started_at,
        "run_completed_at": run_started_at,  # run_results is generated at end
        "dbt_command": args.get("which", "unknown"),
        "success": success,
        "total_models": len(model_results),
        "total_tests": len(test_results),
        "total_runtime_seconds": elapsed_time,
        "dbt_version": metadata.get("dbt_version", "unknown"),
        "target_name": metadata.get("target_name", "unknown"),
    }


def parse_model_executions(run_results, manifest):
    """Parse individual model execution details."""
    invocation_id = get_invocation_id(run_results)
    results = run_results.get("results", [])
    nodes = manifest.get("nodes", {})

    model_executions = []

    for result in results:
        unique_id = result.get("unique_id", "")

        # Only process models (not tests, seeds, etc.)
        if not unique_id.startswith("model."):
            continue

        # Get node metadata from manifest
        node = nodes.get(unique_id, {})

        timing = result.get("timing", [])
        execute_timing = next((t for t in timing if t.get("name") == "execute"), None)
        execution_time = execute_timing.get("duration", 0) if execute_timing else 0

        adapter_response = result.get("adapter_response", {})
        rows_affected = adapter_response.get("rows_affected", 0)

        model_executions.append(
            {
                "invocation_id": invocation_id,
                "model_name": node.get("name", unique_id.split(".")[-1]),
                "schema_name": node.get("schema", "unknown"),
                "materialization": node.get("config", {}).get(
                    "materialized", "unknown"
                ),
                "status": result.get("status", "unknown"),
                "execution_time_seconds": execution_time,
                "rows_affected": rows_affected,
                "executed_at": result.get("timing", [{}])[-1].get("completed_at"),
                "unique_id": unique_id,
            }
        )

    return model_executions


def insert_run_summary(con, run_summary):
    """Insert run summary into dbt_run_history table."""
    sql = """
        INSERT INTO core_monitoring.dbt_run_history (
            invocation_id,
            run_started_at,
            run_completed_at,
            dbt_command,
            success,
            total_models,
            total_tests,
            total_runtime_seconds,
            dbt_version,
            target_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    con.execute(
        sql,
        [
            run_summary["invocation_id"],
            run_summary["run_started_at"],
            run_summary["run_completed_at"],
            run_summary["dbt_command"],
            run_summary["success"],
            run_summary["total_models"],
            run_summary["total_tests"],
            run_summary["total_runtime_seconds"],
            run_summary["dbt_version"],
            run_summary["target_name"],
        ],
    )


def insert_model_executions(con, model_executions):
    """Insert model executions into dbt_model_history table."""
    if not model_executions:
        return

    sql = """
        INSERT INTO core_monitoring.dbt_model_history (
            invocation_id,
            model_name,
            schema_name,
            materialization,
            status,
            execution_time_seconds,
            rows_affected,
            executed_at,
            unique_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for execution in model_executions:
        con.execute(
            sql,
            [
                execution["invocation_id"],
                execution["model_name"],
                execution["schema_name"],
                execution["materialization"],
                execution["status"],
                execution["execution_time_seconds"],
                execution["rows_affected"],
                execution["executed_at"],
                execution["unique_id"],
            ],
        )


def main():
    """Main function to log dbt run results."""
    print("=" * 80)
    print("DBT CUSTOM MONITORING - Logging Run Results")
    print("=" * 80)

    # Load JSON files
    print("\n1. Loading dbt artifacts...")
    run_results = load_json_file(RUN_RESULTS_PATH)
    if not run_results:
        print("❌ Cannot proceed without run_results.json")
        sys.exit(1)

    manifest = load_json_file(MANIFEST_PATH)
    if not manifest:
        print("❌ Cannot proceed without manifest.json")
        sys.exit(1)

    print(f"✓ Loaded run_results.json")
    print(f"✓ Loaded manifest.json")

    # Parse data
    print("\n2. Parsing run results...")
    run_summary = parse_run_summary(run_results, manifest)
    model_executions = parse_model_executions(run_results, manifest)

    print(f"✓ Invocation ID: {run_summary['invocation_id']}")
    print(f"✓ Command: {run_summary['dbt_command']}")
    print(f"✓ Models executed: {len(model_executions)}")
    print(f"✓ Runtime: {run_summary['total_runtime_seconds']:.2f}s")

    # Connect to database
    print("\n3. Connecting to DuckDB...")
    try:
        con = duckdb.connect(str(DB_PATH))
        print(f"✓ Connected to {DB_PATH}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

    # Insert data
    print("\n4. Inserting data into monitoring tables...")
    try:
        con.begin()
        insert_run_summary(con, run_summary)
        print(f"✓ Inserted run summary")

        insert_model_executions(con, model_executions)
        print(f"✓ Inserted {len(model_executions)} model executions")

        con.commit()
        print("✓ Committed transaction")
    except Exception as e:
        print(f"❌ Failed to insert data: {e}")
        try:
            con.rollback()
        except:
            pass
        sys.exit(1)
    finally:
        con.close()

    print("\n" + "=" * 80)
    print("✅ SUCCESS - Run results logged to monitoring tables")
    print("=" * 80)


if __name__ == "__main__":
    main()
