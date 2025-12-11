# Databricks notebook source

"""
Cleanup Script: Drop Incorrectly Named Gold Schema

Drops the wanderbricks_gold schema that was created without the dev prefix.
The correct schema name should be dev_prashanth_subrahmanyam_wanderbricks_gold.

Usage:
  Run this once to clean up before redeploying with correct schema name.
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Cleanup Incorrect Gold Schema").getOrCreate()

catalog = "prashanth_subrahmanyam_catalog"
incorrect_schema = "wanderbricks_gold"

print("=" * 80)
print("CLEANUP: DROP INCORRECT GOLD SCHEMA")
print("=" * 80)

try:
    # Drop the incorrectly named schema (CASCADE drops all tables)
    print(f"\nDropping schema: {catalog}.{incorrect_schema}...")
    spark.sql(f"DROP SCHEMA IF EXISTS {catalog}.{incorrect_schema} CASCADE")
    print(f"✓ Dropped {catalog}.{incorrect_schema}")
    
    print("\n" + "=" * 80)
    print("✓ Cleanup complete!")
    print("=" * 80)
    print("\nNext step: Redeploy bundle with correct schema name")
    print(f"  databricks bundle deploy -t dev")
    print(f"  databricks bundle run gold_setup_job -t dev")
    
except Exception as e:
    print(f"\n❌ Error during cleanup: {str(e)}")
    raise
    
finally:
    spark.stop()

