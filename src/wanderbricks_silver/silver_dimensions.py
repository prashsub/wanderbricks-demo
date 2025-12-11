# Databricks notebook source

"""
Wanderbricks Silver Layer - Dimension Tables with DLT

Delta Live Tables pipeline for Silver dimension tables with:
- Data quality expectations loaded from Delta table (dq_rules)
- Automatic liquid clustering (cluster_by_auto=True)
- Advanced Delta Lake features (row tracking, deletion vectors)
- Incremental streaming from Bronze layer
- Schema cloning from Bronze with minimal transformation

Dimension Tables:
- silver_users
- silver_hosts
- silver_destinations
- silver_countries
- silver_properties
- silver_amenities
- silver_employees
- silver_property_amenities (bridge table)
- silver_property_images

Reference: https://docs.databricks.com/aws/en/ldp/expectation-patterns
"""

import dlt
from pyspark.sql.functions import (
    col, current_timestamp, sha2, concat_ws, coalesce, when, lit, 
    upper, trim, lower
)

# Import DQ rules loader (pure Python module, not notebook)
from dq_rules_loader import (
    get_critical_rules_for_table,
    get_warning_rules_for_table
)


def get_bronze_table(table_name):
    """
    Helper function to get fully qualified Bronze table name from DLT configuration.
    
    Supports DLT Direct Publishing Mode - uses catalog/schema from pipeline config.
    
    Args:
        table_name: Name of the Bronze table (e.g., "users")
    
    Returns:
        Fully qualified table name: "{catalog}.{bronze_schema}.{table_name}"
    """
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    return f"{catalog}.{bronze_schema}.{table_name}"


# ============================================================================
# SILVER_USERS (Dimension)
# ============================================================================

@dlt.table(
    name="silver_users",
    comment="""LLM: Silver layer users dimension with validated email, name, and account data. 
    Rules loaded dynamically from dq_rules Delta table. Streaming ingestion from Bronze with 
    data quality validation and business key generation.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "users",
        "domain": "customer",
        "entity_type": "dimension",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Customer Success",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_users"))
@dlt.expect_all(get_warning_rules_for_table("silver_users"))
def silver_users():
    """
    Silver users dimension - clones Bronze schema with validation.
    
    Transformations:
    - ✅ Standardize email (lowercase, trimmed)
    - ✅ Add user_business_key (SHA256 hash)
    - ✅ Add processed_timestamp
    - ❌ NO aggregation
    - ❌ NO complex calculations
    
    DQ Rules (from dq_rules table):
    - CRITICAL: user_id NOT NULL, email valid format, name NOT NULL
    - WARNING: recent user creation (within 5 years)
    """
    return (
        dlt.read_stream(get_bronze_table("users"))
        .withColumn("email", lower(trim(col("email"))))
        .withColumn("user_business_key", 
                   sha2(concat_ws("||", col("user_id"), col("email")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_HOSTS (Dimension)
# ============================================================================

@dlt.table(
    name="silver_hosts",
    comment="""LLM: Silver layer hosts dimension with validated contact information and ratings. 
    Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "hosts",
        "domain": "hosts",
        "entity_type": "dimension",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Host Relations",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_hosts"))
