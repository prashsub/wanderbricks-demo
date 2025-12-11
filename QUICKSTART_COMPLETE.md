# Wanderbricks Complete Quick Start

**Goal:** Deploy Bronze → Silver → Gold layers with 26 TVFs in 30 minutes

---

## Prerequisites

- ✅ Databricks workspace access
- ✅ Unity Catalog enabled
- ✅ Databricks CLI authenticated
- ✅ SQL Warehouse provisioned

---

## Phase 1: Silver Layer (20 min)

### Step 1: Setup DQ Rules (5 min)
```bash
# Validate and deploy
databricks bundle validate
databricks bundle deploy -t dev

# Create DQ rules table (MUST RUN FIRST!)
databricks bundle run silver_dq_setup_job -t dev
```

### Step 2: Run DLT Pipeline (10 min)
```bash
# Trigger Silver DLT pipeline
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# Wait for completion (monitor in UI)
# Expected: ~10 minutes for first run
```

### Step 3: Validate Silver (5 min)
```bash
# Run validation job
databricks bundle run silver_validation_job -t dev
```

**Expected Output:**
- ✅ 17 Silver tables created
- ✅ 2 Quarantine tables
- ✅ 4 DQ monitoring views
- ✅ Quarantine rate < 5%

---

## Phase 2: Gold Layer (10 min)

### Step 4: Create Gold Tables & TVFs
```bash
# Run Gold setup (creates tables, constraints, and TVFs)
databricks bundle run gold_setup_job -t dev
```

**This creates:**
- 8 Gold layer tables (5 dimensions + 3 facts)
- 26 Table-Valued Functions (TVFs)
- Primary and Foreign Key constraints

**Expected Output:**
```
✓ Task setup_all_tables completed (creates 8 tables)
✓ Task add_fk_constraints completed (applies FKs)
✓ Task create_table_valued_functions completed (creates 26 TVFs)
```

---

## Phase 3: Verification (5 min)

### Step 5: Verify Gold Deployment

```sql
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

-- Check tables (expect 8)
SHOW TABLES;

-- Check TVFs (expect 26)
SHOW FUNCTIONS LIKE 'get_%';

-- Test a TVF
SELECT * FROM get_revenue_by_period('2024-01-01', '2024-12-31', 'month')
LIMIT 5;
```

---

## Complete Deployment Summary

| Layer | Tables | Functions | Jobs | Pipeline |
|-------|--------|-----------|------|----------|
| Bronze | TBD | 0 | 0 | 0 |
| Silver | 17 + 2 quarantine | 0 | 2 | 1 |
| Gold | 8 | 26 TVFs | 2 | 0 |
| **Total** | **27+** | **26** | **4** | **1** |

---

## TVF Quick Test Suite

```sql
-- Revenue analysis
SELECT * FROM get_revenue_by_period('2024-01-01', '2024-12-31', 'month');
SELECT * FROM get_top_properties_by_revenue('2024-01-01', '2024-12-31', 5);

-- Engagement analysis
SELECT * FROM get_property_engagement('2024-01-01', '2024-12-31', NULL);
SELECT * FROM get_conversion_funnel('2024-01-01', '2024-12-31', NULL);

-- Host performance
SELECT * FROM get_host_performance('2024-01-01', '2024-12-31', NULL);
SELECT * FROM get_host_quality_metrics('2024-01-01', '2024-12-31', 10);

-- Customer segmentation
SELECT * FROM get_customer_segments('2024-01-01', '2024-12-31');
SELECT * FROM get_customer_ltv('2024-01-01', '2024-12-31', 20);

-- Property management
SELECT * FROM get_property_performance('2024-01-01', '2024-12-31', NULL);
SELECT * FROM get_pricing_analysis('2024-01-01', '2024-12-31');
```

---

## All TVFs by Domain

### 💰 Revenue (6)
1. `get_revenue_by_period` - Revenue trends
2. `get_top_properties_by_revenue` - Top performers
3. `get_revenue_by_destination` - Geographic revenue
4. `get_payment_metrics` - Payment analysis
5. `get_cancellation_analysis` - Cancellation patterns
6. `get_revenue_forecast_inputs` - ML forecasting data

### 📊 Engagement (5)
1. `get_property_engagement` - Engagement metrics
2. `get_conversion_funnel` - Funnel analysis
3. `get_traffic_source_analysis` - Source performance
4. `get_engagement_trends` - Trend analysis
5. `get_top_engaging_properties` - Best engagement

