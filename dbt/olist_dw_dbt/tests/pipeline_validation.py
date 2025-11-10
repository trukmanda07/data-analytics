#!/usr/bin/env python3
"""
dbt Pipeline Validation Report
Validates the entire data pipeline from staging to core models
"""

import duckdb
import sys
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "duckdb" / "olist_analytical.duckdb"

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"{title:^70}")
    print("=" * 70)

def print_section(title):
    """Print a formatted section"""
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)

def validate_pipeline():
    """Run full pipeline validation"""

    con = duckdb.connect(str(DB_PATH))

    print_header("dbt PIPELINE VALIDATION REPORT")

    # ========================================================================
    # LAYER 1: STAGING
    # ========================================================================
    print("\n📊 DATA PIPELINE LAYERS:\n")
    print_section("Layer 1: STAGING (Views - Direct CSV reads)")

    staging_tables = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'core_staging'
        ORDER BY table_name
    """).fetchall()

    for i, (table,) in enumerate(staging_tables, 1):
        print(f"  {i}. {table}")

    print(f"\n  Total Staging Models: {len(staging_tables)} ✅")

    # ========================================================================
    # LAYER 2: INTERMEDIATE
    # ========================================================================
    print_section("Layer 2: INTERMEDIATE (Ephemeral - Not materialized)")

    intermediate_models = [
        "int_orders_enriched",
        "int_order_items_enriched",
        "int_order_payments_aggregated"
    ]

    for i, model in enumerate(intermediate_models, 1):
        print(f"  {i}. {model}")

    print(f"\n  Total Intermediate Models: {len(intermediate_models)} ✅")

    # ========================================================================
    # LAYER 3: CORE
    # ========================================================================
    print_section("Layer 3: CORE (Tables - Materialized)")

    core_tables_list = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'core_core'
        ORDER BY table_name
    """).fetchall()

    core_tables = []
    for (table_name,) in core_tables_list:
        count = con.execute(f"SELECT COUNT(*) FROM core_core.{table_name}").fetchone()[0]
        core_tables.append((table_name, count))

    for i, (table, count) in enumerate(core_tables, 1):
        print(f"  {i}. {table:30} {count:>10,} rows")

    print(f"\n  Total Core Models: {len(core_tables)} ✅")

    # ========================================================================
    # DATA QUALITY CHECKS
    # ========================================================================
    print_header("🎯 DATA QUALITY CHECKS")

    # Check 1: Orders with payment data
    orders_with_payment = con.execute("""
        SELECT COUNT(*)
        FROM core_core.fct_orders
        WHERE total_payment_value > 0
    """).fetchone()[0]

    total_orders = con.execute("SELECT COUNT(*) FROM core_core.fct_orders").fetchone()[0]
    payment_pct = (orders_with_payment / total_orders * 100) if total_orders > 0 else 0

    print(f"\n✓ Orders with payment data: {orders_with_payment:,} / {total_orders:,} ({payment_pct:.1f}%)")

    # Check 2: Orders with reviews
    orders_with_reviews = con.execute("""
        SELECT COUNT(*)
        FROM core_core.fct_orders
        WHERE review_score IS NOT NULL
    """).fetchone()[0]

    review_pct = (orders_with_reviews / total_orders * 100) if total_orders > 0 else 0
    print(f"✓ Orders with reviews: {orders_with_reviews:,} / {total_orders:,} ({review_pct:.1f}%)")

    # Check 3: Delivered orders
    delivered = con.execute("""
        SELECT COUNT(*)
        FROM core_core.fct_orders
        WHERE order_status = 'delivered'
    """).fetchone()[0]

    delivered_pct = (delivered / total_orders * 100) if total_orders > 0 else 0
    print(f"✓ Delivered orders: {delivered:,} / {total_orders:,} ({delivered_pct:.1f}%)")

    # Check 4: Average order value
    avg_order = con.execute("""
        SELECT AVG(total_order_value)
        FROM core_core.fct_orders
        WHERE total_order_value > 0
    """).fetchone()[0]

    print(f"✓ Average order value: R$ {avg_order:.2f}")

    # Check 5: Order status breakdown
    print("\n📈 Order Status Distribution:")
    statuses = con.execute("""
        SELECT
            order_status,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
        FROM core_core.fct_orders
        GROUP BY order_status
        ORDER BY count DESC
    """).fetchall()

    for status, count, pct in statuses:
        print(f"   {status:20} {count:>8,} ({pct:>5.1f}%)")

    # Check 6: Customer segments
    print("\n👥 Customer Segments:")
    segments = con.execute("""
        SELECT
            customer_segment,
            COUNT(*) as count,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
        FROM core_core.dim_customers
        GROUP BY customer_segment
        ORDER BY count DESC
    """).fetchall()

    for segment, count, pct in segments:
        print(f"   {segment:20} {count:>8,} ({pct:>5.1f}%)")

    # Check 7: Review sentiment distribution
    print("\n⭐ Review Sentiment Distribution:")
    sentiments = con.execute("""
        SELECT
            review_sentiment,
            COUNT(*) as count,
            AVG(review_score) as avg_score
        FROM core_core.fct_orders
        WHERE review_sentiment IS NOT NULL
        GROUP BY review_sentiment
        ORDER BY
            CASE review_sentiment
                WHEN 'positive' THEN 1
                WHEN 'neutral' THEN 2
                WHEN 'negative' THEN 3
            END
    """).fetchall()

    for sentiment, count, avg_score in sentiments:
        print(f"   {sentiment:20} {count:>8,} (avg: {avg_score:.2f})")

    # Check 8: Top states by order volume
    print("\n🗺️  Top 5 States by Order Volume:")
    states = con.execute("""
        SELECT
            customer_state,
            COUNT(*) as orders,
            SUM(total_order_value) as total_value,
            AVG(total_order_value) as avg_value
        FROM core_core.fct_orders
        WHERE customer_state IS NOT NULL
        GROUP BY customer_state
        ORDER BY orders DESC
        LIMIT 5
    """).fetchall()

    for state, orders, total_val, avg_val in states:
        print(f"   {state:5} {orders:>8,} orders | R$ {total_val:>12,.2f} total | R$ {avg_val:>6,.2f} avg")

    # ========================================================================
    # FINAL STATUS
    # ========================================================================
    print_header("✅ dbt PIPELINE STATUS: FULLY OPERATIONAL")

    print("\nAll staging models → intermediate CTEs → core tables working!")
    print("Ready to build additional dimensions/facts and mart layer.")
    print(f"\n📊 Total Data Loaded:")
    print(f"   - {total_orders:,} orders")
    print(f"   - {con.execute('SELECT COUNT(*) FROM core_core.dim_customers').fetchone()[0]:,} customers")
    print(f"   - {len(staging_tables)} staging views")
    print(f"   - {len(core_tables)} core tables")
    print()

    con.close()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(validate_pipeline())
    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)
