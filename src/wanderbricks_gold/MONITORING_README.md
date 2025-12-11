# Wanderbricks Lakehouse Monitoring

## Overview

Lakehouse Monitoring provides automated data quality tracking, custom business metrics, and drift detection for critical Gold layer tables.

**Status:** ✅ Implemented  
**Monitors:** 5 monitors with 19 custom metrics  
**Tables Monitored:** fact_booking_daily, fact_property_engagement, dim_property, dim_host, dim_user

---

## Monitor Summary

| # | Monitor | Domain | Table | Custom Metrics | Slicing |
|---|---------|--------|-------|----------------|---------|
| 1 | Revenue | 💰 Revenue | fact_booking_daily | 6 (4 AGGREGATE, 1 DERIVED, 1 DRIFT) | destination_id, property_id |
| 2 | Engagement | 📊 Engagement | fact_property_engagement | 4 (3 AGGREGATE, 1 DERIVED) | property_id |
| 3 | Property | 🏠 Property | dim_property | 3 (3 AGGREGATE) | property_type, destination_id |
| 4 | Host | 👤 Host | dim_host | 5 (4 AGGREGATE, 1 DERIVED) | country, is_verified |
| 5 | Customer | 🎯 Customer | dim_user | 4 (2 AGGREGATE, 1 DERIVED, 1 DRIFT) | country, user_type |

---

## Deployment

### Two Workflows Available

**1. Initial Setup (with deletion)** - Use for first-time setup or complete refresh
- Job: `lakehouse_monitoring_job`
- Deletes existing monitors before creating new ones
- Historical data lost

**2. Update (without deletion)** - Use for metric updates
- Job: `update_lakehouse_monitoring_job`
- Updates existing monitors
- Historical data preserved

---

### Initial Setup Workflow

Use this for first-time monitor creation or when you need a complete refresh.

**Step 1: Deploy Bundle**

```bash
# Validate configuration
databricks bundle validate

# Deploy to dev
databricks bundle deploy -t dev
```

**Step 2: Run Monitoring Setup**

```bash
# Create all 5 monitors (deletes existing)
databricks bundle run lakehouse_monitoring_job -t dev
```

**⚠️ WARNING:** This deletes existing monitors and all historical monitoring data!

---

### Update Workflow

Use this to update metrics or configuration without losing historical data.

**Step 1: Deploy Bundle**

```bash
# Deploy updated configuration
databricks bundle deploy -t dev
```

**Step 2: Update Monitors**

```bash
# Update all 5 monitors (preserves existing)
databricks bundle run update_lakehouse_monitoring_job -t dev
```

**✅ SAFE:** Preserves historical monitoring data

**Expected Output:**
```
WANDERBRICKS LAKEHOUSE MONITORING SETUP
================================================================================
Catalog: prashanth_subrahmanyam_catalog
Schema: wanderbricks_gold
================================================================================

--- Creating Monitors ---

Creating monitor for prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily...
✓ Monitor created for prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily
  Monitor ID: fact_booking_daily
  Status: PENDING
  Dashboard ID: 01ef1234...

[... 4 more monitors ...]

================================================================================
Monitor Creation Summary:
  Created: 5 (fact_booking_daily (Revenue), fact_property_engagement (Engagement), dim_property (Property), dim_host (Host), dim_user (Customer))
  Failed: 0 (None)
================================================================================

✓ All monitors created successfully!

⚠️  IMPORTANT: Monitors need 15-20 minutes to initialize.
   Profile and custom metrics will be available after initialization.
   Check monitor status in Databricks UI or via API.
```

### Step 3: Wait for Initialization

**⚠️ CRITICAL:** Monitors take **15-20 minutes** to initialize after creation.

**Check Status:**
- Navigate to **Databricks UI → Data → Lakehouse Monitoring**
- Look for your monitors (e.g., `fact_booking_daily`)
- Status should change from `PENDING` → `ACTIVE`

