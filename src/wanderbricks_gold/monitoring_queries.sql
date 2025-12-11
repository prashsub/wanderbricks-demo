-- Wanderbricks Lakehouse Monitoring Queries
-- 
-- Query patterns for monitoring metrics across all 5 monitors.
-- 
-- Output Tables:
-- - {catalog}.{schema}__{table}_profile_metrics - Column stats + custom metrics
-- - {catalog}.{schema}__{table}_drift_metrics - Drift detection results
-- 
-- CRITICAL: Replace ${catalog} and ${schema} with actual values!

-- ============================================================================
-- 💰 REVENUE MONITOR (fact_booking_daily)
-- ============================================================================

-- Latest revenue metrics (table-level KPIs)
SELECT 
    window.start,
    window.end,
    granularity,
    MAX(CASE WHEN custom_metric_name = 'daily_revenue' THEN custom_metric_value END) as daily_revenue,
    MAX(CASE WHEN custom_metric_name = 'avg_booking_value' THEN custom_metric_value END) as avg_booking_value,
    MAX(CASE WHEN custom_metric_name = 'total_bookings' THEN custom_metric_value END) as total_bookings,
    MAX(CASE WHEN custom_metric_name = 'total_cancellations' THEN custom_metric_value END) as total_cancellations,
    MAX(CASE WHEN custom_metric_name = 'cancellation_rate' THEN custom_metric_value END) as cancellation_rate
FROM ${catalog}.${schema}__tables__fact_booking_daily_profile_metrics
WHERE column_name = ':table'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
GROUP BY window.start, window.end, granularity
ORDER BY window.start DESC;

-- Revenue by destination (sliced metrics)
SELECT 
    window.start,
    slice_key,
    slice_value,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__fact_booking_daily_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'destination_id'
  AND custom_metric_name = 'daily_revenue'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
ORDER BY window.start DESC, custom_metric_value DESC;

-- Revenue drift alerts
SELECT 
    window.start,
    window.end,
    drift_type,
    drift_metric_name,
    drift_metric_value,
    pct_change,
    is_anomaly
FROM ${catalog}.${schema}__tables__fact_booking_daily_drift_metrics
WHERE column_name = ':table'
  AND drift_metric_name = 'revenue_vs_baseline'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -30)
ORDER BY window.start DESC;


-- ============================================================================
-- 📊 ENGAGEMENT MONITOR (fact_property_engagement)
-- ============================================================================

-- Latest engagement metrics
SELECT 
    window.start,
    window.end,
    MAX(CASE WHEN custom_metric_name = 'total_views' THEN custom_metric_value END) as total_views,
    MAX(CASE WHEN custom_metric_name = 'total_clicks' THEN custom_metric_value END) as total_clicks,
    MAX(CASE WHEN custom_metric_name = 'avg_conversion' THEN custom_metric_value END) as avg_conversion,
    MAX(CASE WHEN custom_metric_name = 'engagement_health' THEN custom_metric_value END) as engagement_health
FROM ${catalog}.${schema}__tables__fact_property_engagement_profile_metrics
WHERE column_name = ':table'
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
GROUP BY window.start, window.end
ORDER BY window.start DESC;

-- Engagement by property
SELECT 
    window.start,
    slice_value as property_id,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__fact_property_engagement_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'property_id'
  AND custom_metric_name IN ('total_views', 'engagement_health')
  AND window.end >= DATE_ADD(CURRENT_DATE(), -7)
ORDER BY window.start DESC, custom_metric_value DESC;


-- ============================================================================
-- 🏠 PROPERTY MONITOR (dim_property)
-- ============================================================================

-- Latest property metrics (snapshot)
SELECT 
    window.start,
    window.end,
    MAX(CASE WHEN custom_metric_name = 'active_listings' THEN custom_metric_value END) as active_listings,
    MAX(CASE WHEN custom_metric_name = 'avg_price' THEN custom_metric_value END) as avg_price,
    MAX(CASE WHEN custom_metric_name = 'price_variance' THEN custom_metric_value END) as price_variance
FROM ${catalog}.${schema}__tables__dim_property_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start, window.end
ORDER BY window.start DESC
LIMIT 10;

-- Property metrics by type
SELECT 
    window.start,
    slice_value as property_type,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__dim_property_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'property_type'
  AND custom_metric_name IN ('active_listings', 'avg_price')
ORDER BY window.start DESC, slice_value;

-- Property metrics by destination
SELECT 
    window.start,
    slice_value as destination_id,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__dim_property_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'destination_id'
  AND custom_metric_name = 'active_listings'
ORDER BY window.start DESC, custom_metric_value DESC;


-- ============================================================================
-- 👤 HOST MONITOR (dim_host)
-- ============================================================================

