# Databricks notebook source

"""
Wanderbricks Bronze Layer - Clone Sample Data

Clones tables from samples.wanderbricks and samples.accuweather
to the Bronze layer schema for downstream processing.

Usage:
  databricks bundle run bronze_clone_samples_job -t dev
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    bronze_schema = dbutils.widgets.get("bronze_schema")
    
    print(f"Target Catalog: {catalog}")
    print(f"Target Schema: {bronze_schema}")
    
    return catalog, bronze_schema


def clone_table(spark: SparkSession, source_table: str, target_catalog: str, target_schema: str, target_table: str = None):
    """
    Clone a table from source to target schema.
    
    Args:
        spark: SparkSession
        source_table: Fully qualified source table name (e.g., samples.wanderbricks.bookings)
        target_catalog: Target catalog name
        target_schema: Target schema name
        target_table: Optional target table name (defaults to source table name)
    """
    # Extract table name from source if not provided
    if target_table is None:
        target_table = source_table.split(".")[-1]
    
    target_full_name = f"{target_catalog}.{target_schema}.{target_table}"
    
    print(f"Cloning {source_table} → {target_full_name}")
    
    try:
        # Read source table
        source_df = spark.table(source_table)
        
        # Add ingestion metadata
        clone_df = (
            source_df
            .withColumn("_bronze_ingestion_timestamp", current_timestamp())
            .withColumn("_bronze_source_table", lit(source_table))
        )
        
        # Write to target (overwrite mode for idempotent runs)
        clone_df.write.mode("overwrite").saveAsTable(target_full_name)
        
        # Enable Change Data Feed for downstream processing
        spark.sql(f"""
            ALTER TABLE {target_full_name}
            SET TBLPROPERTIES (
                'delta.enableChangeDataFeed' = 'true',
                'layer' = 'bronze',
                'source_table' = '{source_table}'
            )
        """)
        
        count = spark.table(target_full_name).count()
        print(f"  ✓ Cloned {count:,} records")
        return count
        
    except Exception as e:
        print(f"  ✗ Error cloning {source_table}: {str(e)}")
        raise


def main():
    """Clone all sample tables to Bronze layer."""
    
    # Get parameters
    catalog, bronze_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Bronze Clone Samples").getOrCreate()
    
    print("=" * 80)
    print("BRONZE LAYER - CLONE SAMPLE DATA")
    print("=" * 80)
    print(f"Target: {catalog}.{bronze_schema}")
    print("=" * 80)
    
    # Ensure schema exists
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{bronze_schema}")
    print(f"✓ Schema {catalog}.{bronze_schema} ready")
    
    # Define source tables to clone
    wanderbricks_tables = [
        "samples.wanderbricks.amenities",
        "samples.wanderbricks.booking_updates",
        "samples.wanderbricks.bookings",
        "samples.wanderbricks.clickstream",
        "samples.wanderbricks.countries",
        "samples.wanderbricks.customer_support_logs",
        "samples.wanderbricks.destinations",
        "samples.wanderbricks.employees",
        "samples.wanderbricks.hosts",
        "samples.wanderbricks.page_views",
        "samples.wanderbricks.payments",
        "samples.wanderbricks.properties",
        "samples.wanderbricks.property_amenities",
        "samples.wanderbricks.property_images",
        "samples.wanderbricks.reviews",
        "samples.wanderbricks.users",
    ]
    
    accuweather_tables = [
        "samples.accuweather.forecast_daily_calendar_metric",
        "samples.accuweather.historical_daily_calendar_metric",
    ]
    
    all_tables = wanderbricks_tables + accuweather_tables
    
    # Clone all tables
    total_records = 0
    success_count = 0
    failed_tables = []
    
    print(f"\n--- Cloning {len(all_tables)} tables ---\n")
    
    for source_table in all_tables:
        try:
            count = clone_table(spark, source_table, catalog, bronze_schema)
            total_records += count
            success_count += 1
        except Exception as e:
            failed_tables.append(source_table)
            print(f"  ⚠️ Skipping {source_table}: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("CLONE SUMMARY")
    print("=" * 80)
    print(f"Tables cloned: {success_count}/{len(all_tables)}")
    print(f"Total records: {total_records:,}")
    
    if failed_tables:
        print(f"\n⚠️ Failed tables ({len(failed_tables)}):")
        for t in failed_tables:
            print(f"  - {t}")
        raise RuntimeError(f"Failed to clone {len(failed_tables)} tables")
    
    print("\n✅ Bronze layer clone completed successfully!")
    print(f"\nTables are in: {catalog}.{bronze_schema}")


if __name__ == "__main__":
    main()

