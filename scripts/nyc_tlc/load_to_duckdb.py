#!/usr/bin/env python3
"""Load NYC TLC parquet files into DuckDB"""

import os
import sys
from datetime import datetime
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATA_PATH = Path(
    os.getenv(
        "NYC_TLC_DATA_PATH",
        "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/NYC_TLC",
    )
)
DUCKDB_PATH = Path(os.getenv("NYC_TLC_DUCKDB_PATH", "./data/duckdb/nyc_tlc.duckdb"))
MEMORY_LIMIT = os.getenv("NYC_TLC_MEMORY_LIMIT", "32GB")
THREADS = int(os.getenv("NYC_TLC_THREADS", "8"))

# Ensure DuckDB directory exists
DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)


def create_duckdb_connection():
    """Create DuckDB connection with optimized settings"""
    con = duckdb.connect(str(DUCKDB_PATH))

    # Configure for performance
    con.execute(f"SET memory_limit='{MEMORY_LIMIT}'")
    con.execute(f"SET threads={THREADS}")
    con.execute("SET enable_progress_bar=true")

    return con


def load_yellow_trips(con):
    """Load yellow taxi trips from parquet files"""
    yellow_dir = DATA_PATH / "yellow"
    parquet_files = list(yellow_dir.glob("*.parquet"))

    if not parquet_files:
        print(f"❌ No parquet files found in {yellow_dir}")
        return False

    print(f"\n{'='*70}")
    print(f"Loading Yellow Taxi Trips")
    print(f"{'='*70}")
    print(f"Source: {yellow_dir}")
    print(f"Files: {len(parquet_files)}")
    print(f"Database: {DUCKDB_PATH}")
    print(f"{'='*70}\n")

    # Create table from all parquet files
    parquet_pattern = str(yellow_dir / "*.parquet")

    print("Creating table: yellow_trips_2024...")
    start_time = datetime.now()

    # Use DuckDB's efficient parquet reader
    con.execute(
        f"""
        CREATE OR REPLACE TABLE yellow_trips_2024 AS
        SELECT
            *,
            CAST(tpep_pickup_datetime AS DATE) AS pickup_date,
            CAST(tpep_dropoff_datetime AS DATE) AS dropoff_date,
            EXTRACT(YEAR FROM tpep_pickup_datetime) AS pickup_year,
            EXTRACT(MONTH FROM tpep_pickup_datetime) AS pickup_month,
            EXTRACT(HOUR FROM tpep_pickup_datetime) AS pickup_hour,
            CURRENT_TIMESTAMP AS dbt_loaded_at
        FROM read_parquet('{parquet_pattern}')
    """
    )

    load_duration = (datetime.now() - start_time).total_seconds()

    # Get row count and table info
    row_count = con.execute("SELECT COUNT(*) FROM yellow_trips_2024").fetchone()[0]

    print(f"✅ Table created successfully!")
    print(f"   Rows loaded: {row_count:,}")
    print(f"   Load time: {load_duration:.2f} seconds")
    print(f"   Speed: {row_count/load_duration:,.0f} rows/second")

    return True


