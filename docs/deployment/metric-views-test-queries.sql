-- Metric Views Test Queries
-- Wanderbricks - Phase 4.3: Metric Views
-- Use these queries to verify metric views are working correctly

-- Set your catalog and schema
USE CATALOG prashanth_subrahmanyam_catalog;
USE SCHEMA dev_prashanth_subrahmanyam_wanderbricks_gold;

-- =============================================================================
-- VERIFY METRIC VIEW TYPES
-- =============================================================================

-- Check all metric views are type METRIC_VIEW (not just VIEW)
DESCRIBE EXTENDED revenue_analytics_metrics;
DESCRIBE EXTENDED engagement_analytics_metrics;
DESCRIBE EXTENDED property_analytics_metrics;
DESCRIBE EXTENDED host_analytics_metrics;
DESCRIBE EXTENDED customer_analytics_metrics;

-- List all metric views
SHOW VIEWS LIKE '*analytics_metrics';

-- =============================================================================
-- 💰 REVENUE ANALYTICS METRICS - Test Queries
-- =============================================================================

-- Test 1: Revenue by destination
SELECT 
  destination,
  country,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Booking Count`) as bookings,
  MEASURE(`Avg Booking Value`) as avg_value
FROM revenue_analytics_metrics
GROUP BY destination, country
ORDER BY revenue DESC
LIMIT 10;

-- Test 2: Monthly revenue trends
SELECT 
  year,
  month_name,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Booking Count`) as bookings,
  MEASURE(`Cancellation Rate`) as cancel_rate,
  MEASURE(`Payment Rate`) as payment_rate
FROM revenue_analytics_metrics
GROUP BY year, month_name
ORDER BY year DESC, month_name;

-- Test 3: Revenue by property type
SELECT 
  property_type,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Booking Count`) as bookings,
  MEASURE(`Total Guests`) as guests,
  MEASURE(`Avg Nights`) as avg_nights
FROM revenue_analytics_metrics
GROUP BY property_type
ORDER BY revenue DESC;

-- Test 4: Cancellation analysis
SELECT 
  destination,
  MEASURE(`Booking Count`) as total_bookings,
  MEASURE(`Confirmed Count`) as confirmed,
  MEASURE(`Cancellation Count`) as cancelled,
  MEASURE(`Cancellation Rate`) as cancel_rate
FROM revenue_analytics_metrics
GROUP BY destination
HAVING MEASURE(`Booking Count`) > 10
ORDER BY MEASURE(`Cancellation Rate`) DESC
LIMIT 10;

-- =============================================================================
-- 📊 ENGAGEMENT ANALYTICS METRICS - Test Queries
-- =============================================================================

-- Test 1: Top properties by engagement
SELECT 
  property_title,
  destination,
  MEASURE(`Total Views`) as views,
  MEASURE(`Unique Viewers`) as unique_viewers,
  MEASURE(`Total Clicks`) as clicks,
  MEASURE(`Conversion Rate`) as conversion_rate,
  MEASURE(`Click-Through Rate`) as ctr
FROM engagement_analytics_metrics
GROUP BY property_title, destination
ORDER BY views DESC
LIMIT 10;

-- Test 2: Engagement trends over time
SELECT 
  year,
  month_name,
  MEASURE(`Total Views`) as views,
  MEASURE(`Total Clicks`) as clicks,
  MEASURE(`Bookings`) as bookings,
  MEASURE(`Conversion Rate`) as conversion_rate
FROM engagement_analytics_metrics
GROUP BY year, month_name
ORDER BY year DESC, month_name;

-- Test 3: Engagement by property type
SELECT 
  property_type,
  MEASURE(`Total Views`) as views,
  MEASURE(`Unique Viewers`) as unique_viewers,
  MEASURE(`Conversion Rate`) as conversion_rate,
  MEASURE(`Avg Time on Page`) as avg_time
FROM engagement_analytics_metrics
GROUP BY property_type
ORDER BY views DESC;

-- Test 4: Destination engagement performance
SELECT 
  country,
  destination,
  MEASURE(`Total Views`) as views,
  MEASURE(`Search Appearances`) as search_impressions,
  MEASURE(`Conversion Rate`) as conversion_rate
FROM engagement_analytics_metrics
GROUP BY country, destination
ORDER BY views DESC
LIMIT 20;

-- =============================================================================
-- 🏠 PROPERTY ANALYTICS METRICS - Test Queries
-- =============================================================================

-- Test 1: Property portfolio overview
SELECT 
  MEASURE(`Property Count`) as total_properties,
  MEASURE(`Avg Base Price`) as avg_price,
  MEASURE(`Total Capacity`) as total_capacity,
  MEASURE(`Avg Bedrooms`) as avg_bedrooms,
  MEASURE(`Total Revenue`) as total_revenue,
  MEASURE(`Revenue per Property`) as revenue_per_property
FROM property_analytics_metrics;

-- Test 2: Properties by destination
SELECT 
  destination,
  country,
  MEASURE(`Property Count`) as properties,
  MEASURE(`Avg Base Price`) as avg_price,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Bookings per Property`) as bookings_per_property
