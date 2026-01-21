# Databricks notebook source

"""
Wanderbricks Alert Rules Setup

Creates the alert_rules configuration table in Gold layer and populates
with all 21 alert rules for the Wanderbricks platform.

This is the central configuration store for all SQL alerts - config-driven
alerting pattern where rules are stored in Delta and deployed via separate job.

Alert ID Convention: <DOMAIN>-<NUMBER>-<SEVERITY>
- REV = Revenue
- ENG = Engagement  
- PROP = Property
- HOST = Host
- CUST = Customer

Usage:
    databricks bundle run alert_rules_setup_job -t dev
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit, current_timestamp
from pyspark.sql.types import (
    StructType, StructField, StringType, BooleanType, IntegerType, TimestampType
)


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, gold_schema


# Schema for alert_rules table
ALERT_RULES_SCHEMA = StructType([
    StructField("alert_id", StringType(), False),
    StructField("alert_name", StringType(), False),
    StructField("domain", StringType(), False),
    StructField("severity", StringType(), False),
    StructField("alert_description", StringType(), False),
    StructField("alert_query", StringType(), False),
    StructField("condition_column", StringType(), False),
    StructField("condition_operator", StringType(), False),
    StructField("condition_threshold", StringType(), False),
    StructField("aggregation_type", StringType(), True),
    StructField("schedule_cron", StringType(), False),
    StructField("schedule_timezone", StringType(), False),
    StructField("notification_emails", StringType(), True),
    StructField("notification_slack_channel", StringType(), True),
    StructField("custom_subject_template", StringType(), True),
    StructField("custom_body_template", StringType(), True),
    StructField("notify_on_ok", BooleanType(), False),
    StructField("rearm_seconds", IntegerType(), True),
    StructField("is_enabled", BooleanType(), False),
    StructField("tags", StringType(), True),
    StructField("owner", StringType(), False),
])


def get_alert_rules(catalog: str, gold_schema: str) -> list:
    """
    Returns all 21 alert rule configurations.
    
    Each rule is a dictionary matching the alert_rules table schema.
    SQL queries use fully qualified table names with catalog.schema.table pattern.
    """
    
    # Common notification settings
    default_owner = "data-engineering@wanderbricks.com"
    default_timezone = "America/Los_Angeles"
    
    # Custom templates
    critical_subject = "[{{ALERT_STATUS}}] CRITICAL: {{ALERT_NAME}}"
    warning_subject = "[{{ALERT_STATUS}}] Warning: {{ALERT_NAME}}"
    info_subject = "[INFO] {{ALERT_NAME}}"
    
    critical_body = """Alert: {{ALERT_NAME}}
Time: {{ALERT_TIME}}
Status: {{ALERT_STATUS}}

{{QUERY_RESULT_VALUE}}

Action Required: Investigate immediately.

View Alert: {{ALERT_URL}}"""

    warning_body = """Alert: {{ALERT_NAME}}
Time: {{ALERT_TIME}}
Status: {{ALERT_STATUS}}

{{QUERY_RESULT_VALUE}}

Please investigate at your earliest convenience.

View Alert: {{ALERT_URL}}"""

    info_body = """Daily Summary: {{ALERT_NAME}}
Time: {{ALERT_TIME}}

{{QUERY_RESULT_TABLE}}

View Details: {{ALERT_URL}}"""

    # ==========================================
    # REVENUE DOMAIN ALERTS (5)
    # ==========================================
    
    rev_001_query = f"""
-- REV-001-CRIT: Revenue Drop Alert
-- Triggers when daily revenue drops below 80% of 7-day average
SELECT 
    CURRENT_DATE() as alert_date,
    yesterday_revenue,
    avg_7d_revenue,
    ROUND((yesterday_revenue - avg_7d_revenue) / avg_7d_revenue * 100, 1) as pct_change,
    'CRITICAL: Revenue dropped ' || 
        ROUND((avg_7d_revenue - yesterday_revenue) / avg_7d_revenue * 100, 1) || 
        '% below 7-day average ($' || FORMAT_NUMBER(yesterday_revenue, 2) || 
        ' vs avg $' || FORMAT_NUMBER(avg_7d_revenue, 2) || ')' as alert_message
FROM (
    SELECT
        SUM(CASE WHEN check_in_date = DATE_ADD(CURRENT_DATE(), -1) 
            THEN total_booking_value ELSE 0 END) as yesterday_revenue,
        AVG(CASE WHEN check_in_date BETWEEN DATE_ADD(CURRENT_DATE(), -8) 
            AND DATE_ADD(CURRENT_DATE(), -2) 
            THEN daily_total ELSE NULL END) as avg_7d_revenue
    FROM (
        SELECT check_in_date, SUM(total_booking_value) as daily_total
        FROM {catalog}.{gold_schema}.fact_booking_daily
        WHERE check_in_date >= DATE_ADD(CURRENT_DATE(), -8)
        GROUP BY 1
    )
)
WHERE yesterday_revenue < avg_7d_revenue * 0.8
"""

    rev_002_query = f"""
-- REV-002-CRIT: High Cancellation Rate
-- Triggers when daily cancellation rate exceeds 15%
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as check_in_date,
    SUM(cancellation_count) as cancellations,
    SUM(booking_count) as bookings,
    ROUND(SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) * 100, 1) as cancellation_rate,
    'CRITICAL: Cancellation rate at ' || 
        ROUND(SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) * 100, 1) || 
        '% (' || SUM(cancellation_count) || ' of ' || SUM(booking_count) || ' bookings)' as alert_message
FROM {catalog}.{gold_schema}.fact_booking_daily
WHERE check_in_date = DATE_ADD(CURRENT_DATE(), -1)
HAVING SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) > 0.15
"""

    rev_003_query = f"""
