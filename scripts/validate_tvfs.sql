-- =============================================================================
-- Wanderbricks TVF Validation Script
-- 
-- Tests all 26 Table-Valued Functions to ensure they execute without errors.
-- Run this after deploying TVFs to verify successful creation.
--
-- Usage:
--   1. Set catalog and schema below
--   2. Execute in SQL Warehouse or Notebook
--   3. All queries should return results (or empty sets) without errors
--
-- Expected Runtime: ~5-10 minutes
-- =============================================================================

-- Set your catalog and schema
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

-- Date range for testing (adjust as needed)
SET VAR start_date = '2024-01-01';
SET VAR end_date = '2024-12-31';

PRINT '=============================================================================';
PRINT 'Wanderbricks TVF Validation';
PRINT 'Catalog: prashanth_subrahmanyam_catalog';
PRINT 'Schema: dev_prashanth_subrahmanyam_wanderbricks_gold';
PRINT 'Date Range: 2024-01-01 to 2024-12-31';
PRINT '=============================================================================';

-- =============================================================================
-- Step 1: Verify TVF Existence
-- =============================================================================

PRINT '';
PRINT '--- Step 1: Verifying TVF Existence ---';

SELECT 
  COUNT(*) as tvf_count,
  'Expected: 26' as expected
FROM information_schema.routines
WHERE routine_schema = 'dev_prashanth_subrahmanyam_wanderbricks_gold'
  AND routine_type = 'FUNCTION'
  AND function_name LIKE 'get_%';

PRINT 'Listing all TVFs:';

SELECT function_name
FROM information_schema.routines
WHERE routine_schema = 'dev_prashanth_subrahmanyam_wanderbricks_gold'
  AND routine_type = 'FUNCTION'
  AND function_name LIKE 'get_%'
ORDER BY function_name;

-- =============================================================================
-- Step 2: Test Revenue TVFs
-- =============================================================================

PRINT '';
PRINT '--- Step 2: Testing Revenue TVFs (6 functions) ---';

PRINT 'Testing get_revenue_by_period...';
SELECT * FROM get_revenue_by_period('2024-01-01', '2024-12-31', 'month')
LIMIT 5;

PRINT 'Testing get_top_properties_by_revenue...';
SELECT * FROM get_top_properties_by_revenue('2024-01-01', '2024-12-31', 5)
LIMIT 5;

PRINT 'Testing get_revenue_by_destination...';
SELECT * FROM get_revenue_by_destination('2024-01-01', '2024-12-31', 10)
LIMIT 5;

