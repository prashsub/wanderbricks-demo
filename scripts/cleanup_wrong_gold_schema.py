# Databricks notebook source
"""
Cleanup Gold Schema - Remove tables created in wrong schema

This script:
1. Lists tables in wanderbricks_gold (wrong schema)
2. Lists tables in dev_prashanth_subrahmanyam_wanderbricks_gold (correct schema)
3. Drops wanderbricks_gold schema

Run this once to clean up after the initial deployment error.
"""

from pyspark.sql import SparkSession

def main():
    spark = SparkSession.builder.appName("Cleanup Wrong Gold Schema").getOrCreate()
    
    catalog = "prashanth_subrahmanyam_catalog"
    wrong_schema = "wanderbricks_gold"
    correct_schema = "dev_prashanth_subrahmanyam_wanderbricks_gold"
    
    print("=" * 80)
    print("GOLD SCHEMA CLEANUP")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Wrong Schema: {wrong_schema}")
    print(f"Correct Schema: {correct_schema}")
    print()
    
    # Check if wrong schema exists
    try:
        wrong_tables = spark.sql(f"SHOW TABLES IN {catalog}.{wrong_schema}").collect()
        print(f"✓ Found {len(wrong_tables)} tables in {wrong_schema}:")
        for row in wrong_tables:
            print(f"  - {row.tableName}")
        print()
    except Exception as e:
        if "SCHEMA_NOT_FOUND" in str(e):
            print(f"✓ Schema {wrong_schema} does not exist (already cleaned up)")
            print()
            return
        else:
            print(f"Error checking {wrong_schema}: {e}")
            raise
    
    # Check correct schema
    try:
        correct_tables = spark.sql(f"SHOW TABLES IN {catalog}.{correct_schema}").collect()
        print(f"✓ Found {len(correct_tables)} tables in {correct_schema} (correct):")
        for row in correct_tables:
            print(f"  - {row.tableName}")
        print()
    except Exception as e:
        print(f"❌ Error: Correct schema {correct_schema} not found!")
        print(f"Error: {e}")
        raise
    
    # Verify correct schema has data
    if len(correct_tables) >= 8:
        print(f"✓ Correct schema has {len(correct_tables)} tables (expected 8+)")
        
        # Check record counts
        print("\nRecord counts in correct schema:")
        for row in correct_tables:
            table_name = row.tableName
            count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog}.{correct_schema}.{table_name}").collect()[0].cnt
            print(f"  {table_name}: {count:,} records")
        print()
    else:
        print(f"⚠️  Correct schema only has {len(correct_tables)} tables (expected 8)")
        print("You may need to re-run: databricks bundle run gold_setup_job -t dev")
        print()
    
    # Drop wrong schema
    if len(wrong_tables) > 0:
        print(f"Dropping schema {catalog}.{wrong_schema}...")
        
        # Drop schema CASCADE (drops all tables in it)
        try:
            spark.sql(f"DROP SCHEMA IF EXISTS {catalog}.{wrong_schema} CASCADE")
            print(f"✓ Successfully dropped {catalog}.{wrong_schema}")
        except Exception as e:
            print(f"❌ Error dropping schema: {e}")
            raise
    
    print()
    print("=" * 80)
    print("✓ Cleanup complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()