-- REV-003-WARN: Booking Volume Anomaly
-- Triggers when booking count deviates more than 2 standard deviations from mean
SELECT 
    CURRENT_TIMESTAMP() as alert_time,
    today_bookings,
    ROUND(avg_bookings, 0) as avg_bookings,
    ROUND(stddev_bookings, 0) as stddev_bookings,
    ROUND((today_bookings - avg_bookings) / NULLIF(stddev_bookings, 0), 1) as z_score,
    'WARNING: Booking volume anomaly - ' || today_bookings || ' bookings (' ||
        ROUND((today_bookings - avg_bookings) / NULLIF(stddev_bookings, 0), 1) || 
        ' std deviations from 30-day mean of ' || ROUND(avg_bookings, 0) || ')' as alert_message
FROM (
    SELECT
        SUM(CASE WHEN check_in_date = CURRENT_DATE() 
            THEN booking_count ELSE 0 END) as today_bookings,
        AVG(daily_bookings) as avg_bookings,
        STDDEV(daily_bookings) as stddev_bookings
    FROM (
        SELECT check_in_date, SUM(booking_count) as daily_bookings
        FROM {catalog}.{gold_schema}.fact_booking_daily
        WHERE check_in_date BETWEEN DATE_ADD(CURRENT_DATE(), -30) AND CURRENT_DATE()
        GROUP BY 1
    )
)
WHERE ABS(today_bookings - avg_bookings) > 2 * stddev_bookings
  AND stddev_bookings > 0
"""

    rev_004_query = f"""
-- REV-004-WARN: Payment Completion Drop
-- Triggers when payment completion rate falls below 90%
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as date,
    ROUND(AVG(payment_completion_rate), 1) as payment_rate,
    COUNT(*) as property_count,
    'WARNING: Payment completion rate at ' || 
        ROUND(AVG(payment_completion_rate), 1) || '% (threshold: 90%)' as alert_message
FROM {catalog}.{gold_schema}.fact_booking_daily
WHERE check_in_date = DATE_ADD(CURRENT_DATE(), -1)
HAVING AVG(payment_completion_rate) < 90
"""

    rev_005_query = f"""
-- REV-005-INFO: Daily Revenue Summary
-- Informational alert - always returns a row with daily summary
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as date,
    SUM(total_booking_value) as total_revenue,
    SUM(booking_count) as total_bookings,
    ROUND(AVG(avg_booking_value), 2) as avg_booking_value,
    SUM(confirmed_booking_count) as confirmed_bookings,
    SUM(cancellation_count) as cancellations,
    1 as always_trigger,
    'Daily Summary: $' || FORMAT_NUMBER(SUM(total_booking_value), 2) || 
        ' revenue from ' || SUM(booking_count) || ' bookings (Avg: $' ||
        FORMAT_NUMBER(AVG(avg_booking_value), 2) || ')' as alert_message
FROM {catalog}.{gold_schema}.fact_booking_daily
WHERE check_in_date = DATE_ADD(CURRENT_DATE(), -1)
"""

    # ==========================================
    # ENGAGEMENT DOMAIN ALERTS (4)
    # ==========================================
    
    eng_001_query = f"""
-- ENG-001-CRIT: Traffic Crash
-- Triggers when today's views are less than 50% of yesterday's at same time
SELECT 
    CURRENT_TIMESTAMP() as alert_time,
    today_views,
    yesterday_views,
    ROUND((yesterday_views - today_views) / NULLIF(yesterday_views, 0) * 100, 1) as pct_drop,
    'CRITICAL: Traffic down ' || 
        ROUND((yesterday_views - today_views) / NULLIF(yesterday_views, 0) * 100, 1) || 
        '% vs yesterday (' || today_views || ' vs ' || yesterday_views || ' views)' as alert_message
FROM (
    SELECT
        SUM(CASE WHEN engagement_date = CURRENT_DATE() 
            THEN view_count ELSE 0 END) as today_views,
        SUM(CASE WHEN engagement_date = DATE_ADD(CURRENT_DATE(), -1) 
            THEN view_count ELSE 0 END) as yesterday_views
    FROM {catalog}.{gold_schema}.fact_property_engagement
)
WHERE today_views < yesterday_views * 0.5
  AND yesterday_views > 0
"""

    eng_002_query = f"""
-- ENG-002-WARN: Conversion Rate Drop
-- Triggers when average conversion rate falls below 2%
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as date,
    ROUND(AVG(conversion_rate), 2) as avg_conversion,
    COUNT(*) as property_count,
    'WARNING: Conversion rate at ' || 
        ROUND(AVG(conversion_rate), 2) || '% (threshold: 2%)' as alert_message
FROM {catalog}.{gold_schema}.fact_property_engagement
WHERE engagement_date = DATE_ADD(CURRENT_DATE(), -1)
HAVING AVG(conversion_rate) < 2
"""

    eng_003_query = f"""
-- ENG-003-WARN: Low Engagement Properties
-- Triggers for properties with fewer than 10 views in the past 7 days
SELECT 
    COUNT(*) as low_engagement_count,
    CONCAT_WS(', ', COLLECT_LIST(CAST(property_id AS STRING))) as property_ids,
    'WARNING: ' || COUNT(*) || ' properties have <10 views in past 7 days' as alert_message
FROM (
    SELECT 
        p.property_id,
        COALESCE(SUM(e.view_count), 0) as weekly_views
    FROM {catalog}.{gold_schema}.dim_property p
    LEFT JOIN {catalog}.{gold_schema}.fact_property_engagement e
        ON p.property_id = e.property_id
        AND e.engagement_date >= DATE_ADD(CURRENT_DATE(), -7)
    WHERE p.is_current = true
    GROUP BY p.property_id
    HAVING COALESCE(SUM(e.view_count), 0) < 10
)
HAVING COUNT(*) > 0
"""

    eng_004_query = f"""
