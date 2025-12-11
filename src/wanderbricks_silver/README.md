# Wanderbricks Silver Layer

Production-grade Delta Live Tables (DLT) Silver layer with Delta table-based data quality rules.

## 📁 Project Structure

```
src/wanderbricks_silver/
├── setup_dq_rules_table.py        # One-time: Create and populate DQ rules Delta table
├── dq_rules_loader.py             # Pure Python (NO notebook header) - load rules from Delta table
├── silver_dimensions.py           # DLT: Dimension tables (users, hosts, destinations, etc.)
├── silver_bookings.py             # DLT: Bookings and payments with quarantine
├── silver_engagement.py           # DLT: Engagement tables (clickstream, reviews, support)
├── data_quality_monitoring.py     # DLT: Data quality monitoring views
└── README.md                      # This file

resources/silver/
├── silver_dq_setup_job.yml        # Asset Bundle: DQ rules setup job
└── silver_dlt_pipeline.yml        # Asset Bundle: Silver DLT pipeline
```

## 🎯 Key Features

### Delta Table-Based Data Quality Rules
- ✅ **Centralized Rule Management** - All rules stored in Unity Catalog Delta table
- ✅ **Runtime Updates** - Change rules via SQL UPDATE (no code deployment needed)
- ✅ **Auditable** - Full change history via Delta time travel
- ✅ **Portable** - Same rules across dev/prod environments

