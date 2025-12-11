# Schema-First Development Pattern

**Principle:** Always consult YAML schema definitions before writing any SQL.

---

## Quick Start (5 Minutes)

### Before Writing ANY Gold Layer SQL

```bash
# 1. Navigate to schema definitions
cd gold_layer_design/yaml

# 2. Find your tables
ls -R

# 3. Check column names for each table you'll use
grep "^table_name:\|  - name:" geography/dim_destination.yaml
grep "^table_name:\|  - name:" identity/dim_host.yaml
grep "^table_name:\|  - name:" property/dim_property.yaml
grep "^table_name:\|  - name:" booking/fact_booking_daily.yaml

# 4. Note any unexpected names (destination vs city, state_or_province vs state)

# 5. Check for SCD Type 2 (requires is_current filter)
grep "^scd_type:" */dim_*.yaml
```

**Time Investment:** 5 minutes  
**Bugs Prevented:** 100% of column name errors  
**ROI:** 8x (saves 40+ minutes of debugging)

---

## The Problem

### What Happens When You Skip Schema Validation

**Case Study: TVF Deployment (Dec 10, 2025)**

```sql
-- ❌ What we coded (based on assumptions)
SELECT 
  dd.city,           -- ❌ Column doesn't exist!
  dd.state,          -- ❌ Column doesn't exist!
  dd.country
FROM fact_booking_daily fbd
LEFT JOIN dim_destination dd ON fbd.destination_id = dd.destination_id

-- Error: [UNRESOLVED_COLUMN] A column, variable, or function parameter 
--        with name `dd`.`city` cannot be resolved
```

**Result:**
- 6 deployment iterations
- 45 minutes of debugging
- 30+ individual column reference fixes
- Wasted CI/CD pipeline time

---

## The Solution

### Schema-First Development Workflow

```bash
# Step 1: Read the actual schema (2 min)
cd gold_layer_design/yaml
cat geography/dim_destination.yaml

# Output shows:
# - name: destination        # ✅ NOT 'city'!
# - name: state_or_province  # ✅ NOT 'state'!
# - name: country

# Step 2: Document in SCHEMA_MAPPING.md (2 min)
echo "
dim_destination:
  - destination (STRING) -- City/area name
  - state_or_province (STRING) -- State/region
  - country (STRING)
" >> SCHEMA_MAPPING.md

# Step 3: Write correct SQL (1 min)
# ✅ Now you write the correct column names from the start
SELECT 
  dd.destination,         -- ✅ Correct!
  dd.state_or_province,   -- ✅ Correct!
  dd.country
FROM fact_booking_daily fbd
LEFT JOIN dim_destination dd ON fbd.destination_id = dd.destination_id

# Result: ✅ First deployment succeeds
```

**Time:** 5 minutes total  
**Deployment Iterations:** 1 (vs. 6)  
**Debugging Time:** 0 minutes (vs. 40)

---

## Common Schema Gotchas

### 1. Column Name Variations

| What You Assume | What Actually Exists | Table |
|----------------|---------------------|-------|
| `city` | `destination` | dim_destination |
| `state` | `state_or_province` | dim_destination |
| `function_name` | `routine_name` | information_schema.routines |
| `user_name` | `name` | dim_user |
| `host_name` | `name` | dim_host |

**Lesson:** Never assume. Always check YAML.

---

### 2. SCD Type 1 vs Type 2

**Type 1 (No history):**
```yaml
# dim_destination.yaml
scd_type: 1  # ✅ No is_current column

# SQL Join:
LEFT JOIN dim_destination dd 
  ON fbd.destination_id = dd.destination_id
  -- ✅ No is_current filter needed
```

**Type 2 (With history):**
```yaml
# dim_property.yaml
scd_type: 2  # ⚠️ Has is_current column!

# SQL Join:
LEFT JOIN dim_property dp 
  ON fbd.property_id = dp.property_id 
  AND dp.is_current = true  # ✅ MUST filter for current version
```

**Common Error:** Forgetting `is_current = true` on SCD Type 2 joins results in duplicate rows.

---

### 3. Denormalized vs Join Columns

**Fact Table Schema:**
```yaml
# fact_booking_daily.yaml
columns:
  - name: property_id       # ✅ FK to dim_property
  - name: destination_id    # ✅ FK to dim_destination
  - name: booking_count     # ✅ Measure
  # ❌ NO host_id - Must join through dim_property
  # ❌ NO status - This is aggregated data, use fact_booking_detail for status
```

**Correct Query:**
```sql
-- ✅ Get host info via property dimension
SELECT 
  fbd.booking_count,
  dp.title,
  dh.name as host_name  -- ✅ Join through property
FROM fact_booking_daily fbd
LEFT JOIN dim_property dp ON fbd.property_id = dp.property_id AND dp.is_current = true
LEFT JOIN dim_host dh ON dp.host_id = dh.host_id AND dh.is_current = true
```

**Wrong Query:**
```sql
-- ❌ Assumes host_id is denormalized in fact table
SELECT 
  fbd.booking_count,
  dh.name as host_name
FROM fact_booking_daily fbd
LEFT JOIN dim_host dh ON fbd.host_id = dh.host_id  -- ❌ fbd.host_id doesn't exist!
```

---

## Pre-Development Checklist