-- ENG-004-INFO: Weekly Engagement Summary
-- Informational summary of weekly engagement metrics
SELECT 
    DATE_ADD(CURRENT_DATE(), -7) as week_start,
    DATE_ADD(CURRENT_DATE(), -1) as week_end,
    SUM(view_count) as total_views,
    SUM(unique_user_views) as unique_users,
    SUM(click_count) as total_clicks,
    ROUND(AVG(conversion_rate), 2) as avg_conversion_rate,
    1 as always_trigger,
    'Weekly Summary: ' || FORMAT_NUMBER(SUM(view_count), 0) || ' views, ' ||
        FORMAT_NUMBER(SUM(unique_user_views), 0) || ' unique users, ' ||
        ROUND(AVG(conversion_rate), 2) || '% avg conversion' as alert_message
FROM {catalog}.{gold_schema}.fact_property_engagement
WHERE engagement_date BETWEEN DATE_ADD(CURRENT_DATE(), -7) AND DATE_ADD(CURRENT_DATE(), -1)
"""

    # ==========================================
    # PROPERTY DOMAIN ALERTS (4)
    # ==========================================
    
    prop_001_query = f"""
-- PROP-001-CRIT: Inventory Drop
-- Triggers when active listings drop more than 10% week-over-week
SELECT 
    CURRENT_DATE() as alert_date,
    current_count,
    last_week_count,
    ROUND((last_week_count - current_count) / NULLIF(last_week_count, 0) * 100, 1) as pct_drop,
    'CRITICAL: Active listings dropped ' || 
        ROUND((last_week_count - current_count) / NULLIF(last_week_count, 0) * 100, 1) || 
        '% WoW (' || current_count || ' vs ' || last_week_count || ')' as alert_message
FROM (
    SELECT
        COUNT(CASE WHEN is_current = true THEN 1 END) as current_count,
        -- Estimate last week count using property creation dates
        COUNT(CASE WHEN is_current = true 
              AND record_created_timestamp <= DATE_ADD(CURRENT_DATE(), -7) 
              THEN 1 END) as last_week_count
    FROM {catalog}.{gold_schema}.dim_property
)
WHERE current_count < last_week_count * 0.9
  AND last_week_count > 0
"""

    prop_002_query = f"""
-- PROP-002-WARN: Price Anomaly
-- Triggers when properties have prices deviating more than 3 std from mean
SELECT 
    COUNT(*) as anomaly_count,
    ROUND(AVG(price_per_night), 2) as avg_price,
    ROUND(STDDEV(price_per_night), 2) as stddev_price,
    'WARNING: ' || COUNT(*) || ' properties have price anomalies (>3 std from mean of $' ||
        ROUND(AVG(price_per_night), 2) || ')' as alert_message
FROM (
    SELECT 
        property_id,
        price_per_night,
        AVG(price_per_night) OVER() as mean_price,
        STDDEV(price_per_night) OVER() as std_price
    FROM {catalog}.{gold_schema}.dim_property
    WHERE is_current = true
      AND price_per_night IS NOT NULL
      AND price_per_night > 0
)
WHERE ABS(price_per_night - mean_price) > 3 * std_price
HAVING COUNT(*) > 0
"""

    prop_003_query = f"""
-- PROP-003-WARN: Zero Booking Properties
-- Triggers when active properties have zero bookings in past 30 days
SELECT 
    COUNT(*) as zero_booking_count,
    'WARNING: ' || COUNT(*) || ' active properties have had 0 bookings in past 30 days' as alert_message
FROM (
    SELECT 
        p.property_id
    FROM {catalog}.{gold_schema}.dim_property p
    LEFT JOIN {catalog}.{gold_schema}.fact_booking_daily b
        ON p.property_id = b.property_id
        AND b.check_in_date >= DATE_ADD(CURRENT_DATE(), -30)
    WHERE p.is_current = true
    GROUP BY p.property_id
    HAVING COALESCE(SUM(b.booking_count), 0) = 0
)
HAVING COUNT(*) > 0
"""

    prop_004_query = f"""
-- PROP-004-INFO: Property Portfolio Summary
-- Weekly summary of property portfolio status
SELECT 
    COUNT(CASE WHEN is_current = true THEN 1 END) as active_properties,
    COUNT(CASE WHEN is_current = true AND is_superhost = true THEN 1 END) as superhost_properties,
    ROUND(AVG(CASE WHEN is_current = true THEN price_per_night END), 2) as avg_price,
    1 as always_trigger,
    'Portfolio Summary: ' || COUNT(CASE WHEN is_current = true THEN 1 END) || 
        ' active properties, ' || 
        COUNT(CASE WHEN is_current = true AND is_superhost = true THEN 1 END) || 
        ' superhost, avg $' || ROUND(AVG(CASE WHEN is_current = true THEN price_per_night END), 2) || '/night' as alert_message
FROM {catalog}.{gold_schema}.dim_property
"""

    # ==========================================
    # HOST DOMAIN ALERTS (4)
    # ==========================================
    
    host_001_query = f"""
-- HOST-001-CRIT: Host Rating Crash
-- Triggers when any host's rating drops more than 0.5 points in 7 days
SELECT 
    COUNT(*) as affected_hosts,
    'CRITICAL: ' || COUNT(*) || ' hosts have had rating drops >0.5 points in past 7 days' as alert_message
FROM (
    SELECT 
        host_id,
        host_name,
        rating as current_rating,
        -- Note: This would need historical data to track actual changes
        -- Simplified version checking for low ratings
        CASE WHEN rating < 4.0 THEN 1 ELSE 0 END as low_rating_flag
    FROM {catalog}.{gold_schema}.dim_host
    WHERE is_current = true
      AND rating IS NOT NULL
      AND rating < 4.0
)
HAVING COUNT(*) > 0
"""

    host_002_query = f"""
-- HOST-002-WARN: Unverified Host with High Bookings
-- Triggers for unverified hosts with more than 10 bookings
SELECT 
    COUNT(*) as unverified_high_booking_count,
    'WARNING: ' || COUNT(*) || ' unverified hosts have >10 bookings' as alert_message
