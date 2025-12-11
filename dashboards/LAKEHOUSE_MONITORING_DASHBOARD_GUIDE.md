# Wanderbricks Lakehouse Monitoring Dashboard Guide

## Overview

This AI/BI dashboard visualizes custom metrics from all 5 Lakehouse Monitoring monitors created for the Wanderbricks Gold layer.

**Dashboard File:** `wanderbricks_lakehouse_monitoring_dashboard.lvdash.json`

---

## Monitors Visualized

The dashboard displays metrics from these monitors:

### 1. 💰 Revenue Monitor (`fact_booking_daily`)
**Custom Metrics:**
- `daily_revenue` - Total booking value per day
- `avg_booking_value` - Average booking amount
- `total_bookings` - Sum of booking count
- `total_cancellations` - Sum of cancellation count
- `cancellation_rate` - Derived: cancellations/bookings * 100
- `revenue_vs_baseline` - Drift: Period-over-period revenue change

**Slicing:** `destination_id`, `property_id`

---

### 2. 📊 Engagement Monitor (`fact_property_engagement`)
**Custom Metrics:**
- `total_views` - Sum of property views
- `total_clicks` - Sum of property clicks
- `avg_conversion` - Average conversion rate
- `engagement_health` - Derived: clicks/views * 100 (CTR)

**Slicing:** `property_id`

---

### 3. 🏠 Property Monitor (`dim_property`)
**Custom Metrics:**
- `active_listings` - Count of current active properties
- `avg_price` - Average base price of active listings
- `price_variance` - Standard deviation of prices

**Slicing:** `property_type`, `destination_id`

---

### 4. 👤 Host Monitor (`dim_host`)
**Custom Metrics:**
- `active_hosts` - Count of active current hosts
- `total_current_hosts` - Count of all current hosts
- `verification_rate` - Derived: verified_hosts/total_hosts * 100
- `avg_rating` - Average host rating

**Slicing:** `country`, `is_verified`

---

### 5. 🎯 Customer Monitor (`dim_user`)
**Custom Metrics:**
- `total_customers` - Count of current customers
- `business_customers` - Count of business customers
- `business_customer_rate` - Derived: business/total * 100
- `customer_growth` - Drift: Period-over-period customer growth

**Slicing:** `country`, `user_type`

---

## Dashboard Pages

### Page 1: Monitoring Overview
**Purpose:** High-level KPIs and alerts across all monitors

**Widgets:**
- 6 KPI Counters (1x2 each):
  - Daily Revenue
  - Avg Booking Value
  - Cancellation Rate
  - Engagement Health
  - Active Listings
  - Total Customers

- 2 Line Charts (3x6 each):
  - Daily Revenue Trend (7 days)
  - Engagement Health Trend (7 days)

- 1 Alert Table (6x6):
  - All monitoring alerts (last 7 days)
  - Filters: Revenue drop >20%, High cancellation >15%, Low engagement <5%

---

### Page 2: Revenue Monitoring
**Purpose:** Deep dive into revenue metrics and drift detection

**Widgets:**
- 3 KPI Counters (2x2 each):
  - Total Bookings
  - Total Cancellations
  - Cancellation Rate

- 3 Charts:
  - Revenue Metrics Trend (6x6) - Multi-metric line chart
  - Revenue Drift Detection (6x6) - Bar chart with alert levels
  - Revenue by Destination (6x6) - Bar chart of sliced metric

---

### Page 3: Engagement Monitoring
**Purpose:** Property engagement and conversion metrics

**Widgets:**
- 3 KPI Counters (2x2 each):
  - Total Views
  - Total Clicks
  - Avg Conversion Rate

- 1 Line Chart (6x6):
  - Views & Clicks Trend (7 days)

---

### Page 4: Dimension Monitors
**Purpose:** SCD2 dimension table health metrics

**Widgets:**
- 3 KPI Counters (2x2 each):
  - Avg Property Price
  - Active Hosts
  - Host Verification Rate

- 3 Charts:
  - Properties by Type (3x6) - Sliced by property_type
  - Hosts by Country (3x6) - Top 10, sliced by country
  - Customer Growth Trend (6x6) - Drift metric with growth rate

---

## Data Source Tables

The dashboard queries these Lakehouse Monitoring output tables:

| Monitor | Profile Metrics Table | Drift Metrics Table |
|---|-----|-----|
| Revenue | `{catalog}.{schema}__tables__fact_booking_daily_profile_metrics` | `{catalog}.{schema}__tables__fact_booking_daily_drift_metrics` |
| Engagement | `{catalog}.{schema}__tables__fact_property_engagement_profile_metrics` | N/A |
| Property | `{catalog}.{schema}__tables__dim_property_profile_metrics` | N/A |
| Host | `{catalog}.{schema}__tables__dim_host_profile_metrics` | N/A |
| Customer | `{catalog}.{schema}__tables__dim_user_profile_metrics` | `{catalog}.{schema}__tables__dim_user_drift_metrics` |

