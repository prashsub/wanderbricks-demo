# Databricks notebook source

"""
Wanderbricks Silver Layer - Table Count Validation

Validates that all expected Silver tables exist and have data.

Expected Tables:
- 9 dimensions
- 6 facts
- 2 quarantine tables
- 4 monitoring views
- 1 dq_rules table

Total: 22 tables
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lit


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    silver_schema = dbutils.widgets.get("silver_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Silver Schema: {silver_schema}")
    
    return catalog, silver_schema


def validate_table_exists(spark: SparkSession, catalog: str, schema: str, table_name: str) -> dict:
    """
    Check if a table exists and get its record count.
    
    Returns:
        dict with table_name, exists, record_count
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    try:
        df = spark.table(full_table_name)
        record_count = df.count()
        return {
            "table_name": table_name,
            "exists": True,
            "record_count": record_count,
            "status": "PASS" if record_count > 0 else "WARNING: Empty table"
        }
    except Exception as e:
        return {
            "table_name": table_name,
            "exists": False,
            "record_count": 0,
            "status": f"FAIL: {str(e)}"
        }


def main():
    """Main validation logic."""
    catalog, silver_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Silver Table Count Validation").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS SILVER LAYER - TABLE COUNT VALIDATION")
    print("=" * 80)
    
    # Expected tables
    expected_tables = {
        "Dimensions": [
            "silver_users",
            "silver_hosts",
            "silver_destinations",
            "silver_countries",
            "silver_properties",
            "silver_amenities",
            "silver_employees",
            "silver_property_amenities",
            "silver_property_images"
        ],
        "Facts": [
            "silver_bookings",
            "silver_booking_updates",
            "silver_payments",
            "silver_reviews",
            "silver_clickstream",
            "silver_page_views",
            "silver_customer_support_logs",
        ],
        "Weather": [
            "silver_forecast_daily_metric",
            "silver_historical_daily_metric"
        ],
        "Quarantine": [
            "silver_bookings_quarantine",
            "silver_payments_quarantine"
        ],
        "Monitoring": [
            "dq_bookings_metrics",
            "dq_payments_metrics",
            "dq_referential_integrity",
            "dq_overall_health"
        ],
        "Metadata": [
            "dq_rules"
        ]
    }
    
    # Validate all tables
    all_results = []
    failed_tables = []
    empty_tables = []
    
    for category, tables in expected_tables.items():
        print(f"\n{category} Tables:")
        print("-" * 80)
        
        for table in tables:
            result = validate_table_exists(spark, catalog, silver_schema, table)
            all_results.append(result)
            
            status_icon = "✓" if result["exists"] and result["record_count"] > 0 else "✗"
            print(f"  {status_icon} {table}: {result['record_count']:,} records - {result['status']}")
            
            if not result["exists"]:
                failed_tables.append(table)
            elif result["record_count"] == 0:
                empty_tables.append(table)
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    total_expected = sum(len(tables) for tables in expected_tables.values())
    total_exists = sum(1 for r in all_results if r["exists"])
    total_with_data = sum(1 for r in all_results if r["exists"] and r["record_count"] > 0)
    
    print(f"Total expected tables: {total_expected}")
    print(f"Tables that exist: {total_exists}")
    print(f"Tables with data: {total_with_data}")
    
    if failed_tables:
        print(f"\n❌ FAILED: {len(failed_tables)} tables do not exist:")
        for table in failed_tables:
            print(f"  - {table}")
        raise RuntimeError(f"Validation failed: {len(failed_tables)} tables missing")
    
    if empty_tables:
        print(f"\n⚠️  WARNING: {len(empty_tables)} tables are empty:")
        for table in empty_tables:
            print(f"  - {table}")
        print("\nNote: Empty monitoring views are expected if no data has been processed yet.")
    
    print("\n✅ Table count validation PASSED!")
    print(f"All {total_exists} expected tables exist.")
    
    spark.stop()


if __name__ == "__main__":
    main()