**Official Pattern:** [Portable and Reusable Expectations](https://docs.databricks.com/aws/en/ldp/expectation-patterns#portable-and-reusable-expectations)

### Streaming Ingestion
- ✅ **Incremental** - Reads from Bronze via `dlt.read_stream()`
- ✅ **Auto-scaling** - Serverless compute adjusts to workload
- ✅ **Change Data Feed** - Enabled on all tables for downstream propagation

### Data Quality Enforcement
- ✅ **Critical Rules** - Records dropped/quarantined if violated (pipeline continues)
- ✅ **Warning Rules** - Violations logged but records pass through
- ✅ **Quarantine Tables** - Invalid records captured for review
- ✅ **Never Fails** - Pipeline continues even with data quality issues

### Monitoring
- ✅ **DQ Metrics** - Real-time quality metrics per table
- ✅ **Referential Integrity** - Cross-table FK validation
- ✅ **Overall Health** - Dashboard showing freshness and counts

## 📊 Silver Tables Created

### Dimension Tables
- `silver_users` - User accounts with validated emails
- `silver_hosts` - Property hosts with ratings
- `silver_destinations` - Travel destinations with geography
- `silver_countries` - Country reference data
- `silver_properties` - Property listings with pricing
- `silver_amenities` - Property amenities catalog
- `silver_employees` - Host employees
- `silver_property_amenities` - Property-amenity bridge table
- `silver_property_images` - Property image URLs

### Fact Tables
- `silver_bookings` - Reservation bookings (with quarantine)
- `silver_booking_updates` - Booking modification history
- `silver_payments` - Payment transactions (with quarantine)
- `silver_reviews` - Property reviews and ratings
- `silver_clickstream` - User interaction events (view, click, search, filter)
- `silver_page_views` - Property detail page views
- `silver_customer_support_logs` - Support tickets with nested messages

### Quarantine Tables
- `silver_bookings_quarantine` - Invalid bookings
- `silver_payments_quarantine` - Invalid payments

### Monitoring Views
- `dq_bookings_metrics` - Bookings quality metrics
- `dq_payments_metrics` - Payments quality metrics
- `dq_referential_integrity` - FK validation checks
- `dq_overall_health` - Overall pipeline health

## 🚀 Deployment Guide

### Prerequisites

1. **Bronze layer** deployed and populated
2. **databricks.yml** configured with variables:
   ```yaml
   variables:
     catalog:
       default: prashanth_subrahmanyam_catalog
     bronze_schema:
       default: wanderbricks
     silver_schema:
       default: wanderbricks_silver
   ```

### Step 1: Create DQ Rules Table (One-Time)

**This MUST be run BEFORE deploying the DLT pipeline.**

```bash
# Deploy the job
databricks bundle deploy -t dev

# Run the DQ setup job
databricks bundle run silver_dq_setup_job -t dev
```

**Expected Output:**
```
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
|silver_payments              |warning   |1         |
...
+-----------------------------+----------+----------+
```

**Verify:**
```sql
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
ORDER BY table_name, severity, rule_name;
```

### Step 2: Deploy Silver DLT Pipeline

```bash
# Already deployed in Step 1, now trigger the pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"
```

**Monitor Progress:**
- Open Databricks workspace
- Navigate to **Workflows** → **Delta Live Tables**
- Click on pipeline: **[dev] Wanderbricks Silver Layer Pipeline**
- Watch pipeline graph and logs

### Step 3: Verify Silver Tables

```sql
-- Check table counts
SELECT 
  'silver_users' as table_name, COUNT(*) as record_count 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_users
UNION ALL
SELECT 'silver_bookings', COUNT(*) 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings
UNION ALL
SELECT 'silver_bookings_quarantine', COUNT(*) 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine;

-- Check DQ metrics
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_bookings_metrics;

-- Check referential integrity
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_referential_integrity
WHERE status != 'PASS';

-- Check overall health
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_overall_health
ORDER BY table_type, table_name;
```

## 🔧 Managing Data Quality Rules at Runtime

### View Rules

```sql
-- View all rules for a table
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
WHERE table_name = 'silver_bookings'
ORDER BY severity, rule_name;

-- Count rules by severity
SELECT 
  table_name,
  severity,
  COUNT(*) as rule_count
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
GROUP BY table_name, severity
ORDER BY table_name, severity;
```

### Update Rules (No Code Deployment!)

```sql
-- Update a constraint threshold
UPDATE prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
SET constraint_sql = 'total_amount BETWEEN 5 AND 150000',
    updated_timestamp = CURRENT_TIMESTAMP()
WHERE table_name = 'silver_bookings' 
  AND rule_name = 'reasonable_amount';

-- Change severity (downgrade from critical to warning)
UPDATE prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
SET severity = 'warning',
    updated_timestamp = CURRENT_TIMESTAMP()
WHERE table_name = 'silver_bookings' 
  AND rule_name = 'valid_guests';

-- Add new rule
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

**After updating:** Trigger the DLT pipeline to apply new rules:
```bash
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"
```

### Audit Rule Changes (Delta Time Travel)

```sql
-- View rules as of specific version
SELECT * 
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules VERSION AS OF 1
WHERE table_name = 'silver_bookings';

-- Compare current vs previous rules
SELECT 
  current.rule_name,
  current.constraint_sql as current_constraint,
  current.severity as current_severity,
  previous.constraint_sql as previous_constraint,
  previous.severity as previous_severity
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules current
LEFT JOIN prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules VERSION AS OF 1 previous
  ON current.table_name = previous.table_name 
  AND current.rule_name = previous.rule_name
WHERE current.constraint_sql != previous.constraint_sql
   OR current.severity != previous.severity;
```

## 📈 Monitoring Queries

### Check Quarantine Rates

```sql
SELECT 
  metric_timestamp,
  silver_record_count,
  quarantine_record_count,
  silver_pass_rate,
  quarantine_rate
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_bookings_metrics
ORDER BY metric_timestamp DESC;
```

### Find Quarantined Records

```sql
-- View quarantined bookings
SELECT 
  booking_id,
  user_id,
  property_id,
  quarantine_reason,
  quarantine_timestamp
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine
ORDER BY quarantine_timestamp DESC
LIMIT 100;
```

### Check Data Freshness

```sql
SELECT 
  table_name,
  table_type,
  record_count,
  last_processed_timestamp,
  minutes_since_update,
  data_freshness_status
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_overall_health
WHERE data_freshness_status != 'CURRENT'
ORDER BY minutes_since_update DESC;
```

## 🐛 Troubleshooting

### Issue: "Table or view not found: dq_rules"

**Solution:** You need to run `silver_dq_setup_job` BEFORE deploying the DLT pipeline.

```bash
databricks bundle run silver_dq_setup_job -t dev
```

### Issue: "No module named 'dq_rules_loader'"

**Solution:** Verify `dq_rules_loader.py` does NOT have `# Databricks notebook source` header.

```bash
# Check file
head -1 src/wanderbricks_silver/dq_rules_loader.py

# Should output:
# """

# Should NOT output:
# # Databricks notebook source
```

If you see the notebook header, remove it:
```bash
# Remove first line if it's the notebook header
sed -i '' '1{/# Databricks notebook source/d;}' src/wanderbricks_silver/dq_rules_loader.py
```

### Issue: High Quarantine Rate

**Solution:** Review quarantine reasons and adjust rules:

```sql
-- Find most common quarantine reasons
SELECT 
  quarantine_reason,
  COUNT(*) as failure_count
FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.silver_bookings_quarantine
GROUP BY quarantine_reason
ORDER BY failure_count DESC;

-- If a rule is too strict, update it
UPDATE prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules
SET severity = 'warning'  -- or adjust constraint_sql
WHERE table_name = 'silver_bookings' AND rule_name = 'problematic_rule';
```

### Issue: Pipeline Failing

**Solution:** Check pipeline logs in Databricks UI:

1. Navigate to **Workflows** → **Delta Live Tables**
2. Click on **[dev] Wanderbricks Silver Layer Pipeline**
3. Click **Event Logs** tab
4. Filter by severity: **ERROR** or **WARN**

Common fixes:
- Verify Bronze tables exist and have data
- Check that all variables in `databricks.yml` are correct
- Ensure catalog/schema have proper permissions

## 📚 Key Design Principles

### 1. Schema Cloning (Silver = Bronze + DQ)
- ✅ Same column names as Bronze
- ✅ Same data types
- ✅ Add data quality rules (main value-add)
- ✅ Add simple derived flags (is_*, has_*)
- ❌ NO complex transformations (save for Gold)
- ❌ NO aggregations (save for Gold)

### 2. Pipeline Never Fails
- ✅ Critical rules drop/quarantine records, pipeline continues
- ✅ Warning rules log violations, records pass through
- ✅ No `@dlt.expect_or_fail()` - always use `@dlt.expect_all_or_drop()`

### 3. Delta Table for Rules (Best Practice)
- ✅ Single source of truth: Delta table in Unity Catalog
- ✅ Updateable at runtime (no code changes)
- ✅ Auditable (Delta versioning)
- ✅ Queryable for documentation

### 4. Governance First
- ✅ Complete table properties on every table
- ✅ Include: layer, domain, entity_type, contains_pii, data_classification
- ✅ Business owner + Technical owner

## 📖 References

### Official Databricks Documentation
- [DLT Expectations](https://docs.databricks.com/aws/en/dlt/expectations)
- [DLT Expectation Patterns](https://docs.databricks.com/aws/en/ldp/expectation-patterns)
- [Portable and Reusable Expectations](https://docs.databricks.com/aws/en/ldp/expectation-patterns#portable-and-reusable-expectations)
- [Automatic Clustering](https://docs.databricks.com/aws/en/delta/clustering#enable-or-disable-automatic-liquid-clustering)

### Framework Rules
- `07-dlt-expectations-patterns.mdc` - Complete DLT patterns
- `02-databricks-asset-bundles.mdc` - Asset Bundle configuration
- `04-databricks-table-properties.mdc` - Table properties standards

## 🎓 Summary

**Core Philosophy:** Silver = Bronze schema clone + Delta table-driven data quality validation

**Time Estimate:** 3-4 hours for initial setup, automatic thereafter

**Deployment Order:**
1. Deploy and run `silver_dq_setup_job` (creates dq_rules table)
2. Deploy and run `silver_dlt_pipeline` (loads rules from table)
3. Update rules in Delta table as needed (no redeployment!)

**Next Steps:** Proceed to Gold layer creation for business-level aggregates and analytics-ready datasets.