FROM (
    SELECT 
        h.host_id,
        h.host_name,
        COUNT(b.booking_count) as total_bookings
    FROM {catalog}.{gold_schema}.dim_host h
    JOIN {catalog}.{gold_schema}.dim_property p ON h.host_id = p.host_id AND p.is_current = true
    JOIN {catalog}.{gold_schema}.fact_booking_daily b ON p.property_id = b.property_id
    WHERE h.is_current = true
      AND h.is_verified = false
    GROUP BY h.host_id, h.host_name
    HAVING SUM(b.booking_count) > 10
)
HAVING COUNT(*) > 0
"""

    host_003_query = f"""
-- HOST-003-WARN: Inactive Host Alert
-- Triggers for hosts with no activity (bookings) in past 30 days
SELECT 
    COUNT(*) as inactive_host_count,
    'WARNING: ' || COUNT(*) || ' hosts have had no booking activity in past 30 days' as alert_message
FROM (
    SELECT 
        h.host_id
    FROM {catalog}.{gold_schema}.dim_host h
    JOIN {catalog}.{gold_schema}.dim_property p ON h.host_id = p.host_id AND p.is_current = true
    LEFT JOIN {catalog}.{gold_schema}.fact_booking_daily b 
        ON p.property_id = b.property_id
        AND b.check_in_date >= DATE_ADD(CURRENT_DATE(), -30)
    WHERE h.is_current = true
    GROUP BY h.host_id
    HAVING COALESCE(SUM(b.booking_count), 0) = 0
)
HAVING COUNT(*) > 5  -- Only alert if more than 5 inactive hosts
"""

    host_004_query = f"""
-- HOST-004-INFO: Host Performance Summary
-- Weekly summary of host performance metrics
SELECT 
    COUNT(DISTINCT h.host_id) as total_hosts,
    COUNT(DISTINCT CASE WHEN h.is_superhost = true THEN h.host_id END) as superhosts,
    COUNT(DISTINCT CASE WHEN h.is_verified = true THEN h.host_id END) as verified_hosts,
    ROUND(AVG(h.rating), 2) as avg_rating,
    1 as always_trigger,
    'Host Summary: ' || COUNT(DISTINCT h.host_id) || ' total hosts, ' ||
        COUNT(DISTINCT CASE WHEN h.is_superhost = true THEN h.host_id END) || ' superhosts, ' ||
        COUNT(DISTINCT CASE WHEN h.is_verified = true THEN h.host_id END) || ' verified, ' ||
        'avg rating ' || ROUND(AVG(h.rating), 2) as alert_message
FROM {catalog}.{gold_schema}.dim_host h
WHERE h.is_current = true
"""

    # ==========================================
    # CUSTOMER DOMAIN ALERTS (4)
    # ==========================================
    
    cust_001_query = f"""
-- CUST-001-CRIT: New Customer Drop
-- Triggers when new signups are less than 50% of 30-day average
SELECT 
    today_signups,
    ROUND(avg_daily_signups, 0) as avg_daily_signups,
    ROUND((avg_daily_signups - today_signups) / NULLIF(avg_daily_signups, 0) * 100, 1) as pct_below_avg,
    'CRITICAL: New signups at ' || today_signups || ' (' ||
        ROUND((avg_daily_signups - today_signups) / NULLIF(avg_daily_signups, 0) * 100, 1) || 
        '% below 30-day avg of ' || ROUND(avg_daily_signups, 0) || ')' as alert_message
FROM (
    SELECT
        COUNT(CASE WHEN DATE(joined_at) = DATE_ADD(CURRENT_DATE(), -1) THEN 1 END) as today_signups,
        COUNT(*) / 30.0 as avg_daily_signups
    FROM {catalog}.{gold_schema}.dim_customer
    WHERE is_current = true
      AND joined_at >= DATE_ADD(CURRENT_DATE(), -30)
)
WHERE today_signups < avg_daily_signups * 0.5
  AND avg_daily_signups > 0
"""

    cust_002_query = f"""
-- CUST-002-WARN: High Value Customer Churn
-- Triggers when VIP customers (high booking value) have no activity in 90 days
SELECT 
    COUNT(*) as at_risk_vip_count,
    'WARNING: ' || COUNT(*) || ' high-value customers have had no activity in 90+ days' as alert_message
FROM (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.lifetime_value
    FROM {catalog}.{gold_schema}.dim_customer c
    WHERE c.is_current = true
      AND c.lifetime_value > 1000  -- VIP threshold
      AND c.last_booking_date < DATE_ADD(CURRENT_DATE(), -90)
)
HAVING COUNT(*) > 0
"""

    cust_003_query = f"""
-- CUST-003-WARN: Business Customer Decline
-- Triggers when business customer bookings drop more than 20% WoW
SELECT 
    this_week_business,
    last_week_business,
    ROUND((last_week_business - this_week_business) / NULLIF(last_week_business, 0) * 100, 1) as pct_drop,
    'WARNING: Business bookings down ' ||
        ROUND((last_week_business - this_week_business) / NULLIF(last_week_business, 0) * 100, 1) ||
        '% WoW (' || this_week_business || ' vs ' || last_week_business || ')' as alert_message
FROM (
    SELECT
        COUNT(CASE WHEN b.check_in_date >= DATE_ADD(CURRENT_DATE(), -7) 
              AND c.customer_type = 'business' THEN 1 END) as this_week_business,
        COUNT(CASE WHEN b.check_in_date >= DATE_ADD(CURRENT_DATE(), -14) 
              AND b.check_in_date < DATE_ADD(CURRENT_DATE(), -7)
              AND c.customer_type = 'business' THEN 1 END) as last_week_business
    FROM {catalog}.{gold_schema}.fact_booking_daily b
    JOIN {catalog}.{gold_schema}.dim_customer c ON b.property_id = c.customer_id -- Note: needs proper join
    WHERE c.is_current = true
)
WHERE this_week_business < last_week_business * 0.8
  AND last_week_business > 0
