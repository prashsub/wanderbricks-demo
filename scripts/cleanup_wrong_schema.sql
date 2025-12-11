-- Cleanup Wrong Gold Schema
-- Run this in Databricks SQL Editor

USE CATALOG prashanth_subrahmanyam_catalog;

-- Step 1: Verify correct schema has data
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

SELECT 'Verification - Tables in CORRECT schema:' as step;

SELECT 
    'dim_user' as table_name, 
    COUNT(*) as records 
FROM dim_user
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
UNION ALL
SELECT 'dim_weather_location', COUNT(*) FROM dim_weather_location
UNION ALL
SELECT 'fact_weather_daily', COUNT(*) FROM fact_weather_daily
ORDER BY table_name;

-- Expected: 240,000+ total records across 10 tables

-- Step 2: Drop the wrong schema (CASCADE drops all tables)
SELECT 'Dropping WRONG schema (wanderbricks_gold)...' as step;

DROP SCHEMA IF EXISTS prashanth_subrahmanyam_catalog.wanderbricks_gold CASCADE;

-- Step 3: Verify only correct schema remains
SELECT 'Verification - Only correct schema should remain:' as step;

SHOW SCHEMAS IN prashanth_subrahmanyam_catalog LIKE '*gold*';

-- Expected output: Only dev_prashanth_subrahmanyam_wanderbricks_gold

SELECT 'Cleanup complete!' as step;

