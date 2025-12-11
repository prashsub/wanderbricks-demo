# Databricks notebook source

"""
Wanderbricks Silver Layer - Quarantine Analysis

Analyzes quarantined records to identify:
1. Most common failure reasons
2. Quarantine trends over time
3. Recommendations for rule adjustments
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    silver_schema = dbutils.widgets.get("silver_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Silver Schema: {silver_schema}")
    
    return catalog, silver_schema


def analyze_quarantine_table(spark: SparkSession, catalog: str, schema: str, 
                              table_name: str, entity_name: str):
    """Analyze a specific quarantine table."""
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    try:
        quarantine_df = spark.table(full_table_name)
        total_quarantined = quarantine_df.count()
        
        print(f"\n{entity_name} Quarantine Analysis:")
        print("-" * 80)
        print(f"Total quarantined records: {total_quarantined:,}")
        
        if total_quarantined == 0:
            print("✓ No records in quarantine (excellent data quality!)")
            return
        
        # Top failure reasons
        print(f"\nTop failure reasons:")
        failure_reasons = (
            quarantine_df
            .groupBy("quarantine_reason")
            .agg(count("*").alias("failure_count"))
            .orderBy(desc("failure_count"))
            .limit(10)
        )
        failure_reasons.show(truncate=False)
        
        # Sample quarantined records
        print(f"\nSample quarantined records (first 5):")
        quarantine_df.limit(5).show(truncate=False)
        
        # Recommendations
        top_reason = failure_reasons.first()
        if top_reason:
            reason = top_reason["quarantine_reason"]
            fail_count = top_reason["failure_count"]
            pct = (fail_count / total_quarantined) * 100
            
            print(f"\n💡 RECOMMENDATION:")
            print(f"   {pct:.1f}% of failures are due to: {reason}")
            print(f"   Consider reviewing the corresponding DQ rule in dq_rules table.")
            
            if "Missing" in reason:
                print(f"   → Check if upstream Bronze data is incomplete")
            elif "Invalid" in reason:
                print(f"   → Review data type constraints and value ranges")
        
    except Exception as e:
        print(f"⚠️  Could not analyze {table_name}: {str(e)}")


def main():
    """Main analysis logic."""
    catalog, silver_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Silver Quarantine Analysis").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS SILVER LAYER - QUARANTINE ANALYSIS")
    print("=" * 80)
    
    try:
        # Analyze bookings quarantine
        analyze_quarantine_table(
            spark, catalog, silver_schema,
            "silver_bookings_quarantine",
            "Bookings"
        )
        
        # Analyze payments quarantine
        analyze_quarantine_table(
            spark, catalog, silver_schema,
            "silver_payments_quarantine",
            "Payments"
        )
        
        print("\n" + "=" * 80)
        print("✅ QUARANTINE ANALYSIS COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review failure reasons and adjust DQ rules if needed")
        print("2. Update dq_rules table via SQL UPDATE (no code deployment)")
        print("3. Re-run DLT pipeline to apply updated rules")
        
    except Exception as e:
        print(f"\n❌ Quarantine analysis FAILED: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

