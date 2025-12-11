-- =============================================================================
-- Wanderbricks Gold Layer - Create All Table-Valued Functions
-- 
-- Master SQL file to create all TVFs across all domains.
-- This file sources domain-specific TVF files for organization.
--
-- TVF Domains:
-- - Revenue (6 functions): Revenue trends, top properties, payments, cancellations
-- - Engagement (5 functions): Property engagement, funnels, trends
-- - Property (5 functions): Performance, inventory, pricing, amenities
-- - Host (5 functions): Host performance, quality, retention, geography
-- - Customer (5 functions): Segmentation, LTV, frequency, geography
--
-- Total: 26 Table-Valued Functions
--
-- Usage: 
--   Execute via SQL Warehouse:
--   SOURCE /Workspace/Repos/.../src/wanderbricks_gold/create_all_tvfs.sql
--
-- Prerequisites:
--   - Gold layer tables must exist (dim_*, fact_*)
--   - SQL Warehouse with appropriate permissions
--   - Unity Catalog access
--
-- Created: December 2025
-- =============================================================================

-- Verify we're in the correct context
USE CATALOG ${catalog};
USE SCHEMA ${gold_schema};

-- Display context for verification
SELECT 
  current_catalog() as catalog,
  current_schema() as schema,
  current_user() as user,
  current_timestamp() as execution_time;

PRINT '=============================================================================';
PRINT 'Creating Wanderbricks Table-Valued Functions (TVFs)';
PRINT 'Catalog: ${catalog}';
PRINT 'Schema: ${gold_schema}';
PRINT '=============================================================================';

-- =============================================================================
-- Revenue Domain TVFs (6 functions)
-- =============================================================================

PRINT '';
PRINT '--- Creating Revenue Domain TVFs ---';

SOURCE /Workspace/src/wanderbricks_gold/tvfs/revenue_tvfs.sql;

PRINT '✓ Revenue TVFs created:';
PRINT '  1. get_revenue_by_period';
PRINT '  2. get_top_properties_by_revenue';
PRINT '  3. get_revenue_by_destination';
PRINT '  4. get_payment_metrics';
PRINT '  5. get_cancellation_analysis';
PRINT '  6. get_revenue_forecast_inputs';

-- =============================================================================
-- Engagement Domain TVFs (5 functions)
-- =============================================================================

PRINT '';
PRINT '--- Creating Engagement Domain TVFs ---';

SOURCE /Workspace/src/wanderbricks_gold/tvfs/engagement_tvfs.sql;

PRINT '✓ Engagement TVFs created:';
PRINT '  1. get_property_engagement';
PRINT '  2. get_conversion_funnel';
PRINT '  3. get_traffic_source_analysis';
PRINT '  4. get_engagement_trends';
PRINT '  5. get_top_engaging_properties';

-- =============================================================================
-- Property Domain TVFs (5 functions)
-- =============================================================================

PRINT '';
PRINT '--- Creating Property Domain TVFs ---';

SOURCE /Workspace/src/wanderbricks_gold/tvfs/property_tvfs.sql;

PRINT '✓ Property TVFs created:';
PRINT '  1. get_property_performance';
PRINT '  2. get_availability_by_destination';
PRINT '  3. get_property_type_analysis';
PRINT '  4. get_amenity_impact';
PRINT '  5. get_pricing_analysis';

-- =============================================================================
-- Host Domain TVFs (5 functions)
-- =============================================================================

PRINT '';
PRINT '--- Creating Host Domain TVFs ---';

SOURCE /Workspace/src/wanderbricks_gold/tvfs/host_tvfs.sql;

PRINT '✓ Host TVFs created:';
PRINT '  1. get_host_performance';
PRINT '  2. get_host_quality_metrics';
PRINT '  3. get_host_retention_analysis';
PRINT '  4. get_host_geographic_distribution';
PRINT '  5. get_multi_property_hosts';

-- =============================================================================
-- Customer Domain TVFs (5 functions)
-- =============================================================================

PRINT '';
PRINT '--- Creating Customer Domain TVFs ---';

SOURCE /Workspace/src/wanderbricks_gold/tvfs/customer_tvfs.sql;

PRINT '✓ Customer TVFs created:';
PRINT '  1. get_customer_segments';
PRINT '  2. get_customer_ltv';
PRINT '  3. get_booking_frequency_analysis';
PRINT '  4. get_customer_geographic_analysis';
PRINT '  5. get_business_vs_leisure_analysis';

-- =============================================================================
-- Verification & Summary
-- =============================================================================

PRINT '';
PRINT '=============================================================================';
PRINT 'TVF Creation Complete';
PRINT '=============================================================================';
PRINT '';
PRINT 'Summary:';
PRINT '  Revenue Domain:    6 TVFs';
PRINT '  Engagement Domain: 5 TVFs';
PRINT '  Property Domain:   5 TVFs';
PRINT '  Host Domain:       5 TVFs';
PRINT '  Customer Domain:   5 TVFs';
PRINT '  ─────────────────────────';
PRINT '  Total:            26 TVFs';
PRINT '';

-- List all created TVFs
PRINT 'Verifying TVF creation...';
PRINT '';

SELECT 
  function_name,
  function_type,
  comment
FROM ${catalog}.information_schema.routines
WHERE routine_schema = '${gold_schema}'
  AND routine_type = 'FUNCTION'
  AND function_name LIKE 'get_%'
ORDER BY function_name;

PRINT '';
PRINT '✅ All Wanderbricks TVFs created successfully!';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Test TVFs with sample queries';
PRINT '  2. Add TVFs to Genie Space as trusted assets';
PRINT '  3. Document example questions for each TVF';
PRINT '  4. Monitor TVF performance and usage';
PRINT '';
PRINT '=============================================================================';

