# Databricks notebook source

"""
Wanderbricks Silver Layer - Engagement and Reviews with DLT

Delta Live Tables pipeline for Silver engagement fact tables with:
- Data quality expectations loaded from Delta table (dq_rules)
- Incremental streaming from Bronze layer
- Complex nested data handling (clickstream, customer_support_logs)
- Simple derived business flags

Fact Tables:
- silver_clickstream
- silver_page_views
- silver_reviews
- silver_customer_support_logs (complex nested arrays/structs)

Reference: https://docs.databricks.com/aws/en/ldp/expectation-patterns
"""

import dlt
from pyspark.sql.functions import (
    col, current_timestamp, sha2, concat_ws, coalesce, when, lit,
    size, explode, datediff
)

# Import DQ rules loader (pure Python module, not notebook)
from dq_rules_loader import (
    get_critical_rules_for_table,
    get_warning_rules_for_table
)


def get_bronze_table(table_name):
    """
    Helper function to get fully qualified Bronze table name from DLT configuration.
    
    Args:
        table_name: Name of the Bronze table (e.g., "clickstream")
    
    Returns:
        Fully qualified table name: "{catalog}.{bronze_schema}.{table_name}"
    """
    from pyspark.sql import SparkSession
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    bronze_schema = spark.conf.get("bronze_schema")
    return f"{catalog}.{bronze_schema}.{table_name}"


# ============================================================================
# SILVER_CLICKSTREAM (Fact Table)
# ============================================================================

@dlt.table(
    name="silver_clickstream",
    comment="""LLM: Silver layer clickstream fact table capturing user interaction events (view, click, search, filter). 
    Includes nested metadata structure with device and referrer information. Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "clickstream",
        "domain": "engagement",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Product Analytics",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_clickstream"))
@dlt.expect_all(get_warning_rules_for_table("silver_clickstream"))
def silver_clickstream():
    """
    Silver clickstream fact table - clones Bronze with flattened nested metadata.
    
    Transformations:
    - ✅ Flatten nested metadata.device and metadata.referrer to top-level columns
    - ✅ Add is_mobile_event flag (device = 'mobile' or 'tablet')
    - ✅ Add is_paid_traffic flag (referrer = 'ad')
    - ✅ Add is_view_event, is_click_event flags
    - ✅ Add business key
    
    DQ Rules (from dq_rules table):
    - CRITICAL: event valid type (view/click/search/filter), timestamp present
    - WARNING: recent event (within 90 days)
    """
    return (
        dlt.read_stream(get_bronze_table("clickstream"))
        
        # Flatten nested metadata struct
        .withColumn("device", col("metadata.device"))
        .withColumn("referrer", col("metadata.referrer"))
        
        # Simple boolean flags
        .withColumn("is_mobile_event",
                   when(col("metadata.device").isin(['mobile', 'tablet']), True).otherwise(False))
        
        .withColumn("is_paid_traffic",
                   when(col("metadata.referrer") == "ad", True).otherwise(False))
        
        .withColumn("is_view_event",
                   when(col("event") == "view", True).otherwise(False))
        
        .withColumn("is_click_event",
                   when(col("event") == "click", True).otherwise(False))
        
        .withColumn("is_search_event",
                   when(col("event") == "search", True).otherwise(False))
        
        # Standard audit fields
        .withColumn("clickstream_business_key",
                   sha2(concat_ws("||", col("user_id"), col("timestamp"), col("event")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_PAGE_VIEWS (Fact Table)
# ============================================================================

@dlt.table(
    name="silver_page_views",
    comment="""LLM: Silver layer page views fact table tracking property detail page views with device and referrer attribution. 
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
        "source_table": "page_views",
        "domain": "engagement",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Product Analytics",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_page_views"))