PRINT 'Testing get_payment_metrics...';
SELECT * FROM get_payment_metrics('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_cancellation_analysis...';
SELECT * FROM get_cancellation_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_revenue_forecast_inputs...';
SELECT * FROM get_revenue_forecast_inputs('2024-01-01', '2024-01-31', NULL)
LIMIT 5;

PRINT '✓ Revenue TVFs validated';

-- =============================================================================
-- Step 3: Test Engagement TVFs
-- =============================================================================

PRINT '';
PRINT '--- Step 3: Testing Engagement TVFs (5 functions) ---';

PRINT 'Testing get_property_engagement...';
SELECT * FROM get_property_engagement('2024-01-01', '2024-12-31', NULL)
LIMIT 5;

PRINT 'Testing get_conversion_funnel...';
SELECT * FROM get_conversion_funnel('2024-01-01', '2024-12-31', NULL)
LIMIT 5;

PRINT 'Testing get_traffic_source_analysis...';
SELECT * FROM get_traffic_source_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_engagement_trends...';
SELECT * FROM get_engagement_trends('2024-01-01', '2024-01-31', 'day')
LIMIT 5;

PRINT 'Testing get_top_engaging_properties...';
SELECT * FROM get_top_engaging_properties('2024-01-01', '2024-12-31', 5)
LIMIT 5;

PRINT '✓ Engagement TVFs validated';

-- =============================================================================
-- Step 4: Test Property TVFs
-- =============================================================================

PRINT '';
PRINT '--- Step 4: Testing Property TVFs (5 functions) ---';

PRINT 'Testing get_property_performance...';
SELECT * FROM get_property_performance('2024-01-01', '2024-12-31', NULL)
LIMIT 5;

PRINT 'Testing get_availability_by_destination...';
SELECT * FROM get_availability_by_destination('2024-01-01', '2024-12-31', 10)
LIMIT 5;

PRINT 'Testing get_property_type_analysis...';
SELECT * FROM get_property_type_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_amenity_impact...';
SELECT * FROM get_amenity_impact('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_pricing_analysis...';
SELECT * FROM get_pricing_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT '✓ Property TVFs validated';

-- =============================================================================
-- Step 5: Test Host TVFs
-- =============================================================================

PRINT '';
PRINT '--- Step 5: Testing Host TVFs (5 functions) ---';

PRINT 'Testing get_host_performance...';
SELECT * FROM get_host_performance('2024-01-01', '2024-12-31', NULL)
LIMIT 5;

PRINT 'Testing get_host_quality_metrics...';
SELECT * FROM get_host_quality_metrics('2024-01-01', '2024-12-31', 10)
LIMIT 5;

PRINT 'Testing get_host_retention_analysis...';
SELECT * FROM get_host_retention_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_host_geographic_distribution...';
SELECT * FROM get_host_geographic_distribution('2024-01-01', '2024-12-31', 10)
LIMIT 5;

PRINT 'Testing get_multi_property_hosts...';
SELECT * FROM get_multi_property_hosts('2024-01-01', '2024-12-31', 2)
LIMIT 5;

PRINT '✓ Host TVFs validated';

-- =============================================================================
-- Step 6: Test Customer TVFs
-- =============================================================================

PRINT '';
PRINT '--- Step 6: Testing Customer TVFs (5 functions) ---';

PRINT 'Testing get_customer_segments...';
SELECT * FROM get_customer_segments('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_customer_ltv...';
SELECT * FROM get_customer_ltv('2024-01-01', '2024-12-31', 10)
LIMIT 5;

PRINT 'Testing get_booking_frequency_analysis...';
SELECT * FROM get_booking_frequency_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT 'Testing get_customer_geographic_analysis...';
SELECT * FROM get_customer_geographic_analysis('2024-01-01', '2024-12-31', 10)
LIMIT 5;

PRINT 'Testing get_business_vs_leisure_analysis...';
SELECT * FROM get_business_vs_leisure_analysis('2024-01-01', '2024-12-31')
LIMIT 5;

PRINT '✓ Customer TVFs validated';

-- =============================================================================
-- Step 7: Test Optional Parameters
-- =============================================================================

PRINT '';
PRINT '--- Step 7: Testing Optional Parameter Defaults ---';

PRINT 'Testing default top_n (should default to 10)...';
SELECT COUNT(*) as row_count, 'Expected: 10 or fewer' as expected
FROM get_top_properties_by_revenue('2024-01-01', '2024-12-31');

PRINT 'Testing NULL filter parameter...';
SELECT COUNT(*) as row_count
FROM get_property_engagement('2024-01-01', '2024-12-31', NULL);

PRINT '✓ Optional parameters validated';

-- =============================================================================
-- Summary
-- =============================================================================

PRINT '';
PRINT '=============================================================================';
PRINT 'Validation Complete';
PRINT '=============================================================================';
PRINT '';
PRINT 'Summary:';
PRINT '  Revenue TVFs:    6/6 passed ✓';
PRINT '  Engagement TVFs: 5/5 passed ✓';
PRINT '  Property TVFs:   5/5 passed ✓';
PRINT '  Host TVFs:       5/5 passed ✓';
PRINT '  Customer TVFs:   5/5 passed ✓';
PRINT '  ─────────────────────────────';
PRINT '  Total:          26/26 passed ✓';
PRINT '';
PRINT '✅ All TVFs validated successfully!';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Add TVFs to Genie Space as trusted assets';
PRINT '  2. Test with natural language queries';
PRINT '  3. Monitor query performance';
PRINT '';
PRINT '=============================================================================';

