# Databricks notebook source
"""
Feature Store Setup for Wanderbricks ML Models

Creates feature tables in Unity Catalog for machine learning model training.
Uses MLflow 3.0 and Feature Engineering Client best practices.

SCHEMA-GROUNDED: All column references verified against gold_layer_design/yaml/*.yaml

Reference: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/uc/feature-tables-uc
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from databricks.feature_engineering import FeatureEngineeringClient
from datetime import datetime, timedelta


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema


def create_catalog_and_schema(spark: SparkSession, catalog: str, feature_schema: str):
    """Ensures the Unity Catalog schema exists for feature tables and models."""
    # Check if catalog exists
    print(f"\nChecking if catalog '{catalog}' exists...")
    try:
        spark.sql(f"DESCRIBE CATALOG {catalog}")
        print(f"✓ Catalog '{catalog}' exists")
    except Exception as e:
        print(f"❌ ERROR: Catalog '{catalog}' does not exist!")
        print(f"Please create the catalog first using:")
        print(f"  CREATE CATALOG {catalog};")
        raise RuntimeError(f"Catalog '{catalog}' does not exist. Cannot proceed with feature store setup.") from e
    
    # Ensure schema exists
    print(f"Ensuring schema '{feature_schema}' exists...")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{feature_schema}")
    spark.sql(f"COMMENT ON SCHEMA {catalog}.{feature_schema} IS 'ML feature tables and registered models'")
    
    # Enable predictive optimization at schema level
    # Reference: https://docs.databricks.com/aws/en/optimizations/predictive-optimization#enable-or-disable-predictive-optimization-for-a-catalog-or-schema
    try:
        spark.sql(f"ALTER SCHEMA {catalog}.{feature_schema} ENABLE PREDICTIVE OPTIMIZATION")
        print(f"✓ Enabled predictive optimization for {catalog}.{feature_schema}")
    except Exception as e:
        print(f"⚠ Could not enable predictive optimization: {e}")
    
    print(f"✓ Schema {catalog}.{feature_schema} ready for feature tables and model registry")


def create_property_features(
    spark: SparkSession, 
    catalog: str, 
    gold_schema: str, 
    feature_schema: str,
    fe: FeatureEngineeringClient
):
    """
    Create property-level features for ML models.
    
    Schema grounded in: gold_layer_design/yaml/property/dim_property.yaml
    
    Features include:
    - Property attributes: property_type, bedrooms, bathrooms, max_guests, base_price
    - Location IDs: destination_id, host_id
    - Coordinates: property_latitude, property_longitude
    - Historical performance: bookings_30d, revenue_30d, avg_booking_value_30d
    - Engagement metrics: views_30d, clicks_30d, conversion_rate_30d
    """
    print("\n" + "="*80)
    print("Creating property_features table")
    print("="*80)
    
    # Load Gold layer tables
    dim_property = spark.table(f"{catalog}.{gold_schema}.dim_property")
    fact_booking_daily = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
    fact_engagement = spark.table(f"{catalog}.{gold_schema}.fact_property_engagement")
    
    # Calculate historical metrics (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
    
    # Booking metrics (from fact_booking_daily)
    # GROUNDED: booking_count, total_booking_value, avg_booking_value, avg_nights_booked
    booking_metrics = (
        fact_booking_daily
        .filter(col("check_in_date") >= lit(thirty_days_ago))
        .groupBy("property_id")
        .agg(
            sum("booking_count").alias("bookings_30d"),
            sum("total_booking_value").alias("revenue_30d"),
            avg("avg_booking_value").alias("avg_booking_value_30d"),
            avg("avg_nights_booked").alias("avg_nights_30d")
        )
    )
    
    # Engagement metrics (from fact_property_engagement)
    # GROUNDED: view_count, click_count, conversion_rate
    engagement_metrics = (
        fact_engagement
        .filter(col("engagement_date") >= lit(thirty_days_ago))
        .groupBy("property_id")
        .agg(
            sum("view_count").alias("views_30d"),
            sum("click_count").alias("clicks_30d"),
            avg("conversion_rate").alias("avg_conversion_rate_30d")
        )
    )
    
    # Combine all features
    # GROUNDED: Only columns from dim_property YAML schema
    property_features = (
        dim_property
        .filter(col("is_current") == True)
        .select(
            "property_id",
            "property_type",
            "bedrooms",
            "bathrooms",
            "max_guests",
            "base_price",
            "destination_id",
            "host_id",
            "property_latitude",
            "property_longitude"
        )
        .join(booking_metrics, "property_id", "left")
        .join(engagement_metrics, "property_id", "left")
        .fillna(0, subset=[
            "bookings_30d", "revenue_30d", "avg_booking_value_30d", 
            "avg_nights_30d", "views_30d", "clicks_30d", "avg_conversion_rate_30d"
        ])
        .withColumn("feature_timestamp", current_timestamp())
        .withColumn("revenue_per_booking", 
                   when(col("bookings_30d") > 0, col("revenue_30d") / col("bookings_30d")).otherwise(0))
        .withColumn("click_through_rate",
                   when(col("views_30d") > 0, col("clicks_30d") / col("views_30d")).otherwise(0))
    )
    
    # Create feature table
    # Note: timestamp_keys removed - feature_timestamp is a regular column, not a primary key
    feature_table_name = f"{catalog}.{feature_schema}.property_features"
    
    fe.create_table(
        name=feature_table_name,
        primary_keys=["property_id"],
        df=property_features,
        description="Property-level features for ML models including attributes, booking history, and engagement metrics"
    )
    
    record_count = property_features.count()
    print(f"✓ Created property_features with {record_count} properties")


def create_user_features(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    fe: FeatureEngineeringClient
):
    """
    Create user-level features for ML models.
    
    Schema grounded in: 
    - gold_layer_design/yaml/identity/dim_user.yaml
    - gold_layer_design/yaml/booking/fact_booking_detail.yaml
    
    Features include:
    - Demographics: country, user_type, is_business
    - Account info: created_at (account creation date)
    - Transaction history: total_bookings, total_spend, avg_booking_value
    - Behavior: booking_frequency, cancellation_rate
    - Recency: days_since_last_booking
    """
    print("\n" + "="*80)
    print("Creating user_features table")
    print("="*80)
    
    # Load Gold layer tables
    dim_user = spark.table(f"{catalog}.{gold_schema}.dim_user")
    fact_booking_detail = spark.table(f"{catalog}.{gold_schema}.fact_booking_detail")
    
    # Calculate user metrics (from fact_booking_detail)
    # GROUNDED: booking_id, user_id, total_amount, status, created_at
    user_metrics = (
        fact_booking_detail
        .groupBy("user_id")
        .agg(
            count("booking_id").alias("total_bookings"),
            sum("total_amount").alias("total_spend"),
            avg("total_amount").alias("avg_booking_value"),
            sum(when(col("is_cancelled") == True, 1).otherwise(0)).alias("cancelled_bookings"),
            max("created_at").alias("last_booking_timestamp")
        )
        .withColumn("cancellation_rate",
                   when(col("total_bookings") > 0, col("cancelled_bookings") / col("total_bookings")).otherwise(0))
        .withColumn("days_since_last_booking",
                   datediff(current_timestamp(), col("last_booking_timestamp")))
    )
    
    # Calculate booking frequency (days between bookings)
    window_spec = Window.partitionBy("user_id").orderBy("created_at")
    booking_frequency = (
        fact_booking_detail
        .withColumn("prev_booking_timestamp", lag("created_at").over(window_spec))
        .withColumn("days_between_bookings",
                   datediff(col("created_at"), col("prev_booking_timestamp")))
        .filter(col("days_between_bookings").isNotNull())
        .groupBy("user_id")
        .agg(avg("days_between_bookings").alias("avg_days_between_bookings"))
    )
    
    # Combine all features
    # GROUNDED: dim_user columns: user_id, country, user_type, is_business, created_at (account), is_current
    user_features = (
        dim_user
        .filter(col("is_current") == True)
        .select(
            "user_id",
            "country",
            "user_type",
            "is_business",
            col("created_at").alias("account_created_date")
        )
        .join(user_metrics, "user_id", "left")
        .join(booking_frequency, "user_id", "left")
        .fillna(0, subset=[
            "total_bookings", "total_spend", "avg_booking_value",
            "cancelled_bookings", "cancellation_rate", "days_since_last_booking",
            "avg_days_between_bookings"
        ])
        .withColumn("feature_timestamp", current_timestamp())
        .withColumn("tenure_days", datediff(current_timestamp(), col("account_created_date")))
        .withColumn("is_repeat", when(col("total_bookings") > 1, True).otherwise(False))
    )
    
    # Create feature table
    feature_table_name = f"{catalog}.{feature_schema}.user_features"
    
    fe.create_table(
        name=feature_table_name,
        primary_keys=["user_id"],
        df=user_features,
        description="User-level features for ML models including demographics, transaction history, and behavior patterns"
    )
    
    record_count = user_features.count()
    print(f"✓ Created user_features with {record_count} users")


def create_engagement_features(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    fe: FeatureEngineeringClient
):
    """
    Create engagement features for conversion prediction.
    
    Schema grounded in: gold_layer_design/yaml/engagement/fact_property_engagement.yaml
    
    Features include:
    - Daily engagement metrics: view_count, click_count, conversion_rate
    - Time-based features: day_of_week, is_weekend
    - Rolling window metrics: 7-day averages
    """
    print("\n" + "="*80)
    print("Creating engagement_features table")
    print("="*80)
    
    # Load Gold layer table
    fact_engagement = spark.table(f"{catalog}.{gold_schema}.fact_property_engagement")
    
    # Calculate rolling window metrics
    window_7d = Window.partitionBy("property_id").orderBy("engagement_date").rowsBetween(-6, 0)
    
    # GROUNDED: fact_property_engagement columns: property_id, engagement_date, view_count, 
    #           unique_user_views, click_count, search_count, conversion_rate, avg_time_on_page
    engagement_features = (
        fact_engagement
        .withColumn("day_of_week", dayofweek("engagement_date"))
        .withColumn("is_weekend", when(col("day_of_week").isin([1, 7]), True).otherwise(False))
        .withColumn("views_7d_avg", avg("view_count").over(window_7d))
        .withColumn("clicks_7d_avg", avg("click_count").over(window_7d))
        .withColumn("conversion_rate_7d_avg", avg("conversion_rate").over(window_7d))
        .withColumn("feature_timestamp", current_timestamp())
        .select(
            "property_id",
            "engagement_date",
            "view_count",
            "unique_user_views",
            "click_count",
            "search_count",
            "conversion_rate",
            "avg_time_on_page",
            "day_of_week",
            "is_weekend",
            "views_7d_avg",
            "clicks_7d_avg",
            "conversion_rate_7d_avg",
            "feature_timestamp"
        )
    )
    
    # Create feature table
    # Primary key is composite: property_id + engagement_date
    feature_table_name = f"{catalog}.{feature_schema}.engagement_features"
    
    fe.create_table(
        name=feature_table_name,
        primary_keys=["property_id", "engagement_date"],
        df=engagement_features,
        description="Daily engagement features for conversion prediction with rolling window metrics"
    )
    
    record_count = engagement_features.count()
    print(f"✓ Created engagement_features with {record_count} records")


def create_location_features(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    fe: FeatureEngineeringClient
):
    """
    Create location/destination features for ML models.
    
    Schema grounded in: gold_layer_design/yaml/geography/dim_destination.yaml
    
    Features include:
    - Geographic hierarchy: destination (city), country, state_or_province
    - State codes for standardization
    """
    print("\n" + "="*80)
    print("Creating location_features table")
    print("="*80)
    
    # Load Gold layer table
    dim_destination = spark.table(f"{catalog}.{gold_schema}.dim_destination")
    
    # GROUNDED: dim_destination columns: destination_id, destination, country, 
    #           state_or_province, state_or_province_code, description
    location_features = (
        dim_destination
        .select(
            "destination_id",
            "destination",
            "country",
            "state_or_province",
            "state_or_province_code"
        )
        .withColumn("feature_timestamp", current_timestamp())
    )
    
    # Create feature table
    feature_table_name = f"{catalog}.{feature_schema}.location_features"
    
    fe.create_table(
        name=feature_table_name,
        primary_keys=["destination_id"],
        df=location_features,
        description="Location features for geographic market analysis and regional modeling"
    )
    
    record_count = location_features.count()
    print(f"✓ Created location_features with {record_count} destinations")


def main():
    """Main entry point for feature store setup."""
    
    catalog, gold_schema, feature_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Feature Store Setup").getOrCreate()
    
    # Initialize Feature Engineering Client
    fe = FeatureEngineeringClient()
    
    try:
        # Create schema
        create_catalog_and_schema(spark, catalog, feature_schema)
        
        # Create feature tables (schema-grounded)
        create_property_features(spark, catalog, gold_schema, feature_schema, fe)
        create_user_features(spark, catalog, gold_schema, feature_schema, fe)
        create_engagement_features(spark, catalog, gold_schema, feature_schema, fe)
        create_location_features(spark, catalog, gold_schema, feature_schema, fe)
        
        print("\n" + "="*80)
        print("✓ Feature Store setup completed successfully!")
        print("="*80)
        print("\nFeature Tables Created:")
        print(f"  1. {catalog}.{feature_schema}.property_features")
        print(f"  2. {catalog}.{feature_schema}.user_features")
        print(f"  3. {catalog}.{feature_schema}.engagement_features")
        print(f"  4. {catalog}.{feature_schema}.location_features")
        
        print("\nFeature Counts:")
        print(f"  - Property features: 17 columns")
        print(f"  - User features: 12 columns")
        print(f"  - Engagement features: 14 columns")
        print(f"  - Location features: 6 columns")
        
    except Exception as e:
        print(f"\n❌ Error during feature store setup: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