### 🏠 Property (5)
1. `get_property_performance` - Property KPIs
2. `get_availability_by_destination` - Inventory
3. `get_property_type_analysis` - Type comparison
4. `get_amenity_impact` - Amenity analysis
5. `get_pricing_analysis` - Pricing optimization

### 👤 Host (5)
1. `get_host_performance` - Host KPIs
2. `get_host_quality_metrics` - Quality analysis
3. `get_host_retention_analysis` - Retention tracking
4. `get_host_geographic_distribution` - Geography
5. `get_multi_property_hosts` - Portfolio analysis

### 🎯 Customer (5)
1. `get_customer_segments` - Segmentation
2. `get_customer_ltv` - Lifetime value
3. `get_booking_frequency_analysis` - Frequency
4. `get_customer_geographic_analysis` - Geography
5. `get_business_vs_leisure_analysis` - B2B vs B2C

---

## Project Structure

```
Wanderbricks/
├── src/
│   ├── wanderbricks_silver/         # Silver layer (DLT)
│   │   ├── silver_*.py              # 17 Silver tables
│   │   ├── dq_rules_loader.py       # DQ framework
│   │   └── README.md
│   └── wanderbricks_gold/           # Gold layer
│       ├── setup_tables.py          # Table creation
│       ├── add_fk_constraints.py    # FK constraints
│       ├── merge_gold_tables.py     # Data merging
│       ├── create_all_tvfs.sql      # TVF master file
│       └── tvfs/                    # TVF SQL files
│           ├── revenue_tvfs.sql     # 6 functions
│           ├── engagement_tvfs.sql  # 5 functions
│           ├── property_tvfs.sql    # 5 functions
│           ├── host_tvfs.sql        # 5 functions
│           ├── customer_tvfs.sql    # 5 functions
│           └── README.md
├── resources/
│   ├── schemas.yml                  # UC schemas
│   ├── silver/
│   │   ├── silver_dlt_pipeline.yml
│   │   ├── silver_dq_setup_job.yml
│   │   └── silver_validation_job.yml
│   └── gold/
│       ├── gold_setup_job.yml       # Creates tables + TVFs
│       └── gold_merge_job.yml
├── gold_layer_design/yaml/          # Gold table schemas
├── plans/                           # Implementation plans
└── databricks.yml                   # Bundle config
```

---

## Common Commands

```bash
# Deploy everything
databricks bundle deploy -t dev

# Silver layer
databricks bundle run silver_dq_setup_job -t dev
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"
databricks bundle run silver_validation_job -t dev

# Gold layer
databricks bundle run gold_setup_job -t dev      # Creates tables + TVFs
databricks bundle run gold_merge_job -t dev      # Populates data

# Cleanup (⚠️ CAUTION!)
databricks bundle destroy -t dev
```

---

## Next Steps

1. **Populate Gold Layer**
   ```bash
   databricks bundle run gold_merge_job -t dev
   ```

2. **Test TVFs in Genie Space**
   - Configure Genie Space with 26 TVFs
   - Test natural language queries
   - Example: "What are the top 10 properties by revenue?"

3. **Create Metric Views**
   - Build semantic layer on top of TVFs
   - Enable AI/BI dashboards

4. **Setup Lakehouse Monitoring**
   - Monitor data quality metrics
   - Track TVF usage and performance

---

## Documentation

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete deployment guide |
| [QUICKSTART.md](QUICKSTART.md) | Silver layer quick start |
| [plans/QUICKSTART_TVFs.md](plans/QUICKSTART_TVFs.md) | TVF quick start |
| [plans/IMPLEMENTATION_SUMMARY_TVFs.md](plans/IMPLEMENTATION_SUMMARY_TVFs.md) | TVF implementation details |
| [scripts/validate_tvfs.sql](scripts/validate_tvfs.sql) | TVF validation script |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "dq_rules not found" | Run `silver_dq_setup_job` before DLT pipeline |
| "Function not found" | Run `gold_setup_job` to create TVFs |
| "Table does not exist" | Ensure Gold tables created before TVFs |
| High quarantine rate | Review quarantine tables, adjust DQ rules |
| Bundle validation fails | Check YAML syntax errors |

---

**Total Time:** ~30 minutes  
**Status:** ✅ Production-ready  
**TVFs:** 26 functions ready for Genie integration

