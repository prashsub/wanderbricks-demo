# Metric Views Deployment Status

**Date:** December 9, 2025  
**Status:** 🔧 Debugging - Deployment Issues  
**Phase:** 4.3 - Metric Views

---

## Summary

Created 5 metric views for Wanderbricks platform, but encountering deployment failures. Root cause investigation in progress.

---

## ✅ What's Working

### 1. Asset Bundle Configuration
- ✅ Bundle validates successfully
- ✅ Deploys without errors
- ✅ Schema parameters are correct (`dev_prashanth_subrahmanyam_wanderbricks_gold`)
- ✅ Job created and can be triggered

### 2. YAML Files Structure
- ✅ All 5 YAML files parse correctly
- ✅ Version field in correct location (inside list item)
- ✅ Parameter substitution works (${catalog}, ${gold_schema})
- ✅ Dimensions, measures, joins, formats all valid

**Test Results:**
```
✓ host_analytics_metrics.yaml - valid
✓ property_analytics_metrics.yaml - valid
✓ engagement_analytics_metrics.yaml - valid
✓ customer_analytics_metrics.yaml - valid
✓ revenue_analytics_metrics.yaml - valid
```

### 3. Python Script
- ✅ `create_metric_views.py` uses correct syntax
- ✅ `WITH METRICS LANGUAGE YAML` format
- ✅ `dbutils.widgets.get()` for parameters (notebook_task compatible)
- ✅ Error handling with RuntimeError

---

## ❌ What's Not Working

### Metric View Creation Failures

**Error:** All 5 metric views failed to create

```
RuntimeError: Failed to create 5 metric view(s): 
  - customer_analytics_metrics
  - host_analytics_metrics
  - property_analytics_metrics
  - engagement_analytics_metrics
  - revenue_analytics_metrics
```

**Job Run:** https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#job/122150901545863/run/893612048799227

**Problem:** The job logs don't show the specific SQL errors - only that all views failed.

---

## 🔍 Root Cause Investigation

### Hypothesis 1: Missing Gold Layer Tables ⚠️

**Metric views reference these tables:**
- `fact_booking_daily`
- `fact_booking_detail`
- `fact_property_engagement`
- `dim_property`
- `dim_destination`
- `dim_host`
- `dim_user`
- `dim_date`

**Need to verify:** Do these tables exist in `dev_prashanth_subrahmanyam_wanderbricks_gold`?

**To check:**
```sql
SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold 
LIKE 'fact_*';

SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold 
LIKE 'dim_*';
```

### Hypothesis 2: SQL Syntax or Databricks API Issue

**Test created:** `test_single_metric_view.py`
- Simplified metric view with minimal fields
- Will show actual SQL error messages
- Uploaded to workspace: `/Users/prashanth.subrahmanyam@databricks.com/test_single_metric_view`

**To run test:**
1. Open notebook in Databricks workspace
2. Run all cells
3. Check error messages

### Hypothesis 3: Metric View Specification v1.1 Compatibility

**Concern:** Some syntax might not be compatible with v1.1

**Evidence:**
- YAML structure matches spec: `version: '1.1'` inside list item
- No unsupported fields (`time_dimension`, `window_measures`)
- All joins have `name`, `source`, `'on'`
- Column references use correct prefixes

---

## 📋 Next Steps (Prioritized)

### Step 1: Verify Gold Layer Tables Exist ⚡ CRITICAL

```sql
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

-- List all tables
SHOW TABLES;

-- Check specific tables
SELECT 'fact_booking_daily' as table_name, COUNT(*) as row_count 
FROM fact_booking_daily
UNION ALL
SELECT 'fact_booking_detail', COUNT(*) FROM fact_booking_detail
UNION ALL
SELECT 'fact_property_engagement', COUNT(*) FROM fact_property_engagement
UNION ALL
SELECT 'dim_property', COUNT(*) FROM dim_property
UNION ALL
SELECT 'dim_destination', COUNT(*) FROM dim_destination
UNION ALL
SELECT 'dim_host', COUNT(*) FROM dim_host
UNION ALL
SELECT 'dim_user', COUNT(*) FROM dim_user
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date;
```