**⚠️ Important:** Custom metrics appear as **NEW COLUMNS** in these tables, not in a separate table!

---

## Query Patterns

### Querying Table-Level Custom Metrics

```sql
-- Pattern: PIVOT custom metrics from profile_metrics table
SELECT 
    MAX(window.end) as latest_date,
    MAX(CASE WHEN custom_metric_name = 'metric1' THEN custom_metric_value END) as metric1,
    MAX(CASE WHEN custom_metric_name = 'metric2' THEN custom_metric_value END) as metric2
FROM {catalog}.{schema}__tables__{table}_profile_metrics
WHERE column_name = ':table'  -- Table-level metrics
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
GROUP BY 1
ORDER BY latest_date DESC
```

### Querying Sliced Metrics

```sql
-- Pattern: Get metrics by slice dimension
SELECT 
    window.start,
    slice_key,
    slice_value,
    custom_metric_name,
    custom_metric_value
FROM {catalog}.{schema}__tables__{table}_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'dimension_name'  -- e.g., 'destination_id'
  AND custom_metric_name = 'metric_name'
ORDER BY window.start DESC, custom_metric_value DESC
```

### Querying Drift Metrics

```sql
-- Pattern: Get drift detection results
SELECT 
    DATE(window.end) as date,
    drift_metric_value as current_value,
    pct_change,
    is_anomaly
FROM {catalog}.{schema}__tables__{table}_drift_metrics
WHERE column_name = ':table'
  AND drift_metric_name = 'drift_metric_name'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -30)
ORDER BY date DESC
```

---

## Deployment Instructions

### Step 1: Upload Dashboard to Databricks

**Option A: Via Databricks SQL UI**
1. Go to Databricks SQL workspace
2. Click "Dashboards" → "Create dashboard" → "Import from file"
3. Upload `wanderbricks_lakehouse_monitoring_dashboard.lvdash.json`
4. Confirm import

**Option B: Via Databricks CLI**
```bash
databricks dashboards import \
  --file dashboards/wanderbricks_lakehouse_monitoring_dashboard.lvdash.json
```

---

### Step 2: Configure Dashboard Parameters

After import, set these parameters:

| Parameter | Value | Description |
|---|---|---|
| `catalog` | `prashanth_subrahmanyam_catalog` | Your Unity Catalog name |
| `schema` | `wanderbricks_gold` | Your Gold schema name |

**Note:** Monitoring output tables use naming pattern:
```
{catalog}.{schema}__tables__{table}_profile_metrics
```

If your schema is `wanderbricks_gold`, tables will be in `wanderbricks_gold__tables__*`.

---

### Step 3: Verify Data Availability

**Check monitoring tables exist:**
```sql
-- Show all monitoring tables
SHOW TABLES IN prashanth_subrahmanyam_catalog.wanderbricks_gold__tables__;

-- Expected tables:
-- fact_booking_daily_profile_metrics
-- fact_booking_daily_drift_metrics
-- fact_property_engagement_profile_metrics
-- dim_property_profile_metrics
-- dim_host_profile_metrics
-- dim_user_profile_metrics
-- dim_user_drift_metrics
```

**Verify custom metrics are present:**
```sql
-- Check revenue metrics
SELECT DISTINCT custom_metric_name
FROM prashanth_subrahmanyam_catalog.wanderbricks_gold__tables__.fact_booking_daily_profile_metrics
WHERE column_name = ':table'
ORDER BY custom_metric_name;

-- Expected: avg_booking_value, cancellation_rate, daily_revenue, 
--           total_bookings, total_cancellations
```

---

### Step 4: Refresh Dashboard

1. Open the imported dashboard
2. Click "Refresh" to load data
3. Verify all widgets populate with data
4. Check date ranges (last 7 days for most metrics)

---

## Troubleshooting

### Issue: "Table not found" errors

**Cause:** Monitoring tables don't exist yet (monitors still initializing)

