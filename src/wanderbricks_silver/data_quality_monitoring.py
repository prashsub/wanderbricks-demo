# Databricks notebook source

"""
Wanderbricks Silver Layer - Data Quality Monitoring Views

Delta Live Tables views for monitoring data quality metrics, expectation failures,
and overall pipeline health across the Silver layer.

Monitoring Views:
- dq_bookings_metrics
- dq_payments_metrics  
- dq_referential_integrity
- dq_overall_health

Reference: https://docs.databricks.com/aws/en/dlt/observability
"""

import dlt
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, min as spark_min, 
    max as spark_max, current_timestamp, lit, when, round as spark_round
)


# ============================================================================
# DATA QUALITY METRICS - BOOKINGS
# ============================================================================

@dlt.table(
    name="dq_bookings_metrics",
    comment="""LLM: Real-time data quality metrics for bookings showing record counts, 
    validation pass rates, quarantine rates, and business rule compliance""",
    table_properties={
        "quality": "monitoring",
        "layer": "silver",
        "domain": "governance",
        "pipelines.autoOptimize.managed": "true"
    }
)
def dq_bookings_metrics():
    """
    Comprehensive data quality metrics for bookings.
    
    Metrics:
    - Total records processed
    - Records in Silver vs Quarantine
    - Pass/fail rates
    - Business rule violations
    """
    silver = dlt.read("silver_bookings")
    quarantine = dlt.read("silver_bookings_quarantine")
    
    # Calculate metrics
    silver_metrics = silver.agg(
        count("*").alias("silver_record_count"),
        spark_sum(when(col("is_long_stay"), 1).otherwise(0)).alias("long_stay_count"),
        spark_sum(when(col("is_high_value"), 1).otherwise(0)).alias("high_value_count"),
        avg("total_amount").alias("avg_booking_amount"),
        avg("nights_booked").alias("avg_nights_booked")
    )
    
    quarantine_metrics = quarantine.agg(
        count("*").alias("quarantine_record_count")
    )
    
    # Combine and calculate rates
    return (
        silver_metrics
        .crossJoin(quarantine_metrics)
        .withColumn("total_records", 
                   col("silver_record_count") + col("quarantine_record_count"))
        .withColumn("silver_pass_rate",
                   spark_round((col("silver_record_count") / col("total_records")) * 100, 2))
        .withColumn("quarantine_rate",
                   spark_round((col("quarantine_record_count") / col("total_records")) * 100, 2))
        .withColumn("metric_timestamp", current_timestamp())
    )


# ============================================================================
# DATA QUALITY METRICS - PAYMENTS
# ============================================================================

@dlt.table(
    name="dq_payments_metrics",
    comment="""LLM: Real-time data quality metrics for payments showing record counts, 
    validation pass rates, quarantine rates, and payment method distribution""",
    table_properties={
        "quality": "monitoring",
        "layer": "silver",
        "domain": "governance",
        "pipelines.autoOptimize.managed": "true"
    }
)
def dq_payments_metrics():
    """
    Comprehensive data quality metrics for payments.
    
    Metrics:
    - Total records processed
    - Records in Silver vs Quarantine
    - Pass/fail rates
    - Payment status distribution
    """
    silver = dlt.read("silver_payments")
    quarantine = dlt.read("silver_payments_quarantine")
    
    # Calculate metrics
    silver_metrics = silver.agg(
        count("*").alias("silver_record_count"),
        spark_sum(when(col("is_completed"), 1).otherwise(0)).alias("completed_count"),
        spark_sum(when(col("is_refund"), 1).otherwise(0)).alias("refund_count"),
        spark_sum(when(col("is_digital_payment"), 1).otherwise(0)).alias("digital_payment_count"),
        spark_sum("amount").alias("total_payment_amount"),
        avg("amount").alias("avg_payment_amount")
    )
    
    quarantine_metrics = quarantine.agg(
        count("*").alias("quarantine_record_count")
    )
    
    # Combine and calculate rates
    return (
        silver_metrics
        .crossJoin(quarantine_metrics)
        .withColumn("total_records", 
                   col("silver_record_count") + col("quarantine_record_count"))
        .withColumn("silver_pass_rate",
                   spark_round((col("silver_record_count") / col("total_records")) * 100, 2))
        .withColumn("quarantine_rate",
                   spark_round((col("quarantine_record_count") / col("total_records")) * 100, 2))
        .withColumn("metric_timestamp", current_timestamp())
    )


# ============================================================================
# REFERENTIAL INTEGRITY CHECKS
# ============================================================================