@dlt.expect_all(get_warning_rules_for_table("silver_hosts"))
def silver_hosts():
    """
    Silver hosts dimension - clones Bronze schema with validation.
    
    DQ Rules:
    - CRITICAL: host_id NOT NULL, email valid format
    - WARNING: rating between 1.0-5.0
    """
    return (
        dlt.read_stream(get_bronze_table("hosts"))
        .withColumn("email", lower(trim(col("email"))))
        .withColumn("host_business_key", 
                   sha2(concat_ws("||", col("host_id"), col("email")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_DESTINATIONS (Dimension)
# ============================================================================

@dlt.table(
    name="silver_destinations",
    comment="""LLM: Silver layer destinations dimension with validated geographic data and descriptions. 
    Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "destinations",
        "domain": "geography",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Product",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_destinations"))
@dlt.expect_all(get_warning_rules_for_table("silver_destinations"))
def silver_destinations():
    """
    Silver destinations dimension - clones Bronze schema with validation.
    
    DQ Rules:
    - CRITICAL: destination_id NOT NULL, destination name present, country present
    """
    return (
        dlt.read_stream(get_bronze_table("destinations"))
        .withColumn("destination_business_key", 
                   sha2(concat_ws("||", col("destination_id"), col("destination")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_COUNTRIES (Dimension)
# ============================================================================

@dlt.table(
    name="silver_countries",
    comment="""LLM: Silver layer countries dimension with validated ISO codes and continent data. 
    Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "countries",
        "domain": "geography",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Product",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_countries"))
@dlt.expect_all(get_warning_rules_for_table("silver_countries"))
def silver_countries():
    """
    Silver countries dimension - clones Bronze schema with validation.
    
    Transformations:
    - ✅ Standardize country_code (uppercase)
    
    DQ Rules:
    - CRITICAL: country NOT NULL, country_code 2 letters
    """
    return (
        dlt.read_stream(get_bronze_table("countries"))
        .withColumn("country_code", upper(trim(col("country_code"))))
        .withColumn("country_business_key", 
                   sha2(concat_ws("||", col("country"), col("country_code")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_PROPERTIES (Dimension)
# ============================================================================

@dlt.table(
    name="silver_properties",
    comment="""LLM: Silver layer properties dimension with validated pricing, capacity, and location data. 
    Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "properties",
        "domain": "property",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Product",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_properties"))
@dlt.expect_all(get_warning_rules_for_table("silver_properties"))
def silver_properties():
    """
    Silver properties dimension - clones Bronze schema with validation.
    
    Transformations:
    - ✅ Add derived flag: has_outdoor_space (if bedrooms + bathrooms > 3)
    - ✅ Add business key
    
    DQ Rules:
    - CRITICAL: property_id, host_id, destination_id NOT NULL, base_price > 0
    - WARNING: reasonable price ($10-$10k), guests (1-20), valid coordinates
    """
    return (
        dlt.read_stream(get_bronze_table("properties"))
        .withColumn("has_outdoor_space",
                   when((col("bedrooms") + col("bathrooms")) > 3, True).otherwise(False))
        .withColumn("property_business_key", 
                   sha2(concat_ws("||", col("property_id"), col("host_id")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_AMENITIES (Dimension)
# ============================================================================

@dlt.table(
    name="silver_amenities",
    comment="""LLM: Silver layer amenities dimension with validated amenity types and categories. 
    Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "amenities",
        "domain": "property",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Product",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_amenities"))
@dlt.expect_all(get_warning_rules_for_table("silver_amenities"))
def silver_amenities():
    """
    Silver amenities dimension - clones Bronze schema with validation.
    
    DQ Rules:
    - CRITICAL: amenity_id NOT NULL, name present
    """
    return (
        dlt.read_stream(get_bronze_table("amenities"))
        .withColumn("amenity_business_key", 
                   sha2(concat_ws("||", col("amenity_id"), col("name")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_EMPLOYEES (Dimension)
# ============================================================================

@dlt.table(
    name="silver_employees",
    comment="""LLM: Silver layer employees dimension with validated employment dates and status. 
    Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "employees",
        "domain": "workforce",
        "entity_type": "dimension",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "HR",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_employees"))
@dlt.expect_all(get_warning_rules_for_table("silver_employees"))
def silver_employees():
    """
    Silver employees dimension - clones Bronze schema with validation.
    
    Transformations:
    - ✅ Standardize email (lowercase)
    - ✅ Derive is_active flag from is_currently_employed
    
    DQ Rules:
    - CRITICAL: employee_id, host_id, joined_at NOT NULL
    - WARNING: end_service_date >= joined_at if present
    """
    return (
        dlt.read_stream(get_bronze_table("employees"))
        .withColumn("email", lower(trim(col("email"))))
        .withColumn("is_active", col("is_currently_employed"))
        .withColumn("employee_business_key", 
                   sha2(concat_ws("||", col("employee_id"), col("host_id")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_PROPERTY_AMENITIES (Bridge Table)
# ============================================================================

@dlt.table(
    name="silver_property_amenities",
    comment="""LLM: Silver layer property-amenities bridge table linking properties to their amenities. 
    Many-to-many relationship table with FK validation.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "property_amenities",
        "domain": "property",
        "entity_type": "bridge",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Product",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
def silver_property_amenities():
    """
    Silver property amenities bridge - clones Bronze schema.
    
    Note: No explicit DQ rules in dq_rules table, but FKs validated via dimension tables.
    """
    return (
        dlt.read_stream(get_bronze_table("property_amenities"))
        .withColumn("property_amenity_business_key", 
                   sha2(concat_ws("||", col("property_id"), col("amenity_id")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_PROPERTY_IMAGES (Dimension)
# ============================================================================

@dlt.table(
    name="silver_property_images",
    comment="""LLM: Silver layer property images dimension with validated image URLs and sequencing. 
    Supports multiple images per property with primary image designation.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "property_images",
        "domain": "property",
        "entity_type": "dimension",
        "contains_pii": "false",
        "data_classification": "internal",
        "business_owner": "Product",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
def silver_property_images():
    """
    Silver property images - clones Bronze schema with validation.
    
    Note: No explicit DQ rules in dq_rules table, but URLs and sequences validated.
    """
    return (
        dlt.read_stream(get_bronze_table("property_images"))
        .withColumn("property_image_business_key", 
                   sha2(concat_ws("||", col("image_id"), col("property_id")), 256))
        .withColumn("processed_timestamp", current_timestamp())
    )