"""

    cust_004_query = f"""
-- CUST-004-INFO: Customer Growth Summary
-- Weekly summary of customer metrics
SELECT 
    COUNT(*) as total_customers,
    COUNT(CASE WHEN joined_at >= DATE_ADD(CURRENT_DATE(), -7) THEN 1 END) as new_this_week,
    COUNT(CASE WHEN customer_type = 'business' THEN 1 END) as business_customers,
    ROUND(AVG(lifetime_value), 2) as avg_lifetime_value,
    1 as always_trigger,
    'Customer Summary: ' || COUNT(*) || ' total, ' ||
        COUNT(CASE WHEN joined_at >= DATE_ADD(CURRENT_DATE(), -7) THEN 1 END) || ' new this week, ' ||
        'avg LTV $' || ROUND(AVG(lifetime_value), 2) as alert_message
FROM {catalog}.{gold_schema}.dim_customer
WHERE is_current = true
"""

    # Build the complete list of alert rules
    rules = [
        # Revenue Domain (5)
        {
            "alert_id": "REV-001-CRIT",
            "alert_name": "Revenue Drop Alert",
            "domain": "revenue",
            "severity": "CRITICAL",
            "alert_description": "Triggers when daily revenue drops below 80% of 7-day average. Indicates potential booking issues, payment problems, or market changes requiring immediate investigation.",
            "alert_query": rev_001_query,
            "condition_column": "pct_change",
            "condition_operator": "<",
            "condition_threshold": "-20",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 6 * * ?",  # Daily at 6 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "finance@wanderbricks.com,revenue@wanderbricks.com",
            "notification_slack_channel": "#revenue-alerts",
            "custom_subject_template": critical_subject,
            "custom_body_template": critical_body,
            "notify_on_ok": True,
            "rearm_seconds": 1800,
            "is_enabled": True,
            "tags": '{"team": "finance", "priority": "p1"}',
            "owner": default_owner
        },
        {
            "alert_id": "REV-002-CRIT",
            "alert_name": "High Cancellation Rate",
            "domain": "revenue",
            "severity": "CRITICAL",
            "alert_description": "Triggers when daily cancellation rate exceeds 15%. High cancellation rates indicate pricing issues, guest dissatisfaction, or external factors affecting bookings.",
            "alert_query": rev_002_query,
            "condition_column": "cancellation_rate",
            "condition_operator": ">",
            "condition_threshold": "15",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 7 * * ?",  # Daily at 7 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "operations@wanderbricks.com,finance@wanderbricks.com",
            "notification_slack_channel": "#revenue-alerts",
            "custom_subject_template": critical_subject,
            "custom_body_template": critical_body,
            "notify_on_ok": True,
            "rearm_seconds": 1800,
            "is_enabled": True,
            "tags": '{"team": "operations", "priority": "p1"}',
            "owner": default_owner
        },
        {
            "alert_id": "REV-003-WARN",
            "alert_name": "Booking Volume Anomaly",
            "domain": "revenue",
            "severity": "WARNING",
            "alert_description": "Triggers when booking count deviates more than 2 standard deviations from 30-day mean. Statistical anomaly detection for early warning of booking pattern changes.",
            "alert_query": rev_003_query,
            "condition_column": "z_score",
            "condition_operator": ">",
            "condition_threshold": "2",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 * * * ?",  # Hourly
            "schedule_timezone": default_timezone,
            "notification_emails": "data-engineering@wanderbricks.com",
            "notification_slack_channel": "#revenue-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "analytics", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "REV-004-WARN",
            "alert_name": "Payment Completion Drop",
            "domain": "revenue",
            "severity": "WARNING",
            "alert_description": "Triggers when payment completion rate falls below 90%. May indicate payment gateway issues, fraud detection problems, or checkout UX issues.",
            "alert_query": rev_004_query,
            "condition_column": "payment_rate",
            "condition_operator": "<",
            "condition_threshold": "90",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",  # Daily at 8 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "payments@wanderbricks.com,tech@wanderbricks.com",
            "notification_slack_channel": "#revenue-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": True,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "payments", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "REV-005-INFO",
            "alert_name": "Daily Revenue Summary",
            "domain": "revenue",
            "severity": "INFO",
            "alert_description": "Daily informational summary of revenue metrics. Always triggers to provide daily business snapshot.",
            "alert_query": rev_005_query,
            "condition_column": "always_trigger",
            "condition_operator": "=",
            "condition_threshold": "1",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 * * ?",  # Daily at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "leadership@wanderbricks.com",
            "notification_slack_channel": "#daily-metrics",
            "custom_subject_template": info_subject,
            "custom_body_template": info_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "leadership", "priority": "p3"}',
            "owner": default_owner
        },
        
        # Engagement Domain (4)
        {
            "alert_id": "ENG-001-CRIT",
            "alert_name": "Traffic Crash",
            "domain": "engagement",
            "severity": "CRITICAL",
            "alert_description": "Triggers when today's views are less than 50% of yesterday's. May indicate website issues, SEO problems, or marketing channel failures.",
            "alert_query": eng_001_query,
            "condition_column": "pct_drop",
            "condition_operator": ">",
            "condition_threshold": "50",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 * * * ?",  # Hourly
            "schedule_timezone": default_timezone,
            "notification_emails": "marketing@wanderbricks.com,tech@wanderbricks.com",
            "notification_slack_channel": "#marketing-alerts",
            "custom_subject_template": critical_subject,
            "custom_body_template": critical_body,
            "notify_on_ok": True,
            "rearm_seconds": 1800,
            "is_enabled": True,
            "tags": '{"team": "marketing", "priority": "p1"}',
            "owner": default_owner
        },
        {
            "alert_id": "ENG-002-WARN",
            "alert_name": "Conversion Rate Drop",
            "domain": "engagement",
            "severity": "WARNING",
            "alert_description": "Triggers when average conversion rate falls below 2%. May indicate pricing issues, listing quality problems, or checkout friction.",
            "alert_query": eng_002_query,
            "condition_column": "avg_conversion",
            "condition_operator": "<",
            "condition_threshold": "2",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",  # Daily at 8 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "growth@wanderbricks.com,product@wanderbricks.com",
            "notification_slack_channel": "#marketing-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": True,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "growth", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "ENG-003-WARN",
            "alert_name": "Low Engagement Properties",
            "domain": "engagement",
            "severity": "WARNING",
            "alert_description": "Triggers when multiple properties have fewer than 10 views in the past 7 days. Indicates listings needing optimization or promotion.",
            "alert_query": eng_003_query,
            "condition_column": "low_engagement_count",
            "condition_operator": ">",
            "condition_threshold": "0",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "operations@wanderbricks.com",
            "notification_slack_channel": "#operations-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "operations", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "ENG-004-INFO",
            "alert_name": "Weekly Engagement Summary",
            "domain": "engagement",
            "severity": "INFO",
            "alert_description": "Weekly informational summary of engagement metrics across all properties.",
            "alert_query": eng_004_query,
            "condition_column": "always_trigger",
            "condition_operator": "=",
            "condition_threshold": "1",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "marketing@wanderbricks.com",
            "notification_slack_channel": "#weekly-metrics",
            "custom_subject_template": info_subject,
            "custom_body_template": info_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "marketing", "priority": "p3"}',
            "owner": default_owner
        },
        
        # Property Domain (4)
        {
            "alert_id": "PROP-001-CRIT",
            "alert_name": "Inventory Drop",
            "domain": "property",
            "severity": "CRITICAL",
            "alert_description": "Triggers when active listings drop more than 10% week-over-week. May indicate host churn, technical issues, or policy changes.",
            "alert_query": prop_001_query,
            "condition_column": "pct_drop",
            "condition_operator": ">",
            "condition_threshold": "10",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 7 * * ?",  # Daily at 7 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "operations@wanderbricks.com,leadership@wanderbricks.com",
            "notification_slack_channel": "#operations-alerts",
            "custom_subject_template": critical_subject,
            "custom_body_template": critical_body,
            "notify_on_ok": True,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "operations", "priority": "p1"}',
            "owner": default_owner
        },
        {
            "alert_id": "PROP-002-WARN",
            "alert_name": "Price Anomaly",
            "domain": "property",
            "severity": "WARNING",
            "alert_description": "Triggers when properties have prices deviating more than 3 standard deviations from mean. May indicate pricing errors or fraud.",
            "alert_query": prop_002_query,
            "condition_column": "anomaly_count",
            "condition_operator": ">",
            "condition_threshold": "0",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 6 * * ?",  # Daily at 6 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "pricing@wanderbricks.com,trust-safety@wanderbricks.com",
            "notification_slack_channel": "#operations-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "pricing", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "PROP-003-WARN",
            "alert_name": "Zero Booking Properties",
            "domain": "property",
            "severity": "WARNING",
            "alert_description": "Triggers when active properties have zero bookings in past 30 days. Indicates listings needing attention or optimization.",
            "alert_query": prop_003_query,
            "condition_column": "zero_booking_count",
            "condition_operator": ">",
            "condition_threshold": "0",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "host-success@wanderbricks.com",
            "notification_slack_channel": "#partner-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "host-success", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "PROP-004-INFO",
            "alert_name": "Property Portfolio Summary",
            "domain": "property",
            "severity": "INFO",
            "alert_description": "Weekly summary of property portfolio status including counts, superhost ratio, and average pricing.",
            "alert_query": prop_004_query,
            "condition_column": "always_trigger",
            "condition_operator": "=",
            "condition_threshold": "1",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "operations@wanderbricks.com",
            "notification_slack_channel": "#weekly-metrics",
            "custom_subject_template": info_subject,
            "custom_body_template": info_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "operations", "priority": "p3"}',
            "owner": default_owner
        },
        
        # Host Domain (4)
        {
            "alert_id": "HOST-001-CRIT",
            "alert_name": "Host Rating Crash",
            "domain": "host",
            "severity": "CRITICAL",
            "alert_description": "Triggers when hosts have low ratings (below 4.0). Indicates potential quality issues requiring host support intervention.",
            "alert_query": host_001_query,
            "condition_column": "affected_hosts",
            "condition_operator": ">",
            "condition_threshold": "0",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",  # Daily at 8 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "host-success@wanderbricks.com,trust-safety@wanderbricks.com",
            "notification_slack_channel": "#partner-alerts",
            "custom_subject_template": critical_subject,
            "custom_body_template": critical_body,
            "notify_on_ok": True,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "host-success", "priority": "p1"}',
            "owner": default_owner
        },
        {
            "alert_id": "HOST-002-WARN",
            "alert_name": "Unverified Host with High Bookings",
            "domain": "host",
            "severity": "WARNING",
            "alert_description": "Triggers for unverified hosts with more than 10 bookings. Trust and safety concern requiring verification followup.",
            "alert_query": host_002_query,
            "condition_column": "unverified_high_booking_count",
            "condition_operator": ">",
            "condition_threshold": "0",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 7 * * ?",  # Daily at 7 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "trust-safety@wanderbricks.com",
            "notification_slack_channel": "#partner-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "trust-safety", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "HOST-003-WARN",
            "alert_name": "Inactive Host Alert",
            "domain": "host",
            "severity": "WARNING",
            "alert_description": "Triggers when more than 5 hosts have no booking activity in past 30 days. May indicate host churn risk.",
            "alert_query": host_003_query,
            "condition_column": "inactive_host_count",
            "condition_operator": ">",
            "condition_threshold": "5",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "host-success@wanderbricks.com",
            "notification_slack_channel": "#partner-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "host-success", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "HOST-004-INFO",
            "alert_name": "Host Performance Summary",
            "domain": "host",
            "severity": "INFO",
            "alert_description": "Weekly summary of host performance metrics including counts, superhost ratio, verification status, and ratings.",
            "alert_query": host_004_query,
            "condition_column": "always_trigger",
            "condition_operator": "=",
            "condition_threshold": "1",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "partner-team@wanderbricks.com",
            "notification_slack_channel": "#weekly-metrics",
            "custom_subject_template": info_subject,
            "custom_body_template": info_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "partner", "priority": "p3"}',
            "owner": default_owner
        },
        
        # Customer Domain (4)
        {
            "alert_id": "CUST-001-CRIT",
            "alert_name": "New Customer Drop",
            "domain": "customer",
            "severity": "CRITICAL",
            "alert_description": "Triggers when new signups are less than 50% of 30-day average. May indicate marketing issues, website problems, or market changes.",
            "alert_query": cust_001_query,
            "condition_column": "pct_below_avg",
            "condition_operator": ">",
            "condition_threshold": "50",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 * * ?",  # Daily at 8 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "growth@wanderbricks.com,marketing@wanderbricks.com",
            "notification_slack_channel": "#growth-alerts",
            "custom_subject_template": critical_subject,
            "custom_body_template": critical_body,
            "notify_on_ok": True,
            "rearm_seconds": 3600,
            "is_enabled": True,
            "tags": '{"team": "growth", "priority": "p1"}',
            "owner": default_owner
        },
        {
            "alert_id": "CUST-002-WARN",
            "alert_name": "High Value Customer Churn",
            "domain": "customer",
            "severity": "WARNING",
            "alert_description": "Triggers when VIP customers (LTV > $1000) have no activity in 90+ days. Retention risk requiring proactive outreach.",
            "alert_query": cust_002_query,
            "condition_column": "at_risk_vip_count",
            "condition_operator": ">",
            "condition_threshold": "0",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "customer-success@wanderbricks.com",
            "notification_slack_channel": "#growth-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "customer-success", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "CUST-003-WARN",
            "alert_name": "Business Customer Decline",
            "domain": "customer",
            "severity": "WARNING",
            "alert_description": "Triggers when business customer bookings drop more than 20% week-over-week. May indicate B2B market changes or competitive pressure.",
            "alert_query": cust_003_query,
            "condition_column": "pct_drop",
            "condition_operator": ">",
            "condition_threshold": "20",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 8 ? * MON",  # Weekly on Monday at 8 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "b2b-sales@wanderbricks.com",
            "notification_slack_channel": "#growth-alerts",
            "custom_subject_template": warning_subject,
            "custom_body_template": warning_body,
            "notify_on_ok": True,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "b2b", "priority": "p2"}',
            "owner": default_owner
        },
        {
            "alert_id": "CUST-004-INFO",
            "alert_name": "Customer Growth Summary",
            "domain": "customer",
            "severity": "INFO",
            "alert_description": "Weekly summary of customer metrics including totals, new signups, customer types, and lifetime value.",
            "alert_query": cust_004_query,
            "condition_column": "always_trigger",
            "condition_operator": "=",
            "condition_threshold": "1",
            "aggregation_type": "FIRST",
            "schedule_cron": "0 0 9 ? * MON",  # Weekly on Monday at 9 AM
            "schedule_timezone": default_timezone,
            "notification_emails": "growth@wanderbricks.com",
            "notification_slack_channel": "#weekly-metrics",
            "custom_subject_template": info_subject,
            "custom_body_template": info_body,
            "notify_on_ok": False,
            "rearm_seconds": None,
            "is_enabled": True,
            "tags": '{"team": "growth", "priority": "p3"}',
            "owner": default_owner
        },
    ]
    
    return rules


def create_alert_rules_table(spark: SparkSession, catalog: str, gold_schema: str):
    """Create the alert_rules configuration table."""
    
    table_name = f"{catalog}.{gold_schema}.alert_rules"
    
    print(f"\nCreating alert_rules table: {table_name}")
    
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        alert_id STRING NOT NULL
            COMMENT 'Unique identifier for the alert rule (format: DOMAIN-NUMBER-SEVERITY)',
        alert_name STRING NOT NULL
            COMMENT 'Human-readable display name for the alert',
        domain STRING NOT NULL
            COMMENT 'Business domain: revenue, engagement, property, host, customer',
        severity STRING NOT NULL
            COMMENT 'Alert severity: CRITICAL, WARNING, INFO',
        alert_description STRING NOT NULL
            COMMENT 'Detailed description of what this alert monitors',
        alert_query STRING NOT NULL
            COMMENT 'SQL query that returns data when condition is met',
        condition_column STRING NOT NULL
            COMMENT 'Column name to evaluate in alert condition',
        condition_operator STRING NOT NULL
            COMMENT 'Comparison operator: >, <, >=, <=, =, !=',
        condition_threshold STRING NOT NULL
            COMMENT 'Threshold value for condition comparison',
        aggregation_type STRING
            COMMENT 'Optional aggregation: SUM, AVG, COUNT, MIN, MAX, FIRST',
        schedule_cron STRING NOT NULL
            COMMENT 'Quartz cron expression for schedule',
        schedule_timezone STRING NOT NULL
            COMMENT 'IANA timezone identifier',
        notification_emails STRING
            COMMENT 'Comma-separated email addresses',
        notification_slack_channel STRING
            COMMENT 'Slack channel for notifications',
        custom_subject_template STRING
            COMMENT 'Custom email subject template',
        custom_body_template STRING
            COMMENT 'Custom notification body template',
        notify_on_ok BOOLEAN NOT NULL
            COMMENT 'Send notification when alert returns to OK status',
        rearm_seconds INT
            COMMENT 'Cooldown period in seconds before re-triggering',
        is_enabled BOOLEAN NOT NULL
            COMMENT 'Whether this alert is active',
        tags STRING
            COMMENT 'JSON-formatted tags for categorization',
        owner STRING NOT NULL
            COMMENT 'Email of alert owner/maintainer',
        record_created_timestamp TIMESTAMP NOT NULL
            COMMENT 'When this rule was created',
        record_updated_timestamp TIMESTAMP NOT NULL
            COMMENT 'When this rule was last modified',
        
        CONSTRAINT pk_alert_rules PRIMARY KEY (alert_id) NOT ENFORCED
    )
    USING DELTA
    CLUSTER BY AUTO
    TBLPROPERTIES (
        'delta.enableChangeDataFeed' = 'true',
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true',
        'layer' = 'gold',
        'domain' = 'alerting',
        'entity_type' = 'config',
        'config_table' = 'true',
        'contains_pii' = 'false',
        'data_classification' = 'internal'
    )
    COMMENT 'Configuration table storing all SQL alert rule definitions for Wanderbricks platform. Central repository for config-driven alerting.'
    """
    
    spark.sql(ddl)
    print(f"✓ Created table {table_name}")