def create_summary_views(con):
    """Create helpful summary views"""
    print(f"\n{'='*70}")
    print("Creating Summary Views")
    print(f"{'='*70}\n")

    # Monthly summary view
    print("Creating view: vw_monthly_summary...")
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_monthly_summary AS
        SELECT
            pickup_year,
            pickup_month,
            COUNT(*) AS trip_count,
            SUM(total_amount) AS total_revenue,
            AVG(total_amount) AS avg_fare,
            AVG(trip_distance) AS avg_distance,
            AVG(passenger_count) AS avg_passengers
        FROM yellow_trips_2024
        GROUP BY pickup_year, pickup_month
        ORDER BY pickup_year, pickup_month
    """
    )
    print("   ✅ Created: vw_monthly_summary")

    # Zone summary view
    print("Creating view: vw_zone_summary...")
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_zone_summary AS
        SELECT
            PULocationID AS location_id,
            COUNT(*) AS trip_count,
            SUM(total_amount) AS total_revenue,
            AVG(trip_distance) AS avg_distance,
            AVG(total_amount) AS avg_fare
        FROM yellow_trips_2024
        GROUP BY PULocationID
        ORDER BY trip_count DESC
    """
    )
    print("   ✅ Created: vw_zone_summary")

    # Data quality view
    print("Creating view: vw_data_quality...")
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_data_quality AS
        SELECT
            pickup_date,
            COUNT(*) AS total_trips,
            SUM(CASE WHEN passenger_count = 0 THEN 1 ELSE 0 END) AS zero_passengers,
            SUM(CASE WHEN trip_distance = 0 THEN 1 ELSE 0 END) AS zero_distance,
            SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END) AS zero_fare,
            SUM(CASE WHEN tpep_dropoff_datetime < tpep_pickup_datetime THEN 1 ELSE 0 END) AS invalid_times,
            AVG(total_amount) AS avg_fare,
            AVG(trip_distance) AS avg_distance
        FROM yellow_trips_2024
        GROUP BY pickup_date
        ORDER BY pickup_date
    """
    )
    print("   ✅ Created: vw_data_quality")


def run_sample_queries(con):
    """Run sample queries to test performance"""
    print(f"\n{'='*70}")
    print("Running Sample Queries")
    print(f"{'='*70}\n")

    # Query 1: Total trips
    print("Query 1: Total trip count...")
    start = datetime.now()
    result = con.execute("SELECT COUNT(*) FROM yellow_trips_2024").fetchone()[0]
    duration = (datetime.now() - start).total_seconds()
    print(f"   Result: {result:,} trips")
    print(f"   Time: {duration:.3f} seconds\n")

    # Query 2: Monthly summary
    print("Query 2: Monthly aggregation...")
    start = datetime.now()
    df = con.execute("SELECT * FROM vw_monthly_summary").df()
    duration = (datetime.now() - start).total_seconds()
    print(f"   Result: {len(df)} months")
    print(f"   Time: {duration:.3f} seconds\n")
    print(df.to_string(index=False))
    print()

    # Query 3: Top 10 zones
    print("\nQuery 3: Top 10 pickup zones...")
    start = datetime.now()
    df = con.execute("SELECT * FROM vw_zone_summary LIMIT 10").df()
    duration = (datetime.now() - start).total_seconds()
    print(f"   Result: Top 10 zones")
    print(f"   Time: {duration:.3f} seconds\n")
    print(df.to_string(index=False))


def get_database_stats(con):
    """Get database statistics"""
    print(f"\n{'='*70}")
    print("Database Statistics")
    print(f"{'='*70}\n")

    # Table info
    tables = con.execute(
        """
        SELECT
            table_name,
            estimated_size
        FROM duckdb_tables()
        WHERE table_name = 'yellow_trips_2024'
    """
    ).df()

    print("Tables:")
    print(tables.to_string(index=False))

    # Views
    views = con.execute(
        """
        SELECT view_name
        FROM duckdb_views()
        WHERE view_name LIKE 'vw_%'
    """
    ).df()

    print(f"\nViews ({len(views)}):")
    for view in views["view_name"]:
        print(f"   - {view}")

    # Database file size
    if DUCKDB_PATH.exists():
        db_size = DUCKDB_PATH.stat().st_size
        print(f"\nDatabase file size: {db_size / (1024**3):.2f} GB")


def main():
    """Main execution"""
    print("=" * 70)
    print("NYC TLC DuckDB Loader")
    print("=" * 70)
    print(f"Memory limit: {MEMORY_LIMIT}")
    print(f"Threads: {THREADS}")
    print(f"DuckDB path: {DUCKDB_PATH}")
    print("=" * 70)

    try:
        # Create connection
        con = create_duckdb_connection()

        # Load data
        success = load_yellow_trips(con)

        if not success:
            sys.exit(1)

        # Create views
        create_summary_views(con)

        # Run sample queries
        run_sample_queries(con)

        # Get stats
        get_database_stats(con)

        # Close connection
        con.close()

        print(f"\n{'='*70}")
        print("✅ Data Loading Complete!")
        print(f"{'='*70}")
        print(f"\nNext steps:")
        print(f"1. Run benchmark: python scripts/nyc_tlc/benchmark.py")
        print(f"2. Explore data: duckdb {DUCKDB_PATH}")
        print(f"3. Query views: SELECT * FROM vw_monthly_summary")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
