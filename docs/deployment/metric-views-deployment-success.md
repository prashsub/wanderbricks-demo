# Metric Views Deployment - SUCCESS ✅

**Date:** 2025-12-09  
**Environment:** dev  
**Catalog:** prashanth_subrahmanyam_catalog  
**Schema:** dev_prashanth_subrahmanyam_wanderbricks_gold  
**Status:** ✅ ALL 5 METRIC VIEWS DEPLOYED SUCCESSFULLY

---

## Deployed Metric Views

| # | Metric View Name | Source Table | Status | Description |
|---|-----------------|--------------|--------|-------------|
| 1 | `revenue_analytics_metrics` | `fact_booking_daily` | ✅ SUCCESS | Revenue and booking analytics with 8 dimensions and 10 measures |
| 2 | `property_analytics_metrics` | `fact_booking_daily` | ✅ SUCCESS | Property performance and portfolio analytics with 10 dimensions and 8 measures |
| 3 | `customer_analytics_metrics` | `dim_user` | ✅ SUCCESS | Customer behavior and segmentation analytics with 7 dimensions and 8 measures |
| 4 | `host_analytics_metrics` | `dim_host` | ✅ SUCCESS | Host performance and quality analytics with 8 dimensions and 8 measures |
| 5 | `engagement_analytics_metrics` | `fact_property_engagement` | ✅ SUCCESS | Property engagement and conversion analytics with 7 dimensions and 8 measures |

---

## Issues Fixed During Deployment

### Critical Discovery: `name` Field Not Supported in Metric View YAML v1.1

**Problem:** Initial YAML files included a `name` field at the top level, which caused this error:
```
[METRIC_VIEW_INVALID_VIEW_DEFINITION] Unrecognized field "name" 
(known properties: "measures", "version", "joins", "source", "dimensions", "comment", "filter", "materialization")
```

**Root Cause:** In Metric Views v1.1, the view name is specified in the `CREATE VIEW {name}` SQL statement, NOT in the YAML definition.

**Fix:** 
- Removed `name` field from all 5 YAML files
- Updated Python script to extract view name from filename instead of YAML content
- Changed function signature: `create_metric_view(spark, catalog, schema, view_name, metric_view)`

**Files Changed:**
- All 5 YAML files in `src/wanderbricks_gold/semantic/metric_views/`
- `src/wanderbricks_gold/semantic/create_metric_views.py`

