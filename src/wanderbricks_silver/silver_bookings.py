# Databricks notebook source

"""
Wanderbricks Silver Layer - Bookings and Payments with DLT

Delta Live Tables pipeline for Silver bookings fact tables with:
- Data quality expectations loaded from Delta table (dq_rules)
- Quarantine tables for records that fail critical validations
- Incremental streaming from Bronze layer
- Simple derived business flags

Fact Tables:
- silver_bookings (with quarantine)
- silver_booking_updates
- silver_payments (with quarantine)

Reference: https://docs.databricks.com/aws/en/ldp/expectation-patterns
"""

import dlt
from pyspark.sql.functions import (
    col, current_timestamp, sha2, concat_ws, coalesce, when, lit,
    datediff, round as spark_round
)

# Import DQ rules loader (pure Python module, not notebook)
from dq_rules_loader import (
    get_critical_rules_for_table,
    get_warning_rules_for_table,
    get_quarantine_condition
)


def get_bronze_table(table_name):
    """
    Helper function to get fully qualified Bronze table name from DLT configuration.
    
    Args:
        table_name: Name of the Bronze table (e.g., "bookings")
    
    Returns:
        Fully qualified table name: "{catalog}.{bronze_schema}.{table_name}"
    """
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    return f"{catalog}.{bronze_schema}.{table_name}"


# ============================================================================
# SILVER_BOOKINGS (Fact Table with Quarantine)
# ============================================================================

