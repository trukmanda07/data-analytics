"""
Olist Dataset Utilities
========================

Reusable functions for loading and working with the Olist Brazilian E-Commerce dataset
in marimo notebooks with DuckDB.

Usage in marimo notebooks:
    from olist_utils import setup_duckdb, get_dataset_path, load_all_tables

Author: Generated for Olist Analysis Project
"""

import os
from pathlib import Path
from typing import Optional

import duckdb
from dotenv import load_dotenv

# Load environment variables from .env file
# This will look for .env in the current directory and parent directories
load_dotenv()


def get_dataset_path() -> str:
    """
    Get the dataset path from environment variable or default location.

    Returns:
        str: Absolute path to the Olist dataset directory

    Environment Variables:
        DATASET_PATH: Override the default dataset location
    """
    # Try to get from environment variable first
    env_path = os.getenv("DATASET_PATH")
    if env_path:
        return env_path

    # Default path
    default_path = "/media/dhafin/42a9538d-5eb4-4681-ad99-92d4f59d5f9a/dhafin/datasets/Kaggle/Olist/"

    # Validate path exists
    if not Path(default_path).exists():
        raise FileNotFoundError(
            f"Dataset path not found: {default_path}\n"
            "Please set DATASET_PATH environment variable or check the path."
        )

    return default_path


def setup_duckdb(
    database: Optional[str] = None, read_only: bool = False
) -> duckdb.DuckDBPyConnection:
    """
    Initialize a DuckDB connection with optimal settings for analysis.

    Args:
        database: Path to database file. If None, uses in-memory database.
        read_only: If True, opens database in read-only mode.

    Returns:
        duckdb.DuckDBPyConnection: Configured DuckDB connection

    Example:
        >>> con = setup_duckdb()
        >>> con.execute("SELECT 42").fetchall()
    """
    # Connect to DuckDB (in-memory if database is None)
    if database is None:
        con = duckdb.connect()
    else:
        con = duckdb.connect(database=database, read_only=read_only)

    # Configure optimal settings
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads=4")

    return con


def load_all_tables(
    con: duckdb.DuckDBPyConnection, dataset_path: Optional[str] = None
) -> None:
    """
    Load all Olist dataset CSV files into DuckDB views.

    This function creates the following views:
        - customers
        - orders
        - order_items
        - payments
        - reviews
        - products
        - sellers
        - geolocation
        - category_translation

    Args:
        con: DuckDB connection object
        dataset_path: Path to dataset directory. If None, uses get_dataset_path()

    Example:
        >>> con = setup_duckdb()
        >>> load_all_tables(con)
        >>> result = con.execute("SELECT COUNT(*) FROM orders").fetchone()
    """
    if dataset_path is None:
        dataset_path = get_dataset_path()

    # Ensure path ends with /
    if not dataset_path.endswith("/"):
        dataset_path += "/"

    # Define all tables and their corresponding CSV files
    tables = {
        "customers": "olist_customers_dataset.csv",
        "orders": "olist_orders_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "payments": "olist_order_payments_dataset.csv",
        "reviews": "olist_order_reviews_dataset.csv",
        "products": "olist_products_dataset.csv",
        "sellers": "olist_sellers_dataset.csv",
        "geolocation": "olist_geolocation_dataset.csv",
        "category_translation": "product_category_name_translation.csv",
    }

    # Load each table as a view
    loaded_count = 0
    for view_name, csv_file in tables.items():
        file_path = dataset_path + csv_file

        # Validate file exists
        if not Path(file_path).exists():
            print(f"Warning: File not found: {file_path}")
            continue

        try:
            con.execute(
                f"""
                CREATE OR REPLACE VIEW {view_name} AS
                SELECT * FROM read_csv_auto('{file_path}')
            """
            )
            loaded_count += 1
        except Exception as e:
            print(f"Error loading {view_name} from {file_path}: {e}")
            raise

    print(f"✓ Loaded {loaded_count}/{len(tables)} tables into DuckDB")


def get_table_info(con: duckdb.DuckDBPyConnection, table_name: str) -> None:
    """
    Display information about a table including schema and row count.

    Args:
        con: DuckDB connection object
        table_name: Name of the table/view to inspect

    Example:
        >>> con = setup_duckdb()
        >>> load_all_tables(con)
        >>> get_table_info(con, 'orders')
    """
    print(f"\n{'='*60}")
    print(f"Table: {table_name}")
    print(f"{'='*60}")

    # Get row count
    try:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"Rows: {count:,}")
    except Exception as e:
        print(f"Error getting row count: {e}")
        return

    # Get schema
    print("\nSchema:")
    try:
        schema = con.execute(f"DESCRIBE {table_name}").fetchdf()
        print(schema.to_string(index=False))
    except Exception as e:
        print(f"Error getting schema: {e}")

    # Show sample
    print("\nSample (first 3 rows):")
    try:
        sample = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchdf()
        print(sample.to_string(index=False))
    except Exception as e:
        print(f"Error getting sample: {e}")

    print(f"{'='*60}\n")


