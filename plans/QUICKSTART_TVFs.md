# TVF Quick Start Guide

**Goal:** Deploy and test 26 Table-Valued Functions in 10 minutes

---

## Prerequisites

- ✅ Gold layer tables deployed (`databricks bundle run gold_setup_job -t dev`)
- ✅ SQL Warehouse access
- ✅ Databricks CLI authenticated

---

## Step 1: Deploy TVFs (2 min)

```bash
# From project root
cd /path/to/Wanderbricks

# Validate bundle
databricks bundle validate

# Deploy (includes TVF creation)
databricks bundle deploy -t dev

# Run setup job (Task 3 creates TVFs)
databricks bundle run gold_setup_job -t dev
```

**Expected Output:**
```
✓ Task setup_all_tables completed successfully
✓ Task add_fk_constraints completed successfully
✓ Task create_table_valued_functions completed successfully
```

---

## Step 2: Verify TVF Creation (1 min)

```sql
-- List all TVFs
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

SHOW FUNCTIONS LIKE 'get_%';
```

**Expected:** 26 functions listed

---

## Step 3: Test Revenue TVFs (2 min)

```sql
-- Test 1: Revenue by period
SELECT * FROM get_revenue_by_period('2024-01-01', '2024-12-31', 'month');

-- Test 2: Top 5 properties by revenue
SELECT * FROM get_top_properties_by_revenue('2024-01-01', '2024-12-31', 5);

-- Test 3: Payment metrics
SELECT * FROM get_payment_metrics('2024-01-01', '2024-12-31');
```

---

## Step 4: Test Engagement TVFs (2 min)

```sql
-- Test 1: Property engagement
SELECT * FROM get_property_engagement('2024-01-01', '2024-12-31', NULL);

-- Test 2: Conversion funnel
SELECT * FROM get_conversion_funnel('2024-01-01', '2024-12-31', NULL);

-- Test 3: Engagement trends (daily)
SELECT * FROM get_engagement_trends('2024-01-01', '2024-12-31', 'day');
```

---

## Step 5: Test Host & Customer TVFs (2 min)

```sql
-- Test 1: Top 10 hosts by performance
SELECT * FROM get_host_performance('2024-01-01', '2024-12-31', NULL);

-- Test 2: Customer segments
SELECT * FROM get_customer_segments('2024-01-01', '2024-12-31');

-- Test 3: Customer LTV (top 20)
SELECT * FROM get_customer_ltv('2024-01-01', '2024-12-31', 20);
```

---

## Step 6: Test Property TVFs (1 min)

```sql
-- Test 1: Property performance
SELECT * FROM get_property_performance('2024-01-01', '2024-12-31', NULL);

-- Test 2: Pricing analysis
SELECT * FROM get_pricing_analysis('2024-01-01', '2024-12-31');
```

---

## Troubleshooting

### Issue: "Function not found"
**Solution:** Run `databricks bundle run gold_setup_job -t dev` again

### Issue: "Table does not exist"
**Solution:** Ensure Gold tables are created first

### Issue: "Parameter type mismatch"
**Solution:** Use STRING for dates: `'2024-01-01'` not `DATE('2024-01-01')`

---

## Next Steps

1. **Add TVFs to Genie Space**
   - Configure Genie Space with these 26 functions
   - Test natural language queries

2. **Test Example Questions**
   - "What are the top 10 properties by revenue?"
   - "Show me engagement trends for last quarter"
   - "Which hosts have highest ratings?"

3. **Monitor Performance**
   - Check query execution times
   - Optimize slow-running TVFs

---

## Complete TVF List

### Revenue (6)
- get_revenue_by_period
- get_top_properties_by_revenue
- get_revenue_by_destination
- get_payment_metrics
- get_cancellation_analysis
- get_revenue_forecast_inputs

### Engagement (5)
- get_property_engagement
- get_conversion_funnel
- get_traffic_source_analysis
- get_engagement_trends
- get_top_engaging_properties

### Property (5)
- get_property_performance
- get_availability_by_destination
- get_property_type_analysis
- get_amenity_impact
- get_pricing_analysis

### Host (5)
- get_host_performance
- get_host_quality_metrics
- get_host_retention_analysis
- get_host_geographic_distribution
- get_multi_property_hosts

### Customer (5)
- get_customer_segments
- get_customer_ltv
- get_booking_frequency_analysis
- get_customer_geographic_analysis
- get_business_vs_leisure_analysis

---

**Total Time:** ~10 minutes  
**Status:** ✅ Ready for Genie integration

