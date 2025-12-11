# Wanderbricks Silver Layer - Complete Deployment Guide

## 📋 Prerequisites Checklist

Before deploying the Silver layer, ensure:

- [ ] **Databricks CLI installed** (v0.200.0+)
  ```bash
  databricks --version
  ```

- [ ] **Authenticated to Databricks workspace**
  ```bash
  databricks auth login --host <workspace-url> --profile wanderbricks
  export DATABRICKS_CONFIG_PROFILE=wanderbricks
  ```

- [ ] **Bronze layer deployed** and populated with data
  ```sql
  -- Verify Bronze tables exist
  SHOW TABLES IN prashanth_subrahmanyam_catalog.wanderbricks;
  ```

- [ ] **Workspace permissions** - Must have:
  - CREATE CATALOG permission
  - CREATE SCHEMA permission
  - CREATE TABLE permission
  - Can run DLT pipelines

---

## 🚀 Deployment Steps

### Step 1: Validate Asset Bundle Configuration

```bash
# Navigate to project root
cd /path/to/Wanderbricks

# Validate bundle syntax
databricks bundle validate

# Expected output:
# ✓ Bundle validation passed
```

**If validation fails:**
- Check `databricks.yml` syntax
- Ensure all `resources/*.yml` files are valid YAML
- Verify file paths in `include:` section

---

### Step 2: Deploy Bundle Resources

```bash
# Deploy to dev environment
databricks bundle deploy -t dev

# Expected output:
# ✓ Created schema: prashanth_subrahmanyam_catalog.wanderbricks_silver
# ✓ Created job: [dev] Wanderbricks Silver - DQ Rules Setup
# ✓ Created pipeline: [dev] Wanderbricks Silver Layer Pipeline
# ✓ Created job: [dev] Wanderbricks Silver - Validation & Testing
```

**This creates:**
- Unity Catalog schemas (Bronze, Silver, Gold)
- DQ setup job
- Silver DLT pipeline (not running yet)
- Validation job

---

### Step 3: Create DQ Rules Table (CRITICAL - Must Run First!)

```bash
# Run the DQ setup job
databricks bundle run silver_dq_setup_job -t dev

# Monitor in Databricks UI:
# Workflows → Jobs → [dev] Wanderbricks Silver - DQ Rules Setup
```

**Expected output:**
```
================================================================================
WANDERBRICKS DATA QUALITY RULES TABLE SETUP
================================================================================
Creating prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules table...
✓ Created DQ rules table
✓ Populated 70+ data quality rules

Data Quality Rules Summary:
+-----------------------------+----------+----------+
|table_name                   |severity  |rule_count|
+-----------------------------+----------+----------+
|silver_bookings              |critical  |8         |
|silver_bookings              |warning   |3         |
|silver_payments              |critical  |5         |
...
+-----------------------------+----------+----------+

✓ DQ rules table created and populated!
```

**Verify DQ rules table:**
```sql
SELECT 
  table_name,
  severity,
  COUNT(*) as rule_count
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
GROUP BY table_name, severity
ORDER BY table_name, severity;

-- Expected: 70+ rules across all Silver tables
```

---

### Step 4: Trigger Silver DLT Pipeline

```bash
# Start the DLT pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# Monitor in Databricks UI:
# Workflows → Delta Live Tables → [dev] Wanderbricks Silver Layer Pipeline
```

**Expected pipeline graph:**
```
dq_rules (metadata)
    ↓
bronze_users → silver_users
bronze_hosts → silver_hosts
bronze_destinations → silver_destinations
...
bronze_bookings → silver_bookings
                → silver_bookings_quarantine
bronze_payments → silver_payments
                → silver_payments_quarantine
...
    ↓
dq_bookings_metrics
dq_payments_metrics
dq_referential_integrity
dq_overall_health
```

**Pipeline runtime:** ~5-15 minutes (depending on Bronze data volume)

**Watch for:**
- ✅ All tables show "COMPLETED" status
- ✅ No fatal errors (warnings are OK)
- ⚠️ Check quarantine tables for records (some are expected)

---

### Step 5: Run Validation Job

```bash
# Run comprehensive validation
databricks bundle run silver_validation_job -t dev

# Monitor in Databricks UI:
# Workflows → Jobs → [dev] Wanderbricks Silver - Validation & Testing
```

**Validation checks:**
1. ✅ **Table counts** - All 22 Silver tables exist
2. ✅ **DQ metrics** - Rules loaded, quarantine rates acceptable
3. ✅ **Referential integrity** - All FK relationships valid
4. ✅ **Quarantine analysis** - Failure patterns identified

