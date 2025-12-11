# Rule Improvement: Metric Views Schema Validation Patterns

**Date:** 2025-12-09  
**Project:** Wanderbricks Phase 4 Addendum 4.3 - Metric Views  
**Issue Type:** Systematic schema validation failures  
**Impact:** 5/5 metric views initially failed deployment, requiring 7 iterations to fix  
**Time to Resolution:** ~2 hours of debugging  
**Root Cause:** No schema validation before YAML creation

---

## Executive Summary

During the deployment of 5 metric views for the Wanderbricks platform, **100% of views failed** on initial deployment due to:
1. **Incorrect YAML structure** (`name` field not supported in v1.1)
2. **Column schema mismatches** (referencing non-existent columns)
3. **Transitive join limitations** (chained joins not supported)
4. **No pre-creation validation** (assumed schemas without verification)

**Key Discovery:** The existing `.cursor/rules/semantic-layer/14-metric-views-patterns.mdc` rule contained **incorrect examples** showing the `name` field in YAML, which is not supported in Metric Views v1.1. The rule also showed `time_dimension` and `window_measures` in examples despite documenting them as unsupported.

This post-mortem documents the issues, fixes, and prevention strategies to ensure **zero schema-related failures** in future metric view deployments.

---

## Deployment Timeline

| Iteration | Metric Views Passing | Issue Fixed | Time |
|-----------|---------------------|-------------|------|
| 1 | 0/5 | ❌ All failed: `name` field error | +15 min |
| 2 | 0/5 | ❌ All failed: YAML list wrapper | +10 min |
| 3 | 0/5 | ❌ All failed: YAML indentation | +15 min |
| 4 | 2/5 | ✅ Fixed `name` field issue | +20 min |
| 5 | 3/5 | ✅ Fixed `customer_analytics` column mismatch | +15 min |
| 6 | 4/5 | ✅ Fixed `host_analytics` column mismatch | +15 min |
| 7 | 5/5 | ✅ Fixed `engagement_analytics` transitive join | +20 min |

**Total Time:** ~2 hours  
**Total Iterations:** 7  
**Final Status:** ✅ All 5 metric views deployed successfully

---

## Critical Issue #1: `name` Field Not Supported in v1.1

### The Problem

**All 5 metric views failed** with this error:
```
[METRIC_VIEW_INVALID_VIEW_DEFINITION] The metric view definition is invalid. 
Reason: Failed to parse YAML: Unrecognized field "name" 
(class com.databricks.sql.serde.v11.MetricView), not marked as ignorable 
(8 known properties: "measures", "version", "joins", "source", "dimensions", 
"comment", "filter", "materialization"])
```

### Root Cause

**The existing cursor rule showed incorrect examples:**

```yaml
# ❌ WRONG (from existing rule)
version: "1.1"
- name: sales_performance_metrics  # This field is NOT supported!
  comment: ...
  source: ...
```

**The agent faithfully followed the rule's example**, which was incorrect for v1.1.

### The Fix

**Metric view name is specified in SQL, NOT YAML:**

```python
# ✅ CORRECT: View name in CREATE VIEW statement
view_name = "revenue_analytics_metrics"  # From filename
fully_qualified_name = f"{catalog}.{schema}.{view_name}"

create_sql = f"""
CREATE VIEW {fully_qualified_name}  -- Name here!
WITH METRICS
LANGUAGE YAML
AS $$
version: '1.1'               -- No 'name' field here!
comment: 'Description...'
source: catalog.schema.fact_table
dimensions:
  - name: dimension1
    expr: source.column1
$$
"""
```

### Changes Made

1. **Removed `name` field** from all 5 YAML files
2. **Updated Python script** to extract view name from filename:
   ```python
   # Before (wrong)
   def load_metric_views_yaml(catalog, schema):
       metric_view = yaml.safe_load(yaml_content)
       return [metric_view]  # Expected 'name' key in dict
   
   # After (correct)
   def load_metric_views_yaml(catalog, schema):
       view_name = yaml_file.stem  # Extract from filename
       metric_view = yaml.safe_load(yaml_content)
       return [(view_name, metric_view)]  # Tuple of (name, dict)
   ```

