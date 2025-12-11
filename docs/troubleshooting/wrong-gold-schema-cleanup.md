# Gold Schema Cleanup - Wrong Schema Created

**Date:** December 10, 2025  
**Issue:** Tables created in `wanderbricks_gold` instead of `dev_prashanth_subrahmanyam_wanderbricks_gold`  
**Status:** ✅ IDENTIFIED - Ready to Clean Up

---

## 🔍 Root Cause Analysis

### Which Job Created the Wrong Schema?

**Culprit:** `gold_setup_job` (first run)

**Timeline:**
1. **Initial Run** (before config fix):
   - `databricks.yml` had `gold_schema: wanderbricks_gold` (default, no dev prefix)
   - `gold_setup_job` ran and created 8 tables in `wanderbricks_gold` ❌
   
2. **Config Fix:**
   - Updated `databricks.yml` to set `gold_schema: dev_prashanth_subrahmanyam_wanderbricks_gold` in dev target
   - Redeployed bundle
   
3. **Correct Run:**
   - `gold_setup_job` ran again (after fix) and created 8 tables in `dev_prashanth_subrahmanyam_wanderbricks_gold` ✅
   - `gold_merge_job` populated tables in correct schema ✅

**Evidence:**
```yaml
# databricks.yml - BEFORE fix (line 26)
gold_schema:
  default: wanderbricks_gold  # ← No dev prefix

# databricks.yml - AFTER fix (line 46)
targets:
  dev:
    variables:
      gold_schema: dev_prashanth_subrahmanyam_wanderbricks_gold  # ← Correct prefix
```

---

## 📊 Current State

### Schema 1: `wanderbricks_gold` (WRONG - TO BE DELETED)

**Created by:** `gold_setup_job` (first run, before config fix)

**Tables:** 8 tables created but **NO DATA** (merge job used correct schema)

Expected tables:
- dim_user
- dim_host
- dim_property
- dim_destination
- dim_date
- fact_booking_detail
- fact_booking_daily
- fact_property_engagement

---

### Schema 2: `dev_prashanth_subrahmanyam_wanderbricks_gold` (CORRECT - KEEP THIS)

**Created by:** `gold_setup_job` (second run, after config fix)  
**Populated by:** `gold_merge_job` ✅

**Tables:** 8 tables with **238,000+ records** ✅

---

## 🛠️ Cleanup Steps

### Option 1: SQL Command (Simplest)

Run this in Databricks SQL Editor:

```sql
-- Verify correct schema has data
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

SELECT 'dim_user' as table_name, COUNT(*) as records FROM dim_user
UNION ALL
SELECT 'dim_host', COUNT(*) FROM dim_host
UNION ALL
SELECT 'dim_property', COUNT(*) FROM dim_property
UNION ALL
SELECT 'dim_destination', COUNT(*) FROM dim_destination
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'fact_booking_detail', COUNT(*) FROM fact_booking_detail
UNION ALL
SELECT 'fact_booking_daily', COUNT(*) FROM fact_booking_daily
UNION ALL
SELECT 'fact_property_engagement', COUNT(*) FROM fact_property_engagement;

-- Expected: 238,000+ total records
-- If correct, proceed with cleanup:

-- Drop the wrong schema
DROP SCHEMA IF EXISTS prashanth_subrahmanyam_catalog.wanderbricks_gold CASCADE;

-- Verify it's gone
SHOW SCHEMAS IN prashanth_subrahmanyam_catalog LIKE '*gold*';

-- Expected output: Only dev_prashanth_subrahmanyam_wanderbricks_gold
```

---

### Option 2: Python Cleanup Script (Automated)

A Python script has been created at: `/Workspace/Users/prashanth.subrahmanyam@databricks.com/scripts/cleanup_wrong_gold_schema`

**To run:**
1. Go to Databricks Workspace
2. Navigate to `/Workspace/Users/prashanth.subrahmanyam@databricks.com/scripts/`
3. Open `cleanup_wrong_gold_schema`
4. Run the notebook

**What it does:**
1. Lists tables in `wanderbricks_gold` (wrong schema)
2. Lists tables in `dev_prashanth_subrahmanyam_wanderbricks_gold` (correct schema)
3. Verifies correct schema has data
4. Drops `wanderbricks_gold` schema CASCADE

---

## ✅ Post-Cleanup Verification

After cleanup, verify only the correct schema exists:

```sql
-- Should show only one Gold schema
SHOW SCHEMAS IN prashanth_subrahmanyam_catalog LIKE '*gold*';

-- Expected output:
-- dev_prashanth_subrahmanyam_wanderbricks_gold
```

---

## 🔒 Prevention

### Config Now Correct ✅

The `databricks.yml` configuration is now correct:

```yaml
targets:
  dev:
    mode: development
    variables:
      gold_schema: dev_prashanth_subrahmanyam_wanderbricks_gold  # ✅ Correct
```

All future runs of `gold_setup_job` and `gold_merge_job` will use the correct schema.

---

## 📋 Summary

| Item | Status |
|------|--------|
| **Wrong Schema** | `wanderbricks_gold` (empty, will be dropped) |
| **Correct Schema** | `dev_prashanth_subrahmanyam_wanderbricks_gold` (238K+ records) ✅ |
| **Culprit Job** | `gold_setup_job` (first run) |
| **Root Cause** | Missing dev prefix in databricks.yml dev target |
| **Fix Applied** | ✅ databricks.yml updated (line 46) |
| **Cleanup Action** | Drop `wanderbricks_gold` CASCADE |

---

## 🚀 Next Steps

1. **Run cleanup SQL** (Option 1) or **Python script** (Option 2)
2. **Verify** only correct schema exists
3. **Continue** with semantic layer development (TVFs, Metric Views)

---

**Cleanup SQL (Copy-Paste):**
```sql
DROP SCHEMA IF EXISTS prashanth_subrahmanyam_catalog.wanderbricks_gold CASCADE;
```

**Verification:**
```sql
SHOW SCHEMAS IN prashanth_subrahmanyam_catalog LIKE '*gold*';
-- Should only show: dev_prashanth_subrahmanyam_wanderbricks_gold
```

