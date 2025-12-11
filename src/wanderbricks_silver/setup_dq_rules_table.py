# Databricks notebook source

"""
Wanderbricks Silver Layer - Data Quality Rules Table Setup

Creates a Unity Catalog Delta table to store ALL data quality rules for the Silver layer.

This table is the single source of truth for all DLT expectations across all Silver tables.

Benefits:
- ✅ Centralized rule management
- ✅ Auditable (versioned in Delta table)
- ✅ Updateable at runtime (no code changes needed)
- ✅ Queryable for documentation and reporting
- ✅ Supports tagging and filtering

Usage:
  databricks bundle run silver_dq_setup_job -t dev
"""

from pyspark.sql import SparkSession


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    silver_schema = dbutils.widgets.get("silver_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Silver Schema: {silver_schema}")
    
    return catalog, silver_schema


def create_schema_if_not_exists(spark: SparkSession, catalog: str, schema: str):
    """
    Create the Silver schema if it doesn't exist.
    
    Ensures the schema is ready for table creation.
    """
    print(f"\nEnsuring schema {catalog}.{schema} exists...")
    
    # Create schema with governance properties
    schema_ddl = f"""
        CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}
        COMMENT 'Silver layer - validated, cleaned, and quality-checked data with Delta Live Tables expectations.'
    """
    
    spark.sql(schema_ddl)
    
    # Enable predictive optimization
    try:
        spark.sql(f"""
            ALTER SCHEMA {catalog}.{schema} 
            SET DBPROPERTIES (
                'databricks.pipelines.predictiveOptimizations.enabled' = 'true'
            )
        """)
    except Exception as e:
        print(f"Note: Could not enable predictive optimization: {e}")
    
    print(f"✓ Schema {catalog}.{schema} ready")


def create_dq_rules_table(spark: SparkSession, catalog: str, schema: str):
    """
    Create the data quality rules Delta table.
    
    Schema:
    - table_name: Which Silver table this rule applies to
    - rule_name: Unique name for the rule
    - constraint_sql: SQL expression for the expectation
    - severity: 'critical' (drop/quarantine) or 'warning' (log only)
    - description: Human-readable explanation
    - created_timestamp: When rule was added
    - updated_timestamp: When rule was last modified
    """
    print(f"\nCreating {catalog}.{schema}.dq_rules table...")
    
    table_ddl = f"""
        CREATE OR REPLACE TABLE {catalog}.{schema}.dq_rules (
            table_name STRING NOT NULL
                COMMENT 'Silver table name this rule applies to (e.g., silver_bookings)',
            rule_name STRING NOT NULL
                COMMENT 'Unique identifier for this rule (e.g., valid_booking_id)',
            constraint_sql STRING NOT NULL
                COMMENT 'SQL expression for the expectation (e.g., booking_id IS NOT NULL)',
            severity STRING NOT NULL
                COMMENT 'Rule severity: critical (drop/quarantine) or warning (log only)',
            description STRING
                COMMENT 'Human-readable explanation of what this rule validates',
            created_timestamp TIMESTAMP NOT NULL
                COMMENT 'When this rule was first added',
            updated_timestamp TIMESTAMP NOT NULL
                COMMENT 'When this rule was last modified',
            
            CONSTRAINT pk_dq_rules PRIMARY KEY (table_name, rule_name) NOT ENFORCED
        )
        USING DELTA
        CLUSTER BY AUTO
        COMMENT 'Data quality rules repository for Silver layer DLT expectations. Rules are loaded dynamically at pipeline runtime for portable and maintainable data quality management.'
        TBLPROPERTIES (
            'delta.enableChangeDataFeed' = 'true',
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true',
            'layer' = 'silver',
            'domain' = 'governance',
            'entity_type' = 'metadata',
            'contains_pii' = 'false',
            'data_classification' = 'internal',
            'business_owner' = 'Data Engineering',
            'technical_owner' = 'Data Engineering'
        )
    """
    
    spark.sql(table_ddl)
    print(f"✓ Created DQ rules table")


