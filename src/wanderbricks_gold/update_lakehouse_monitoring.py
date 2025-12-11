# Databricks notebook source

"""
Wanderbricks Gold Layer - Lakehouse Monitoring Update

Updates existing Lakehouse Monitors with new custom metrics or configuration changes.
Does NOT delete existing monitors - only updates them.

Use Cases:
- Add new custom metrics
- Update metric definitions
- Change slicing expressions
- Modify time series granularity

Monitors Updated:
1. Revenue Monitor (fact_booking_daily) - 6 custom metrics
2. Engagement Monitor (fact_property_engagement) - 4 custom metrics
3. Property Monitor (dim_property) - 3 custom metrics
4. Host Monitor (dim_host) - 5 custom metrics
5. Customer Monitor (dim_user) - 4 custom metrics

Critical Patterns:
- NO deletion (preserves historical data)
- Updates configuration only
- Error handling (jobs must fail if updates fail)
- Table-level metrics use input_columns=[":table"]

Usage:
  databricks bundle run update_lakehouse_monitoring_job -t dev
"""

import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import (
    MonitorInfoStatus, 
    MonitorTimeSeries, 
    MonitorSnapshot,
    MonitorMetric,
    MonitorMetricType
)


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, gold_schema


def update_monitor_with_custom_metrics(
    w: WorkspaceClient,
    table_name: str,
    custom_metrics: list,
    time_series_config: MonitorTimeSeries = None,
    snapshot_config: MonitorSnapshot = None,
    slicing_exprs: list = None,
    baseline_table: str = None
):
    """
    Update existing Lakehouse Monitor with new custom metrics.
    
    Does NOT delete the monitor - only updates configuration.
    
    Args:
        w: Databricks WorkspaceClient
        table_name: Fully qualified table name (catalog.schema.table)
        custom_metrics: List of custom metric definitions
        time_series_config: Time series configuration (for fact tables)
        snapshot_config: Snapshot configuration (for dimension tables)
        slicing_exprs: Columns to slice metrics by
        baseline_table: Baseline table for drift detection
    
    Returns:
        Monitor info or None if update failed
    """
    print(f"\nUpdating monitor for {table_name}...")
    
    try:
        # Check if monitor exists
        existing = w.quality_monitors.get(table_name=table_name)
        if not existing:
            print(f"✗ Monitor does not exist for {table_name}")
            print(f"  Run setup_lakehouse_monitoring_job first to create monitors")
            return None
        
        print(f"  Found existing monitor (status: {existing.status})")
        
        # Get current user for assets directory
        current_user = w.current_user.me().user_name
        table_short_name = table_name.split('.')[-1]
        
        # Build monitor update parameters
        update_params = {
            "table_name": table_name,
            "assets_dir": f"/Workspace/Users/{current_user}/wanderbricks/monitors/{table_short_name}",
            "output_schema_name": table_name.split('.')[0] + "." + table_name.split('.')[1],  # catalog.schema
            "custom_metrics": custom_metrics
        }
        
        # Add optional parameters
        if time_series_config:
            update_params["time_series"] = time_series_config
        
        if snapshot_config:
            update_params["snapshot"] = snapshot_config
        
        if slicing_exprs:
            update_params["slicing_exprs"] = slicing_exprs
        
        if baseline_table:
            update_params["baseline_table_name"] = baseline_table
        
        # Update monitor
        monitor_info = w.quality_monitors.update(**update_params)
        
        print(f"✓ Monitor updated for {table_name}")
        
        # Defensive attribute access (SDK version differences)
        if hasattr(monitor_info, 'table_name'):
            print(f"  Table: {monitor_info.table_name}")
        if hasattr(monitor_info, 'status'):
            print(f"  Status: {monitor_info.status}")
        if hasattr(monitor_info, 'dashboard_id'):
            print(f"  Dashboard ID: {monitor_info.dashboard_id}")
        
        return monitor_info
        
    except Exception as e:
        print(f"✗ Error updating monitor for {table_name}: {str(e)}")
        return None


# ============================================================================
# 💰 REVENUE MONITOR - fact_booking_daily
# ============================================================================