FROM property_analytics_metrics
GROUP BY destination, country
ORDER BY properties DESC
LIMIT 10;

-- Test 3: Property type analysis
SELECT 
  property_type,
  MEASURE(`Property Count`) as properties,
  MEASURE(`Avg Base Price`) as avg_price,
  MEASURE(`Avg Bedrooms`) as avg_bedrooms,
  MEASURE(`Total Revenue`) as revenue
FROM property_analytics_metrics
GROUP BY property_type
ORDER BY properties DESC;

-- Test 4: Host performance (verified vs unverified)
SELECT 
  is_verified_host,
  MEASURE(`Property Count`) as properties,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Revenue per Property`) as revenue_per_property
FROM property_analytics_metrics
GROUP BY is_verified_host
ORDER BY properties DESC;

-- =============================================================================
-- 👤 HOST ANALYTICS METRICS - Test Queries
-- =============================================================================

-- Test 1: Host overview
SELECT 
  MEASURE(`Host Count`) as total_hosts,
  MEASURE(`Verified Hosts`) as verified,
  MEASURE(`Verification Rate`) as verification_rate,
  MEASURE(`Avg Host Rating`) as avg_rating,
  MEASURE(`Property Count`) as total_properties,
  MEASURE(`Total Revenue`) as total_revenue
FROM host_analytics_metrics;

-- Test 2: Top hosts by revenue
SELECT 
  host_name,
  country,
  is_verified,
  rating,
  MEASURE(`Property Count`) as properties,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Booking Count`) as bookings,
  MEASURE(`Revenue per Host`) as avg_revenue
FROM host_analytics_metrics
GROUP BY host_name, country, is_verified, rating
ORDER BY MEASURE(`Total Revenue`) DESC
LIMIT 20;

-- Test 3: Host performance by country
SELECT 
  country,
  MEASURE(`Host Count`) as hosts,
  MEASURE(`Verified Hosts`) as verified,
  MEASURE(`Verification Rate`) as verification_rate,
  MEASURE(`Avg Host Rating`) as avg_rating,
  MEASURE(`Total Revenue`) as revenue
FROM host_analytics_metrics
GROUP BY country
ORDER BY hosts DESC;

-- Test 4: Verified vs unverified hosts
SELECT 
  is_verified,
  MEASURE(`Host Count`) as hosts,
  MEASURE(`Property Count`) as properties,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Revenue per Host`) as revenue_per_host,
  MEASURE(`Avg Host Rating`) as avg_rating
FROM host_analytics_metrics
GROUP BY is_verified
ORDER BY hosts DESC;

-- Test 5: Host tenure analysis
SELECT 
  CASE 
    WHEN host_since_days < 30 THEN '0-30 days'
    WHEN host_since_days < 90 THEN '30-90 days'
    WHEN host_since_days < 180 THEN '90-180 days'
    WHEN host_since_days < 365 THEN '180-365 days'
    ELSE '1+ years'
  END as tenure_bucket,
  MEASURE(`Host Count`) as hosts,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Revenue per Host`) as revenue_per_host
FROM host_analytics_metrics
GROUP BY tenure_bucket
ORDER BY 
  CASE tenure_bucket
    WHEN '0-30 days' THEN 1
    WHEN '30-90 days' THEN 2
    WHEN '90-180 days' THEN 3
    WHEN '180-365 days' THEN 4
    ELSE 5
  END;

-- =============================================================================
-- 🎯 CUSTOMER ANALYTICS METRICS - Test Queries
-- =============================================================================