3. **Updated function signature:**
   ```python
   # Before
   def create_metric_view(spark, catalog, schema, metric_view):
       view_name = metric_view['name']  # KeyError!
   
   # After
   def create_metric_view(spark, catalog, schema, view_name, metric_view):
       # view_name passed as parameter
   ```

### Impact

- ✅ Fixed all 5 metric views
- ✅ Aligns with official Databricks documentation
- ✅ Simpler YAML structure (one less field)

### Prevention

**Update cursor rule with correct examples:**
- Remove all `name:` fields from YAML examples
- Document that name is in `CREATE VIEW` statement
- Show correct Python script pattern for filename-based naming

**Reference:** [Official Databricks Metric Views SQL Documentation](https://docs.databricks.com/aws/en/metric-views/create/sql)

---

## Critical Issue #2: Column Schema Mismatches

### The Problem

**3 out of 5 metric views failed** due to referencing columns that don't exist in the source tables.

### Failures Breakdown

#### Failure 1: `customer_analytics_metrics`

**Error:**
```
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter 
with name `source`.`is_active` cannot be resolved. 
Did you mean one of the following? 
[`source`.`email`, `source`.`country`, `source`.`is_business`, 
 `source`.`is_current`, `source`.`name`]. 
SQLSTATE: 42703
```

**Source Table:** `dim_user`  
**Referenced Column:** `is_active` ❌  
**Actual Column:** `is_current` ✅ (SCD Type 2 current version indicator)

**Root Cause:** Assumed dimension tables have `is_active` flag without verifying actual schema.

**Fix:**
```yaml
# Before
dimensions:
  - name: is_active
    expr: source.is_active  # ❌ Column doesn't exist

# After  
dimensions:
  - name: is_current
    expr: source.is_current  # ✅ Correct column
    comment: Current user record version indicator (SCD Type 2)
```

---

#### Failure 2: `host_analytics_metrics`

**Error 1:**
```
Column `source.created_at` doesn't exist in `dim_host`
Available columns include: ..., joined_at, ...
```

**Error 2:**
```
[FIELD_NOT_FOUND] No such struct field `booking_count` 
in `booking_id`, `user_id`, `host_id`, ...
```

**Root Cause:** 
1. `dim_host` uses `joined_at` not `created_at`
2. `fact_booking_detail` has individual booking records, not a `booking_count` column

**Fix:**
```yaml
# Fix 1: Date column name
dimensions:
  - name: joined_at        # ✅ Correct column name
    expr: source.joined_at
  - name: host_since_days
    expr: DATEDIFF(CURRENT_DATE(), source.joined_at)  # ✅ Updated reference

# Fix 2: Count bookings correctly
measures:
  - name: booking_count
    expr: COUNT(fact_booking.booking_id)  # ✅ Count records, not sum column
```

---

#### Failure 3: `engagement_analytics_metrics`

**Error:**
```
Column `source.search_result_count` doesn't exist
Available column: `source.search_count`

Column `source.booking_count` doesn't exist in fact_property_engagement
```

**Root Cause:** 
1. Column name mismatch: `search_result_count` vs `search_count`
2. `fact_property_engagement` tracks engagement metrics only, not bookings

**Fix:**
```yaml
# Fix 1: Correct column name
measures:
  - name: search_appearances
    expr: SUM(source.search_count)  # ✅ Correct column name

# Fix 2: Use pre-calculated conversion rate
measures:
  - name: avg_conversion_rate
    expr: AVG(source.conversion_rate)  # ✅ Use existing calculated field
    comment: Average conversion rate across properties. Pre-calculated in fact table.
```

---

### Pattern Analysis

**All 3 failures shared the same root cause:**

| Issue | Count | Pattern |
|-------|-------|---------|
| Assumed column name without verification | 5 | `is_active`, `created_at`, `booking_count`, `search_result_count` |
| Didn't check source table schema | 3 | All 3 failing views |
| Guessed aggregation logic | 1 | `SUM(booking_count)` vs `COUNT(booking_id)` |

**Key Insight:** We assumed column names based on business logic instead of verifying actual table schemas.

---

## Critical Issue #3: Transitive Join Limitations

### The Problem

**`engagement_analytics_metrics` failed** with:
```
[UNRESOLVED_COLUMN.WITH_SUGGESTION] A column, variable, or function parameter 
with name `dim_property`.`destination_id` cannot be resolved. 
Did you mean one of the following? 
[`dim_destination`.`destination_id`, ...]. 
SQLSTATE: 42703
```

### Root Cause

**Attempted transitive/chained join:**

```yaml
# ❌ WRONG: Tried to join through another joined table
source: fact_property_engagement

joins:
  - name: dim_property
    source: catalog.schema.dim_property
    'on': source.property_id = dim_property.property_id
  
  - name: dim_destination
    source: catalog.schema.dim_destination
    'on': dim_property.destination_id = dim_destination.destination_id  
    # ❌ Can't reference dim_property (another join) in ON clause!

dimensions:
  - name: destination
    expr: dim_destination.destination  # This depends on the chained join
```

**Problem:** Metric Views v1.1 **do not support transitive joins**. Each join must be directly between `source` and the joined table.

### Why This Limitation Exists

Metric Views are designed for **semantic queries** where:
- All joins must be explicit and direct
- Query optimizer can't handle multi-hop join semantics
- Prevents ambiguous join paths

**Allowed:** `source` → `dim_table`  
**Not Allowed:** `source` → `dim_table1` → `dim_table2`

### Available Solutions

#### Option 1: Remove Transitive Join (Chosen)

```yaml
# ✅ SOLUTION: Remove dim_destination join entirely
joins:
  - name: dim_property
    source: catalog.schema.dim_property
    'on': source.property_id = dim_property.property_id
  
  # Removed: dim_destination join

dimensions:
  - name: destination_id  # ✅ Use foreign key instead
    expr: dim_property.destination_id
    comment: Destination identifier for geographic market segmentation
```

**Trade-off:** Users see destination IDs instead of destination names, but can still filter/group by destination.

---

#### Option 2: Add destination_id to Source Table (Alternative)

```python
# In fact_property_engagement creation, denormalize destination_id
fact_engagement = (
    fact_engagement
    .join(dim_property, "property_id")
    .withColumn("destination_id", col("dim_property.destination_id"))
    .select("property_id", "destination_id", "view_count", ...)
)
```

Then in metric view:
```yaml
source: fact_property_engagement  # Now has destination_id!

joins:
  - name: dim_destination
    source: catalog.schema.dim_destination
    'on': source.destination_id = dim_destination.destination_id  # ✅ Direct join!

dimensions:
  - name: destination
    expr: dim_destination.destination  # ✅ Now works!
```

**Trade-off:** Requires modifying fact table structure.

---

#### Option 3: Create Enriched View (Alternative)

```sql
-- Create an enriched view with destination info
CREATE VIEW fact_property_engagement_enriched AS
SELECT 
  fpe.*,
  dp.destination_id,
  dd.destination,
  dd.country
FROM fact_property_engagement fpe
JOIN dim_property dp ON fpe.property_id = dp.property_id
JOIN dim_destination dd ON dp.destination_id = dd.destination_id
WHERE dp.is_current = true;
```

Then use enriched view as source:
```yaml
source: fact_property_engagement_enriched  # Has all columns!

joins:  # No joins needed!

dimensions:
  - name: destination
    expr: source.destination  # ✅ Already in source!
```

**Trade-off:** Creates additional view layer, but provides full flexibility.

---

### The Fix Applied

**We chose Option 1** (remove transitive join) because:
- ✅ Simplest change (no table modifications)
- ✅ Maintains metric view semantics
- ✅ Users can still analyze by destination_id
- ✅ Can enhance later if needed

### Impact

- ✅ Metric view now creates successfully
- ⚠️ Users see destination IDs instead of names (acceptable for initial deployment)
- 📋 Future enhancement: Consider Option 2 or 3 if destination names are critical

---

## Root Cause Analysis

### Primary Root Cause

**No schema validation before YAML creation.**

We created metric view YAML definitions based on:
- ❌ Assumptions about column names
- ❌ Business logic expectations  
- ❌ Patterns from other tables
- ❌ Incorrect cursor rule examples

**We never validated:**
- ✅ Source table exists
- ✅ All referenced columns exist in source table
- ✅ Joined tables exist and have required columns
- ✅ Join conditions reference valid columns
- ✅ Column data types match

### Contributing Factors

1. **Incorrect Cursor Rule Examples**
   - Rule showed `name` field in YAML (not supported)
   - Rule showed `time_dimension` in examples (not supported)
   - Rule showed `window_measures` in examples (not supported)
   - Examples used inconsistent column prefixes

2. **No Pre-Creation Validation Script**
   - No automated schema validation tool
   - Manual SQL checks not performed
   - Assumed Gold layer schemas without verification

3. **Similarity Bias**
   - Assumed `dim_host` schema matches `dim_user`
   - Expected `booking_count` column in all booking-related tables
   - Guessed `is_active` exists in all dimension tables

4. **No Schema Documentation Reference**
   - Didn't consult `gold_layer_design/yaml/` files first
   - Assumed schemas from memory/patterns

---

## Prevention Strategy

### 1. Schema-First Validation Process

**ALWAYS validate schemas BEFORE creating metric view YAML:**

```bash
# Step 1: List all columns in source table
grep "^- name:" gold_layer_design/yaml/{domain}/{table_name}.yaml

# Step 2: List all columns in joined tables
grep "^- name:" gold_layer_design/yaml/{domain}/{dim_table}.yaml

# Step 3: Verify join key existence
# Check that FK in source matches PK in dimension
```

**Example Validation:**
```bash
# For customer_analytics_metrics (source: dim_user)
grep "^- name:" gold_layer_design/yaml/identity/dim_user.yaml
# Output: user_key, user_id, email, name, country, user_type, is_business, 
#         company_name, created_at, effective_from, effective_to, is_current, ...
# ✅ Verify: is_current exists (not is_active)

# For joined fact_booking_detail
grep "^- name:" gold_layer_design/yaml/booking/fact_booking_detail.yaml
# Output: booking_id, user_id, host_id, property_id, ...
# ✅ Verify: Has booking_id (use COUNT), no booking_count column
```

---

### 2. Pre-Creation Validation Script

**Create automated schema validator:**

```python
# scripts/validate_metric_view_yaml.py
import yaml
from pathlib import Path
from databricks import sql

def validate_metric_view_schema(metric_view_yaml: dict, catalog: str, schema: str):
    """
    Validates that all columns referenced in metric view YAML exist in source tables.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # 1. Check source table exists and get columns
    source_table = metric_view_yaml['source']
    source_columns = get_table_columns(source_table)
    
    # 2. Validate dimensions
    for dim in metric_view_yaml.get('dimensions', []):
        expr = dim['expr']
        if expr.startswith('source.'):
            column = expr.replace('source.', '')
            if column not in source_columns:
                errors.append(f"Dimension '{dim['name']}': Column '{column}' not in source table")
    
    # 3. Validate measures
    for measure in metric_view_yaml.get('measures', []):
        # Parse expr to extract column references
        columns = extract_columns_from_expr(measure['expr'])
        for col_ref in columns:
            if col_ref.startswith('source.'):
                column = col_ref.replace('source.', '')
                if column not in source_columns:
                    errors.append(f"Measure '{measure['name']}': Column '{column}' not in source table")
    
    # 4. Validate joins
    for join in metric_view_yaml.get('joins', []):
        joined_table = join['source']
        joined_columns = get_table_columns(joined_table)
        
        # Validate ON clause columns
        on_clause = join['on']
        # Parse and validate columns in ON clause
        # ...
    
    return errors

def get_table_columns(fully_qualified_table: str) -> set:
    """Get list of columns from table using DESCRIBE TABLE."""
    # Execute: DESCRIBE TABLE {fully_qualified_table}
    # Return set of column names
    pass

# Usage
yaml_file = Path("src/wanderbricks_gold/semantic/metric_views/revenue_analytics_metrics.yaml")
metric_view = yaml.safe_load(open(yaml_file))

errors = validate_metric_view_schema(metric_view, catalog, schema)
if errors:
    print("❌ Validation Failed:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("✅ Validation Passed")
```

**Run before deployment:**
```bash
python scripts/validate_metric_view_yaml.py \
  --yaml src/wanderbricks_gold/semantic/metric_views/*.yaml \
  --catalog prashanth_subrahmanyam_catalog \
  --schema dev_prashanth_subrahmanyam_wanderbricks_gold
```

---

### 3. Pre-Creation Checklist

**Before creating any metric view YAML, complete this checklist:**

#### Schema Validation
- [ ] Run `DESCRIBE TABLE {source_table}` and save column list
- [ ] For each joined table, run `DESCRIBE TABLE` and save column list
- [ ] Verify all dimension `expr` columns exist in source or joined tables
- [ ] Verify all measure `expr` columns exist in source or joined tables
- [ ] Verify join ON clause columns exist in both source and joined tables
- [ ] Check column data types match for join keys

#### YAML Structure
- [ ] Version is `"1.1"` (quoted string)
- [ ] **NO `name` field** (name is in CREATE VIEW statement)
- [ ] NO `time_dimension` field (not supported in v1.1)
- [ ] NO `window_measures` field (not supported in v1.1)
- [ ] All dimensions use `source.` prefix for source columns
- [ ] All dimensions use `{join_name}.` prefix for joined columns
- [ ] All measures use correct column references with prefixes

#### Join Validation
- [ ] Each join is direct: `source.column = joined_table.column`
- [ ] NO transitive joins (no `joined_table1.col = joined_table2.col`)
- [ ] For SCD2 tables, include `AND {table}.is_current = true`
- [ ] Join keys have matching data types

#### Business Logic
- [ ] COUNT measures use `COUNT({table}.primary_key_column)`
- [ ] SUM measures reference actual numeric columns (not count columns)
- [ ] AVG measures use appropriate columns
- [ ] Pre-calculated columns (like conversion_rate) use AVG not SUM

---

### 4. Updated Cursor Rule

**Fix existing rule examples:**

```yaml
# ❌ OLD (incorrect)
version: "1.1"
- name: sales_performance_metrics  # NOT SUPPORTED!
  comment: ...
  
# ✅ NEW (correct)
version: "1.1"
comment: ...  # No 'name' field!
source: ...
```

**Add schema validation section to rule:**
```markdown
## Pre-Creation Schema Validation (MANDATORY)

Before creating metric view YAML, ALWAYS:

1. Verify source table schema:
   ```bash
   grep "^- name:" gold_layer_design/yaml/{domain}/{table}.yaml
   ```

2. Verify all joined table schemas

3. Create column reference checklist:
   - Source columns: [list]
   - dim_table1 columns: [list]
   - dim_table2 columns: [list]

4. Validate every `expr` field references only existing columns

5. For COUNT measures, verify primary key column exists

6. For SCD2 joins, verify `is_current` column exists
```

---

### 5. Documentation Standards

**Always document column sources in YAML comments:**

```yaml
dimensions:
  - name: is_current
    expr: source.is_current
    comment: >
      Current user record version indicator (SCD Type 2). 
      TRUE for active version, FALSE for historical records.
      Column: dim_user.is_current (BOOLEAN)
    # ^ Document actual column name and type
```

---

## Metrics & Impact

### Time Investment vs Savings

**Investment:**
- Post-mortem analysis: 30 min
- Rule update: 20 min
- Validation script creation: 30 min
- Documentation: 40 min
- **Total: 2 hours**

**Expected Savings (per future metric view deployment):**
- Schema validation errors: 0 (was 5)
- Deployment iterations: 1 (was 7)
- Debugging time: <5 min (was 2 hours)
- **Per-deployment savings: ~2 hours × 90% = 1.8 hours**

**ROI:** After 2 future deployments, investment is fully recovered.

---

## Success Metrics

### Before (This Deployment)
- ❌ 0/5 metric views succeeded on first deployment
- ❌ 7 deployment iterations required
- ❌ 2 hours total debugging time
- ❌ 100% of failures were preventable schema issues
- ❌ 0% schema validation before creation

### After (With Prevention Strategy)
- ✅ Target: 5/5 metric views succeed on first deployment
- ✅ Target: 1 deployment iteration (validation + deploy)
- ✅ Target: <10 min debugging time (only edge cases)
- ✅ Target: 100% schema validation before YAML creation
- ✅ Target: Automated pre-deployment validation catches all schema issues

---

## Key Learnings

### 1. Schema is Source of Truth

**Lesson:** Never assume column names or structure. Always verify against actual table schemas.

**Action:** Consult `gold_layer_design/yaml/` definitions before creating metric view YAML.

---

### 2. Cursor Rules Must Be Accurate

**Lesson:** Incorrect examples in cursor rules lead to systematic errors across all implementations.

**Action:** 
- Validate all rule examples against official documentation
- Remove deprecated/unsupported fields from examples
- Update rules immediately when discovering inaccuracies

---

### 3. Validation Before Implementation

**Lesson:** Manual validation is tedious but automated validation is robust.

**Action:** 
- Create automated schema validation scripts
- Integrate into CI/CD pipeline
- Make validation mandatory before deployment

---

### 4. Error Messages Are Helpful

**Lesson:** Databricks provides excellent error messages with column suggestions.

**Example:**
```
Did you mean one of the following? 
[`source`.`email`, `source`.`country`, `source`.`is_current`]
```

**Action:** Always read full error messages - they often contain the solution.

---

### 5. Transitive Joins Not Supported

**Lesson:** Metric Views v1.1 only support direct `source` → `joined_table` joins.

**Workaround:**
1. Remove transitive join (use foreign key directly)
2. Denormalize fact table to include needed columns
3. Create enriched view with all needed columns

---

## Recommendations

### Immediate Actions (Complete)
- [x] Fix all 5 metric view YAML files
- [x] Update Python deployment script
- [x] Update `.cursor/rules/semantic-layer/14-metric-views-patterns.mdc`
- [x] Document post-mortem findings

### Short-Term Actions (Next Sprint)
- [ ] Create automated schema validation script
- [ ] Add validation to CI/CD pipeline
- [ ] Document schema validation process in deployment guide
- [ ] Create metric view creation checklist template

### Long-Term Actions (Next Quarter)
- [ ] Build schema validation into metric view authoring tool
- [ ] Create interactive schema browser for Gold layer
- [ ] Implement automated schema drift detection
- [ ] Add metric view schema validation to pre-commit hooks

---

## Conclusion

The initial deployment of 5 metric views resulted in **100% failure rate** due to preventable schema validation issues. Through systematic debugging and root cause analysis, we identified three critical gaps:

1. **Incorrect cursor rule examples** showing unsupported `name` field
2. **No schema validation** before YAML creation
3. **Transitive join limitations** not clearly documented

By implementing a **schema-first validation process**, **automated validation scripts**, and **updated cursor rules**, we can reduce future metric view deployment failures from 100% to near-zero.

**Investment:** 2 hours of prevention  
**Return:** ~2 hours saved per future deployment  
**ROI:** Immediate (breaks even after 1 deployment)

---

## References

- [Databricks Metric Views SQL Documentation](https://docs.databricks.com/aws/en/metric-views/create/sql)
- [Metric Views YAML Reference](https://docs.databricks.com/aws/en/metric-views/yaml-ref)
- [Metric Views Joins Documentation](https://docs.databricks.com/aws/en/metric-views/joins)
- [Gold Layer Schema Definitions](../../gold_layer_design/yaml/)
- [Deployment Success Summary](../deployment/metric-views-deployment-success.md)

---

**Post-mortem completed:** 2025-12-09  
**Status:** All issues resolved, prevention strategies documented  
**Next Review:** After next metric view deployment