def update_revenue_monitor(
    w: WorkspaceClient,
    catalog: str,
    schema: str
):
    """
    Update monitor for fact_booking_daily with revenue metrics.
    
    Custom Metrics:
    - daily_revenue: Total booking value per day
    - avg_booking_value: Average booking amount
    - cancellation_rate: Percentage of bookings cancelled
    - revenue_vs_baseline: Drift detection for revenue changes
    
    Slicing: destination_id, property_id
    """
    table_name = f"{catalog}.{schema}.fact_booking_daily"
    
    custom_metrics = [
        # AGGREGATE: Revenue KPIs
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="daily_revenue",
            input_columns=[":table"],
            definition="SUM(total_booking_value)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="avg_booking_value",
            input_columns=[":table"],
            definition="AVG(avg_booking_value)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_bookings",
            input_columns=[":table"],
            definition="SUM(booking_count)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_cancellations",
            input_columns=[":table"],
            definition="SUM(cancellation_count)",
            output_data_type="double"
        ),
        
        # DERIVED: Calculated metrics
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
            name="cancellation_rate",
            input_columns=[":table"],
            definition="({{total_cancellations}} / NULLIF({{total_bookings}}, 0)) * 100",
            output_data_type="double"
        ),
        
        # DRIFT: Revenue change detection
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
            name="revenue_vs_baseline",
            input_columns=[":table"],
            definition="{{daily_revenue}}",
            output_data_type="double"
        )
    ]
    
    time_series_config = MonitorTimeSeries(
        timestamp_col="check_in_date",
        granularities=["1 day", "1 week"]
    )
    
    return update_monitor_with_custom_metrics(
        w=w,
        table_name=table_name,
        custom_metrics=custom_metrics,
        time_series_config=time_series_config,
        slicing_exprs=["destination_id", "property_id"]
    )


# ============================================================================
# 📊 ENGAGEMENT MONITOR - fact_property_engagement
# ============================================================================

def update_engagement_monitor(
    w: WorkspaceClient,
    catalog: str,
    schema: str
):
    """
    Update monitor for fact_property_engagement with engagement metrics.
    
    Custom Metrics:
    - total_views: Sum of property views
    - conversion_rate: Average conversion from view to booking
    - engagement_health: Click-through rate (clicks/views)
    
    Slicing: property_id
    """
    table_name = f"{catalog}.{schema}.fact_property_engagement"
    
    custom_metrics = [
        # AGGREGATE: Engagement KPIs
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_views",
            input_columns=[":table"],
            definition="SUM(view_count)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_clicks",
            input_columns=[":table"],
            definition="SUM(click_count)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="avg_conversion",
            input_columns=[":table"],
            definition="AVG(conversion_rate)",
            output_data_type="double"
        ),
        
        # DERIVED: Engagement health
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
            name="engagement_health",
            input_columns=[":table"],
            definition="({{total_clicks}} / NULLIF({{total_views}}, 0)) * 100",
            output_data_type="double"
        )
    ]
    
    time_series_config = MonitorTimeSeries(
        timestamp_col="engagement_date",
        granularities=["1 day", "1 week"]
    )
    
    return update_monitor_with_custom_metrics(
        w=w,
        table_name=table_name,
        custom_metrics=custom_metrics,
        time_series_config=time_series_config,
        slicing_exprs=["property_id"]
    )


# ============================================================================
# 🏠 PROPERTY MONITOR - dim_property
# ============================================================================

def update_property_monitor(
    w: WorkspaceClient,
    catalog: str,
    schema: str
):
    """
    Update monitor for dim_property (dimension table).
    
    Custom Metrics:
    - active_listings: Count of current active properties
    - avg_price: Average base price of active listings
    - price_variance: Standard deviation of prices
    
    Slicing: property_type, destination_id
    """
    table_name = f"{catalog}.{schema}.dim_property"
    
    custom_metrics = [
        # AGGREGATE: Property KPIs
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="active_listings",
            input_columns=[":table"],
            definition="COUNT(CASE WHEN is_current = true THEN 1 END)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="avg_price",
            input_columns=[":table"],
            definition="AVG(CASE WHEN is_current = true THEN base_price END)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="price_variance",
            input_columns=["base_price"],
            definition="STDDEV(base_price)",
            output_data_type="double"
        )
    ]
    
    snapshot_config = MonitorSnapshot()
    
    return update_monitor_with_custom_metrics(
        w=w,
        table_name=table_name,
        custom_metrics=custom_metrics,
        snapshot_config=snapshot_config,
        slicing_exprs=["property_type", "destination_id"]
    )


# ============================================================================
# 👤 HOST MONITOR - dim_host
# ============================================================================

def update_host_monitor(
    w: WorkspaceClient,
    catalog: str,
    schema: str
):
    """
    Update monitor for dim_host (dimension table).
    
    Custom Metrics:
    - active_hosts: Count of active hosts
    - avg_rating: Average host rating
    - verification_rate: Percentage of verified hosts
    
    Slicing: country, is_verified
    """
    table_name = f"{catalog}.{schema}.dim_host"
    
    custom_metrics = [
        # AGGREGATE: Host KPIs
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="active_hosts",
            input_columns=[":table"],
            definition="COUNT(CASE WHEN is_current = true AND is_active = true THEN 1 END)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_current_hosts",
            input_columns=[":table"],
            definition="COUNT(CASE WHEN is_current = true THEN 1 END)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="verified_hosts",
            input_columns=[":table"],
            definition="SUM(CASE WHEN is_verified AND is_current THEN 1 ELSE 0 END)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="avg_rating",
            input_columns=[":table"],
            definition="AVG(CASE WHEN is_current = true THEN rating END)",
            output_data_type="double"
        ),
        
        # DERIVED: Verification rate
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
            name="verification_rate",
            input_columns=[":table"],
            definition="({{verified_hosts}} / NULLIF({{total_current_hosts}}, 0)) * 100",
            output_data_type="double"
        )
    ]
    
    snapshot_config = MonitorSnapshot()
    
    return update_monitor_with_custom_metrics(
        w=w,
        table_name=table_name,
        custom_metrics=custom_metrics,
        snapshot_config=snapshot_config,
        slicing_exprs=["country", "is_verified"]
    )