**Reference:** [Official Databricks Documentation](https://docs.databricks.com/aws/en/metric-views/create/sql)

---

### Issue 1: Column Name Mismatches

#### customer_analytics_metrics
**Error:** Column `source.is_active` doesn't exist in `dim_user`  
**Available Columns:** email, country, is_business, **is_current**, name  
**Fix:** Changed `is_active` → `is_current` (SCD Type 2 current version indicator)

#### host_analytics_metrics
**Error:** Column `source.created_at` doesn't exist in `dim_host`  
**Available Column:** `joined_at`  
**Fix:** Changed all references from `created_at` → `joined_at`

#### engagement_analytics_metrics - Multiple Issues
**Error 1:** Column `source.search_result_count` doesn't exist  
**Available Column:** `search_count`  
**Fix:** Changed `search_result_count` → `search_count`

**Error 2:** Column `source.booking_count` doesn't exist in `fact_property_engagement`  
**Actual Schema:** fact_property_engagement doesn't track bookings, only engagement metrics  
**Fix:** Removed `booking_count` measure entirely and changed `conversion_rate` to use pre-calculated `AVG(source.conversion_rate)`

---

### Issue 2: Fact Table Schema Mismatches

#### host_analytics_metrics
**Error:** `No such struct field booking_count` in `fact_booking_detail`  
**Problem:** YAML referenced `SUM(fact_booking.booking_count)` but fact_booking_detail has individual booking records  
**Fix:** Changed to `COUNT(fact_booking.booking_id)` to count booking records

---

### Issue 3: Transitive Join Limitations in Metric Views v1.1

#### engagement_analytics_metrics
**Error:** 
```
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter 
with name `dim_property`.`destination_id` cannot be resolved.
```

**Problem:** Attempted transitive join:
```yaml
joins:
  - name: dim_property
    'on': source.property_id = dim_property.property_id
  - name: dim_destination
    'on': dim_property.destination_id = dim_destination.destination_id  # ❌ Can't reference another join!
```

**Root Cause:** Metric Views v1.1 **do not support chained/transitive joins**. Each join must be directly between `source` and the joined table.

**Fix:** 
- Removed `dim_destination` join entirely
- Changed dimensions:
  - Removed: `destination` (city name) and `country` 
  - Added: `destination_id` from `dim_property.destination_id`
- This is an acceptable trade-off since destination_id can still be used for filtering/grouping

**Lesson Learned:** Always verify that joins reference `source` directly, not other joined tables.

---

## Job Architecture

The metric views deployment follows a **modular job architecture**:

```
semantic_setup_job (Orchestrator)
├── Task 1: create_table_valued_functions (Notebook)
│   └── Creates 26 TVFs across 5 domains
└── Task 2: create_metric_views (Job Reference)
    └── Calls → metric_views_job
        └── Creates 5 metric views from YAML

metric_views_job (Standalone)
└── Task: create_metric_views (Notebook)
    └── Creates 5 metric views from YAML
```

**Benefits:**
- ✅ **Single Source of Truth:** Metric views logic defined once in `metric_views_job`
- ✅ **Standalone Execution:** Can run `metric_views_job` independently for testing/iteration
- ✅ **Integrated Execution:** `semantic_setup_job` calls `metric_views_job` via `run_job_task`
- ✅ **No Code Duplication:** Same job definition used in both contexts

---

## Deployment Commands

### Option 1: Run Complete Semantic Layer Setup (Recommended)
```bash
# Creates both TVFs and Metric Views
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle deploy -t dev
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run semantic_setup_job -t dev
```

This runs:
1. Table-Valued Functions creation (26 TVFs)
2. Metric Views creation (5 views) - via `run_job_task`

### Option 2: Run Metric Views Job Standalone (Testing/Iteration)
```bash
# Deploy changes
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle deploy -t dev

# Run metric views only
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run metric_views_job -t dev
```

Use this when:
- Testing metric view changes
- Iterating on YAML definitions
- Debugging metric view issues
- No need to recreate TVFs

### Verify Creation
```sql
-- Check all metric views exist
SHOW VIEWS IN prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold 
LIKE '*_metrics';

-- Describe a specific metric view
DESCRIBE EXTENDED prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.revenue_analytics_metrics AS JSON;

-- Test query a metric view
SELECT * FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.revenue_analytics_metrics 
LIMIT 10;
```

---

## Files Modified

### YAML Definitions (5 files)
1. `src/wanderbricks_gold/semantic/metric_views/revenue_analytics_metrics.yaml`
2. `src/wanderbricks_gold/semantic/metric_views/property_analytics_metrics.yaml`
3. `src/wanderbricks_gold/semantic/metric_views/customer_analytics_metrics.yaml`
4. `src/wanderbricks_gold/semantic/metric_views/host_analytics_metrics.yaml`
5. `src/wanderbricks_gold/semantic/metric_views/engagement_analytics_metrics.yaml`

**Changes:**
- Removed `name` field from all files
- Fixed column name mismatches
- Removed transitive joins
- Updated comments and synonyms

### Python Deployment Script
**File:** `src/wanderbricks_gold/semantic/create_metric_views.py`

**Changes:**
- Updated `load_metric_views_yaml()` to return tuples of `(view_name, metric_view_dict)`
- View name extracted from filename (`.stem`) instead of YAML content
- Updated `create_metric_view()` signature to accept `view_name` parameter
- Enhanced error logging with full traceback and YAML content preview

### Asset Bundle Configuration
**File:** `databricks.yml`

**Changes:**
- Added `src/wanderbricks_gold/semantic/metric_views/**/*.yaml` to `sync.include`
- Ensures YAML files are uploaded to Databricks workspace

**File:** `resources/gold/metric_views_job.yml`

No changes needed - job configuration was already correct.

---

## Schema Validation Performed

For each metric view, validated that:
1. ✅ Source table exists
2. ✅ All referenced columns exist in source table
3. ✅ All joined tables exist
4. ✅ Join conditions reference valid columns
5. ✅ Dimensions use correct `source.` or `{join_name}.` prefixes
6. ✅ Measures use correct aggregation functions
7. ✅ No transitive joins (all joins are `source` → `joined_table`)

---

## Testing Recommendations

### 1. Query Each Metric View
```sql
-- Test revenue_analytics_metrics
SELECT check_in_date, total_revenue, booking_count 
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.revenue_analytics_metrics
LIMIT 10;

-- Test customer_analytics_metrics
SELECT country, user_type, customer_count, total_spend
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.customer_analytics_metrics
LIMIT 10;

-- Test host_analytics_metrics
SELECT host_name, is_verified, property_count, total_revenue
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.host_analytics_metrics
LIMIT 10;

-- Test property_analytics_metrics
SELECT property_title, property_type, total_bookings, occupancy_rate
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.property_analytics_metrics
LIMIT 10;

-- Test engagement_analytics_metrics
SELECT engagement_date, property_title, total_views, avg_conversion_rate
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.engagement_analytics_metrics
LIMIT 10;
```

### 2. Test with Genie Natural Language Queries
Once integrated with Genie Spaces, test queries like:
- "Show me total revenue by month"
- "Which hosts have the most properties?"
- "What's the average booking value by country?"
- "Show me properties with the highest engagement rates"

### 3. Create AI/BI Dashboard
Use these metric views as data sources for Lakeview AI/BI dashboards.

---

## Key Learnings

### 1. Metric View YAML Structure (v1.1)
**Valid top-level fields:**
- `version` ✅
- `comment` ✅
- `source` ✅
- `filter` ✅ (optional)
- `dimensions` ✅
- `measures` ✅
- `joins` ✅ (optional)
- `materialization` ✅ (optional)

**Invalid fields:**
- ~~`name`~~ ❌ (specified in CREATE VIEW statement)
- ~~`time_dimension`~~ ❌ (not supported in v1.1)
- ~~`window_measures`~~ ❌ (not supported in v1.1)

### 2. Column References in Metric Views
**Source table columns:** Use `source.{column_name}`
```yaml
expr: source.total_revenue
```

**Joined table columns:** Use `{join_name}.{column_name}`
```yaml
expr: dim_property.property_type
```

### 3. Join Limitations
- ❌ **No transitive joins:** Can't reference other joined tables in ON clause
- ✅ **Only source-to-table joins:** Each join must be `source.column = joined_table.column`
- ✅ **Multiple joins allowed:** But each independent from source

### 4. Schema Validation is Critical
**Before creating metric views:**
1. Run `DESCRIBE TABLE {source_table}` to verify column names
2. Check all joined tables exist and have required columns
3. Verify column data types match (especially for join keys)
4. Test join conditions manually with SQL before adding to YAML

### 5. Error Messages Are Helpful
Databricks provides excellent error messages with:
- **Exact column name** that's missing
- **Suggestions** for similar column names
- **Available columns** in the table
- **Line number** in YAML where error occurred

**Always read the full error message!**

---

## Production Deployment Checklist

Before deploying to production:

- [ ] All 5 metric views tested in dev environment
- [ ] Sample queries executed successfully
- [ ] Joins return expected row counts
- [ ] Measures calculate correctly
- [ ] Dimensions have appropriate cardinality
- [ ] Comments and synonyms are comprehensive
- [ ] Format specifications are correct (currency, percentage, number)
- [ ] Grant `SELECT` permissions to appropriate groups
- [ ] Document metric views in data catalog
- [ ] Create sample queries for business users
- [ ] Integrate with Genie Spaces
- [ ] Create AI/BI dashboards
- [ ] Set up monitoring/alerting on metric view queries

---

## Next Steps (Phase 4 Addendum 4.3)

1. ✅ Create 5 metric views (COMPLETE)
2. ⏭️ Test metric views with Genie natural language queries
3. ⏭️ Create AI/BI dashboards using metric views
4. ⏭️ Set up Genie Space with metric views as trusted assets
5. ⏭️ Grant permissions to business users
6. ⏭️ Create user documentation and sample queries

---

## References

- [Databricks Metric Views - SQL Creation](https://docs.databricks.com/aws/en/metric-views/create/sql)
- [Metric Views YAML Reference](https://docs.databricks.com/aws/en/metric-views/yaml-ref)
- [Metric Views Semantic Metadata](https://docs.databricks.com/aws/en/metric-views/semantic-metadata)
- [Query Metric Views](https://docs.databricks.com/aws/en/metric-views/query)
- [Use Metric Views with AI/BI](https://docs.databricks.com/aws/en/dashboards/ai-bi-lakeview#use-metric-views)

---

**Deployment completed successfully on 2025-12-09 at 22:06:50 UTC** ✅