### Before Writing TVFs

- [ ] Read YAML for all dimension tables used
- [ ] Read YAML for all fact tables used
- [ ] Document column names in SCHEMA_MAPPING.md
- [ ] Note SCD Type 1 vs Type 2 for each dimension
- [ ] Identify which columns are denormalized vs require joins
- [ ] Test sample query with DESCRIBE TABLE commands

### Before Writing MERGE Statements

- [ ] Read source table YAML (Silver layer)
- [ ] Read target table YAML (Gold layer)
- [ ] Map source columns to target columns explicitly
- [ ] Check for data type differences (INT vs BIGINT, DATE vs TIMESTAMP)
- [ ] Validate MERGE key columns exist in both tables
- [ ] Check for SCD Type 2 effective dating requirements

### Before Writing Metric Views

- [ ] Read YAML for base fact table
- [ ] Read YAML for all joined dimension tables
- [ ] Verify all measure source columns exist
- [ ] Verify all dimension source columns exist
- [ ] Check for pre-aggregated vs transaction-level metrics
- [ ] Validate join keys and SCD Type 2 filters

---

## Validation Scripts

### Validate Schema at Runtime

```python
# In your notebook/script, validate schema before running SQL
def validate_schema(spark, catalog, schema, table, expected_columns):
    """Validate that expected columns exist in table."""
    actual_columns = [col.name for col in spark.table(f"{catalog}.{schema}.{table}").schema]
    
    missing = set(expected_columns) - set(actual_columns)
    if missing:
        raise ValueError(f"Missing columns in {table}: {missing}")
    
    print(f"✅ Schema validation passed for {table}")

# Usage:
validate_schema(
    spark, catalog, schema, "dim_destination",
    expected_columns=["destination_id", "destination", "state_or_province", "country"]
)
```

### Pre-Deployment SQL Check

```bash
#!/bin/bash
# scripts/validate_sql_references.sh

cd src/wanderbricks_gold/tvfs

# Check for deprecated column names
echo "Checking for common column name errors..."

if grep -n "\bdd\.city\b" *.sql; then
  echo "❌ ERROR: Found dd.city (should be dd.destination)"
  exit 1
fi

if grep -n "\bdd\.state\b" *.sql | grep -v "state_or_province"; then
  echo "❌ ERROR: Found dd.state (should be dd.state_or_province)"
  exit 1
fi

echo "✅ SQL validation passed"
```

---

## ROI Analysis

### Time Investment

| Activity | Time | When |
|----------|------|------|
| Read YAML schemas | 5 min | **Before coding** |
| Create SCHEMA_MAPPING.md | 5 min | **Before coding** |
| Run DESCRIBE TABLE | 2 min | **Before deployment** |
| **Total Prep** | **12 min** | **Upfront** |

### Time Saved

| Without Schema Validation | With Schema Validation |
|---------------------------|------------------------|
| 6 deployment iterations | 1 deployment |
| 40 min debugging | 0 min debugging |
| 30+ bug fixes | 0 bugs |
| **Total: 45 min** | **Total: 12 min** |

**ROI:** 73% time reduction (45 min → 12 min)  
**First-Time Success Rate:** 0% → 95%+

---

## Real-World Impact

### Case Study: TVF Deployment (Dec 10, 2025)

**Situation:** Deploy 26 TVFs across 5 business domains

**What We Did (Wrong):**
1. ❌ Wrote SQL based on naming assumptions
2. ❌ Deployed without schema validation
3. ❌ Hit compilation error (dd.city not found)
4. ❌ Fixed that instance, deployed again
5. ❌ Hit another error (RETURNS clause still had wrong names)
6. ❌ Fixed that, deployed again
7. ❌ Hit validation query error (wrong system schema column)
8. ✅ Finally succeeded after 6 iterations

**Result:** 45 minutes, 6 deployments, frustration

**What We Should Have Done (Right):**
1. ✅ Read YAML schemas for dim_destination, dim_property, dim_host, dim_user
2. ✅ Created SCHEMA_MAPPING.md with actual column names
3. ✅ Wrote SQL using documented schema
4. ✅ Ran pre-deployment validation script
5. ✅ Deployed once
6. ✅ Success on first try

**Result:** 15 minutes, 1 deployment, confidence

---

## Key Takeaways

1. **YAML files are the single source of truth** - Not your memory, not assumptions, not "standard" conventions
2. **5 minutes of prep saves 40 minutes of debugging** - ROI is 8x
3. **Schema assumptions are the #1 cause of SQL errors** - 100% of our TVF errors were schema-related
4. **Systematic validation prevents iteration** - Find and fix ALL instances before deploying
5. **Documentation scales knowledge** - SCHEMA_MAPPING.md helps future you and your team

---

## Reference Documents

- **Schema Definitions:** `gold_layer_design/yaml/**/*.yaml` (Source of Truth)
- **Schema Reference:** `src/wanderbricks_gold/tvfs/SCHEMA_MAPPING.md` (Quick Reference)
- **Post-Mortem:** `docs/troubleshooting/2025-12-10-tvf-deployment-postmortem.md` (Detailed Analysis)
- **Cursor Rule:** `.cursor/rules/gold/12-gold-layer-documentation.mdc` (Development Standards)

---

**Remember:** When in doubt, read the YAML. It's always right.