**Alternative (API Check):**
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
monitor_info = w.quality_monitors.get(
    table_name="prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily"
)
print(f"Status: {monitor_info.status}")
```

---

## Monitor Details

### 💰 Revenue Monitor (fact_booking_daily)

**Purpose:** Track revenue trends, booking volumes, and cancellation rates

**Custom Metrics:**
| Metric | Type | Definition | Alert Threshold |
|--------|------|------------|-----------------|
| daily_revenue | AGGREGATE | SUM(total_booking_value) | <80% of baseline |
| avg_booking_value | AGGREGATE | AVG(avg_booking_value) | deviation >20% |
| total_bookings | AGGREGATE | SUM(booking_count) | <90% of 7-day avg |
| total_cancellations | AGGREGATE | SUM(cancellation_count) | - |
| cancellation_rate | DERIVED | (cancellations/bookings)*100 | >15% |
| revenue_vs_baseline | DRIFT | Percent change detection | <-20% |

**Slicing:** destination_id, property_id  
**Time Series:** 1 day, 1 week granularity  
**Dashboard:** Auto-generated in Databricks UI

---

### 📊 Engagement Monitor (fact_property_engagement)

**Purpose:** Track property engagement metrics and conversion rates

**Custom Metrics:**
| Metric | Type | Definition | Alert Threshold |
|--------|------|------------|-----------------|
| total_views | AGGREGATE | SUM(view_count) | <50% of baseline |
| total_clicks | AGGREGATE | SUM(click_count) | - |
| avg_conversion | AGGREGATE | AVG(conversion_rate) | deviation >30% |
| engagement_health | DERIVED | (clicks/views)*100 | <5% |

**Slicing:** property_id  
**Time Series:** 1 day, 1 week granularity

---

### 🏠 Property Monitor (dim_property)

**Purpose:** Monitor property inventory and pricing trends

**Custom Metrics:**
| Metric | Type | Definition | Alert Threshold |
|--------|------|------------|-----------------|
| active_listings | AGGREGATE | COUNT(is_current) | drop >10% |
| avg_price | AGGREGATE | AVG(base_price) | deviation >15% |
| price_variance | AGGREGATE | STDDEV(base_price) | variance doubles |

**Slicing:** property_type, destination_id  
**Snapshot:** Latest state monitoring

---

### 👤 Host Monitor (dim_host)

**Purpose:** Track host activity and verification rates

**Custom Metrics:**
| Metric | Type | Definition | Alert Threshold |
|--------|------|------------|-----------------|
| active_hosts | AGGREGATE | COUNT(is_current AND is_active) | - |
| total_current_hosts | AGGREGATE | COUNT(is_current) | - |
| verified_hosts | AGGREGATE | SUM(is_verified AND is_current) | - |
| avg_rating | AGGREGATE | AVG(rating) | drop >0.5 |
| verification_rate | DERIVED | (verified/total)*100 | - |

**Slicing:** country, is_verified  
**Snapshot:** Latest state monitoring

---

### 🎯 Customer Monitor (dim_user)

**Purpose:** Monitor customer growth and business customer mix

**Custom Metrics:**
| Metric | Type | Definition | Alert Threshold |
|--------|------|------------|-----------------|
| total_customers | AGGREGATE | COUNT(is_current) | - |
| business_customers | AGGREGATE | SUM(is_business AND is_current) | - |
| business_customer_rate | DERIVED | (business/total)*100 | - |
| customer_growth | DRIFT | Growth rate tracking | <0 |

**Slicing:** country, user_type  
**Snapshot:** Latest state monitoring

---

## Querying Metrics

### Output Tables

Each monitor creates these tables in the Gold schema:

| Table Pattern | Contents |
|--------------|----------|
| `{schema}__tables__{table}_profile_metrics` | Row count, null rates, custom metrics |
| `{schema}__tables__{table}_drift_metrics` | Drift detection results |

**Example:**
- `wanderbricks_gold__tables__fact_booking_daily_profile_metrics`
- `wanderbricks_gold__tables__fact_booking_daily_drift_metrics`

### Query Examples

See `monitoring_queries.sql` for comprehensive query examples.

**Quick Start:**

```sql
-- Latest revenue metrics
SELECT 
    window.start,
    MAX(CASE WHEN custom_metric_name = 'daily_revenue' THEN custom_metric_value END) as daily_revenue,
    MAX(CASE WHEN custom_metric_name = 'cancellation_rate' THEN custom_metric_value END) as cancellation_rate
FROM wanderbricks_gold__tables__fact_booking_daily_profile_metrics
WHERE column_name = ':table'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
GROUP BY window.start, window.end
ORDER BY window.start DESC;

-- Revenue by destination
SELECT 
    window.start,
    slice_value as destination_id,
    custom_metric_value as daily_revenue
FROM wanderbricks_gold__tables__fact_booking_daily_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'destination_id'
  AND custom_metric_name = 'daily_revenue'
