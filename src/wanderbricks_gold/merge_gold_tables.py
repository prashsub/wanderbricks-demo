# Databricks notebook source

"""
Wanderbricks Gold Layer - MERGE Operations

Performs Delta MERGE operations to update Gold layer tables from Silver.

Handles:
- Schema-aware transformations (column mapping)
- SCD Type 2 dimension updates
- Fact table aggregation and deduplication
- Late-arriving data
- Schema validation
- Grain validation

Usage:
  databricks bundle run gold_merge_job -t dev
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, md5, concat_ws, 
    when, sum as spark_sum, count, avg, lit, coalesce,
    datediff, to_date, max as spark_max, countDistinct
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    silver_schema = dbutils.widgets.get("silver_schema")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Silver Schema: {silver_schema}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, silver_schema, gold_schema


def safe_merge(merge_func, *args, **kwargs):
    """
    Wrapper to safely execute merge functions with error handling.
    
    Args:
        merge_func: The merge function to execute
        *args: Arguments to pass to the merge function
        **kwargs: Keyword arguments to pass to the merge function
    
    Returns:
        True if successful, False if skipped/failed
    """
    func_name = merge_func.__name__
    try:
        merge_func(*args, **kwargs)
        return True
    except Exception as e:
        error_str = str(e)
        if "TABLE_OR_VIEW_NOT_FOUND" in error_str or "cannot be found" in error_str:
            print(f"  ⚠️  {func_name}: Source table not found - skipping")
        else:
            print(f"  ❌ {func_name}: Error - {error_str[:200]}")
            raise  # Re-raise unexpected errors
        return False


# ============================================================================
# DIMENSION MERGE FUNCTIONS (SCD Type 2)
# ============================================================================

def merge_dim_user(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge dim_user from Silver to Gold (SCD Type 2).
    
    Key patterns:
    - Deduplication before MERGE (latest record per user_id)
    - SCD Type 2: Update timestamp only (no new version creation in this simple pattern)
    - Surrogate key generation
    """
    print("\n--- Merging dim_user (SCD Type 2) ---")
    
    silver_table = f"{catalog}.{silver_schema}.silver_users"
    gold_table = f"{catalog}.{gold_schema}.dim_user"
    
    # Step 1: Read and deduplicate Silver source
    silver_raw = spark.table(silver_table)
    original_count = silver_raw.count()
    
    silver_df = (
        silver_raw
        .orderBy(col("processed_timestamp").desc())  # Latest first
        .dropDuplicates(["user_id"])  # Keep first (latest) per business key
    )
    
    dedupe_count = silver_df.count()
    print(f"  Deduplicated: {original_count} → {dedupe_count} records ({original_count - dedupe_count} duplicates removed)")
    
    # Step 2: Prepare updates with column mappings
    updates_df = (
        silver_df
        # Generate surrogate key
        .withColumn("user_key", 
                   md5(concat_ws("||", col("user_id"), col("processed_timestamp"))))
        
        # SCD Type 2 columns
        .withColumn("effective_from", col("processed_timestamp"))
        .withColumn("effective_to", lit(None).cast("timestamp"))
        .withColumn("is_current", lit(True))
        
        # Cast created_at to DATE (from timestamp)
        .withColumn("created_at", to_date(col("created_at")))
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        # Select ONLY columns in Gold DDL
        .select(
            "user_key",
            "user_id",
            "email",
            "name",
            "country",
            "user_type",
            "is_business",
            "company_name",
            "created_at",
            "effective_from",
            "effective_to",
            "is_current",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Step 3: MERGE into Gold (SCD Type 2 - simple pattern)
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        "target.user_id = source.user_id AND target.is_current = true"
    ).whenMatchedUpdate(set={
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into dim_user")


def merge_dim_host(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge dim_host from Silver to Gold (SCD Type 2).
    
    Key patterns:
    - Deduplication before MERGE
    - SCD Type 2 tracking
    - Surrogate key generation
    """
    print("\n--- Merging dim_host (SCD Type 2) ---")
    
    silver_table = f"{catalog}.{silver_schema}.silver_hosts"
    gold_table = f"{catalog}.{gold_schema}.dim_host"
    
    # Step 1: Read and deduplicate
    silver_raw = spark.table(silver_table)
    original_count = silver_raw.count()
    
    silver_df = (
        silver_raw
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates(["host_id"])
    )
    
    dedupe_count = silver_df.count()
    print(f"  Deduplicated: {original_count} → {dedupe_count} records ({original_count - dedupe_count} duplicates removed)")
    
    # Step 2: Prepare updates
    updates_df = (
        silver_df
        # Generate surrogate key
        .withColumn("host_key", 
                   md5(concat_ws("||", col("host_id"), col("processed_timestamp"))))
        
        # SCD Type 2 columns
        .withColumn("effective_from", col("processed_timestamp"))
        .withColumn("effective_to", lit(None).cast("timestamp"))
        .withColumn("is_current", lit(True))
        
        # Cast joined_at to DATE
        .withColumn("joined_at", to_date(col("joined_at")))
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "host_key",
            "host_id",
            "name",
            "email",
            "phone",
            "is_verified",
            "is_active",
            "rating",
            "country",
            "joined_at",
            "effective_from",
            "effective_to",
            "is_current",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Step 3: MERGE into Gold
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        "target.host_id = source.host_id AND target.is_current = true"
    ).whenMatchedUpdate(set={
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into dim_host")


def merge_dim_property(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge dim_property from Silver to Gold (SCD Type 2).
    
    Key patterns:
    - Deduplication before MERGE
    - SCD Type 2 tracking
    - Surrogate key generation
    """
    print("\n--- Merging dim_property (SCD Type 2) ---")
    
    silver_table = f"{catalog}.{silver_schema}.silver_properties"
    gold_table = f"{catalog}.{gold_schema}.dim_property"
    
    # Step 1: Read and deduplicate
    silver_raw = spark.table(silver_table)
    original_count = silver_raw.count()
    
    silver_df = (
        silver_raw
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates(["property_id"])
    )
    
    dedupe_count = silver_df.count()
    print(f"  Deduplicated: {original_count} → {dedupe_count} records ({original_count - dedupe_count} duplicates removed)")
    
    # Step 2: Prepare updates
    updates_df = (
        silver_df
        # Generate surrogate key
        .withColumn("property_key", 
                   md5(concat_ws("||", col("property_id"), col("processed_timestamp"))))
        
        # SCD Type 2 columns
        .withColumn("effective_from", col("processed_timestamp"))
        .withColumn("effective_to", lit(None).cast("timestamp"))
        .withColumn("is_current", lit(True))
        
        # Cast created_at to DATE
        .withColumn("created_at", to_date(col("created_at")))
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "property_key",
            "property_id",
            "host_id",
            "destination_id",
            "title",
            "description",
            "base_price",
            "property_type",
            "max_guests",
            "bedrooms",
            "bathrooms",
            "property_latitude",
            "property_longitude",
            "created_at",
            "effective_from",
            "effective_to",
            "is_current",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Step 3: MERGE into Gold
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        "target.property_id = source.property_id AND target.is_current = true"
    ).whenMatchedUpdate(set={
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into dim_property")


def merge_dim_destination(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge dim_destination from Silver to Gold (SCD Type 1).
    
    Type 1: Overwrite all fields when matched.
    """
    print("\n--- Merging dim_destination (SCD Type 1) ---")
    
    silver_table = f"{catalog}.{silver_schema}.silver_destinations"
    gold_table = f"{catalog}.{gold_schema}.dim_destination"
    
    # Step 1: Read and deduplicate
    silver_raw = spark.table(silver_table)
    original_count = silver_raw.count()
    
    silver_df = (
        silver_raw
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates(["destination_id"])
    )
    
    dedupe_count = silver_df.count()
    print(f"  Deduplicated: {original_count} → {dedupe_count} records ({original_count - dedupe_count} duplicates removed)")
    
    # Step 2: Prepare updates
    updates_df = (
        silver_df
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "destination_id",
            "destination",
            "country",
            "state_or_province",
            "state_or_province_code",
            "description",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Step 3: MERGE into Gold (Type 1 - update all fields)
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        "target.destination_id = source.destination_id"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into dim_destination")


def generate_dim_date(spark: SparkSession, catalog: str, gold_schema: str):
    """
    Generate dim_date (not from Silver - generated data).
    
    Creates date dimension for 2020-2030 range.
    """
    print("\n--- Generating dim_date ---")
    
    gold_table = f"{catalog}.{gold_schema}.dim_date"
    
    date_sql = f"""
        INSERT OVERWRITE {gold_table}
        SELECT
            date,
            YEAR(date) as year,
            QUARTER(date) as quarter,
            MONTH(date) as month,
            DATE_FORMAT(date, 'MMMM') as month_name,
            WEEKOFYEAR(date) as week_of_year,
            DAYOFWEEK(date) as day_of_week,
            DATE_FORMAT(date, 'EEEE') as day_of_week_name,
            DAY(date) as day_of_month,
            DAYOFYEAR(date) as day_of_year,
            CASE WHEN DAYOFWEEK(date) IN (1, 7) THEN true ELSE false END as is_weekend,
            false as is_holiday
        FROM (
            SELECT EXPLODE(
                SEQUENCE(
                    TO_DATE('2020-01-01'),
                    TO_DATE('2030-12-31'),
                    INTERVAL 1 DAY
                )
            ) as date
        )
    """
    
    spark.sql(date_sql)
    date_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {gold_table}").collect()[0].cnt
    
    print(f"✓ Generated {date_count:,} date records (2020-2030)")


# ============================================================================
# FACT MERGE FUNCTIONS
# ============================================================================

def merge_fact_booking_detail(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge fact_booking_detail from Silver to Gold.
    
    Transaction-level fact (no aggregation).
    
    Key patterns:
    - Deduplication by booking_id
    - Join with users, properties, payments
    - Column mapping from Silver
    - Derived metrics calculation
    - Schema validation
    """
    print("\n--- Merging fact_booking_detail ---")
    
    silver_bookings = f"{catalog}.{silver_schema}.silver_bookings"
    silver_payments = f"{catalog}.{silver_schema}.silver_payments"
    silver_users = f"{catalog}.{silver_schema}.silver_users"
    silver_properties = f"{catalog}.{silver_schema}.silver_properties"
    gold_table = f"{catalog}.{gold_schema}.fact_booking_detail"
    
    # Step 1: Read bookings and deduplicate
    bookings_raw = spark.table(silver_bookings)
    original_count = bookings_raw.count()
    
    bookings = (
        bookings_raw
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates(["booking_id"])
    )
    
    dedupe_count = bookings.count()
    print(f"  Deduplicated bookings: {original_count} → {dedupe_count} records")
    
    # Step 2: Join with payments (get payment_amount and payment_method)
    payments = spark.table(silver_payments)
    
    # Get most recent successful payment per booking
    successful_payments = (
        payments
        .filter(col("status") == "completed")
        .orderBy(col("payment_date").desc())
        .dropDuplicates(["booking_id"])
        .select(
            col("booking_id"),
            col("amount").alias("payment_amount"),
            col("payment_method")
        )
    )
    
    # Step 3: Join with users (get is_business)
    users = spark.table(silver_users).select("user_id", "is_business")
    
    # Step 4: Join with properties (get host_id and destination_id)
    properties = spark.table(silver_properties).select("property_id", "host_id", "destination_id")
    
    # Step 5: Prepare fact data with all joins and derived metrics
    fact_df = (
        bookings
        .join(successful_payments, on="booking_id", how="left")
        .join(users, on="user_id", how="left")
        .join(properties, on="property_id", how="left")
        
        # Cast dates
        .withColumn("check_in_date", to_date(col("check_in")))
        .withColumn("check_out_date", to_date(col("check_out")))
        
        # Derived metrics
        .withColumn("nights_booked", 
                   datediff(col("check_out"), col("check_in")))
        .withColumn("days_between_booking_and_checkin",
                   datediff(col("check_in"), col("created_at")))
        .withColumn("is_cancelled", 
                   when(col("status") == "cancelled", True).otherwise(False))
        .withColumn("is_business_booking", 
                   coalesce(col("is_business"), lit(False)))  # Default to False if NULL
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "booking_id",
            "user_id",
            "host_id",  # From properties join
            "property_id",
            "destination_id",  # From properties join
            "check_in_date",
            "check_out_date",
            "guests_count",
            "nights_booked",
            col("total_amount").cast("decimal(18,2)").alias("total_amount"),
            col("payment_amount").cast("decimal(18,2)"),
            "payment_method",
            "status",
            "created_at",
            "updated_at",
            "days_between_booking_and_checkin",
            "is_cancelled",
            "is_business_booking",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Step 4: Validate grain (should be one row per booking_id)
    distinct_grain_count = fact_df.select("booking_id").distinct().count()
    total_row_count = fact_df.count()
    
    if distinct_grain_count != total_row_count:
        raise ValueError(
            f"Grain validation failed! Expected one row per booking_id.\n"
            f"  Distinct booking_ids: {distinct_grain_count}\n"
            f"  Total rows: {total_row_count}\n"
            f"  Duplicates: {total_row_count - distinct_grain_count}"
        )
    
    print(f"  ✓ Grain validation passed: {total_row_count} unique bookings")
    
    # Step 5: MERGE into Gold
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        fact_df.alias("source"),
        "target.booking_id = source.booking_id"
    ).whenMatchedUpdate(set={
        "status": "source.status",
        "updated_at": "source.updated_at",
        "payment_amount": "source.payment_amount",
        "payment_method": "source.payment_method",
        "is_cancelled": "source.is_cancelled",
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = fact_df.count()
    print(f"✓ Merged {record_count} records into fact_booking_detail")


def merge_fact_booking_daily(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge fact_booking_daily from Silver bookings.
    
    Aggregated fact: one row per property per check-in date.
    
    Key patterns:
    - Aggregation to daily grain
    - Grain validation (composite PK)
    - Pre-calculated metrics
    """
    print("\n--- Merging fact_booking_daily ---")
    
    silver_bookings = f"{catalog}.{silver_schema}.silver_bookings"
    silver_payments = f"{catalog}.{silver_schema}.silver_payments"
    silver_properties = f"{catalog}.{silver_schema}.silver_properties"
    gold_table = f"{catalog}.{gold_schema}.fact_booking_daily"
    
    # Read bookings
    bookings = spark.table(silver_bookings)
    
    # Join with properties to get destination_id
    properties = spark.table(silver_properties).select("property_id", "destination_id")
    
    # Join with payments for completion rate
    payments = (
        spark.table(silver_payments)
        .filter(col("status") == "completed")
        .select("booking_id", "amount")
        .withColumnRenamed("amount", "payment_amount")
    )
    
    # Combine all joins
    bookings_enriched = (
        bookings
        .join(properties, on="property_id", how="left")
        .join(payments, on="booking_id", how="left")
    )
    
    # Step 1: Aggregate to daily grain
    daily_aggregates = (
        bookings_enriched
        .withColumn("check_in_date", to_date(col("check_in")))
        .withColumn("nights_booked", datediff(col("check_out"), col("check_in")))
        
        .groupBy("property_id", "destination_id", "check_in_date")
        .agg(
            # Booking counts
            count("booking_id").alias("booking_count"),
            spark_sum(when(col("status") == "confirmed", 1).otherwise(0)).alias("confirmed_booking_count"),
            spark_sum(when(col("status") == "cancelled", 1).otherwise(0)).alias("cancellation_count"),
            
            # Revenue measures
            spark_sum(col("total_amount")).cast("decimal(18,2)").alias("total_booking_value"),
            avg(col("total_amount")).cast("decimal(18,2)").alias("avg_booking_value"),
            
            # Guest counts
            spark_sum(col("guests_count")).alias("total_guests"),
            avg(col("nights_booked")).cast("decimal(10,2)").alias("avg_nights_booked"),
            
            # Payment completion rate
            (spark_sum(when(col("payment_amount").isNotNull(), 1).otherwise(0)) / 
             count("booking_id") * 100).cast("decimal(5,2)").alias("payment_completion_rate")
        )
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
    )
    
    # Step 2: Validate grain (one row per property-date)
    distinct_grain_count = daily_aggregates.select("property_id", "check_in_date").distinct().count()
    total_row_count = daily_aggregates.count()
    
    if distinct_grain_count != total_row_count:
        raise ValueError(
            f"Grain validation failed! Expected one row per property-date.\n"
            f"  Distinct combinations: {distinct_grain_count}\n"
            f"  Total rows: {total_row_count}\n"
            f"  Duplicates: {total_row_count - distinct_grain_count}"
        )
    
    print(f"  ✓ Grain validation passed: {total_row_count} unique property-date combinations")
    
    # Step 3: MERGE into Gold
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        daily_aggregates.alias("source"),
        """target.property_id = source.property_id 
           AND target.check_in_date = source.check_in_date"""
    ).whenMatchedUpdate(set={
        "booking_count": "source.booking_count",
        "total_booking_value": "source.total_booking_value",
        "avg_booking_value": "source.avg_booking_value",
        "total_guests": "source.total_guests",
        "avg_nights_booked": "source.avg_nights_booked",
        "cancellation_count": "source.cancellation_count",
        "confirmed_booking_count": "source.confirmed_booking_count",
        "payment_completion_rate": "source.payment_completion_rate",
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = daily_aggregates.count()
    print(f"✓ Merged {record_count} records into fact_booking_daily")


def merge_fact_property_engagement(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge fact_property_engagement from Silver clickstream/page views.
    
    Aggregated fact: one row per property per engagement date.
    
    Key patterns:
    - Aggregation to daily grain
    - Multiple source tables (page_views, clickstream)
    - Pre-calculated conversion rate
    """
    print("\n--- Merging fact_property_engagement ---")
    
    silver_page_views = f"{catalog}.{silver_schema}.silver_page_views"
    silver_clickstream = f"{catalog}.{silver_schema}.silver_clickstream"
    gold_table = f"{catalog}.{gold_schema}.fact_property_engagement"
    
    # Step 1: Aggregate page views
    page_views = spark.table(silver_page_views)
    
    page_view_metrics = (
        page_views
        .withColumn("engagement_date", to_date(col("timestamp")))
        .groupBy("property_id", "engagement_date")
        .agg(
            count("view_id").alias("view_count"),
            countDistinct("user_id").alias("unique_user_views")
        )
    )
    
    # Step 2: Aggregate clickstream
    clickstream = spark.table(silver_clickstream)
    
    click_metrics = (
        clickstream
        .withColumn("engagement_date", to_date(col("timestamp")))
        .groupBy("property_id", "engagement_date")
        .agg(
            spark_sum(when(col("event") == "click", 1).otherwise(0)).alias("click_count"),
            spark_sum(when(col("event") == "search", 1).otherwise(0)).alias("search_count")
        )
    )
    
    # Step 3: Combine metrics
    engagement_metrics = (
        page_view_metrics
        .join(click_metrics, on=["property_id", "engagement_date"], how="outer")
        
        # Fill nulls
        .withColumn("view_count", coalesce(col("view_count"), lit(0)))
        .withColumn("unique_user_views", coalesce(col("unique_user_views"), lit(0)))
        .withColumn("click_count", coalesce(col("click_count"), lit(0)))
        .withColumn("search_count", coalesce(col("search_count"), lit(0)))
        
        # Conversion rate (will be calculated by joining with bookings - set to 0 for now)
        .withColumn("conversion_rate", lit(0.0).cast("decimal(5,2)"))
        
        # Average time on page (not available in current schema - set to NULL)
        .withColumn("avg_time_on_page", lit(None).cast("decimal(10,2)"))
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "property_id",
            "engagement_date",
            "view_count",
            "unique_user_views",
            "click_count",
            "search_count",
            "conversion_rate",
            "avg_time_on_page",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Step 4: Validate grain
    distinct_grain_count = engagement_metrics.select("property_id", "engagement_date").distinct().count()
    total_row_count = engagement_metrics.count()
    
    if distinct_grain_count != total_row_count:
        raise ValueError(
            f"Grain validation failed! Expected one row per property-engagement_date.\n"
            f"  Distinct combinations: {distinct_grain_count}\n"
            f"  Total rows: {total_row_count}\n"
            f"  Duplicates: {total_row_count - distinct_grain_count}"
        )
    
    print(f"  ✓ Grain validation passed: {total_row_count} unique property-date combinations")
    
    # Step 5: MERGE into Gold
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        engagement_metrics.alias("source"),
        """target.property_id = source.property_id 
           AND target.engagement_date = source.engagement_date"""
    ).whenMatchedUpdate(set={
        "view_count": "source.view_count",
        "unique_user_views": "source.unique_user_views",
        "click_count": "source.click_count",
        "search_count": "source.search_count",
        "conversion_rate": "source.conversion_rate",
        "avg_time_on_page": "source.avg_time_on_page",
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = engagement_metrics.count()
    print(f"✓ Merged {record_count} records into fact_property_engagement")


# ============================================================================
# WEATHER TABLES
# ============================================================================

def merge_dim_weather_location(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge dim_weather_location from Silver to Gold.
    
    SCD Type 1 dimension (updates in place).
    
    Key patterns:
    - Deduplication by locationKey
    - Column mapping from Silver (flatten nested structures)
    - Generate surrogate key
    """
    print("\n--- Merging dim_weather_location (SCD Type 1) ---")
    
    silver_table = f"{catalog}.{silver_schema}.silver_locations"
    gold_table = f"{catalog}.{gold_schema}.dim_weather_location"
    
    # Read and deduplicate
    locations_raw = spark.table(silver_table)
    original_count = locations_raw.count()
    
    locations = (
        locations_raw
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates(["locationKey"])
    )
    
    dedupe_count = locations.count()
    print(f"  Deduplicated: {original_count} → {dedupe_count} records ({original_count - dedupe_count} duplicates removed)")
    
    # Prepare updates with column mappings and surrogate key
    updates_df = (
        locations
        # Generate surrogate key
        .withColumn("location_key", md5(col("locationKey")))
        
        # Map columns (flatten nested structures)
        .withColumn("country_code", col("country.id"))
        .withColumn("country_name", col("country.localizedName"))
        .withColumn("administrativeArea_id", col("administrativeArea.id"))
        .withColumn("administrativeArea_name", col("administrativeArea.localizedName"))
        .withColumn("timezone_code", col("timeZone.code"))
        .withColumn("timezone_name", col("timeZone.name"))
        .withColumn("gmt_offset", col("timeZone.gmtOffset"))
        .withColumn("latitude", col("geoPosition.latitude"))
        .withColumn("longitude", col("geoPosition.longitude"))
        .withColumn("elevation_metric_value", col("geoPosition.elevation.metric.value"))
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "location_key",
            "locationKey",
            "localizedName",
            "englishName",
            "country_code",
            "country_name",
            "administrativeArea_id",
            "administrativeArea_name",
            "timezone_code",
            "timezone_name",
            "gmt_offset",
            "latitude",
            "longitude",
            "elevation_metric_value",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # MERGE into Gold (Type 1 - update all fields)
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        updates_df.alias("source"),
        "target.locationKey = source.locationKey"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = updates_df.count()
    print(f"✓ Merged {record_count} records into dim_weather_location")


def merge_fact_weather_daily(spark: SparkSession, catalog: str, silver_schema: str, gold_schema: str):
    """
    Merge fact_weather_daily from Silver to Gold.
    
    Daily weather forecast fact table.
    
    Key patterns:
    - Composite grain (locationKey + date)
    - Deduplication
    - Grain validation
    - Generate surrogate FK to dim_weather_location
    """
    print("\n--- Merging fact_weather_daily ---")
    
    silver_table = f"{catalog}.{silver_schema}.silver_forecast_daily"
    gold_table = f"{catalog}.{gold_schema}.fact_weather_daily"
    
    # Read and deduplicate forecasts
    forecasts_raw = spark.table(silver_table)
    original_count = forecasts_raw.count()
    
    forecasts = (
        forecasts_raw
        .orderBy(col("processed_timestamp").desc())
        .dropDuplicates(["locationKey", "date"])
    )
    
    dedupe_count = forecasts.count()
    print(f"  Deduplicated forecasts: {original_count} → {dedupe_count} records")
    
    # Prepare fact data with surrogate FK
    fact_df = (
        forecasts
        # Generate surrogate FK to dim_weather_location
        .withColumn("location_key", md5(col("locationKey")))
        
        # Map columns (flatten nested structures)
        .withColumn("temperatureMin", col("temperature.minimum.value"))
        .withColumn("temperatureMax", col("temperature.maximum.value"))
        .withColumn("temperatureUnit", col("temperature.minimum.unit"))
        .withColumn("realFeelMin", col("realFeelTemperature.minimum.value"))
        .withColumn("realFeelMax", col("realFeelTemperature.maximum.value"))
        .withColumn("day_iconPhrase", col("day.iconPhrase"))
        .withColumn("day_hasPrecipitation", col("day.hasPrecipitation"))
        .withColumn("night_iconPhrase", col("night.iconPhrase"))
        .withColumn("night_hasPrecipitation", col("night.hasPrecipitation"))
        
        # Timestamps
        .withColumn("record_created_timestamp", current_timestamp())
        .withColumn("record_updated_timestamp", current_timestamp())
        
        .select(
            "locationKey",
            "location_key",
            "date",
            "epochDate",
            "temperatureMin",
            "temperatureMax",
            "temperatureUnit",
            "realFeelMin",
            "realFeelMax",
            "hoursOfSun",
            "precipitationProbability",
            "thunderstormProbability",
            "rainProbability",
            "snowProbability",
            "iceProbability",
            "day_iconPhrase",
            "day_hasPrecipitation",
            "night_iconPhrase",
            "night_hasPrecipitation",
            "temperature_range",
            "is_precipitation_expected",
            "record_created_timestamp",
            "record_updated_timestamp"
        )
    )
    
    # Grain validation (composite key: locationKey + date)
    distinct_grain_count = fact_df.select("locationKey", "date").distinct().count()
    total_row_count = fact_df.count()
    
    if distinct_grain_count != total_row_count:
        raise ValueError(
            f"Grain validation failed! Expected one row per location-date.\n"
            f"  Distinct combinations: {distinct_grain_count}\n"
            f"  Total rows: {total_row_count}\n"
            f"  Duplicates: {total_row_count - distinct_grain_count}"
        )
    
    print(f"  ✓ Grain validation passed: {total_row_count} unique location-date combinations")
    
    # MERGE into Gold
    delta_gold = DeltaTable.forName(spark, gold_table)
    
    delta_gold.alias("target").merge(
        fact_df.alias("source"),
        """target.locationKey = source.locationKey 
           AND target.date = source.date"""
    ).whenMatchedUpdate(set={
        "temperatureMin": "source.temperatureMin",
        "temperatureMax": "source.temperatureMax",
        "realFeelMin": "source.realFeelMin",
        "realFeelMax": "source.realFeelMax",
        "hoursOfSun": "source.hoursOfSun",
        "precipitationProbability": "source.precipitationProbability",
        "thunderstormProbability": "source.thunderstormProbability",
        "rainProbability": "source.rainProbability",
        "snowProbability": "source.snowProbability",
        "iceProbability": "source.iceProbability",
        "temperature_range": "source.temperature_range",
        "is_precipitation_expected": "source.is_precipitation_expected",
        "record_updated_timestamp": "source.record_updated_timestamp"
    }).whenNotMatchedInsertAll(
    ).execute()
    
    record_count = fact_df.count()
    print(f"✓ Merged {record_count} records into fact_weather_daily")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point for Gold layer MERGE operations."""
    from pyspark.sql import SparkSession
    
    catalog, silver_schema, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Wanderbricks Gold Layer MERGE").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS GOLD LAYER MERGE OPERATIONS")
    print("=" * 80)
    print(f"Source: {catalog}.{silver_schema}")
    print(f"Target: {catalog}.{gold_schema}")
    print("=" * 80)
    
    try:
        successful_merges = []
        skipped_merges = []
        
        # Phase 1: Generate date dimension (no Silver source)
        print("\n" + "=" * 80)
        print("PHASE 1: GENERATE DATE DIMENSION")
        print("=" * 80)
        if safe_merge(generate_dim_date, spark, catalog, gold_schema):
            successful_merges.append("dim_date")
        else:
            skipped_merges.append("dim_date")
        
        # Phase 2: Merge Type 1 dimensions
        print("\n" + "=" * 80)
        print("PHASE 2: MERGE TYPE 1 DIMENSIONS")
        print("=" * 80)
        if safe_merge(merge_dim_destination, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("dim_destination")
        else:
            skipped_merges.append("dim_destination")
        
        if safe_merge(merge_dim_weather_location, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("dim_weather_location")
        else:
            skipped_merges.append("dim_weather_location")
        
        # Phase 3: Merge Type 2 dimensions
        print("\n" + "=" * 80)
        print("PHASE 3: MERGE TYPE 2 DIMENSIONS")
        print("=" * 80)
        if safe_merge(merge_dim_user, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("dim_user")
        else:
            skipped_merges.append("dim_user")
            
        if safe_merge(merge_dim_host, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("dim_host")
        else:
            skipped_merges.append("dim_host")
            
        if safe_merge(merge_dim_property, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("dim_property")
        else:
            skipped_merges.append("dim_property")
        
        # Phase 4: Merge facts
        print("\n" + "=" * 80)
        print("PHASE 4: MERGE FACT TABLES")
        print("=" * 80)
        if safe_merge(merge_fact_booking_detail, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("fact_booking_detail")
        else:
            skipped_merges.append("fact_booking_detail")
            
        if safe_merge(merge_fact_booking_daily, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("fact_booking_daily")
        else:
            skipped_merges.append("fact_booking_daily")
            
        if safe_merge(merge_fact_property_engagement, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("fact_property_engagement")
        else:
            skipped_merges.append("fact_property_engagement")
        
        if safe_merge(merge_fact_weather_daily, spark, catalog, silver_schema, gold_schema):
            successful_merges.append("fact_weather_daily")
        else:
            skipped_merges.append("fact_weather_daily")
        
        print("\n" + "=" * 80)
        print("GOLD LAYER MERGE SUMMARY")
        print("=" * 80)
        print(f"✓ Successful: {len(successful_merges)} tables")
        for table in successful_merges:
            print(f"  - {table}")
        
        if skipped_merges:
            print(f"\n⚠️  Skipped: {len(skipped_merges)} tables (source not found)")
            for table in skipped_merges:
                print(f"  - {table}")
        
        print("=" * 80)
        
        # Summary
        print("\nTable Summary:")
        tables = spark.sql(f"SHOW TABLES IN {catalog}.{gold_schema}").collect()
        for table in tables:
            table_name = table.tableName
            if table_name.startswith("dim_") or table_name.startswith("fact_"):
                row_count = spark.table(f"{catalog}.{gold_schema}.{table_name}").count()
                print(f"  - {table_name}: {row_count:,} records")
        
    except Exception as e:
        print(f"\n❌ Error during Gold layer MERGE: {str(e)}")
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

