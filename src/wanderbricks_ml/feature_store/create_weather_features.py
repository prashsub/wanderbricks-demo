# Databricks notebook source
"""
Weather-Aware Feature Engineering for Demand Forecasting

Creates enhanced property features with weather, seasonality, and regional patterns.
Based on production requirements for 8.4% MAPE accuracy target with regional forecasting.

Reference: 
- phase4-addendum-4.1-ml-models.md
- Weather screenshots showing regional/seasonal patterns
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window
from databricks.feature_engineering import FeatureEngineeringClient
from datetime import datetime


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, gold_schema, feature_schema


def create_weather_aware_property_features(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    fe: FeatureEngineeringClient
):
    """
    Create property features enhanced with weather, seasonality, and regional patterns.
    
    Features Added:
    - Weather: Temperature range, precipitation probability, hours of sun
    - Seasonality: Month, quarter, is_peak_season, is_holiday
    - Regional: Destination-level aggregates, market competitiveness
    - Event-driven: Holiday seasons, weekly patterns
    
    Target Accuracy: MAPE < 10% (shown as 8.4% in screenshots)
    """
    print("\n" + "="*80)
    print("Creating Weather-Aware Property Features")
    print("="*80)
    
    # =========================================================================
    # 1. Base Property Attributes
    # =========================================================================
    dim_property = spark.table(f"{catalog}.{gold_schema}.dim_property")
    
    # Get current property records (SCD2)
    base_properties = (
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
    )
    
    # =========================================================================
    # 2. Weather Features (from new weather tables)
    # =========================================================================
    dim_destination = spark.table(f"{catalog}.{gold_schema}.dim_destination")
    
    # Link destinations to weather locations (by city/region match)
    # For now, use destination_id as approximation
    # In production, would join on location matching
    
    try:
        fact_weather = spark.table(f"{catalog}.{gold_schema}.fact_weather_daily")
        dim_weather_location = spark.table(f"{catalog}.{gold_schema}.dim_weather_location")
        
        # Get latest 30-day weather forecast by location
        weather_window = Window.partitionBy("locationKey").orderBy(desc("date"))
        
        weather_features = (
            fact_weather
            .withColumn("row_num", row_number().over(weather_window))
            .filter(col("row_num") <= 30)
            .groupBy("locationKey", "location_key")
            .agg(
                avg("temperatureMin").alias("avg_temp_min_30d"),
                avg("temperatureMax").alias("avg_temp_max_30d"),
                avg("realFeelMin").alias("avg_realfeel_min_30d"),
                avg("realFeelMax").alias("avg_realfeel_max_30d"),
                avg("hoursOfSun").alias("avg_hours_sun_30d"),
                avg("precipitationProbability").alias("avg_precip_prob_30d"),
                max("thunderstormProbability").alias("max_thunderstorm_prob_30d"),
                sum(when(col("is_precipitation_expected"), 1).otherwise(0)).alias("precip_days_30d")
            )
        )
        
        print("✓ Weather features created from fact_weather_daily")
    except Exception as e:
        print(f"⚠ Weather tables not available: {e}")
        print("Creating placeholder weather features")
        weather_features = None
    
    # =========================================================================
    # 3. Historical Booking Patterns (30/90/365 day windows)
    # =========================================================================
    fact_booking_daily = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
    
    # Calculate rolling windows for demand patterns
    booking_features = (
        fact_booking_daily
        .groupBy("property_id")
        .agg(
            # 30-day metrics (existing)
            sum(when(datediff(current_date(), col("check_in_date")) <= 30, col("booking_count")).otherwise(0)).alias("bookings_30d"),
            sum(when(datediff(current_date(), col("check_in_date")) <= 30, col("total_booking_value")).otherwise(0)).alias("revenue_30d"),
            avg(when(datediff(current_date(), col("check_in_date")) <= 30, col("avg_booking_value")).otherwise(None)).alias("avg_booking_value_30d"),
            avg(when(datediff(current_date(), col("check_in_date")) <= 30, col("avg_nights_booked")).otherwise(None)).alias("avg_nights_30d"),
            
            # 90-day metrics (for trend analysis)
            sum(when(datediff(current_date(), col("check_in_date")) <= 90, col("booking_count")).otherwise(0)).alias("bookings_90d"),
            sum(when(datediff(current_date(), col("check_in_date")) <= 90, col("total_booking_value")).otherwise(0)).alias("revenue_90d"),
            avg(when(datediff(current_date(), col("check_in_date")) <= 90, col("avg_booking_value")).otherwise(None)).alias("avg_booking_value_90d"),
            
            # 365-day metrics (for year-over-year)
            sum(when(datediff(current_date(), col("check_in_date")) <= 365, col("booking_count")).otherwise(0)).alias("bookings_365d"),
            sum(when(datediff(current_date(), col("check_in_date")) <= 365, col("total_booking_value")).otherwise(0)).alias("revenue_365d"),
            
            # Trend indicators
            sum(when(datediff(current_date(), col("check_in_date")).between(31, 60), col("booking_count")).otherwise(0)).alias("bookings_31_60d"),
            sum(when(datediff(current_date(), col("check_in_date")).between(61, 90), col("booking_count")).otherwise(0)).alias("bookings_61_90d")
        )
        .withColumn("booking_trend_30_60d", 
                   when(col("bookings_31_60d") > 0, 
                        (col("bookings_30d") - col("bookings_31_60d")) / col("bookings_31_60d"))
                   .otherwise(0))
        .withColumn("booking_trend_60_90d",
                   when(col("bookings_61_90d") > 0,
                        (col("bookings_31_60d") - col("bookings_61_90d")) / col("bookings_61_90d"))
                   .otherwise(0))
    )
    
    # =========================================================================
    # 4. Engagement Features
    # =========================================================================
    fact_property_engagement = spark.table(f"{catalog}.{gold_schema}.fact_property_engagement")
    
    engagement_features = (
        fact_property_engagement
        .groupBy("property_id")
        .agg(
            sum(when(datediff(current_date(), col("engagement_date")) <= 30, col("view_count")).otherwise(0)).alias("views_30d"),
            sum(when(datediff(current_date(), col("engagement_date")) <= 30, col("click_count")).otherwise(0)).alias("clicks_30d"),
            avg(when(datediff(current_date(), col("engagement_date")) <= 30, col("conversion_rate")).otherwise(None)).alias("avg_conversion_rate_30d")
        )
        .withColumn("revenue_per_booking", 
                   when(col("bookings_30d") > 0, col("revenue_30d") / col("bookings_30d")).otherwise(0))
        .withColumn("click_through_rate",
                   when(col("views_30d") > 0, col("clicks_30d") / col("views_30d")).otherwise(0))
    )
    
    # =========================================================================
    # 5. Regional/Destination-Level Metrics
    # =========================================================================
    destination_metrics = (
        fact_booking_daily
        .join(dim_property.select("property_id", "destination_id"), "property_id")
        .groupBy("destination_id")
        .agg(
            avg("avg_booking_value").alias("destination_avg_booking_value"),
            avg("occupancy_rate").alias("destination_occupancy_rate"),
            count("booking_id").alias("destination_total_bookings"),
            sum("total_booking_value").alias("destination_total_revenue")
        )
        .withColumn("destination_revpar", 
                   col("destination_total_revenue") / col("destination_total_bookings"))
    )
    
    # =========================================================================
    # 6. Seasonality Features
    # =========================================================================
    # These are added at feature_date level during table creation
    
    # =========================================================================
    # 7. Combine All Features
    # =========================================================================
    all_features = (
        base_properties
        .join(booking_features, "property_id", "left")
        .join(engagement_features, "property_id", "left")
        .join(destination_metrics, "destination_id", "left")
    )
    
    # Add weather if available
    if weather_features:
        # Join weather via destination (would need location mapping in production)
        all_features = all_features.join(weather_features, "location_key", "left")
    
    # Add temporal features for feature_date
    all_features = (
        all_features
        .withColumn("feature_date", current_date())
        .withColumn("feature_timestamp", current_timestamp())
        .withColumn("day_of_week", dayofweek("feature_date"))
        .withColumn("is_weekend", dayofweek("feature_date").isin([1, 7]))
        .withColumn("month", month("feature_date"))
        .withColumn("quarter", quarter("feature_date"))
        .withColumn("is_peak_season", month("feature_date").isin([6, 7, 8, 12]))  # Summer + December
        
        # Holiday calendar (simplified - production would use proper calendar)
        .withColumn("is_holiday", lit(0))
    )
    
    # Fill nulls with zeros
    numeric_cols = [f.name for f in all_features.schema.fields if f.dataType.simpleString() in ['bigint', 'int', 'double', 'float']]
    all_features = all_features.fillna(0, subset=numeric_cols)
    
    print(f"✓ Weather-aware features created: {all_features.count()} records")
    print(f"  Total columns: {len(all_features.columns)}")
    
    # =========================================================================
    # 8. Write to Feature Store
    # =========================================================================
    feature_table_name = f"{catalog}.{feature_schema}.property_features_weather_v2"
    
    fe.create_table(
        name=feature_table_name,
        primary_keys=["property_id", "feature_date"],
        timeseries_columns="feature_date",
        df=all_features,
        description="Weather-aware property features with seasonality and regional patterns for demand forecasting"
    )
    
    print(f"✓ Feature table created: {feature_table_name}")
    
    return feature_table_name


def main():
    """Main entry point for weather-aware feature creation."""
    
    catalog, gold_schema, feature_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Weather Feature Engineering").getOrCreate()
    
    fe = FeatureEngineeringClient()
    
    try:
        feature_table = create_weather_aware_property_features(
            spark, catalog, gold_schema, feature_schema, fe
        )
        
        print("\n" + "="*80)
        print("✓ Weather-aware feature engineering completed!")
        print("="*80)
        print(f"\nFeature Table: {feature_table}")
        print("\nNext Steps:")
        print("1. Update demand_predictor training to use new feature table")
        print("2. Add seasonality analysis patterns")
        print("3. Train regional-specific models")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        dbutils.notebook.exit(f"FAILED: {str(e)}")
    
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()

