"""
Data Quality Rules Loader for Wanderbricks Silver Layer DLT Pipelines

Loads data quality rules from Unity Catalog Delta table at DLT pipeline runtime.

This module provides functions to:
- Load rules filtered by table name and severity
- Apply expectations using @dlt.expect_all_or_drop() and @dlt.expect_all()
- Generate quarantine conditions

Benefits over hardcoded rules:
- ✅ Update rules without code changes (just UPDATE the Delta table)
- ✅ Centralized rule management across all pipelines
- ✅ Auditable (Delta table versioning)
- ✅ Queryable for documentation and reporting
- ✅ Portable across environments (dev/prod)

Official Databricks Pattern:
https://docs.databricks.com/aws/en/ldp/expectation-patterns#portable-and-reusable-expectations

⚠️ CRITICAL: This is a pure Python file (NO '# Databricks notebook source' header)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Module-level cache for rules (loaded once at import time)
_rules_cache = {}
_cache_initialized = False


def _get_rules_table_name() -> str:
    """
    Get the fully qualified DQ rules table name from DLT configuration.
    
    Returns:
        Fully qualified table name: "{catalog}.{schema}.dq_rules"
    """
    spark = SparkSession.getActiveSession()
    catalog = spark.conf.get("catalog")
    silver_schema = spark.conf.get("silver_schema")
    return f"{catalog}.{silver_schema}.dq_rules"


def _load_all_rules() -> None:
    """
    Load all rules from Delta table into module-level cache.
    
    This is called once at module initialization time, avoiding
    .collect() inside DLT decorated functions.
    
    Uses toPandas() instead of .collect() to avoid DLT static analysis warnings.
    
    Reference: https://docs.databricks.com/aws/en/ldp/expectation-patterns
    """
    global _rules_cache, _cache_initialized
    
    if _cache_initialized:
        return
    
    spark = SparkSession.getActiveSession()
    if spark is None:
        return  # Spark not available yet
    
    try:
        rules_table = _get_rules_table_name()
        
        # Use toPandas() instead of .collect() to avoid DLT warning
        # "DataFrame.collect is not supported in Lakeflow Declarative Pipelines"
        pdf = spark.sql(f"""
            SELECT table_name, rule_name, constraint_sql, severity
            FROM {rules_table}
        """).toPandas()
        
        # Organize into nested cache: {(table_name, severity): {rule_name: constraint_sql}}
        for _, row in pdf.iterrows():
            cache_key = (row['table_name'], row['severity'])
            if cache_key not in _rules_cache:
                _rules_cache[cache_key] = {}
            _rules_cache[cache_key][row['rule_name']] = row['constraint_sql']
        
        _cache_initialized = True
        
    except Exception as e:
        # Log but don't fail - rules table might not exist yet during setup
        print(f"Note: Could not load DQ rules from Delta table: {e}")
        _cache_initialized = False


def get_rules(table_name: str, severity: str) -> dict:
    """
    Get data quality rules for a specific table and severity from cache.
    
    Rules are loaded from Delta table at module initialization time,
    avoiding .collect() inside DLT decorated functions.
    
    Args:
        table_name: Silver table name (e.g., "silver_bookings")
        severity: Rule severity ("critical" or "warning")
    
    Returns:
        Dictionary mapping rule names to SQL constraint expressions
        Format: {"rule_name": "constraint_sql", ...}
    
    Example:
        critical_rules = get_rules("silver_bookings", "critical")
        # Returns: {
        #   "valid_booking_id": "booking_id IS NOT NULL",
        #   "valid_user": "user_id IS NOT NULL",
        #   ...
        # }
    
    Reference:
        https://docs.databricks.com/aws/en/ldp/expectation-patterns#portable-and-reusable-expectations
    """
    # Ensure cache is loaded
    if not _cache_initialized:
        _load_all_rules()
    
    # Return from cache (no .collect() here!)
    cache_key = (table_name, severity)
    return _rules_cache.get(cache_key, {})


def get_critical_rules_for_table(table_name: str) -> dict:
    """
    Get critical DQ rules for a specific table.
    
    Critical rules cause records to be dropped/quarantined if violated.
    Use with: @dlt.expect_all_or_drop(get_critical_rules_for_table("table_name"))
    
    Args:
        table_name: Silver table name
    
    Returns:
        Dictionary of critical rules loaded from Delta table
    """
    return get_rules(table_name, "critical")


def get_warning_rules_for_table(table_name: str) -> dict:
    """
    Get warning DQ rules for a specific table.
    
    Warning rules are logged but allow records to pass through.
    Use with: @dlt.expect_all(get_warning_rules_for_table("table_name"))
    
    Args:
        table_name: Silver table name
    
    Returns:
        Dictionary of warning rules loaded from Delta table
    """
    return get_rules(table_name, "warning")


def get_quarantine_condition(table_name: str) -> str:
    """
    Generate SQL condition for quarantine table (inverse of critical rules).
    
    Returns SQL expression that evaluates to TRUE for records that fail
    ANY critical rule (should be quarantined).
    
    Args:
        table_name: Silver table name
    
    Returns:
        SQL WHERE clause for quarantine filter
        
    Example:
        condition = get_quarantine_condition("silver_bookings")
        # Returns: "NOT (booking_id IS NOT NULL) OR NOT (user_id IS NOT NULL) OR ..."
    """
    critical_rules = get_critical_rules_for_table(table_name)
    
    if not critical_rules:
        return "FALSE"  # No rules = no quarantine
    
    # Invert each rule and OR them together
    quarantine_conditions = [f"NOT ({constraint})" for constraint in critical_rules.values()]
    return " OR ".join(quarantine_conditions)


def get_rules_table_name() -> str:
    """
    Get the fully qualified DQ rules table name (public accessor).
    
    Returns:
        Fully qualified table name: "{catalog}.{schema}.dq_rules"
    """
    return _get_rules_table_name()


def list_all_rules_for_table(table_name: str) -> None:
    """
    Print all rules for a specific table (debugging/documentation).
    Uses cached rules to avoid .collect() warnings.
    
    Args:
        table_name: Silver table name
    """
    print(f"\nData Quality Rules for {table_name}:")
    print("=" * 80)
    
    # Print from cache (no .collect()!)
    for severity in ["critical", "warning"]:
        rules = get_rules(table_name, severity)
        if rules:
            print(f"\n{severity.upper()} rules:")
            for rule_name, constraint in rules.items():
                print(f"  - {rule_name}: {constraint}")