@dlt.table(
    name="dq_referential_integrity",
    comment="""LLM: Referential integrity validation between fact and dimension tables. 
    Identifies orphaned records and missing references.""",
    table_properties={
        "quality": "monitoring",
        "layer": "silver",
        "domain": "governance"
    }
)
def dq_referential_integrity():
    """
    Check referential integrity between Silver fact and dimension tables.
    
    Validates:
    - Bookings reference valid users, properties
    - Payments reference valid bookings
    - Reviews reference valid bookings, properties, users
    """
    bookings = dlt.read("silver_bookings")
    users = dlt.read("silver_users")
    properties = dlt.read("silver_properties")
    payments = dlt.read("silver_payments")
    reviews = dlt.read("silver_reviews")
    
    # Check bookings -> users
    bookings_to_users = (
        bookings
        .join(users.select("user_id"), ["user_id"], "left_anti")
        .agg(
            lit("bookings_to_users").alias("check_name"),
            count("*").alias("orphaned_records")
        )
        .withColumn("status",
                   when(col("orphaned_records") == 0, "PASS")
                   .when(col("orphaned_records") < 10, "WARNING")
                   .otherwise("FAIL"))
        .withColumn("check_timestamp", current_timestamp())
    )
    
    # Check bookings -> properties
    bookings_to_properties = (
        bookings
        .join(properties.select("property_id"), ["property_id"], "left_anti")
        .agg(
            lit("bookings_to_properties").alias("check_name"),
            count("*").alias("orphaned_records")
        )
        .withColumn("status",
                   when(col("orphaned_records") == 0, "PASS")
                   .when(col("orphaned_records") < 10, "WARNING")
                   .otherwise("FAIL"))
        .withColumn("check_timestamp", current_timestamp())
    )
    
    # Check payments -> bookings
    payments_to_bookings = (
        payments
        .join(bookings.select("booking_id"), ["booking_id"], "left_anti")
        .agg(
            lit("payments_to_bookings").alias("check_name"),
            count("*").alias("orphaned_records")
        )
        .withColumn("status",
                   when(col("orphaned_records") == 0, "PASS")
                   .when(col("orphaned_records") < 10, "WARNING")
                   .otherwise("FAIL"))
        .withColumn("check_timestamp", current_timestamp())
    )
    
    # Check reviews -> bookings
    reviews_to_bookings = (
        reviews
        .join(bookings.select("booking_id"), ["booking_id"], "left_anti")
        .agg(
            lit("reviews_to_bookings").alias("check_name"),
            count("*").alias("orphaned_records")
        )
        .withColumn("status",
                   when(col("orphaned_records") == 0, "PASS")
                   .when(col("orphaned_records") < 10, "WARNING")
                   .otherwise("FAIL"))
        .withColumn("check_timestamp", current_timestamp())
    )
    
    return (
        bookings_to_users
        .union(bookings_to_properties)
        .union(payments_to_bookings)
        .union(reviews_to_bookings)
    )


# ============================================================================
# OVERALL DQ HEALTH DASHBOARD
# ============================================================================

@dlt.table(
    name="dq_overall_health",
    comment="""LLM: Overall data quality health dashboard showing table counts, quarantine rates, 
    and data freshness across all Silver tables""",
    table_properties={
        "quality": "monitoring",
        "layer": "silver",
        "domain": "governance"
    }
)
def dq_overall_health():
    """
    Overall data quality health metrics across all Silver tables.
    
    Metrics per table:
    - Record count
    - Latest processed timestamp
    - Data freshness (minutes since last update)
    """
    # Dimensions
    users = dlt.read("silver_users")
    hosts = dlt.read("silver_hosts")
    destinations = dlt.read("silver_destinations")
    properties = dlt.read("silver_properties")
    
    # Facts
    bookings = dlt.read("silver_bookings")
    payments = dlt.read("silver_payments")
    reviews = dlt.read("silver_reviews")
    clickstream = dlt.read("silver_clickstream")
    page_views = dlt.read("silver_page_views")
    
    # Quarantine
    bookings_q = dlt.read("silver_bookings_quarantine")
    payments_q = dlt.read("silver_payments_quarantine")
    
    # Function to get table metrics - handles different timestamp columns
    def table_metrics(df, table_name, table_type):
        """Get metrics for a table, handling quarantine tables that use different timestamp column."""
        # Quarantine tables have quarantine_timestamp, others have processed_timestamp
        if "quarantine" in table_type.lower():
            timestamp_col = "quarantine_timestamp"
        else:
            timestamp_col = "processed_timestamp"
        
        return df.agg(
            lit(table_name).alias("table_name"),
            lit(table_type).alias("table_type"),
            count("*").alias("record_count"),
            spark_max(timestamp_col).alias("last_processed_timestamp")
        )
    
    # Gather metrics for all tables
    users_m = table_metrics(users, "silver_users", "dimension")
    hosts_m = table_metrics(hosts, "silver_hosts", "dimension")
    destinations_m = table_metrics(destinations, "silver_destinations", "dimension")
    properties_m = table_metrics(properties, "silver_properties", "dimension")
    
    bookings_m = table_metrics(bookings, "silver_bookings", "fact")
    payments_m = table_metrics(payments, "silver_payments", "fact")
    reviews_m = table_metrics(reviews, "silver_reviews", "fact")
    clickstream_m = table_metrics(clickstream, "silver_clickstream", "fact")
    page_views_m = table_metrics(page_views, "silver_page_views", "fact")
    
    bookings_q_m = table_metrics(bookings_q, "silver_bookings_quarantine", "quarantine")
    payments_q_m = table_metrics(payments_q, "silver_payments_quarantine", "quarantine")
    
    # Union all metrics
    all_metrics = (
        users_m
        .union(hosts_m)
        .union(destinations_m)
        .union(properties_m)
        .union(bookings_m)
        .union(payments_m)
        .union(reviews_m)
        .union(clickstream_m)
        .union(page_views_m)
        .union(bookings_q_m)
        .union(payments_q_m)
    )
    
    # Add data freshness calculation
    return (
        all_metrics
        .withColumn("check_timestamp", current_timestamp())
        .withColumn("minutes_since_update",
                   spark_round(
                       (col("check_timestamp").cast("long") - col("last_processed_timestamp").cast("long")) / 60,
                       2
                   ))
        .withColumn("data_freshness_status",
                   when(col("minutes_since_update") < 60, "CURRENT")
                   .when(col("minutes_since_update") < 1440, "STALE")
                   .otherwise("VERY_STALE"))
    )