@dlt.table(
    name="silver_bookings",
    comment="""LLM: Silver layer bookings fact table with validated reservation data including dates, 
    guests, amounts, and status. Rules loaded dynamically from dq_rules Delta table. 
    Records failing CRITICAL rules are quarantined.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "bookings",
        "domain": "bookings",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Revenue Operations",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_bookings"))
@dlt.expect_all(get_warning_rules_for_table("silver_bookings"))
def silver_bookings():
    """
    Silver bookings fact table - clones Bronze with simple derived fields.
    
    Transformations:
    - ✅ Calculate nights_booked (check_out - check_in)
    - ✅ Calculate avg_price_per_night (total_amount / nights_booked)
    - ✅ Add is_long_stay flag (> 7 nights)
    - ✅ Add is_high_value flag (total_amount > 1000)
    - ✅ Add business key
    - ❌ NO aggregation (that's Gold)
    - ❌ NO dimension lookups (that's Gold)
    
    DQ Rules (from dq_rules table):
    - CRITICAL: booking_id, user_id, property_id NOT NULL
    - CRITICAL: check_in/check_out present, check_out > check_in
    - CRITICAL: guests >= 1, total_amount > 0
    - WARNING: reasonable guest count (1-20), amount ($10-$100k), stay (1-365 days)
    """
    return (
        dlt.read_stream(get_bronze_table("bookings"))
        
        # Simple derived fields
        .withColumn("nights_booked",
                   datediff(col("check_out"), col("check_in")))
        
        .withColumn("avg_price_per_night",
                   when(datediff(col("check_out"), col("check_in")) > 0,
                        spark_round(col("total_amount") / datediff(col("check_out"), col("check_in")), 2))
                   .otherwise(col("total_amount")))
        
        # Simple boolean flags
        .withColumn("is_long_stay",
                   when(datediff(col("check_out"), col("check_in")) > 7, True).otherwise(False))
        
        .withColumn("is_high_value",
                   when(col("total_amount") > 1000, True).otherwise(False))
        
        # Standard audit fields
        .withColumn("booking_business_key",
                   sha2(concat_ws("||", col("booking_id")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )


@dlt.table(
    name="silver_bookings_quarantine",
    comment="""LLM: Quarantine table for bookings that failed CRITICAL data quality checks. 
    Records here require manual review and remediation before promotion to Silver.
    Filter condition dynamically generated from dq_rules Delta table.""",
    table_properties={
        "quality": "quarantine",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "bookings",
        "domain": "bookings",
        "entity_type": "quarantine",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Revenue Operations",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
def silver_bookings_quarantine():
    """
    Quarantine table for records that fail CRITICAL validations.
    
    Filter condition is automatically generated from dq_rules table as the
    inverse of all critical rules for silver_bookings.
    
    Pipeline behavior:
    - ✅ Pipeline continues (no failure)
    - ✅ Invalid records captured here
    - ✅ Valid records flow to silver_bookings
    - ✅ WARNING violations not captured (logged only)
    """
    return (
        dlt.read_stream(get_bronze_table("bookings"))
        # Use centralized quarantine condition (loaded from dq_rules table)
        .filter(get_quarantine_condition("silver_bookings"))
        .withColumn("quarantine_reason",
            when(col("booking_id").isNull(), "CRITICAL: Missing booking ID (primary key)")
            .when(col("user_id").isNull(), "CRITICAL: Missing user ID (FK)")
            .when(col("property_id").isNull(), "CRITICAL: Missing property ID (FK)")
            .when(col("check_in").isNull(), "CRITICAL: Missing check-in date")
            .when(col("check_out").isNull(), "CRITICAL: Missing check-out date")
            .when(col("check_out") <= col("check_in"), "CRITICAL: Check-out not after check-in")
            .when(col("guests_count") < 1, "CRITICAL: Invalid guest count")
            .when(col("total_amount") <= 0, "CRITICAL: Invalid total amount")
            .otherwise("CRITICAL: Multiple validation failures"))
        .withColumn("quarantine_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_BOOKING_UPDATES (Fact Table)
# ============================================================================

@dlt.table(
    name="silver_booking_updates",
    comment="""LLM: Silver layer booking updates fact table tracking changes to bookings over time. 
    Captures modifications to dates, guests, amounts, and status. Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "booking_updates",
        "domain": "bookings",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Revenue Operations",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_booking_updates"))
@dlt.expect_all(get_warning_rules_for_table("silver_booking_updates"))
def silver_booking_updates():
    """
    Silver booking updates - clones Bronze with simple derived fields.
    
    Transformations:
    - ✅ Calculate nights_booked
    - ✅ Calculate days_until_check_in (check_in - updated_at)
    - ✅ Add is_cancellation flag (status = 'cancelled')
    - ✅ Add business key
    
    DQ Rules (from dq_rules table):
    - CRITICAL: booking_update_id, booking_id NOT NULL
    - CRITICAL: dates present, check_out > check_in
    - WARNING: updated_at >= created_at if both present
    """
    return (
        dlt.read_stream(get_bronze_table("booking_updates"))
        
        # Simple derived fields
        .withColumn("nights_booked",
                   datediff(col("check_out"), col("check_in")))
        
        .withColumn("days_until_check_in",
                   datediff(col("check_in"), col("updated_at")))
        
        # Simple boolean flags
        .withColumn("is_cancellation",
                   when(col("status") == "cancelled", True).otherwise(False))
        
        .withColumn("is_date_change",
                   when(col("check_in").isNotNull() | col("check_out").isNotNull(), True).otherwise(False))
        
        # Standard audit fields
        .withColumn("booking_update_business_key",
                   sha2(concat_ws("||", col("booking_update_id"), col("booking_id")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_PAYMENTS (Fact Table with Quarantine)
# ============================================================================

@dlt.table(
    name="silver_payments",
    comment="""LLM: Silver layer payments fact table with validated payment amounts, methods, and status. 
    Rules loaded dynamically from dq_rules Delta table. Records failing CRITICAL rules are quarantined.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "payments",
        "domain": "payments",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Finance",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_payments"))
@dlt.expect_all(get_warning_rules_for_table("silver_payments"))
def silver_payments():
    """
    Silver payments fact table - clones Bronze with simple derived fields.
    
    Transformations:
    - ✅ Add is_completed flag (status = 'completed')
    - ✅ Add is_refund flag (status = 'refunded')
    - ✅ Add is_digital_payment flag (method in digital list)
    - ✅ Add business key
    
    DQ Rules (from dq_rules table):
    - CRITICAL: payment_id, booking_id NOT NULL
    - CRITICAL: amount > 0, payment_method present, payment_date present
    - WARNING: reasonable amount ($1-$100k)
    """
    return (
        dlt.read_stream(get_bronze_table("payments"))
        
        # Simple boolean flags
        .withColumn("is_completed",
                   when(col("status") == "completed", True).otherwise(False))
        
        .withColumn("is_refund",
                   when(col("status") == "refunded", True).otherwise(False))
        
        .withColumn("is_digital_payment",
                   when(col("payment_method").isin(['paypal', 'apple_pay', 'google_pay']), True).otherwise(False))
        
        .withColumn("is_card_payment",
                   when(col("payment_method") == "credit_card", True).otherwise(False))
        
        # Standard audit fields
        .withColumn("payment_business_key",
                   sha2(concat_ws("||", col("payment_id"), col("booking_id")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )


@dlt.table(
    name="silver_payments_quarantine",
    comment="""LLM: Quarantine table for payments that failed CRITICAL data quality checks. 
    Records here require manual review and remediation. Filter condition dynamically generated from dq_rules Delta table.""",
    table_properties={
        "quality": "quarantine",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "payments",
        "domain": "payments",
        "entity_type": "quarantine",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Finance",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
def silver_payments_quarantine():
    """
    Quarantine table for payment records that fail CRITICAL validations.
    
    Filter condition is automatically generated from dq_rules table as the
    inverse of all critical rules for silver_payments.
    """
    return (
        dlt.read_stream(get_bronze_table("payments"))
        # Use centralized quarantine condition (loaded from dq_rules table)
        .filter(get_quarantine_condition("silver_payments"))
        .withColumn("quarantine_reason",
            when(col("payment_id").isNull(), "CRITICAL: Missing payment ID (primary key)")
            .when(col("booking_id").isNull(), "CRITICAL: Missing booking ID (FK)")
            .when(col("amount") <= 0, "CRITICAL: Invalid payment amount")
            .when(col("payment_method").isNull(), "CRITICAL: Missing payment method")
            .when(col("payment_date").isNull(), "CRITICAL: Missing payment date")
            .otherwise("CRITICAL: Multiple validation failures"))
        .withColumn("quarantine_timestamp", current_timestamp())
    )

