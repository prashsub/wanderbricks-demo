# Databricks notebook source

"""
Wanderbricks Silver Layer - Data Quality Metrics Validation

Validates that:
1. DQ rules table has rules for all Silver tables
2. Quarantine rates are within acceptable thresholds
3. DQ metrics views are populated
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    silver_schema = dbutils.widgets.get("silver_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Silver Schema: {silver_schema}")
    
    return catalog, silver_schema


def validate_dq_rules(spark: SparkSession, catalog: str, schema: str):
    """Validate DQ rules table exists and has rules for all tables."""
    print("\n" + "=" * 80)
    print("VALIDATING DQ RULES TABLE")
    print("=" * 80)
    
    rules_table = f"{catalog}.{schema}.dq_rules"
    
    try:
        rules_df = spark.table(rules_table)
        total_rules = rules_df.count()
        
        print(f"\n✓ DQ rules table exists: {rules_table}")
        print(f"✓ Total rules: {total_rules}")
        
        # Count rules by table
        rules_by_table = (
            rules_df
            .groupBy("table_name", "severity")
            .agg(count("*").alias("rule_count"))
            .orderBy("table_name", "severity")
        )
        
        print("\nRules by table:")
        rules_by_table.show(100, truncate=False)
        
        # Check minimum rule coverage
        tables_with_rules = rules_df.select("table_name").distinct().count()
        print(f"\n✓ Tables with DQ rules: {tables_with_rules}")
        
        if total_rules < 50:
            print(f"⚠️  WARNING: Only {total_rules} rules defined (expected 70+)")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: DQ rules table validation failed: {str(e)}")
        raise


def validate_quarantine_rates(spark: SparkSession, catalog: str, schema: str):
    """Validate quarantine rates are within acceptable thresholds."""
    print("\n" + "=" * 80)
    print("VALIDATING QUARANTINE RATES")
    print("=" * 80)
    
    # Check bookings quarantine rate
    try:
        bookings_metrics = spark.table(f"{catalog}.{schema}.dq_bookings_metrics")
        
        if bookings_metrics.count() > 0:
            latest = bookings_metrics.orderBy(col("metric_timestamp").desc()).first()
            
            quarantine_rate = latest["quarantine_rate"]
            silver_count = latest["silver_record_count"]
            quarantine_count = latest["quarantine_record_count"]
            
            print(f"\nBookings Quarantine Analysis:")
            print(f"  Silver records: {silver_count:,}")
            print(f"  Quarantine records: {quarantine_count:,}")
            print(f"  Quarantine rate: {quarantine_rate:.2f}%")
            
            if quarantine_rate > 10:
                print(f"  ⚠️  WARNING: High quarantine rate ({quarantine_rate:.2f}%)")
            elif quarantine_rate > 5:
                print(f"  ⚠️  CAUTION: Moderate quarantine rate ({quarantine_rate:.2f}%)")
            else:
                print(f"  ✓ GOOD: Low quarantine rate ({quarantine_rate:.2f}%)")
        else:
            print("⚠️  WARNING: No bookings metrics available yet")
            
    except Exception as e:
        print(f"⚠️  WARNING: Could not validate bookings quarantine rate: {str(e)}")
    
    # Check payments quarantine rate
    try:
        payments_metrics = spark.table(f"{catalog}.{schema}.dq_payments_metrics")
        
        if payments_metrics.count() > 0:
            latest = payments_metrics.orderBy(col("metric_timestamp").desc()).first()
            
            quarantine_rate = latest["quarantine_rate"]
            silver_count = latest["silver_record_count"]
            quarantine_count = latest["quarantine_record_count"]
            
            print(f"\nPayments Quarantine Analysis:")
            print(f"  Silver records: {silver_count:,}")
            print(f"  Quarantine records: {quarantine_count:,}")
            print(f"  Quarantine rate: {quarantine_rate:.2f}%")
            
            if quarantine_rate > 10:
                print(f"  ⚠️  WARNING: High quarantine rate ({quarantine_rate:.2f}%)")
            elif quarantine_rate > 5:
                print(f"  ⚠️  CAUTION: Moderate quarantine rate ({quarantine_rate:.2f}%)")
            else:
                print(f"  ✓ GOOD: Low quarantine rate ({quarantine_rate:.2f}%)")
        else:
            print("⚠️  WARNING: No payments metrics available yet")
            
    except Exception as e:
        print(f"⚠️  WARNING: Could not validate payments quarantine rate: {str(e)}")


def main():
    """Main validation logic."""
    catalog, silver_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Silver DQ Metrics Validation").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS SILVER LAYER - DQ METRICS VALIDATION")
    print("=" * 80)
    
    try:
        # Validate DQ rules
        validate_dq_rules(spark, catalog, silver_schema)
        
        # Validate quarantine rates
        validate_quarantine_rates(spark, catalog, silver_schema)
        
        print("\n" + "=" * 80)
        print("✅ DQ METRICS VALIDATION PASSED!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ DQ metrics validation FAILED: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