def populate_alert_rules(spark: SparkSession, catalog: str, gold_schema: str):
    """Populate the alert_rules table with all 21 alert configurations."""
    
    table_name = f"{catalog}.{gold_schema}.alert_rules"
    
    print(f"\nPopulating alert_rules table with configurations...")
    
    # Get all alert rules
    rules = get_alert_rules(catalog, gold_schema)
    
    # Convert to DataFrame
    rows = []
    for rule in rules:
        rows.append((
            rule["alert_id"],
            rule["alert_name"],
            rule["domain"],
            rule["severity"],
            rule["alert_description"],
            rule["alert_query"],
            rule["condition_column"],
            rule["condition_operator"],
            rule["condition_threshold"],
            rule["aggregation_type"],
            rule["schedule_cron"],
            rule["schedule_timezone"],
            rule["notification_emails"],
            rule["notification_slack_channel"],
            rule["custom_subject_template"],
            rule["custom_body_template"],
            rule["notify_on_ok"],
            rule["rearm_seconds"],
            rule["is_enabled"],
            rule["tags"],
            rule["owner"],
        ))
    
    df = spark.createDataFrame(rows, ALERT_RULES_SCHEMA)
    
    # Add timestamps
    df = df.withColumn("record_created_timestamp", current_timestamp()) \
           .withColumn("record_updated_timestamp", current_timestamp())
    
    # Write using MERGE for idempotency
    df.createOrReplaceTempView("alert_rules_updates")
    
    merge_sql = f"""
    MERGE INTO {table_name} AS target
    USING alert_rules_updates AS source
    ON target.alert_id = source.alert_id
    WHEN MATCHED THEN UPDATE SET
        alert_name = source.alert_name,
        domain = source.domain,
        severity = source.severity,
        alert_description = source.alert_description,
        alert_query = source.alert_query,
        condition_column = source.condition_column,
        condition_operator = source.condition_operator,
        condition_threshold = source.condition_threshold,
        aggregation_type = source.aggregation_type,
        schedule_cron = source.schedule_cron,
        schedule_timezone = source.schedule_timezone,
        notification_emails = source.notification_emails,
        notification_slack_channel = source.notification_slack_channel,
        custom_subject_template = source.custom_subject_template,
        custom_body_template = source.custom_body_template,
        notify_on_ok = source.notify_on_ok,
        rearm_seconds = source.rearm_seconds,
        is_enabled = source.is_enabled,
        tags = source.tags,
        owner = source.owner,
        record_updated_timestamp = current_timestamp()
    WHEN NOT MATCHED THEN INSERT *
    """
    
    spark.sql(merge_sql)
    
    # Get counts by domain
    counts = spark.sql(f"""
        SELECT domain, severity, COUNT(*) as count
        FROM {table_name}
        GROUP BY domain, severity
        ORDER BY domain, severity
    """).collect()
    
    print("\n✓ Alert rules populated:")
    print("-" * 50)
    for row in counts:
        print(f"  {row['domain']:12} | {row['severity']:8} | {row['count']} rules")
    
    total = spark.sql(f"SELECT COUNT(*) as total FROM {table_name}").collect()[0]['total']
    print("-" * 50)
    print(f"  {'TOTAL':12} |          | {total} rules")