-- Test 1: Customer overview
SELECT 
  MEASURE(`Customer Count`) as total_customers,
  MEASURE(`Business Customers`) as business_count,
  MEASURE(`Business Rate`) as business_rate,
  MEASURE(`Booking Count`) as total_bookings,
  MEASURE(`Total Spend`) as total_spend,
  MEASURE(`Spend per Customer`) as customer_ltv
FROM customer_analytics_metrics;

-- Test 2: Top customers by spend
SELECT 
  country,
  user_type,
  is_business,
  MEASURE(`Customer Count`) as customers,
  MEASURE(`Total Spend`) as total_spend,
  MEASURE(`Bookings per Customer`) as booking_frequency,
  MEASURE(`Spend per Customer`) as customer_ltv
FROM customer_analytics_metrics
GROUP BY country, user_type, is_business
ORDER BY MEASURE(`Total Spend`) DESC
LIMIT 20;

-- Test 3: Customer segmentation by booking frequency
SELECT 
  CASE 
    WHEN MEASURE(`Bookings per Customer`) >= 5 THEN 'Frequent (5+)'
    WHEN MEASURE(`Bookings per Customer`) >= 3 THEN 'Regular (3-4)'
    WHEN MEASURE(`Bookings per Customer`) >= 2 THEN 'Occasional (2)'
    ELSE 'One-time (1)'
  END as segment,
  MEASURE(`Customer Count`) as customers,
  MEASURE(`Total Spend`) as revenue,
  MEASURE(`Spend per Customer`) as customer_ltv
FROM customer_analytics_metrics
GROUP BY segment
ORDER BY customers DESC;

-- Test 4: Business vs leisure customers
SELECT 
  is_business,
  MEASURE(`Customer Count`) as customers,
  MEASURE(`Booking Count`) as bookings,
  MEASURE(`Total Spend`) as spend,
  MEASURE(`Avg Booking Value`) as avg_booking_value,
  MEASURE(`Bookings per Customer`) as booking_frequency
FROM customer_analytics_metrics
GROUP BY is_business;

-- Test 5: Customer geography analysis
SELECT 
  country,
  MEASURE(`Customer Count`) as customers,
  MEASURE(`Booking Count`) as bookings,
  MEASURE(`Total Spend`) as spend,
  MEASURE(`Spend per Customer`) as customer_ltv
FROM customer_analytics_metrics
GROUP BY country
ORDER BY customers DESC
LIMIT 20;

-- Test 6: Customer tenure cohorts
SELECT 
  CASE 
    WHEN customer_tenure_days < 30 THEN '0-30 days'
    WHEN customer_tenure_days < 90 THEN '30-90 days'
    WHEN customer_tenure_days < 180 THEN '90-180 days'
    WHEN customer_tenure_days < 365 THEN '180-365 days'
    ELSE '1+ years'
  END as tenure_bucket,
  MEASURE(`Customer Count`) as customers,
  MEASURE(`Total Spend`) as spend,
  MEASURE(`Spend per Customer`) as customer_ltv,
  MEASURE(`Bookings per Customer`) as booking_frequency
FROM customer_analytics_metrics
GROUP BY tenure_bucket
ORDER BY 
  CASE tenure_bucket
    WHEN '0-30 days' THEN 1
    WHEN '30-90 days' THEN 2
    WHEN '90-180 days' THEN 3
    WHEN '180-365 days' THEN 4
    ELSE 5
  END;

-- =============================================================================
-- CROSS-METRIC VIEW ANALYSIS
-- =============================================================================

-- Compare revenue and engagement
SELECT 
  r.destination,
  MEASURE(r.`Total Revenue`) as revenue,
  MEASURE(r.`Booking Count`) as bookings,
  MEASURE(e.`Total Views`) as views,
  MEASURE(e.`Conversion Rate`) as conversion_rate
FROM revenue_analytics_metrics r
JOIN engagement_analytics_metrics e ON r.destination = e.destination
GROUP BY r.destination
ORDER BY revenue DESC
LIMIT 10;

-- Property performance with host metrics
SELECT 
  p.property_type,
  MEASURE(p.`Property Count`) as properties,
  MEASURE(p.`Total Revenue`) as property_revenue,
  MEASURE(h.`Avg Host Rating`) as avg_host_rating,
  MEASURE(h.`Verification Rate`) as host_verification_rate
FROM property_analytics_metrics p
CROSS JOIN host_analytics_metrics h
GROUP BY p.property_type
ORDER BY properties DESC;

