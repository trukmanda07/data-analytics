#!/usr/bin/env python3
"""
Analyze dbt test results from run_results.json and output to Markdown
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def analyze_test_results(results_file="target/run_results.json", output_file=None):
    """Analyze and display test results from dbt run_results.json"""

    try:
        with open(results_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {results_file} not found!")
        print("Run 'dbt test' first to generate results.")
        sys.exit(1)

    # Determine output file path (same directory as results_file)
    if output_file is None:
        results_path = Path(results_file)
        output_file = results_path.parent / "run_results.md"

    # Open output file
    out = open(output_file, "w")

    # Write header
    out.write(f"# dbt Test Results Analysis\n\n")
    out.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    out.write(f"**Results File:** `{results_file}`\n\n")
    out.write("---\n\n")

    out.write("## Test Execution Summary\n\n")

    # Count statuses
    status_count = {}
    for result in data["results"]:
        status = result["status"]
        status_count[status] = status_count.get(status, 0) + 1

    total = len(data["results"])
    out.write(f"**Total Tests Run:** {total}\n\n")
    out.write("### Results by Status\n\n")

    # Create status table
    out.write("| Status | Count | Percentage |\n")
    out.write("|--------|-------|------------|\n")

    for status, count in sorted(status_count.items()):
        percentage = (count / total * 100) if total > 0 else 0
        emoji = {
            "pass": "✅",
            "warn": "⚠️",
            "error": "❌",
            "fail": "❌",
            "skipped": "⏭️",
        }.get(status, "•")
        out.write(f"| {emoji} {status.upper()} | {count} | {percentage:.1f}% |\n")

    out.write("\n")

    # Separate errors and warnings
    errors = [r for r in data["results"] if r["status"] in ["error", "fail"]]
    warnings = [r for r in data["results"] if r["status"] == "warn"]

    # Display errors
    if errors:
        out.write("---\n\n")
        out.write("## ❌ Error Details\n\n")
        out.write(f"**Total Errors:** {len(errors)}\n\n")

        for i, error in enumerate(errors, 1):
            test_name = error["unique_id"].split(".")[-1]
            out.write(f"### {i}. {test_name}\n\n")

            out.write(f"- **Type:** `{error['unique_id'].split('.')[0]}`\n")
            out.write(f"- **Full ID:** `{error.get('unique_id', 'N/A')}`\n")

            if error.get("message"):
                msg = error["message"].strip()
                # Truncate long messages
                if len(msg) > 500:
                    msg = msg[:500] + "..."
                out.write(f"- **Error Message:**\n  ```\n  {msg}\n  ```\n")

            if error.get("failures"):
                out.write(f"- **Failures:** {error['failures']} rows failed\n")

            if error.get("execution_time"):
                out.write(f"- **Execution Time:** {error['execution_time']:.2f}s\n")

            out.write("\n")

    # Display warnings
    if warnings:
        out.write("---\n\n")
        out.write("## ⚠️ Warning Details\n\n")
        out.write(f"**Total Warnings:** {len(warnings)}\n\n")

        # Create warnings table
        out.write("| # | Test Name | Failures | Message |\n")
        out.write("|---|-----------|----------|----------|\n")

        for i, warn in enumerate(warnings[:20], 1):  # Show first 20 warnings
            test_name = warn["unique_id"].split(".")[-1][:50]  # Truncate long names
            failures = warn.get("failures", 0)
            msg = warn.get("message", "").strip()[:100]  # Truncate message
            out.write(f"| {i} | `{test_name}` | {failures} | {msg} |\n")

        if len(warnings) > 20:
            out.write(f"\n*... and {len(warnings) - 20} more warnings*\n")

    # Summary statistics
    out.write("\n---\n\n")
    out.write("## Summary\n\n")

    pass_count = status_count.get("pass", 0)
    pass_rate = (pass_count / total * 100) if total > 0 else 0

    out.write(f"- **Pass Rate:** {pass_rate:.1f}% ({pass_count}/{total})\n")
    out.write(f"- **Errors:** {len(errors)}\n")
    out.write(f"- **Warnings:** {len(warnings)}\n")

    if "elapsed_time" in data:
        out.write(f"- **Total Execution Time:** {data['elapsed_time']:.2f}s\n")

    out.write("\n")

    # Final status
    if errors:
        out.write("### Status: ⚠️ Tests completed with errors\n\n")
        status_emoji = "❌"
    elif warnings:
        out.write("### Status: ⚠️ Tests completed with warnings\n\n")
        status_emoji = "⚠️"
    else:
        out.write("### Status: ✅ All tests passed!\n\n")
        status_emoji = "✅"

    # Close file
    out.close()

    # Print confirmation
    print(f"{status_emoji} Test results written to: {output_file}")
    print(
        f"   Total: {total} | Pass: {pass_count} | Warn: {len(warnings)} | Error: {len(errors)}"
    )

    # Exit code based on results
    if errors:
        return 1
    elif warnings:
        return 0
    else:
        return 0


if __name__ == "__main__":
    # Allow custom path as argument
    results_file = sys.argv[1] if len(sys.argv) > 1 else "target/run_results.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    exit_code = analyze_test_results(results_file, output_file)
    sys.exit(exit_code)