**Expected output:**
```
WANDERBRICKS SILVER LAYER - TABLE COUNT VALIDATION
================================================================================
Dimensions Tables:
  ✓ silver_users: 1,000 records - PASS
  ✓ silver_hosts: 250 records - PASS
  ...

Facts Tables:
  ✓ silver_bookings: 5,000 records - PASS
  ✓ silver_payments: 4,800 records - PASS
  ...

Quarantine Tables:
  ✓ silver_bookings_quarantine: 50 records - PASS
  ✓ silver_payments_quarantine: 20 records - PASS

✅ Table count validation PASSED!
All 22 expected tables exist.

================================================================================
DQ METRICS VALIDATION
================================================================================
✓ DQ rules table exists
✓ Total rules: 75

Bookings Quarantine Analysis:
  Silver records: 5,000
  Quarantine records: 50
  Quarantine rate: 0.99%
  ✓ GOOD: Low quarantine rate

✅ DQ METRICS VALIDATION PASSED!

================================================================================
REFERENTIAL INTEGRITY VALIDATION
================================================================================
+-----------------------------+----------------+--------+
|check_name                   |orphaned_records|status  |
+-----------------------------+----------------+--------+
|bookings_to_users            |0               |PASS    |
|bookings_to_properties       |0               |PASS    |
|payments_to_bookings         |0               |PASS    |
|reviews_to_bookings          |0               |PASS    |
+-----------------------------+----------------+--------+

✅ REFERENTIAL INTEGRITY VALIDATION PASSED!

================================================================================
QUARANTINE ANALYSIS COMPLETE!
================================================================================
```

---

## 🔍 Post-Deployment Verification

### Verify All Tables

```sql
-- List all Silver tables
SHOW TABLES IN prashanth_subrahmanyam_catalog.wanderbricks_silver;

-- Expected: 22 tables
-- 9 dimensions + 6 facts + 2 quarantine + 4 monitoring + 1 dq_rules
```

### Check Table Counts

```sql
SELECT 
  'silver_users' as table_name, COUNT(*) as record_count 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_users
UNION ALL
SELECT 'silver_bookings', COUNT(*) 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings
UNION ALL
SELECT 'silver_bookings_quarantine', COUNT(*) 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine
UNION ALL
SELECT 'dq_rules', COUNT(*) 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules;
```

### Review DQ Metrics

```sql
-- Overall health dashboard
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_overall_health
ORDER BY table_type, table_name;

-- Bookings DQ metrics
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_bookings_metrics;

-- Referential integrity
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_referential_integrity
WHERE status != 'PASS';
```

### Sample Silver Data

```sql
-- Sample users
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_users
LIMIT 10;

-- Sample bookings with derived fields
SELECT 
  booking_id,
  user_id,
  property_id,
  nights_booked,
  is_long_stay,
  is_high_value,
  processed_timestamp
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings
LIMIT 10;

-- Sample quarantined records
SELECT 
  booking_id,
  quarantine_reason,
  quarantine_timestamp
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine
LIMIT 10;
```

---

## 🔧 Managing Data Quality Rules

### View All Rules

```sql
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
ORDER BY table_name, severity, rule_name;
```

### Update a Rule Threshold

```sql
-- Example: Increase maximum booking amount
UPDATE prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
SET constraint_sql = 'total_amount BETWEEN 10 AND 200000',
    updated_timestamp = CURRENT_TIMESTAMP()
WHERE table_name = 'silver_bookings' 
  AND rule_name = 'reasonable_amount';

-- Then re-run DLT pipeline to apply changes
```

### Change Rule Severity

```sql
-- Example: Downgrade from critical to warning
UPDATE prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
SET severity = 'warning',
    updated_timestamp = CURRENT_TIMESTAMP()
WHERE table_name = 'silver_bookings' 
  AND rule_name = 'valid_guests';
```

### Add New Rule

```sql
INSERT INTO prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules VALUES (
  'silver_bookings',
  'valid_status',
  'status IN (''pending'', ''confirmed'', ''cancelled'', ''completed'')',
  'warning',
  'Booking status should be one of the valid types',
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);
```

**After updating rules, re-run the DLT pipeline:**
```bash
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"
```

---

## 🐛 Troubleshooting

### Issue 1: "Table or view not found: dq_rules"

**Cause:** DLT pipeline ran before DQ setup job

**Solution:**
```bash
# Run DQ setup job first
databricks bundle run silver_dq_setup_job -t dev

# Then re-run DLT pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"
```