-- Latest host metrics
SELECT 
    window.start,
    window.end,
    MAX(CASE WHEN custom_metric_name = 'active_hosts' THEN custom_metric_value END) as active_hosts,
    MAX(CASE WHEN custom_metric_name = 'total_current_hosts' THEN custom_metric_value END) as total_current_hosts,
    MAX(CASE WHEN custom_metric_name = 'avg_rating' THEN custom_metric_value END) as avg_rating,
    MAX(CASE WHEN custom_metric_name = 'verification_rate' THEN custom_metric_value END) as verification_rate
FROM ${catalog}.${schema}__tables__dim_host_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start, window.end
ORDER BY window.start DESC
LIMIT 10;

-- Host metrics by country
SELECT 
    window.start,
    slice_value as country,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__dim_host_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'country'
  AND custom_metric_name IN ('active_hosts', 'verification_rate')
ORDER BY window.start DESC, custom_metric_value DESC;

-- Verification status breakdown
SELECT 
    window.start,
    slice_value as is_verified,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__dim_host_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'is_verified'
ORDER BY window.start DESC, slice_value;


-- ============================================================================
-- 🎯 CUSTOMER MONITOR (dim_user)
-- ============================================================================

-- Latest customer metrics
SELECT 
    window.start,
    window.end,
    MAX(CASE WHEN custom_metric_name = 'total_customers' THEN custom_metric_value END) as total_customers,
    MAX(CASE WHEN custom_metric_name = 'business_customers' THEN custom_metric_value END) as business_customers,
    MAX(CASE WHEN custom_metric_name = 'business_customer_rate' THEN custom_metric_value END) as business_customer_rate
FROM ${catalog}.${schema}__tables__dim_user_profile_metrics
WHERE column_name = ':table'
GROUP BY window.start, window.end
ORDER BY window.start DESC
LIMIT 10;

-- Customer growth trend
SELECT 
    window.start,
    window.end,
    drift_type,
    drift_metric_name,
    drift_metric_value,
    pct_change
FROM ${catalog}.${schema}__tables__dim_user_drift_metrics
WHERE column_name = ':table'
  AND drift_metric_name = 'customer_growth'
ORDER BY window.start DESC;

-- Customers by country
SELECT 
    window.start,
    slice_value as country,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__dim_user_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'country'
  AND custom_metric_name = 'total_customers'
ORDER BY window.start DESC, custom_metric_value DESC;

-- Customers by user type
SELECT 
    window.start,
    slice_value as user_type,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${schema}__tables__dim_user_profile_metrics
WHERE column_name = ':table'
  AND slice_key = 'user_type'
ORDER BY window.start DESC, slice_value;


-- ============================================================================
-- 🚨 ALERT QUERIES
-- ============================================================================

-- Revenue drop alert (>20% decline)
SELECT 
    'REVENUE_DROP' as alert_type,
    window.end as alert_time,
    drift_metric_value as current_revenue,
    pct_change
FROM ${catalog}.${schema}__tables__fact_booking_daily_drift_metrics
WHERE column_name = ':table'
  AND drift_metric_name = 'revenue_vs_baseline'
  AND pct_change < -20
  AND window.end >= CURRENT_DATE()
ORDER BY window.end DESC;

-- High cancellation rate alert (>15%)
SELECT 
    'HIGH_CANCELLATION' as alert_type,
    window.end as alert_time,
    custom_metric_value as cancellation_rate
FROM ${catalog}.${schema}__tables__fact_booking_daily_profile_metrics
WHERE column_name = ':table'
  AND custom_metric_name = 'cancellation_rate'
  AND custom_metric_value > 15
  AND window.end >= CURRENT_DATE()
ORDER BY window.end DESC;

-- Low engagement alert (engagement_health <5%)
SELECT 
    'LOW_ENGAGEMENT' as alert_type,
    window.end as alert_time,
    custom_metric_value as engagement_health
FROM ${catalog}.${schema}__tables__fact_property_engagement_profile_metrics
WHERE column_name = ':table'
  AND custom_metric_name = 'engagement_health'
  AND custom_metric_value < 5
  AND window.end >= CURRENT_DATE()
ORDER BY window.end DESC;

-- Listing drop alert (>10% decrease)
SELECT 
    'LISTING_DROP' as alert_type,
    window.start as alert_time,
    custom_metric_value as current_listings,
    LAG(custom_metric_value) OVER (ORDER BY window.start) as previous_listings,
    ((custom_metric_value - LAG(custom_metric_value) OVER (ORDER BY window.start)) 
     / LAG(custom_metric_value) OVER (ORDER BY window.start) * 100) as pct_change
FROM ${catalog}.${schema}__tables__dim_property_profile_metrics
WHERE column_name = ':table'
  AND custom_metric_name = 'active_listings'
ORDER BY window.start DESC
LIMIT 10;

