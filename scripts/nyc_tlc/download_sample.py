#!/usr/bin/env python3
"""Download NYC TLC sample data for Phase 1 prototype (2024 yellow taxi)"""

import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

import requests

# Load environment variables
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration from .env
BASE_URL = os.getenv(
    "NYC_TLC_BASE_URL", "https://d37ci6vzurychx.cloudfront.net/trip-data"
)
DATA_PATH = Path(
    os.getenv(
        "NYC_TLC_DATA_PATH",
        "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/NYC_TLC",
    )
)
METADATA_PATH = Path(os.getenv("NYC_TLC_METADATA_PATH", "./data/metadata/nyc_tlc"))

# Ensure directories exist
DATA_PATH.mkdir(parents=True, exist_ok=True)
METADATA_PATH.mkdir(parents=True, exist_ok=True)


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url: str, output_path: Path) -> dict:
    """Download file with progress bar and return metadata"""
    try:
        print(f"\n📥 Downloading {output_path.name}")
        print(f"   URL: {url}")

        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(output_path, "wb") as f:
            with tqdm(
                total=total_size, unit="B", unit_scale=True, desc=output_path.name
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))

        # Calculate checksum
        checksum = calculate_checksum(output_path)
        file_size = output_path.stat().st_size

        print(f"   ✅ Downloaded: {file_size:,} bytes")
        print(f"   📝 Checksum: {checksum[:16]}...")

        return {
            "status": "success",
            "file_path": str(output_path),
            "file_size": file_size,
            "checksum": checksum,
            "download_timestamp": datetime.now().isoformat(),
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"   ⚠️  File not found (may not be published yet)")
            return {"status": "not_found", "file_path": str(output_path)}
        else:
            print(f"   ❌ HTTP Error: {e}")
            if output_path.exists():
                output_path.unlink()
            return {"status": "error", "file_path": str(output_path), "error": str(e)}

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        if output_path.exists():
            output_path.unlink()
        return {"status": "error", "file_path": str(output_path), "error": str(e)}


def save_metadata(downloads: list, metadata_file: Path):
    """Save download metadata to CSV"""
    import csv

    with open(metadata_file, "w", newline="") as f:
        if downloads:
            writer = csv.DictWriter(f, fieldnames=downloads[0].keys())
            writer.writeheader()
            writer.writerows(downloads)

    print(f"\n📋 Metadata saved to: {metadata_file}")


def main():
    """Download all months of 2024 yellow taxi data"""
    year = 2024
    trip_type = "yellow"
    output_dir = DATA_PATH / trip_type
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("NYC TLC Data Downloader - Phase 1 Prototype")
    print("=" * 70)
    print(f"Trip Type: {trip_type.upper()}")
    print(f"Year: {year}")
    print(f"Output Directory: {output_dir}")
    print("=" * 70)

    downloads = []
    successful = 0
    failed = 0
    not_found = 0

    for month in range(1, 13):
        filename = f"{trip_type}_tripdata_{year}-{month:02d}.parquet"
        url = f"{BASE_URL}/{filename}"
        output_path = output_dir / filename

        # Skip if already downloaded
        if output_path.exists():
            print(f"\n⏭️  Skipping {filename} (already exists)")
            file_size = output_path.stat().st_size
            checksum = calculate_checksum(output_path)
            downloads.append(
                {
                    "status": "existing",
                    "file_path": str(output_path),
                    "file_size": file_size,
                    "checksum": checksum,
                    "download_timestamp": datetime.now().isoformat(),
                }
            )
            successful += 1
            continue

        result = download_file(url, output_path)
        downloads.append(result)

        if result["status"] == "success":
            successful += 1
        elif result["status"] == "not_found":
            not_found += 1
        else:
            failed += 1

    # Save metadata
    metadata_file = METADATA_PATH / f"download_metadata_{trip_type}_{year}.csv"
    save_metadata(downloads, metadata_file)

    # Summary
    print("\n" + "=" * 70)
    print("Download Summary")
    print("=" * 70)
    print(f"✅ Successful: {successful}")
    print(f"⚠️  Not Found: {not_found}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total Files: {len(downloads)}")

    total_size = sum(
        d.get("file_size", 0)
        for d in downloads
        if d["status"] in ["success", "existing"]
    )
    print(f"💾 Total Size: {total_size / (1024**3):.2f} GB")
    print("=" * 70)

    if successful > 0:
        print("\n✅ Phase 1 prototype data download complete!")
        print(f"\nNext steps:")
        print(f"1. Validate parquet files: python scripts/nyc_tlc/validate_parquet.py")
        print(f"2. Load into DuckDB: python scripts/nyc_tlc/load_to_duckdb.py")
        print(f"3. Benchmark performance: python scripts/nyc_tlc/benchmark.py")
    else:
        print("\n❌ No files were successfully downloaded")
        sys.exit(1)


if __name__ == "__main__":
    main()
