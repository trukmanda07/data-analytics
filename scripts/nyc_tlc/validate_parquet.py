#!/usr/bin/env python3
"""Validate downloaded NYC TLC parquet files"""

import os
import sys
from pathlib import Path

import pyarrow.parquet as pq
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = Path(
    os.getenv(
        "NYC_TLC_DATA_PATH",
        "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/NYC_TLC",
    )
)


def validate_parquet_file(file_path: Path) -> dict:
    """Validate a single parquet file"""
    try:
        # Read parquet metadata
        parquet_file = pq.ParquetFile(file_path)

        schema = parquet_file.schema_arrow
        num_rows = parquet_file.metadata.num_rows
        num_columns = len(schema)
        file_size = file_path.stat().st_size

        # Read a small sample to check data integrity
        table = parquet_file.read([0]) if num_rows > 0 else None

        return {
            "file": file_path.name,
            "status": "valid",
            "rows": num_rows,
            "columns": num_columns,
            "size_mb": file_size / (1024**2),
            "schema_fields": [field.name for field in schema],
        }

    except Exception as e:
        return {"file": file_path.name, "status": "invalid", "error": str(e)}


def main():
    """Validate all yellow taxi parquet files"""
    yellow_dir = DATA_PATH / "yellow"

    print("=" * 70)
    print("NYC TLC Parquet File Validator")
    print("=" * 70)
    print(f"Directory: {yellow_dir}")
    print("=" * 70)

    if not yellow_dir.exists():
        print(f"❌ Directory not found: {yellow_dir}")
        sys.exit(1)

    parquet_files = sorted(yellow_dir.glob("*.parquet"))

    if not parquet_files:
        print(f"❌ No parquet files found in {yellow_dir}")
        sys.exit(1)

    print(f"\nFound {len(parquet_files)} parquet files\n")

    results = []
    valid_count = 0
    invalid_count = 0
    total_rows = 0
    total_size = 0

    for file_path in parquet_files:
        print(f"Validating: {file_path.name}...", end=" ")
        result = validate_parquet_file(file_path)
        results.append(result)

        if result["status"] == "valid":
            print(f"✅ ({result['rows']:,} rows, {result['size_mb']:.1f} MB)")
            valid_count += 1
            total_rows += result["rows"]
            total_size += result["size_mb"]
        else:
            print(f"❌ {result.get('error', 'Unknown error')}")
            invalid_count += 1

    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    print(f"✅ Valid Files: {valid_count}")
    print(f"❌ Invalid Files: {invalid_count}")
    print(f"📊 Total Rows: {total_rows:,}")
    print(f"💾 Total Size: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
    print("=" * 70)

    if valid_count > 0:
        # Show schema from first valid file
        first_valid = next(r for r in results if r["status"] == "valid")
        print(f"\nSchema (from {first_valid['file']}):")
        for i, field in enumerate(first_valid["schema_fields"], 1):
            print(f"  {i:2d}. {field}")

    if invalid_count > 0:
        print(f"\n❌ {invalid_count} file(s) failed validation. Please re-download.")
        sys.exit(1)
    else:
        print(f"\n✅ All files are valid! Ready for DuckDB loading.")


if __name__ == "__main__":
    main()
