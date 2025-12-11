# Databricks notebook source

"""Test creating a single metric view to see actual error messages"""

import yaml
from pyspark.sql import SparkSession

def get_parameters():
    """Get job parameters"""
    try:
        catalog = dbutils.widgets.get("catalog")
        gold_schema = dbutils.widgets.get("gold_schema")
    except:
        # Fallback for interactive testing
        catalog = "prashanth_subrahmanyam_catalog"
        gold_schema = "dev_prashanth_subrahmanyam_wanderbricks_gold"
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, gold_schema


def test_metric_view():
    """Test creating a simple metric view"""
    
    catalog, gold_schema = get_parameters()
    spark = SparkSession.builder.appName("Test Metric View").getOrCreate()
    
    # Simple test metric view YAML
    test_yaml = f"""- version: '1.1'
  name: test_revenue_metrics
  comment: Test metric view
  source: {catalog}.{gold_schema}.fact_booking_daily
  dimensions:
    - name: check_in_date
      expr: source.check_in_date
      comment: Check-in date
      display_name: Check-in Date
      synonyms:
        - date
        - booking date
  measures:
    - name: total_revenue
      expr: SUM(source.total_booking_value)
      comment: Total booking revenue
      display_name: Total Revenue
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
      synonyms:
        - revenue
        - sales
"""
    
    metric_view = yaml.safe_load(test_yaml)[0]
    view_name = f"{catalog}.{gold_schema}.test_revenue_metrics"
    
    print(f"\nTesting metric view: {view_name}")
    print("=" * 80)
    
    # Drop existing
    try:
        spark.sql(f"DROP VIEW IF EXISTS {view_name}")
        spark.sql(f"DROP TABLE IF EXISTS {view_name}")
        print("✓ Dropped existing view/table")
    except Exception as e:
        print(f"Warning: {e}")
    
    # Create metric view
    yaml_str = yaml.dump([metric_view], default_flow_style=False, sort_keys=False)
    
    create_sql = f"""
CREATE VIEW {view_name}
WITH METRICS
LANGUAGE YAML
COMMENT 'Test metric view'
AS $$
{yaml_str}
$$
"""
    
    print("\nSQL Statement (first 500 chars):")
    print(create_sql[:500])
    print("...")
    
    try:
        print("\nExecuting CREATE VIEW...")
        spark.sql(create_sql)
        print("✓ CREATE VIEW succeeded!")
        
        # Verify type
        result = spark.sql(f"DESCRIBE EXTENDED {view_name}").collect()
        view_type = next((row.data_type for row in result if row.col_name == "Type"), "UNKNOWN")
        print(f"  View type: {view_type}")
        
        # Try to query it
        print("\nTesting query...")
        df = spark.sql(f"SELECT * FROM {view_name} LIMIT 5")
        print(f"  Row count: {df.count()}")
        
        print("\n✅ Test PASSED!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print(f"\nFull error:\n{e}")
        raise
    
    finally:
        spark.stop()


if __name__ == "__main__":
    test_metric_view()

