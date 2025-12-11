# Lakehouse Monitoring - Quick Start

**Two Workflows Available:**
- **Initial Setup:** 5 min deployment + 20 min initialization (deletes existing)
- **Update:** 5 min deployment (preserves historical data)

---

## Prerequisites

- [x] Gold layer tables created (fact_booking_daily, fact_property_engagement, dim_property, dim_host, dim_user)
- [x] Databricks CLI authenticated
- [x] Asset Bundle configured

---

## Choose Your Workflow

### 🆕 Initial Setup (First Time or Complete Refresh)

Use this when:
- Setting up monitors for the first time
- Need to completely recreate monitors
- Don't need to preserve historical data

**⚠️ WARNING:** Deletes existing monitors!

### 🔄 Update Existing Monitors

Use this when:
- Adding new custom metrics
- Updating metric definitions
- Changing slicing expressions
- Want to preserve historical monitoring data

**✅ SAFE:** Preserves historical data

---

## 🆕 Initial Setup Workflow

### Step 1: Validate Bundle (30 seconds)

```bash
# From project root
databricks bundle validate
```

**Expected Output:**
```
✓ Configuration is valid
```

---

### Step 2: Deploy Bundle (1 minute)

```bash
databricks bundle deploy -t dev
```

**Expected Output:**
```
✓ Deployed resources/gold/lakehouse_monitoring_job.yml
✓ Deployed resources/gold/update_lakehouse_monitoring_job.yml
✓ Job: [dev] Wanderbricks Lakehouse Monitoring Setup
✓ Job: [dev] Wanderbricks Lakehouse Monitoring Update
```

---

### Step 3: Run Initial Setup (3 minutes)

⚠️ **WARNING:** This deletes existing monitors!

```bash
databricks bundle run lakehouse_monitoring_job -t dev
```

**Expected Output:**
```
================================================================================
WANDERBRICKS LAKEHOUSE MONITORING SETUP
================================================================================
Catalog: prashanth_subrahmanyam_catalog
Schema: wanderbricks_gold
================================================================================

--- Creating Monitors ---

Creating monitor for prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily...
  Checking for existing monitor on prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily...
✓ Monitor created for prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily
  Monitor ID: fact_booking_daily
  Status: PENDING
  Dashboard ID: 01ef1234-5678-90ab-cdef-1234567890ab

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

---

### Step 4: Wait for Initialization (15-20 minutes)

**⚠️ DO NOT QUERY METRICS IMMEDIATELY**

Monitors are created in PENDING state and need time to initialize.

**Check Status in UI:**

1. Navigate to **Databricks UI**
2. Go to **Data** → **Lakehouse Monitoring**
3. Find your monitors:
   - `fact_booking_daily`
   - `fact_property_engagement`
   - `dim_property`
   - `dim_host`
   - `dim_user`
4. Wait for status: `PENDING` → `ACTIVE`

---

## 🔄 Update Workflow (Preserves Historical Data)

### Step 1: Validate Bundle (30 seconds)

```bash
databricks bundle validate
```

### Step 2: Deploy Bundle (1 minute)

```bash
databricks bundle deploy -t dev
```

### Step 3: Update Monitors (3 minutes)

✅ **SAFE:** Preserves historical data

```bash
databricks bundle run update_lakehouse_monitoring_job -t dev
```

**Expected Output:**
```
================================================================================
WANDERBRICKS LAKEHOUSE MONITORING UPDATE
================================================================================
Catalog: prashanth_subrahmanyam_catalog
Schema: wanderbricks_gold
================================================================================

⚠️  NOTE: This updates existing monitors without deleting them.
   Historical data is preserved.
================================================================================

--- Updating Monitors ---

Updating monitor for prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily...
  Found existing monitor (status: MONITOR_STATUS_ACTIVE)
✓ Monitor updated for prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily
  Monitor ID: fact_booking_daily
  Status: MONITOR_STATUS_ACTIVE
  Dashboard ID: 01ef1234-5678-90ab-cdef-1234567890ab

[... 4 more monitors ...]

================================================================================
Monitor Update Summary:
  Updated: 5 (fact_booking_daily (Revenue), fact_property_engagement (Engagement), dim_property (Property), dim_host (Host), dim_user (Customer))
  Failed: 0 (None)
================================================================================

✓ All monitors updated successfully!

⚠️  NOTE: Monitor refresh may take a few minutes.
   Check monitor status in Databricks UI.