# ============================================================================
# 🎯 CUSTOMER MONITOR - dim_user
# ============================================================================

def update_customer_monitor(
    w: WorkspaceClient,
    catalog: str,
    schema: str
):
    """
    Update monitor for dim_user (dimension table).
    
    Custom Metrics:
    - total_customers: Count of current customers
    - business_customer_rate: Percentage of business customers
    - customer_growth: Drift tracking for customer growth
    
    Slicing: country, user_type
    """
    table_name = f"{catalog}.{schema}.dim_user"
    
    custom_metrics = [
        # AGGREGATE: Customer KPIs
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="total_customers",
            input_columns=[":table"],
            definition="COUNT(CASE WHEN is_current = true THEN 1 END)",
            output_data_type="double"
        ),
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
            name="business_customers",
            input_columns=[":table"],
            definition="SUM(CASE WHEN is_business AND is_current THEN 1 ELSE 0 END)",
            output_data_type="double"
        ),
        
        # DERIVED: Business customer rate
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DERIVED,
            name="business_customer_rate",
            input_columns=[":table"],
            definition="({{business_customers}} / NULLIF({{total_customers}}, 0)) * 100",
            output_data_type="double"
        ),
        
        # DRIFT: Customer growth tracking
        MonitorMetric(
            type=MonitorMetricType.CUSTOM_METRIC_TYPE_DRIFT,
            name="customer_growth",
            input_columns=[":table"],
            definition="{{total_customers}}",
            output_data_type="double"
        )
    ]
    
    snapshot_config = MonitorSnapshot()
    
    return update_monitor_with_custom_metrics(
        w=w,
        table_name=table_name,
        custom_metrics=custom_metrics,
        snapshot_config=snapshot_config,
        slicing_exprs=["country", "user_type"]
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main entry point for Lakehouse Monitoring update.
    
    Updates existing monitors with new custom metrics.
    Does NOT delete monitors (preserves historical data).
    Raises error if any monitor fails to update.
    """
    catalog, gold_schema = get_parameters()
    
    # Initialize Databricks SDK
    w = WorkspaceClient()
    
    print("=" * 80)
    print("WANDERBRICKS LAKEHOUSE MONITORING UPDATE")
    print("=" * 80)
    print(f"Catalog: {catalog}")
    print(f"Schema: {gold_schema}")
    print("=" * 80)
    print("\n⚠️  NOTE: This updates existing monitors without deleting them.")
    print("   Historical data is preserved.")
    print("=" * 80)
    
    try:
        # Track updated monitors
        monitors_updated = []
        monitors_failed = []
        
        # Update monitors
        print("\n--- Updating Monitors ---")
        
        # 1. Revenue Monitor
        result1 = update_revenue_monitor(w, catalog, gold_schema)
        if result1:
            monitors_updated.append("fact_booking_daily (Revenue)")
        else:
            monitors_failed.append("fact_booking_daily (Revenue)")
        
        # 2. Engagement Monitor
        result2 = update_engagement_monitor(w, catalog, gold_schema)
        if result2:
            monitors_updated.append("fact_property_engagement (Engagement)")
        else:
            monitors_failed.append("fact_property_engagement (Engagement)")
        
        # 3. Property Monitor
        result3 = update_property_monitor(w, catalog, gold_schema)
        if result3:
            monitors_updated.append("dim_property (Property)")
        else:
            monitors_failed.append("dim_property (Property)")
        
        # 4. Host Monitor
        result4 = update_host_monitor(w, catalog, gold_schema)
        if result4:
            monitors_updated.append("dim_host (Host)")
        else:
            monitors_failed.append("dim_host (Host)")
        
        # 5. Customer Monitor
        result5 = update_customer_monitor(w, catalog, gold_schema)
        if result5:
            monitors_updated.append("dim_user (Customer)")
        else:
            monitors_failed.append("dim_user (Customer)")
        
        print("\n" + "=" * 80)
        print(f"Monitor Update Summary:")
        print(f"  Updated: {len(monitors_updated)} ({', '.join(monitors_updated)})")
        print(f"  Failed: {len(monitors_failed)} ({', '.join(monitors_failed) if monitors_failed else 'None'})")
        print("=" * 80)
        
        if monitors_failed:
            raise RuntimeError(
                f"Failed to update {len(monitors_failed)} monitor(s): "
                f"{', '.join(monitors_failed)}"
            )
        
        print("\n✓ All monitors updated successfully!")
        print("\n⚠️  NOTE: Monitor refresh may take a few minutes.")
        print("   Check monitor status in Databricks UI.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()