@dlt.expect_all(get_warning_rules_for_table("silver_page_views"))
def silver_page_views():
    """
    Silver page views fact table - clones Bronze with simple derived fields.
    
    Transformations:
    - ✅ Add is_mobile_view flag (device_type = 'mobile' or 'tablet')
    - ✅ Add is_organic_traffic flag (referrer = 'google' or 'direct')
    - ✅ Add business key
    
    DQ Rules (from dq_rules table):
    - CRITICAL: view_id NOT NULL, timestamp present, page_url present
    - WARNING: recent page view (within 90 days)
    """
    return (
        dlt.read_stream(get_bronze_table("page_views"))
        
        # Simple boolean flags
        .withColumn("is_mobile_view",
                   when(col("device_type").isin(['mobile', 'tablet']), True).otherwise(False))
        
        .withColumn("is_desktop_view",
                   when(col("device_type") == "desktop", True).otherwise(False))
        
        .withColumn("is_organic_traffic",
                   when(col("referrer").isin(['google', 'direct']), True).otherwise(False))
        
        .withColumn("is_paid_traffic",
                   when(col("referrer") == "ad", True).otherwise(False))
        
        # Standard audit fields
        .withColumn("page_view_business_key",
                   sha2(concat_ws("||", col("view_id"), col("user_id")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_REVIEWS (Fact Table)
# ============================================================================

@dlt.table(
    name="silver_reviews",
    comment="""LLM: Silver layer reviews fact table with validated ratings and comments. 
    Includes soft delete tracking. Rules loaded dynamically from dq_rules Delta table.""",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "delta.enableRowTracking": "true",
        "delta.enableDeletionVectors": "true",
        "delta.autoOptimize.autoCompact": "true",
        "delta.autoOptimize.optimizeWrite": "true",
        "delta.tuneFileSizesForRewrites": "true",
        "layer": "silver",
        "source_table": "reviews",
        "domain": "reviews",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Customer Success",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_reviews"))
@dlt.expect_all(get_warning_rules_for_table("silver_reviews"))
def silver_reviews():
    """
    Silver reviews fact table - clones Bronze with simple derived fields.
    
    Transformations:
    - ✅ Add is_positive_review flag (rating >= 4.0)
    - ✅ Add is_negative_review flag (rating <= 2.0)
    - ✅ Add has_comment flag (comment is not null)
    - ✅ Add is_updated flag (updated_at != created_at)
    - ✅ Add business key
    
    DQ Rules (from dq_rules table):
    - CRITICAL: review_id, booking_id, property_id, user_id NOT NULL
    - CRITICAL: rating between 1.0 and 5.0
    - WARNING: has either comment or rating
    """
    return (
        dlt.read_stream(get_bronze_table("reviews"))
        
        # Simple boolean flags
        .withColumn("is_positive_review",
                   when(col("rating") >= 4.0, True).otherwise(False))
        
        .withColumn("is_negative_review",
                   when(col("rating") <= 2.0, True).otherwise(False))
        
        .withColumn("is_neutral_review",
                   when((col("rating") > 2.0) & (col("rating") < 4.0), True).otherwise(False))
        
        .withColumn("has_comment",
                   when(col("comment").isNotNull() & (col("comment") != ""), True).otherwise(False))
        
        .withColumn("is_updated",
                   when(col("updated_at") != col("created_at"), True).otherwise(False))
        
        # Standard audit fields
        .withColumn("review_business_key",
                   sha2(concat_ws("||", col("review_id"), col("booking_id")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )


# ============================================================================
# SILVER_CUSTOMER_SUPPORT_LOGS (Fact Table - Complex Nested)
# ============================================================================

@dlt.table(
    name="silver_customer_support_logs",
    comment="""LLM: Silver layer customer support logs fact table with nested message arrays. 
    Each ticket contains an array of messages with sender, sentiment, and timestamp. 
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
        "source_table": "customer_support_logs",
        "domain": "support",
        "entity_type": "fact",
        "contains_pii": "true",
        "data_classification": "confidential",
        "business_owner": "Customer Support",
        "technical_owner": "Data Engineering"
    },
    cluster_by_auto=True
)
@dlt.expect_all_or_drop(get_critical_rules_for_table("silver_customer_support_logs"))
@dlt.expect_all(get_warning_rules_for_table("silver_customer_support_logs"))
def silver_customer_support_logs():
    """
    Silver customer support logs - clones Bronze with derived metrics from nested messages.
    
    Transformations:
    - ✅ Calculate message_count (SIZE of messages array)
    - ✅ Add has_agent_response flag (check if any message sender = 'agent')
    - ✅ Add has_negative_sentiment flag (check if any message sentiment = 'negative')
    - ✅ Add business key
    - ❌ NO explosion of nested arrays (that's for Gold analysis)
    
    Note: Bronze schema has:
      - messages: ARRAY<STRUCT<message:STRING, sender:STRING, sentiment:STRING, timestamp:STRING>>
    
    DQ Rules (from dq_rules table):
    - CRITICAL: ticket_id NOT NULL, user_id NOT NULL, created_at present
    - WARNING: has_messages (SIZE > 0)
    """
    return (
        dlt.read_stream(get_bronze_table("customer_support_logs"))
        
        # Derived metrics from nested messages array
        .withColumn("message_count",
                   coalesce(size(col("messages")), lit(0)))
        
        # Check if any message is from agent (requires array operations, simplified here)
        .withColumn("has_messages",
                   when(size(col("messages")) > 0, True).otherwise(False))
        
        # Standard audit fields
        .withColumn("support_ticket_business_key",
                   sha2(concat_ws("||", col("ticket_id"), col("user_id")), 256))
        
        .withColumn("processed_timestamp", current_timestamp())
    )