```

### Step 4: Verify Updates (2 minutes)

Monitors update immediately, but refresh may take a few minutes.

**Check in UI:**
- Databricks UI → Data → Lakehouse Monitoring
- Click monitor → View Dashboard
- Verify new metrics appear

---

## Original Documentation Continues Below

### Step 4: Wait for Initialization (15-20 minutes) [Initial Setup Only]

**⚠️ DO NOT QUERY METRICS IMMEDIATELY**

Monitors are created in PENDING state and need time to initialize.

**Check Status in UI:**

1. Navigate to **Databricks UI**
2. Go to **Data** → **Lakehouse Monitoring**
3. Find your monitors:
   - `fact_booking_daily`
   - `fact_property_engagement`
   - `dim_property`
   - `dim_host`
   - `dim_user`
4. Wait for status: `PENDING` → `ACTIVE`

**Check Status via API (optional):**

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
        monitor = w.quality_monitors.get(table_name=fqn)
        print(f"{table}: {monitor.status}")
    except Exception as e:
        print(f"{table}: ERROR - {e}")
```

---

### Step 5: Verify Metrics (after initialization)

Once monitors are ACTIVE, verify metrics are populating:

```sql
-- Check revenue metrics
SELECT 
    window.start,
    window.end,
    MAX(CASE WHEN custom_metric_name = 'daily_revenue' THEN custom_metric_value END) as daily_revenue,
    MAX(CASE WHEN custom_metric_name = 'cancellation_rate' THEN custom_metric_value END) as cancellation_rate
FROM wanderbricks_gold__tables__fact_booking_daily_profile_metrics
WHERE column_name = ':table'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
GROUP BY window.start, window.end
ORDER BY window.start DESC
LIMIT 5;

-- Check engagement metrics
SELECT 
    window.start,
    MAX(CASE WHEN custom_metric_name = 'total_views' THEN custom_metric_value END) as total_views,
    MAX(CASE WHEN custom_metric_name = 'engagement_health' THEN custom_metric_value END) as engagement_health
FROM wanderbricks_gold__tables__fact_property_engagement_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start
ORDER BY window.start DESC
LIMIT 5;
```

**Expected:** Rows with metric values (not NULL)

---

## Troubleshooting

### Monitor Status Still PENDING After 20 Minutes

**Solution:**
```python
# Force refresh
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

w.quality_monitors.run_refresh(
    table_name="prashanth_subrahmanyam_catalog.wanderbricks_gold.fact_booking_daily"
)
```

### Query Returns "Table Not Found"

**Cause:** Incorrect table name pattern

**Solution:** Verify table name format:
```
{schema}__tables__{table}_profile_metrics
```

**Example:**
```
wanderbricks_gold__tables__fact_booking_daily_profile_metrics
```

### No Custom Metrics Appearing

**Cause:** Monitor not fully initialized

**Solution:** Wait for status = ACTIVE, then check dashboard first

### Job Failed with "Missing required parameter"

**Cause:** Bundle variables not set

**Solution:** Check `databricks.yml` has `gold_schema` variable defined

---

## Verify Dashboards

After monitors are ACTIVE:

1. Go to **Databricks UI** → **Data** → **Lakehouse Monitoring**
2. Click on monitor name (e.g., `fact_booking_daily`)
3. Click **View Dashboard**
4. Verify:
   - Profile metrics charts populated
   - Custom metrics visible
   - Drift detection (if applicable)
   - Slice-level breakdowns

---

## Next Steps

✅ **Monitoring Complete**

Now proceed to:

1. **Create SQL Alerts** (Addendum 4.7)
   - Revenue drop alerts
   - High cancellation alerts
   - Low engagement alerts

2. **AI/BI Dashboards** (Addendum 4.5)
   - Build custom dashboards using monitoring metrics
   - Create executive KPI views

3. **Genie Integration** (Addendum 4.6)
   - Query metrics via natural language
   - "What was revenue yesterday?"
   - "Show me cancellation rate trends"

---

## Monitor Summary

| Monitor | Table | Metrics | Slicing | Type |
|---------|-------|---------|---------|------|
| Revenue | fact_booking_daily | 6 | destination_id, property_id | Time Series |
| Engagement | fact_property_engagement | 4 | property_id | Time Series |
| Property | dim_property | 3 | property_type, destination_id | Snapshot |
| Host | dim_host | 5 | country, is_verified | Snapshot |
| Customer | dim_user | 4 | country, user_type | Snapshot |

**Total:** 5 monitors, 19 custom metrics, 7 unique slicing dimensions

---

## Quick Commands Reference

```bash
# Deploy
databricks bundle deploy -t dev

# Run setup
databricks bundle run lakehouse_monitoring_job -t dev

# Check job logs
databricks bundle logs lakehouse_monitoring_job -t dev

# Re-run if needed
databricks bundle run lakehouse_monitoring_job -t dev --force
```

---

## Files Reference

- **Setup Script:** `src/wanderbricks_gold/lakehouse_monitoring.py`
- **Job Config:** `resources/gold/lakehouse_monitoring_job.yml`
- **Query Examples:** `src/wanderbricks_gold/monitoring_queries.sql`
- **Full Documentation:** `src/wanderbricks_gold/MONITORING_README.md`

---

**Status:** ✅ Ready to Deploy

**Deployment Time:** ~5 minutes  
**Initialization Time:** ~20 minutes  
**Total Time:** ~25 minutes