---

### Issue 2: "No module named 'dq_rules_loader'"

**Cause:** `dq_rules_loader.py` has notebook header

**Solution:**
```bash
# Check first line
head -1 src/wanderbricks_silver/dq_rules_loader.py

# Should output: """
# Should NOT output: # Databricks notebook source

# If it has notebook header, remove it:
sed -i '' '1{/# Databricks notebook source/d;}' src/wanderbricks_silver/dq_rules_loader.py

# Re-deploy
databricks bundle deploy -t dev
```

---

### Issue 3: High Quarantine Rate (>10%)

**Cause:** Rules too strict or bad source data

**Solution:**
```sql
-- Find most common failure reasons
SELECT 
  quarantine_reason,
  COUNT(*) as failure_count,
  (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine)) as pct
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine
GROUP BY quarantine_reason
ORDER BY failure_count DESC;

-- Adjust rules based on results
UPDATE prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
SET severity = 'warning'  -- or adjust constraint_sql
WHERE table_name = 'silver_bookings' 
  AND rule_name = 'problematic_rule';
```

---

### Issue 4: Pipeline Failing

**Check pipeline logs:**
1. Navigate to **Workflows** → **Delta Live Tables**
2. Click **[dev] Wanderbricks Silver Layer Pipeline**
3. Click **Event Logs** tab
4. Filter by severity: **ERROR**

**Common fixes:**
- Verify Bronze tables exist and have data
- Check catalog/schema permissions
- Ensure `dq_rules` table exists
- Verify all notebook paths in `silver_dlt_pipeline.yml`

---

### Issue 5: Bundle Validation Errors

**Common errors:**

**Error:** `duplicate resource key`
**Solution:** Each job/pipeline must have unique key in YAML

**Error:** `invalid path reference`
**Solution:** Check relative paths from `resources/` directory:
- From `resources/*.yml` → Use `../src/`
- From `resources/silver/*.yml` → Use `../../src/`

**Error:** `invalid variable reference`
**Solution:** Use `${var.variable_name}` format (not `${variable_name}`)

---

## 📊 Monitoring and Observability

### Real-Time DQ Dashboard

```sql
-- Overall health
SELECT 
  table_name,
  table_type,
  record_count,
  minutes_since_update,
  data_freshness_status
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_overall_health
WHERE data_freshness_status != 'CURRENT'
ORDER BY minutes_since_update DESC;
```

### Quarantine Trends

```sql
-- Quarantine trend over time
SELECT 
  DATE(quarantine_timestamp) as quarantine_date,
  COUNT(*) as quarantined_records
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine
GROUP BY DATE(quarantine_timestamp)
ORDER BY quarantine_date DESC;
```

### DQ Rule Audit

```sql
-- View rule change history
SELECT *
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules VERSION AS OF 1
WHERE table_name = 'silver_bookings';
```

---

## 🎯 Success Criteria

Silver layer deployment is successful when:

- ✅ All 22 tables exist (9 dims + 6 facts + 2 quarantine + 4 monitoring + 1 dq_rules)
- ✅ DQ rules table has 70+ rules
- ✅ Quarantine rate < 5% (ideal < 2%)
- ✅ All referential integrity checks pass
- ✅ Data freshness < 60 minutes
- ✅ No orphaned records in FK checks
- ✅ Monitoring views populated with metrics

---

## 📚 Next Steps

After successful Silver deployment:

1. **Review quarantine patterns** and adjust rules as needed
2. **Set up alerts** for high quarantine rates or failed pipelines
3. **Proceed to Gold layer** implementation for business aggregates
4. **Document domain-specific rules** discovered during validation

---

## 📖 Reference Commands

```bash
# Deploy bundle
databricks bundle deploy -t dev

# Run DQ setup (one-time)
databricks bundle run silver_dq_setup_job -t dev

# Trigger DLT pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# Run validation
databricks bundle run silver_validation_job -t dev

# Destroy all resources (⚠️ CAUTION)
databricks bundle destroy -t dev
```

---

## 🆘 Support

**For issues:**
1. Check this guide's troubleshooting section
2. Review DLT pipeline logs in Databricks UI
3. Run validation job to identify specific failures
4. Check `dq_rules` table for rule definitions

**Documentation:**
- [Silver Layer README](src/wanderbricks_silver/README.md)
- [DLT Expectations Patterns](.cursor/rules/silver/07-dlt-expectations-patterns.mdc)
- [Asset Bundle Configuration](.cursor/rules/common/02-databricks-asset-bundles.mdc)