def list_all_tables(con: duckdb.DuckDBPyConnection) -> list:
    """
    List all available tables/views in the DuckDB connection.

    Args:
        con: DuckDB connection object

    Returns:
        list: List of table names

    Example:
        >>> con = setup_duckdb()
        >>> load_all_tables(con)
        >>> tables = list_all_tables(con)
        >>> print(tables)
    """
    result = con.execute("SHOW TABLES").fetchdf()
    tables = result["name"].tolist() if "name" in result.columns else []
    return tables


def create_common_views(con: duckdb.DuckDBPyConnection) -> None:
    """
    Create commonly used joined views for easier analysis.

    This creates the following views:
        - orders_complete: Orders with customer and payment info
        - order_items_complete: Order items with product and seller info
        - orders_with_reviews: Orders with review scores

    Args:
        con: DuckDB connection object

    Example:
        >>> con = setup_duckdb()
        >>> load_all_tables(con)
        >>> create_common_views(con)
        >>> result = con.execute("SELECT * FROM orders_complete LIMIT 5").fetchdf()
    """
    # Complete orders view with customer and payment info
    con.execute(
        """
        CREATE OR REPLACE VIEW orders_complete AS
        SELECT
            o.*,
            c.customer_unique_id,
            c.customer_zip_code_prefix,
            c.customer_city,
            c.customer_state,
            p.payment_type,
            p.payment_installments,
            p.payment_value
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.customer_id
        LEFT JOIN payments p ON o.order_id = p.order_id
    """
    )

    # Complete order items with product and seller info
    con.execute(
        """
        CREATE OR REPLACE VIEW order_items_complete AS
        SELECT
            oi.*,
            p.product_category_name,
            pt.product_category_name_english,
            p.product_weight_g,
            p.product_length_cm,
            p.product_height_cm,
            p.product_width_cm,
            s.seller_city,
            s.seller_state
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN category_translation pt ON p.product_category_name = pt.product_category_name
        LEFT JOIN sellers s ON oi.seller_id = s.seller_id
    """
    )

    # Orders with reviews
    con.execute(
        """
        CREATE OR REPLACE VIEW orders_with_reviews AS
        SELECT
            o.*,
            r.review_score,
            r.review_comment_title,
            r.review_comment_message,
            r.review_creation_date,
            r.review_answer_timestamp
        FROM orders o
        LEFT JOIN reviews r ON o.order_id = r.order_id
    """
    )

    print(
        "✓ Created 3 common views: orders_complete, order_items_complete, orders_with_reviews"
    )


def quick_start(create_views: bool = True) -> duckdb.DuckDBPyConnection:
    """
    Quick start function to set up everything in one call.

    This function:
    1. Creates DuckDB connection
    2. Loads all dataset tables
    3. Optionally creates common joined views

    Args:
        create_views: If True, creates common joined views

    Returns:
        duckdb.DuckDBPyConnection: Configured connection with all data loaded

    Example:
        >>> con = quick_start()
        >>> # Now you can start querying!
        >>> con.execute("SELECT COUNT(*) FROM orders").fetchone()
    """
    print("🚀 Starting Olist analysis setup...")

    # Setup connection
    con = setup_duckdb()
    print("✓ DuckDB connection established")

    # Load all tables
    load_all_tables(con)

    # Create common views
    if create_views:
        create_common_views(con)

    print("✅ Setup complete! Ready for analysis.\n")

    # Show available tables
    tables = list_all_tables(con)
    print(f"Available tables ({len(tables)}):")
    for table in tables:
        print(f"  - {table}")

    return con


# Convenience function for marimo notebooks
def marimo_setup():
    """
    Optimized setup function for marimo notebooks.
    Returns connection and dataset path.

    Example in marimo cell:
        @app.cell
        def __():
            from olist_utils import marimo_setup
            con, dataset_path = marimo_setup()
            return con, dataset_path
    """
    con = quick_start(create_views=True)
    dataset_path = get_dataset_path()
    return con, dataset_path


if __name__ == "__main__":
    # Example usage when running as script
    print("Olist Utils - Testing")
    print("=" * 60)

    con = quick_start()

    print("\nTesting queries...")

    # Test query
    orders_count = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"\nTotal orders: {orders_count:,}")

    # Show sample
    print("\nSample order:")
    sample = con.execute("SELECT * FROM orders LIMIT 1").fetchdf()
    print(sample.T)

    print("\n✅ All tests passed!")
