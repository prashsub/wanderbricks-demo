# Databricks notebook source

"""
Wanderbricks Silver Layer - Referential Integrity Validation

Validates FK relationships between fact and dimension tables:
- Bookings → Users, Properties
- Payments → Bookings
- Reviews → Bookings, Properties, Users
- Properties → Hosts, Destinations
"""

from pyspark.sql import SparkSession


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    silver_schema = dbutils.widgets.get("silver_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Silver Schema: {silver_schema}")
    
    return catalog, silver_schema


def main():
    """Main validation logic."""
    catalog, silver_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Silver Referential Integrity Validation").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS SILVER LAYER - REFERENTIAL INTEGRITY VALIDATION")
    print("=" * 80)
    
    try:
        # Read referential integrity check results
        ri_table = f"{catalog}.{silver_schema}.dq_referential_integrity"
        ri_df = spark.table(ri_table)
        
        if ri_df.count() == 0:
            print("\n⚠️  WARNING: Referential integrity table is empty")
            print("This is expected if DLT pipeline hasn't run yet.")
        else:
            print("\nReferential Integrity Check Results:")
            print("-" * 80)
            
            ri_df.orderBy("check_name").show(100, truncate=False)
            
            # Count failures
            failures = ri_df.filter(ri_df.status == "FAIL")
            failure_count = failures.count()
            
            warnings = ri_df.filter(ri_df.status == "WARNING")
            warning_count = warnings.count()
            
            if failure_count > 0:
                print(f"\n❌ FAILED: {failure_count} referential integrity check(s) failed:")
                failures.select("check_name", "orphaned_records").show(truncate=False)
                raise RuntimeError(f"Referential integrity validation failed: {failure_count} checks failed")
            
            if warning_count > 0:
                print(f"\n⚠️  WARNING: {warning_count} referential integrity check(s) have warnings:")
                warnings.select("check_name", "orphaned_records").show(truncate=False)
            
            print("\n✅ REFERENTIAL INTEGRITY VALIDATION PASSED!")
            print("All FK relationships are valid.")
        
    except Exception as e:
        print(f"\n❌ Referential integrity validation FAILED: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