ORDER BY window.start DESC, custom_metric_value DESC;
```

---

## Alert Integration

### Recommended Alerts

| Monitor | Metric | Condition | Severity | Action |
|---------|--------|-----------|----------|--------|
| Revenue | daily_revenue | <80% baseline | 🔴 Critical | Alert immediately |
| Revenue | cancellation_rate | >15% | 🟡 Warning | Investigate |
| Engagement | total_views | <50% baseline | 🔴 Critical | Alert immediately |
| Engagement | engagement_health | <5% | 🟡 Warning | Review campaigns |
| Property | active_listings | drop >10% | 🟡 Warning | Review inventory |
| Host | avg_rating | drop >0.5 | 🟡 Warning | Investigate quality |
| Customer | customer_growth | <0 | 🟡 Warning | Review acquisition |

### SQL Alert Example

```sql
-- Create revenue drop alert
CREATE ALERT revenue_drop_alert
SCHEDULE EVERY 1 DAY
AS
SELECT 
    'REVENUE_DROP' as alert_type,
    window.end as alert_time,
    drift_metric_value as current_revenue,
    pct_change as percent_change
FROM wanderbricks_gold__tables__fact_booking_daily_drift_metrics
WHERE column_name = ':table'
  AND drift_metric_name = 'revenue_vs_baseline'
  AND pct_change < -20
  AND window.end = CURRENT_DATE();
```

---

## Monitoring Dashboards

Each monitor creates an **auto-generated dashboard** in Databricks UI:

1. Navigate to **Databricks UI → Data → Lakehouse Monitoring**
2. Click on monitor name (e.g., `fact_booking_daily`)
3. Click **View Dashboard**

**Dashboard Features:**
- Profile metrics over time
- Custom metric trends
- Drift detection visualizations
- Slice-level breakdowns

---

## Troubleshooting

### Monitor Status is PENDING

**Cause:** Monitor initialization takes 15-20 minutes  
**Solution:** Wait for status to change to ACTIVE

### No Custom Metrics

**Cause:** Monitor hasn't completed first refresh  
**Solution:** Check monitor status, wait for ACTIVE

### Query Returns Empty

**Cause:** Incorrect table name or schema  
**Solution:** Verify table name pattern: `{schema}__tables__{table}_profile_metrics`

### Drift Metrics Not Appearing

**Cause:** Not enough historical data for comparison  
**Solution:** Ensure table has data over multiple time windows

---

## Maintenance

### Refresh Monitors

Monitors refresh automatically based on table updates.

**Manual Refresh:**
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.quality_monitors.run_refresh(
    table_name="prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily"
)
```

### Update Monitor Configuration

To update custom metrics or slicing:

1. Delete existing monitor:
   ```python
   w.quality_monitors.delete(table_name="...")
   ```

2. Re-run setup job:
   ```bash
   databricks bundle run lakehouse_monitoring_job -t dev
   ```

### Delete All Monitors

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

tables = [
    "fact_booking_daily",
    "fact_property_engagement",
    "dim_property",
    "dim_host",
    "dim_user"
]

for table in tables:
    fqn = f"prashanth_subrahmanyam_catalog.wanderbricks_gold.{table}"
    try:
        w.quality_monitors.delete(table_name=fqn)
        print(f"✓ Deleted monitor for {table}")
    except Exception as e:
        print(f"✗ Error deleting {table}: {e}")
```

---

## Next Steps

After monitoring is active:

1. ✅ **Create SQL Alerts** - Define thresholds and notification channels
2. ✅ **AI/BI Dashboards** - Build custom dashboards using monitoring metrics
3. ✅ **Genie Integration** - Query metrics via natural language
4. ✅ **Alerting Workflows** - Automate responses to anomalies

See Phase 4 Addendums 4.5-4.7 for these implementations.

---

## References

### Official Documentation
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/)
- [Custom Metrics](https://docs.databricks.com/lakehouse-monitoring/custom-metrics)
- [Monitoring API](https://docs.databricks.com/api/workspace/qualitymonitors)

### Project Documentation
- [Phase 4 Plan](../../plans/phase4-addendum-4.4-lakehouse-monitoring.md)
- [Monitoring Prompt](../../context/prompts/05-monitoring-prompt.md)
- [Monitoring Rules](../../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

---

## Summary

**Implementation Status:** ✅ Complete

**Created:**
- `lakehouse_monitoring.py` - Monitor setup script (500+ lines)
- `lakehouse_monitoring_job.yml` - Asset Bundle job
- `monitoring_queries.sql` - Query examples
- `MONITORING_README.md` - This documentation

**Monitors Active:** 5 monitors with 19 custom metrics  
**Time to Deploy:** ~5 minutes + 15-20 minutes initialization  
**Next Phase:** AI/BI Dashboards (Addendum 4.5)