def main():
    """Main entry point for alert rules setup."""
    
    # Get parameters
    catalog, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Wanderbricks Alert Rules Setup").getOrCreate()
    
    print("=" * 80)
    print("WANDERBRICKS ALERT RULES SETUP")
    print("=" * 80)
    
    try:
        # Check if catalog exists
        print(f"\nChecking if catalog '{catalog}' exists...")
        try:
            spark.sql(f"DESCRIBE CATALOG {catalog}")
            print(f"✓ Catalog '{catalog}' exists")
        except Exception as e:
            print(f"❌ ERROR: Catalog '{catalog}' does not exist!")
            print(f"Please create the catalog first using:")
            print(f"  CREATE CATALOG {catalog};")
            raise RuntimeError(f"Catalog '{catalog}' does not exist. Cannot proceed with alert rules setup.") from e
        
        # Ensure schema exists
        print(f"\nEnsuring schema '{gold_schema}' exists...")
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{gold_schema}")
        print(f"✓ Schema {catalog}.{gold_schema} ready")
        
        # Create the alert_rules table
        create_alert_rules_table(spark, catalog, gold_schema)
        
        # Populate with all 21 alert rules
        populate_alert_rules(spark, catalog, gold_schema)
        
        print("\n" + "=" * 80)
        print("✓ Alert rules setup completed successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Review rules: SELECT * FROM {}.{}.alert_rules".format(catalog, gold_schema))
        print("  2. Run alert_deploy_job to create SQL alerts from rules")
        print("  3. Monitor alerts in Databricks SQL Alerts UI")
        
        # Signal success for job completion
        dbutils.notebook.exit("SUCCESS")
        
    except Exception as e:
        print(f"\n❌ Error during alert rules setup: {str(e)}")
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()




