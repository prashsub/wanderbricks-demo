# Wanderbricks Silver Layer - Quick Start

## ⚡ Fast Track Deployment (5 Commands)

```bash
# 1. Validate bundle
databricks bundle validate

# 2. Deploy resources
databricks bundle deploy -t dev

# 3. Create DQ rules table (MUST RUN FIRST!)
databricks bundle run silver_dq_setup_job -t dev

# 4. Trigger DLT pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# 5. Validate deployment
databricks bundle run silver_validation_job -t dev
```

**Expected Time:** ~20 minutes total

---

## 📋 What Gets Deployed

| Resource | Type | Count | Description |
|----------|------|-------|-------------|
| Schemas | UC Schema | 3 | Bronze, Silver, Gold |
| Tables | Delta | 22 | 9 dims + 6 facts + 2 quarantine + 4 monitoring + 1 dq_rules |
| Jobs | Workflow | 2 | DQ setup + Validation |
| Pipeline | DLT | 1 | Silver streaming pipeline |

---

## 🎯 Key Commands

### Deployment
```bash
# Deploy to dev
databricks bundle deploy -t dev

# Deploy to prod
databricks bundle deploy -t prod
```

### Run Jobs
```bash
# Setup DQ rules (one-time)
databricks bundle run silver_dq_setup_job -t dev

# Run validation
databricks bundle run silver_validation_job -t dev
```

### Manage DLT Pipeline
```bash
# Start pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# Stop pipeline
databricks pipelines stop --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# Get pipeline status
databricks pipelines get --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"
```

### Cleanup
```bash
# Remove all deployed resources (⚠️ CAUTION!)
databricks bundle destroy -t dev
```

---

## 🔍 Quick Verification

```sql
-- Check tables exist (expect 22)
SHOW TABLES IN prashanth_subrahmanyam_catalog.wanderbricks_silver;

-- Check DQ rules (expect 70+)
SELECT COUNT(*) FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_rules;

-- Check quarantine rate (expect <5%)
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_bookings_metrics;

-- Check referential integrity (expect all PASS)
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_silver.dq_referential_integrity;
```

---

## 🚨 Common Issues

| Issue | Quick Fix |
|-------|-----------|
| "dq_rules not found" | Run `silver_dq_setup_job` before DLT pipeline |
| "No module dq_rules_loader" | Remove `# Databricks notebook source` from `dq_rules_loader.py` |
| High quarantine rate | Review quarantine reasons, adjust rules via SQL UPDATE |
| Bundle validation fails | Check YAML syntax in `databricks.yml` and `resources/*.yml` |

---

## 📖 Full Documentation

- **Complete Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Silver README:** [src/wanderbricks_silver/README.md](src/wanderbricks_silver/README.md)
- **Gold Layer:** [gold_layer_design/README.md](gold_layer_design/README.md)
- **ML Models:** [docs/ml/ml-models-guide.md](docs/ml/ml-models-guide.md)
- **Asset Bundles:** [.cursor/rules/common/02-databricks-asset-bundles.mdc](.cursor/rules/common/02-databricks-asset-bundles.mdc)

---

## 🎓 Architecture Summary

```
Bronze Layer (wanderbricks)
    ↓ Incremental Streaming
Silver Layer (wanderbricks_silver)
    ├─ DQ Rules (Delta table-based, runtime-updateable)
    ├─ 17 Silver Tables (dimensions + facts)
    ├─ 2 Quarantine Tables (invalid records)
    └─ 4 Monitoring Views (DQ metrics)
```

**Key Features:**
- ✅ **Delta table-based DQ rules** - Update via SQL, no code deployment
- ✅ **Never fails** - Quarantines bad records, pipeline continues
- ✅ **Streaming** - Incremental reads from Bronze
- ✅ **Comprehensive monitoring** - Real-time DQ metrics

---

## 🆘 Need Help?

1. Run validation: `databricks bundle run silver_validation_job -t dev`
2. Check DLT logs in Databricks UI: **Workflows** → **Delta Live Tables**
3. Review troubleshooting: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#-troubleshooting)