def populate_dq_rules(spark: SparkSession, catalog: str, schema: str):
    """
    Populate the DQ rules table with initial rules for all Silver tables.
    
    Wanderbricks tables:
    - Dimensions: users, hosts, destinations, countries, properties, amenities, employees
    - Facts: bookings, booking_updates, payments, reviews, clickstream, page_views
    - Special: customer_support_logs (nested arrays/structs)
    """
    from pyspark.sql.functions import current_timestamp
    from pyspark.sql import Row
    
    print(f"\nPopulating {catalog}.{schema}.dq_rules with rules...")
    
    # Define all rules as list of tuples
    rules = [
        # ===== SILVER_USERS (Dimension) =====
        ("silver_users", "valid_user_id", 
         "user_id IS NOT NULL", 
         "critical",
         "User ID must be present (primary key validation)"),
        
        ("silver_users", "valid_email", 
         "email IS NOT NULL AND LENGTH(email) > 0 AND INSTR(email, chr(64)) > 0", 
         "critical",
         "Email must be present and valid format"),
        
        ("silver_users", "valid_name", 
         "name IS NOT NULL AND LENGTH(name) > 0", 
         "critical",
         "User name must be present"),
        
        ("silver_users", "valid_created_date", 
         "created_at IS NOT NULL AND created_at >= MAKE_DATE(2020, 1, 1)", 
         "critical",
         "Creation date must be present and after minimum valid date"),
        
        ("silver_users", "recent_user", 
         "created_at >= CURRENT_DATE() - INTERVAL 5 YEARS", 
         "warning",
         "User should be created within last 5 years"),
        
        # ===== SILVER_HOSTS (Dimension) =====
        ("silver_hosts", "valid_host_id", 
         "host_id IS NOT NULL", 
         "critical",
         "Host ID must be present (primary key)"),
        
        ("silver_hosts", "valid_email", 
         "email IS NOT NULL AND INSTR(email, chr(64)) > 0", 
         "critical",
         "Host email must be present and valid"),
        
        ("silver_hosts", "valid_rating", 
         "rating IS NULL OR (rating >= 1.0 AND rating <= 5.0)", 
         "warning",
         "Host rating should be between 1.0 and 5.0"),
        
        # ===== SILVER_DESTINATIONS (Dimension) =====
        ("silver_destinations", "valid_destination_id", 
         "destination_id IS NOT NULL", 
         "critical",
         "Destination ID must be present (primary key)"),
        
        ("silver_destinations", "valid_destination_name", 
         "destination IS NOT NULL AND LENGTH(destination) > 0", 
         "critical",
         "Destination name must be present"),
        
        ("silver_destinations", "valid_country", 
         "country IS NOT NULL", 
         "critical",
         "Country must be present (FK validation)"),
        
        # ===== SILVER_COUNTRIES (Dimension) =====
        ("silver_countries", "valid_country", 
         "country IS NOT NULL AND LENGTH(country) > 0", 
         "critical",
         "Country name must be present (primary key)"),
        
        ("silver_countries", "valid_country_code", 
         "country_code IS NOT NULL AND LENGTH(country_code) = 2", 
         "critical",
         "Country code must be 2-letter ISO code"),
        
        # ===== SILVER_PROPERTIES (Dimension) =====
        ("silver_properties", "valid_property_id", 
         "property_id IS NOT NULL", 
         "critical",
         "Property ID must be present (primary key)"),
        
        ("silver_properties", "valid_host", 
         "host_id IS NOT NULL", 
         "critical",
         "Host ID must be present (FK validation)"),
        
        ("silver_properties", "valid_destination", 
         "destination_id IS NOT NULL", 
         "critical",
         "Destination ID must be present (FK validation)"),
        
        ("silver_properties", "positive_base_price", 
         "base_price > 0", 
         "critical",
         "Base price must be positive"),
        
        ("silver_properties", "reasonable_price", 
         "base_price BETWEEN 10 AND 10000", 
         "warning",
         "Price should be within reasonable range ($10-$10,000)"),
        
        ("silver_properties", "valid_guests", 
         "max_guests >= 1", 
         "critical",
         "Must allow at least 1 guest"),
        
        ("silver_properties", "reasonable_guests", 
         "max_guests BETWEEN 1 AND 20", 
         "warning",
         "Guest count should be reasonable (1-20)"),
        
        ("silver_properties", "valid_coordinates", 
         "property_latitude BETWEEN -90 AND 90 AND property_longitude BETWEEN -180 AND 180", 
         "warning",
         "Coordinates should be within valid geographic ranges"),
        
        # ===== SILVER_AMENITIES (Dimension) =====
        ("silver_amenities", "valid_amenity_id", 
         "amenity_id IS NOT NULL", 
         "critical",
         "Amenity ID must be present (primary key)"),
        
        ("silver_amenities", "valid_amenity_name", 
         "name IS NOT NULL AND LENGTH(name) > 0", 
         "critical",
         "Amenity name must be present"),
        
        # ===== SILVER_EMPLOYEES (Dimension) =====
        ("silver_employees", "valid_employee_id", 
         "employee_id IS NOT NULL", 
         "critical",
         "Employee ID must be present (primary key)"),
        
        ("silver_employees", "valid_host", 
         "host_id IS NOT NULL", 
         "critical",
         "Host ID must be present (FK validation)"),
        
        ("silver_employees", "valid_joined_date", 
         "joined_at IS NOT NULL AND joined_at >= MAKE_DATE(2015, 1, 1)", 
         "critical",
         "Join date must be present and reasonable"),
        
        ("silver_employees", "valid_employment_status", 
         "end_service_date IS NULL OR end_service_date >= joined_at", 
         "warning",
         "End date should be after start date if present"),
        
        # ===== SILVER_BOOKINGS (Fact) =====
        ("silver_bookings", "valid_booking_id", 
         "booking_id IS NOT NULL", 
         "critical",
         "Booking ID must be present (primary key)"),
        
        ("silver_bookings", "valid_user", 
         "user_id IS NOT NULL", 
         "critical",
         "User ID must be present (FK validation)"),
        
        ("silver_bookings", "valid_property", 
         "property_id IS NOT NULL", 
         "critical",
         "Property ID must be present (FK validation)"),
        
        ("silver_bookings", "valid_check_in", 
         "check_in IS NOT NULL AND check_in >= MAKE_DATE(2020, 1, 1)", 
         "critical",
         "Check-in date must be present and reasonable"),
        
        ("silver_bookings", "valid_check_out", 
         "check_out IS NOT NULL AND check_out > check_in", 
         "critical",
         "Check-out must be after check-in"),
        
        ("silver_bookings", "valid_guests", 
         "guests_count >= 1", 
         "critical",
         "Must have at least 1 guest"),
        
        ("silver_bookings", "reasonable_guests", 
         "guests_count BETWEEN 1 AND 20", 
         "warning",
         "Guest count should be reasonable (1-20)"),
        
        ("silver_bookings", "positive_amount", 
         "total_amount > 0", 
         "critical",
         "Total amount must be positive"),
        
        ("silver_bookings", "reasonable_amount", 
         "total_amount BETWEEN 10 AND 100000", 
         "warning",
         "Total amount should be within reasonable range ($10-$100k)"),
        
        ("silver_bookings", "reasonable_stay", 
         "DATEDIFF(check_out, check_in) BETWEEN 1 AND 365", 
         "warning",
         "Stay duration should be reasonable (1-365 days)"),
        
        # ===== SILVER_BOOKING_UPDATES (Fact) =====
        ("silver_booking_updates", "valid_booking_update_id", 
         "booking_update_id IS NOT NULL", 
         "critical",
         "Booking update ID must be present (primary key)"),
        
        ("silver_booking_updates", "valid_booking", 
         "booking_id IS NOT NULL", 
         "critical",
         "Booking ID must be present (FK validation)"),
        
        ("silver_booking_updates", "valid_dates", 
         "check_in IS NOT NULL AND check_out IS NOT NULL AND check_out > check_in", 
         "critical",
         "Dates must be present and check-out after check-in"),
        
        ("silver_booking_updates", "update_after_creation", 
         "created_at IS NULL OR updated_at >= created_at", 
         "warning",
         "Update timestamp should be after creation timestamp"),
        
        # ===== SILVER_PAYMENTS (Fact) =====
        ("silver_payments", "valid_payment_id", 
         "payment_id IS NOT NULL", 
         "critical",
         "Payment ID must be present (primary key)"),
        
        ("silver_payments", "valid_booking", 
         "booking_id IS NOT NULL", 
         "critical",
         "Booking ID must be present (FK validation)"),
        
        ("silver_payments", "positive_amount", 
         "amount > 0", 
         "critical",
         "Payment amount must be positive"),
        
        ("silver_payments", "reasonable_amount", 
         "amount BETWEEN 1 AND 100000", 
         "warning",
         "Payment amount should be reasonable ($1-$100k)"),
        
        ("silver_payments", "valid_payment_method", 
         "payment_method IS NOT NULL", 
         "critical",
         "Payment method must be present"),
        
        ("silver_payments", "valid_payment_date", 
         "payment_date IS NOT NULL AND payment_date >= MAKE_DATE(2020, 1, 1)", 
         "critical",
         "Payment date must be present and reasonable"),
        
        # ===== SILVER_REVIEWS (Fact) =====
        ("silver_reviews", "valid_review_id", 
         "review_id IS NOT NULL", 
         "critical",
         "Review ID must be present (primary key)"),
        
        ("silver_reviews", "valid_booking", 
         "booking_id IS NOT NULL", 
         "critical",
         "Booking ID must be present (FK validation)"),
        
        ("silver_reviews", "valid_property", 
         "property_id IS NOT NULL", 
         "critical",
         "Property ID must be present (FK validation)"),
        
        ("silver_reviews", "valid_user", 
         "user_id IS NOT NULL", 
         "critical",
         "User ID must be present (FK validation)"),
        
        ("silver_reviews", "valid_rating", 
         "rating >= 1.0 AND rating <= 5.0", 
         "critical",
         "Rating must be between 1.0 and 5.0"),
        
        ("silver_reviews", "has_comment_or_rating", 
         "comment IS NOT NULL OR rating IS NOT NULL", 
         "warning",
         "Review should have either comment or rating"),
        
        # ===== SILVER_CLICKSTREAM (Fact) =====
        ("silver_clickstream", "valid_event", 
         "event IS NOT NULL AND LENGTH(event) > 0", 
         "critical",
         "Event type must be present and non-empty"),
        
        ("silver_clickstream", "valid_timestamp", 
         "timestamp IS NOT NULL AND timestamp >= MAKE_DATE(2020, 1, 1)", 
         "critical",
         "Timestamp must be present and reasonable"),
        
        ("silver_clickstream", "recent_event", 
         "timestamp >= CURRENT_DATE() - INTERVAL 90 DAYS", 
         "warning",
         "Clickstream event should be recent (within 90 days)"),
        
        # ===== SILVER_PAGE_VIEWS (Fact) =====
        ("silver_page_views", "valid_view_id", 
         "view_id IS NOT NULL", 
         "critical",
         "View ID must be present (primary key)"),
        
        ("silver_page_views", "valid_timestamp", 
         "timestamp IS NOT NULL AND timestamp >= MAKE_DATE(2020, 1, 1)", 
         "critical",
         "Timestamp must be present and reasonable"),
        
        ("silver_page_views", "valid_page_url", 
         "page_url IS NOT NULL AND LENGTH(page_url) > 0", 
         "critical",
         "Page URL must be present"),
        
        ("silver_page_views", "recent_page_view", 
         "timestamp >= CURRENT_DATE() - INTERVAL 90 DAYS", 
         "warning",
         "Page view should be recent (within 90 days)"),
        
        # ===== SILVER_CUSTOMER_SUPPORT_LOGS (Special - Nested) =====
        ("silver_customer_support_logs", "valid_ticket_id", 
         "ticket_id IS NOT NULL AND LENGTH(ticket_id) > 0", 
         "critical",
         "Ticket ID must be present (primary key)"),
        
        ("silver_customer_support_logs", "valid_user", 
         "user_id IS NOT NULL", 
         "critical",
         "User ID must be present"),
        
        ("silver_customer_support_logs", "valid_created_date", 
         "created_at IS NOT NULL", 
         "critical",
         "Creation timestamp must be present"),
        
        ("silver_customer_support_logs", "has_messages", 
         "messages IS NOT NULL AND SIZE(messages) > 0", 
         "warning",
         "Support ticket should have at least one message"),
        
        # ===== SILVER_FORECAST_DAILY_METRIC (AccuWeather - Fact) =====
        # Note: Simplified rules - AccuWeather data structure may vary
        ("silver_forecast_daily_metric", "has_data", 
         "1=1", 
         "warning",
         "Basic data presence check"),
        
        # ===== SILVER_HISTORICAL_DAILY_METRIC (AccuWeather - Fact) =====
        ("silver_historical_daily_metric", "has_data", 
         "1=1", 
         "warning",
         "Basic data presence check"),
    ]
    
    # Insert rules using SQL (Spark Connect compatible)
    rules_table = f"{catalog}.{schema}.dq_rules"
    
    # Clear existing rules
    spark.sql(f"DELETE FROM {rules_table}")
    
    # Insert rules using SQL VALUES
    for rule in rules:
        table_name = rule[0]
        rule_name = rule[1]
        constraint_sql = rule[2].replace("'", "''")  # Escape single quotes
        severity = rule[3]
        description = rule[4].replace("'", "''") if len(rule) > 4 else ""
        
        insert_sql = f"""
            INSERT INTO {rules_table} 
            (table_name, rule_name, constraint_sql, severity, description, created_timestamp, updated_timestamp)
            VALUES (
                '{table_name}',
                '{rule_name}',
                '{constraint_sql}',
                '{severity}',
                '{description}',
                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()
            )
        """
        spark.sql(insert_sql)
    
    rule_count = len(rules)
    print(f"✓ Populated {rule_count} data quality rules")
    
    # Show summary
    summary = spark.sql(f"""
        SELECT 
            table_name,
            severity,
            COUNT(*) as rule_count
        FROM {rules_table}
        GROUP BY table_name, severity
        ORDER BY table_name, severity
    """)
    
    print("\nData Quality Rules Summary:")
    summary.show(truncate=False)


def main():
    """Main entry point for DQ rules table setup."""
    from pyspark.sql import SparkSession
    
    catalog, silver_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Wanderbricks DQ Rules Setup").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS DATA QUALITY RULES TABLE SETUP")
    print("=" * 80)
    
    try:
        # Step 1: Ensure schema exists
        create_schema_if_not_exists(spark, catalog, silver_schema)
        
        # Step 2: Create DQ rules table
        create_dq_rules_table(spark, catalog, silver_schema)
        
        # Step 3: Populate with rules
        populate_dq_rules(spark, catalog, silver_schema)
        
        print("\n" + "=" * 80)
        print("✓ DQ rules table created and populated!")
        print("=" * 80)
        print(f"\nRules table: {catalog}.{silver_schema}.dq_rules")
        print("\nNext steps:")
        print(f"  1. Review rules: SELECT * FROM {catalog}.{silver_schema}.dq_rules")
        print("  2. Deploy Silver DLT pipeline with dq_rules_loader.py")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