**Expected:** All tables should exist with rows

### Step 2: Run Test Metric View

1. Open: https://e2-demo-field-eng.cloud.databricks.com/?o=1444828305810485#workspace/~/test_single_metric_view
2. Run all cells
3. Review error messages
4. Check what specifically fails

### Step 3: If Tables Missing - Run Gold Layer Setup

```bash
# Run Gold layer setup first
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run gold_setup_job -t dev

# Then run merge to populate data
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run gold_merge_job -t dev
```

### Step 4: If SQL Syntax Issue - Fix YAML or Python Script

Based on test results, adjust:
- YAML structure
- SQL generation in `create_metric_views.py`
- Metric view comments (escape issues?)

### Step 5: Redeploy and Retest

```bash
# Deploy fixes
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle deploy -t dev

# Run metric views job
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run metric_views_job -t dev
```

---

## 🔧 Debugging Commands

### Check Gold Schema Exists

```bash
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks workspace sql \
  "DESCRIBE SCHEMA prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold"
```

### List All Tables in Gold Schema

```bash
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks workspace sql \
  "SHOW TABLES IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold"
```

### Test Simple Metric View Creation Manually

```sql
-- Test in SQL Editor
CREATE VIEW prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.test_metric
WITH METRICS
LANGUAGE YAML
COMMENT 'Test'
AS $$
- version: '1.1'
  name: test_metric
  comment: Test metric view
  source: prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.fact_booking_daily
  dimensions:
    - name: check_in_date
      expr: source.check_in_date
      comment: Date
      display_name: Date
      synonyms: [date]
  measures:
    - name: total
      expr: SUM(source.total_booking_value)
      comment: Total
      display_name: Total
      format:
        type: currency
        currency_code: USD
      synonyms: [total]
$$;
```

---

## 📊 Deployment Timeline

| Time | Action | Status |
|------|--------|--------|
| 21:13 | Initial deploy with v1.1 at top level | ❌ YAML parse error |
| 21:15 | Fixed YAML (version inside list) | ✅ Deployed |
| 21:17 | Run metric views job | ❌ All 5 views failed |
| 21:18 | Created test script | ⏳ Awaiting execution |
| TBD | Verify Gold tables exist | ⏳ Pending |
| TBD | Root cause identified | ⏳ Pending |
| TBD | Fix applied | ⏳ Pending |
| TBD | Successful deployment | ⏳ Pending |

---

## 🎯 Success Criteria

- [ ] All Gold layer tables verified to exist
- [ ] Test metric view creates successfully
- [ ] All 5 production metric views create successfully
- [ ] Views verified as type METRIC_VIEW
- [ ] Test queries return results
- [ ] MEASURE() function works

---

## 📚 Reference

- **Job ID:** 122150901545863
- **Failed Run ID:** 893612048799227
- **Task Run ID:** 459971349076093
- **Test Notebook:** `/Users/prashanth.subrahmanyam@databricks.com/test_single_metric_view`
- **Bundle:** wanderbricks
- **Target:** dev
- **Catalog:** prashanth_subrahmanyam_catalog
- **Schema:** dev_prashanth_subrahmanyam_wanderbricks_gold

---

## 💡 Key Learnings So Far

1. **YAML Structure Matters:** Version field must be inside list item, not at document level
2. **Schema Prefixes:** Dev mode adds prefix - must use correct schema name in parameters
3. **Error Visibility:** Job logs don't always show detailed SQL errors - need direct testing
4. **Dependency Chain:** Metric views depend on Gold layer tables - verify prerequisites first

---

**Last Updated:** 2025-12-09 21:20 PST  
**Next Action:** Verify Gold layer tables exist, run test notebook

