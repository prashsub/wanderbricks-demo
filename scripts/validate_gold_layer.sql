-- Gold Layer Validation Queries
-- Run these to validate the Gold layer deployment

USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

-- ============================================================================
-- 1. VERIFY ALL TABLES EXIST
-- ============================================================================

SHOW TABLES;

-- Expected: 8 tables
-- ✓ dim_user, dim_host, dim_property, dim_destination, dim_date
-- ✓ fact_booking_detail, fact_booking_daily, fact_property_engagement


-- ============================================================================
-- 2. CHECK RECORD COUNTS
-- ============================================================================

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
SELECT 'fact_property_engagement', COUNT(*) FROM fact_property_engagement
ORDER BY table_name;


-- ============================================================================
-- 3. VERIFY NO GRAIN DUPLICATES (Should return 0 rows)
-- ============================================================================

-- Fact: booking_detail (PK: booking_id)
SELECT booking_id, COUNT(*) as dup_count
FROM fact_booking_detail
GROUP BY booking_id
HAVING COUNT(*) > 1;

-- Fact: booking_daily (PK: property_id, check_in_date)
SELECT property_id, check_in_date, COUNT(*) as dup_count
FROM fact_booking_daily
GROUP BY property_id, check_in_date
HAVING COUNT(*) > 1;

-- Fact: property_engagement (PK: property_id, engagement_date)
SELECT property_id, engagement_date, COUNT(*) as dup_count
FROM fact_property_engagement
GROUP BY property_id, engagement_date
HAVING COUNT(*) > 1;


-- ============================================================================
-- 4. VERIFY SCD TYPE 2 (Only one current version per business key)
-- ============================================================================

-- dim_user (should return 0)
SELECT user_id, COUNT(*) as current_versions
FROM dim_user
WHERE is_current = true
GROUP BY user_id
HAVING COUNT(*) > 1;

-- dim_host (should return 0)
SELECT host_id, COUNT(*) as current_versions
FROM dim_host
WHERE is_current = true
GROUP BY host_id
HAVING COUNT(*) > 1;

-- dim_property (should return 0)
SELECT property_id, COUNT(*) as current_versions
FROM dim_property
WHERE is_current = true
GROUP BY property_id
HAVING COUNT(*) > 1;


-- ============================================================================
-- 5. VERIFY FK INTEGRITY (No orphaned records - should return 0)
-- ============================================================================

-- Check fact_booking_detail → dim_user
SELECT COUNT(*) as orphaned_bookings
FROM fact_booking_detail f
LEFT JOIN dim_user d ON f.user_id = d.user_id AND d.is_current = true
WHERE d.user_id IS NULL;

-- Check fact_booking_detail → dim_host
SELECT COUNT(*) as orphaned_bookings
FROM fact_booking_detail f
LEFT JOIN dim_host d ON f.host_id = d.host_id AND d.is_current = true
WHERE d.user_id IS NULL;

-- Check fact_booking_detail → dim_property
SELECT COUNT(*) as orphaned_bookings
FROM fact_booking_detail f
LEFT JOIN dim_property d ON f.property_id = d.property_id AND d.is_current = true
WHERE d.property_id IS NULL;

-- Check fact_booking_detail → dim_destination
SELECT COUNT(*) as orphaned_bookings
FROM fact_booking_detail f
LEFT JOIN dim_destination d ON f.destination_id = d.destination_id
WHERE d.destination_id IS NULL;


-- ============================================================================
-- 6. SAMPLE DATA QUERIES (Verify data quality)
-- ============================================================================

-- Top 10 users by booking count
SELECT 
  u.name,
  u.user_type,
  u.country,
  COUNT(f.booking_id) as booking_count,
  SUM(f.total_amount) as total_spend
FROM fact_booking_detail f
JOIN dim_user u ON f.user_id = u.user_id AND u.is_current = true
GROUP BY u.name, u.user_type, u.country
ORDER BY booking_count DESC
LIMIT 10;

-- Top 10 properties by booking value
SELECT 
  p.title,
  p.property_type,
  d.destination,
  COUNT(f.booking_id) as booking_count,
  SUM(f.total_amount) as total_revenue
FROM fact_booking_detail f
JOIN dim_property p ON f.property_id = p.property_id AND p.is_current = true
JOIN dim_destination d ON f.destination_id = d.destination_id
GROUP BY p.title, p.property_type, d.destination
ORDER BY total_revenue DESC
LIMIT 10;

-- Daily booking trends (last 30 days)
SELECT 
  dt.date as booking_date,
  COUNT(DISTINCT f.property_id) as properties_with_bookings,
  SUM(f.booking_count) as total_bookings,
  SUM(f.total_booking_value) as total_value
FROM fact_booking_daily f
JOIN dim_date dt ON f.check_in_date = dt.date
WHERE dt.date >= CURRENT_DATE() - INTERVAL 30 DAYS
GROUP BY dt.date
ORDER BY dt.date DESC;


-- ============================================================================
-- 7. VERIFY TABLE PROPERTIES
-- ============================================================================

-- Check clustering is enabled
DESCRIBE TABLE EXTENDED dim_user;
-- Look for: Clustering Information: CLUSTER BY AUTO

-- Check table properties
SHOW TBLPROPERTIES dim_user;
-- Expected: layer=gold, domain=identity, etc.

