# Databricks notebook source

"""
Wanderbricks Silver Layer - AccuWeather Data
Delta Live Tables (DLT) definitions for AccuWeather weather data.

Tables:
- silver_forecast_daily_metric: Daily weather forecasts with temperature (metric units)
- silver_historical_daily_metric: Historical daily weather data (metric units)
"""

import dlt
from pyspark.sql.functions import col, current_timestamp, sha2, concat_ws, coalesce, when, lit

from dq_rules_loader import (
    get_critical_rules_for_table,
    get_warning_rules_for_table
)


def get_bronze_table(table_name):
    """
    Get fully qualified Bronze table name from pipeline configuration.
    
    Uses spark.conf to read catalog and bronze_schema passed from DLT pipeline config.
    
    Args:
        table_name: Base table name (e.g., "forecast_daily")
    
    Returns:
        Fully qualified table name: "{catalog}.{bronze_schema}.{table_name}"
    """
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    return f"{catalog}.{bronze_schema}.{table_name}"


# =============================================================================
# SILVER_FORECAST_DAILY_METRIC - Daily Weather Forecasts (Metric)
# =============================================================================

@dlt.table(
    name="silver_forecast_daily_metric",
    comment="""LLM: Silver layer streaming fact table for daily weather forecasts from AccuWeather (metric units).
    Contains temperature predictions, precipitation, and weather conditions in Celsius.
    Useful for analyzing weather impact on bookings and property occupancy.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "application": "wanderbricks",
        "project": "wanderbricks_demo",
        "layer": "silver",
        "source_table": "bronze_forecast_daily_calendar_metric",
        "domain": "weather",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "consumer": "analytics_team",
        "developer": "edp",
        "support": "edp",
        "business_owner": "Revenue Management",
        "technical_owner": "Data Engineering",
        "business_owner_email": "revenue.management@wanderbricks.com",
        "technical_owner_email": "data-engineering@wanderbricks.com"
    },
    cluster_by_auto=True
)
def silver_forecast_daily_metric():
    """
    Daily weather forecast data from AccuWeather (metric units).
    
    Business Key: locationKey + date
    """
    return (
        dlt.read_stream(get_bronze_table("forecast_daily_calendar_metric"))
        # Add processing timestamp
        .withColumn("processed_timestamp", current_timestamp())
    )


# =============================================================================
# SILVER_HISTORICAL_DAILY_METRIC - Historical Daily Weather (Metric)
# =============================================================================

@dlt.table(
    name="silver_historical_daily_metric",
    comment="""LLM: Silver layer streaming fact table for historical daily weather from AccuWeather (metric units).
    Contains past temperature and weather conditions. Useful for historical weather analysis
    and correlating past weather with booking patterns.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "application": "wanderbricks",
        "project": "wanderbricks_demo",
        "layer": "silver",
        "source_table": "bronze_historical_daily_calendar_metric",
        "domain": "weather",
        "entity_type": "fact",
        "contains_pii": "false",
        "data_classification": "internal",
        "consumer": "analytics_team",
        "developer": "edp",
        "support": "edp",
        "business_owner": "Revenue Management",
        "technical_owner": "Data Engineering",
        "business_owner_email": "revenue.management@wanderbricks.com",
        "technical_owner_email": "data-engineering@wanderbricks.com"
    },
    cluster_by_auto=True
)
def silver_historical_daily_metric():
    """
    Historical daily weather data from AccuWeather (metric units).
    
    Business Key: locationKey + date
    """
    return (
        dlt.read_stream(get_bronze_table("historical_daily_calendar_metric"))
        # Add processing timestamp
        .withColumn("processed_timestamp", current_timestamp())
    )