**Solution:**
1. Check monitor status:
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
monitor = w.quality_monitors.get(
    table_name="prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily"
)
print(f"Status: {monitor.status}")
```

2. Wait 15-20 minutes after monitor creation
3. Check assets directory for dashboard creation:
```sql
-- Monitors create dashboards automatically
DESCRIBE EXTENDED prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily;
-- Look for: dashboard_id property
```

---

### Issue: Custom metrics show NULL values

**Cause:** Metrics not yet calculated or query filtering wrong column_name

**Solution:**
1. Verify `column_name = ':table'` for table-level metrics
2. Check window time range (may need more historical data)
3. Refresh monitor:
```python
w.quality_monitors.run_refresh(
    table_name="prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily"
)
```

---

### Issue: No drift metrics

**Cause:** Drift requires baseline comparison (minimum 2 refresh runs)

**Solution:**
1. Wait for at least 2 monitor refresh cycles
2. Check baseline_table configuration
3. Verify drift metrics defined with correct syntax

---

## Alert Thresholds

The dashboard includes these alert thresholds:

| Alert Type | Condition | Severity | Action |
|---|---|---|---|
| Revenue Drop | `pct_change < -20%` | Critical | Immediate investigation |
| Revenue Warning | `pct_change < -10%` | Warning | Monitor closely |
| High Cancellation | `cancellation_rate > 15%` | Warning | Review booking flow |
| Low Engagement | `engagement_health < 5%` | Warning | Check property listings |
| Listing Drop | `>10% decrease` in active_listings | Warning | Contact hosts |

**Customization:**
To adjust thresholds, modify the dataset queries in the JSON file:
```json
{
  "name": "revenue_drift_alerts",
  "query": "... WHERE pct_change < -20 ..."  // Change threshold here
}
```

---

## Scheduling Automated Refreshes

**Option 1: Via Databricks SQL UI**
1. Open dashboard
2. Click "Schedule" → "Add schedule"
3. Set frequency (e.g., Daily at 8 AM)
4. Enable email notifications

**Option 2: Via Databricks Asset Bundle**

Create `resources/monitoring_dashboard_refresh_job.yml`:
```yaml
resources:
  jobs:
    monitoring_dashboard_refresh:
      name: "[${bundle.target}] Monitoring Dashboard Refresh"
      
      tasks:
        - task_key: refresh_dashboard
          sql_task:
            warehouse_id: ${var.warehouse_id}
            dashboard:
              dashboard_id: "<dashboard_id_from_import>"
      
      schedule:
        quartz_cron_expression: "0 0 8 * * ?"  # Daily at 8 AM
        timezone_id: "America/New_York"
        pause_status: UNPAUSED
      
      tags:
        environment: ${bundle.target}
        job_type: monitoring
```

---

## Extending the Dashboard

### Adding New Custom Metrics

1. **Update monitor configuration** (in Python):
```python
# Add new custom metric to existing monitor
new_metric = MonitorMetric(
    type=MonitorMetricType.CUSTOM_METRIC_TYPE_AGGREGATE,
    name="new_metric_name",
    input_columns=[":table"],
    definition="SUM(new_column)",
    output_data_type=T.StructField("output", T.DoubleType()).json()
)

# Update monitor (MUST include ALL existing metrics!)
w.quality_monitors.update(
    table_name=table_name,
    custom_metrics=[...existing_metrics..., new_metric]  # Include all!
)
```

2. **Add dataset to dashboard JSON**:
```json
{
  "name": "new_metric_data",
  "query": "SELECT ... WHERE custom_metric_name = 'new_metric_name'"
}
```

3. **Add widget to page**:
```json
{
  "widget": {
    "name": "new_metric_widget",
    "spec": {"widgetType": "counter", ...}
  },
  "position": {"x": 0, "y": 0, "width": 2, "height": 2}
}
```

---

## Best Practices

### 1. Dashboard Performance
- Limit time ranges to 7-30 days for most queries
- Use `LIMIT` clauses for large result sets
- Cache frequently used datasets

### 2. Alert Configuration
- Set realistic thresholds based on historical data
- Use multiple severity levels (Critical, Warning, Info)
- Enable email notifications for critical alerts only

### 3. Metric Naming
- Use clear, business-friendly metric names
- Include units in display names (%, $, count)
- Document derived metric formulas in descriptions

### 4. Layout Organization
- Group related metrics on same page
- Use consistent widget heights (2, 6, 9)
- Place KPIs at top, charts below

---

## Maintenance

### Weekly Tasks
- [ ] Review alert table for recurring issues
- [ ] Verify all widgets loading data
- [ ] Check for stale metrics (no recent updates)

### Monthly Tasks
- [ ] Review alert thresholds for accuracy
- [ ] Update time ranges if needed
- [ ] Archive old screenshots/exports

### After Monitor Updates
- [ ] Verify new custom metrics appear in queries
- [ ] Update widget descriptions if metrics change
- [ ] Test dashboard after monitor refresh

---

## References

- [Databricks Lakehouse Monitoring Docs](https://docs.databricks.com/lakehouse-monitoring/)
- [AI/BI Dashboard Best Practices](.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)
- [Monitoring Setup Script](../src/wanderbricks_gold/lakehouse_monitoring.py)
- [Monitoring Queries](../src/wanderbricks_gold/monitoring_queries.sql)
- [Lakehouse Monitoring Patterns](.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review monitoring setup documentation
3. Verify monitor status in Databricks UI
4. Check system table queries work independently

---

**Last Updated:** December 11, 2025  
**Dashboard Version:** 1.0  
**Monitors:** 5 (Revenue, Engagement, Property, Host, Customer)  
**Total Custom Metrics:** 20 (11 aggregate, 5 derived, 4 drift)

