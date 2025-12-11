# Databricks notebook source

"""
Check which Silver tables exist for Gold MERGE
"""

from pyspark.sql import SparkSession

catalog = dbutils.widgets.get("catalog") if "dbutils" in globals() else "prashanth_subrahmanyam_catalog"
silver_schema = dbutils.widgets.get("silver_schema") if "dbutils" in globals() else "dev_prashanth_subrahmanyam_wanderbricks_silver"

spark = SparkSession.builder.appName("Check Silver Tables").getOrCreate()

print("=" * 80)
print("CHECKING SILVER LAYER TABLES")
print("=" * 80)
print(f"Catalog: {catalog}")
print(f"Schema: {silver_schema}")
print("=" * 80)

# List all tables in Silver schema
tables = spark.sql(f"SHOW TABLES IN {catalog}.{silver_schema}").collect()

print(f"\n✓ Found {len(tables)} tables in {silver_schema}:\n")
for table in tables:
    table_name = table.tableName
    count = spark.table(f"{catalog}.{silver_schema}.{table_name}").count()
    print(f"  - {table_name}: {count:,} records")

print("\n" + "=" * 80)

spark.stop()

