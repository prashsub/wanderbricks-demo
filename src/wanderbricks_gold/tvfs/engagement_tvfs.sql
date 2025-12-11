-- =============================================================================
-- Wanderbricks Gold Layer - Engagement Domain TVFs for Genie
-- 
-- This file contains engagement and conversion-focused Table-Valued Functions
-- optimized for Genie Spaces and marketing analytics.
--
-- Key Patterns:
-- 1. STRING for date parameters (Genie doesn't support DATE type)
-- 2. Required parameters first, optional (DEFAULT) parameters last
-- 3. ROW_NUMBER + WHERE for Top N (not LIMIT with parameter)
-- 4. NULLIF for all divisions (null safety)
-- 5. is_current = true for SCD2 dimension joins
--
-- Created: December 2025
-- =============================================================================

USE CATALOG ${catalog};
USE SCHEMA ${gold_schema};

-- =============================================================================
-- TVF 1: get_property_engagement
-- Returns engagement metrics for properties
-- =============================================================================

CREATE OR REPLACE FUNCTION get_property_engagement(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  property_id_filter BIGINT DEFAULT NULL COMMENT 'Optional: Filter to specific property (NULL for all)'
)
RETURNS TABLE (
  property_id BIGINT COMMENT 'Property identifier',
  property_title STRING COMMENT 'Property listing title',
  property_type STRING COMMENT 'Property type',
  destination STRING COMMENT 'Property location',
  total_views BIGINT COMMENT 'Total property page views',
  unique_viewers BIGINT COMMENT 'Number of unique users who viewed',
  total_clicks BIGINT COMMENT 'Total clicks on property elements',
  search_appearances BIGINT COMMENT 'Times property appeared in search results',
  conversion_rate DECIMAL(5,2) COMMENT 'Views to bookings conversion rate (%)',
  avg_time_on_page DECIMAL(10,2) COMMENT 'Average time spent viewing property (seconds)',
  engagement_score DECIMAL(10,2) COMMENT 'Composite engagement score (clicks + time weight)'
)
COMMENT 'LLM: Returns engagement metrics for properties including views, clicks, and conversion rates.
Use this for: Marketing analysis, content optimization, funnel analysis, property listing quality assessment.
Parameters: start_date, end_date (YYYY-MM-DD format), optional property_id_filter (NULL for all properties).
Example questions: "Which properties have highest engagement?" "Show conversion rates" "Property engagement metrics"'
RETURN
  WITH engagement_data AS (
    SELECT 
      fpe.property_id,
      dp.title as property_title,
      dp.property_type,
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      SUM(fpe.view_count) as total_views,
      SUM(fpe.unique_user_views) as unique_viewers,
      SUM(fpe.click_count) as total_clicks,
      SUM(fpe.search_count) as search_appearances,
      AVG(fpe.conversion_rate) as conversion_rate,
      AVG(fpe.avg_time_on_page) as avg_time_on_page,
      (SUM(fpe.click_count) / NULLIF(SUM(fpe.view_count), 0) * 50) + 
      (AVG(fpe.avg_time_on_page) / NULLIF(60, 0) * 50) as engagement_score
    FROM ${catalog}.${gold_schema}.fact_property_engagement fpe
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON fpe.property_id = dp.property_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON dp.destination_id = dd.destination_id
    WHERE fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND (property_id_filter IS NULL OR fpe.property_id = property_id_filter)
    GROUP BY fpe.property_id, dp.title, dp.property_type, dd.destination, dd.state_or_province, dd.country
  )
  SELECT 
    property_id,
    property_title,
    property_type,
    destination,
    total_views,
    unique_viewers,
    total_clicks,
    search_appearances,
    conversion_rate,
    avg_time_on_page,
    engagement_score
  FROM engagement_data
  ORDER BY engagement_score DESC;

-- =============================================================================
-- TVF 2: get_conversion_funnel
-- Returns view → click → book funnel analysis
-- =============================================================================

CREATE OR REPLACE FUNCTION get_conversion_funnel(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  destination_filter STRING DEFAULT NULL COMMENT 'Optional: Filter to destination name (NULL for all)'
)
RETURNS TABLE (
  destination STRING COMMENT 'Destination (city, state, country)',
  total_views BIGINT COMMENT 'Total property views (top of funnel)',
  total_clicks BIGINT COMMENT 'Total clicks (middle of funnel)',
  total_bookings BIGINT COMMENT 'Total bookings (bottom of funnel)',
  view_to_click_rate DECIMAL(5,2) COMMENT 'Percentage of views resulting in clicks',
  click_to_booking_rate DECIMAL(5,2) COMMENT 'Percentage of clicks resulting in bookings',
  overall_conversion_rate DECIMAL(5,2) COMMENT 'Percentage of views resulting in bookings',
  funnel_efficiency DECIMAL(5,2) COMMENT 'Composite funnel health score (0-100)'
)
COMMENT 'LLM: Returns conversion funnel analysis from views to clicks to bookings by destination.
Use this for: Marketing funnel optimization, conversion rate analysis, identifying funnel drop-off points, destination performance.
Parameters: start_date, end_date (YYYY-MM-DD format), optional destination_filter (NULL for all destinations).
Example questions: "Show conversion funnel" "Where do users drop off?" "Funnel performance by destination"'
RETURN
  WITH funnel_data AS (
    SELECT 
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      SUM(fpe.view_count) as total_views,
      SUM(fpe.click_count) as total_clicks,
      COUNT(DISTINCT fbd.booking_id) as total_bookings
    FROM ${catalog}.${gold_schema}.fact_property_engagement fpe
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON fpe.property_id = dp.property_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON dp.destination_id = dd.destination_id
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON fpe.property_id = fbd.property_id 
      AND fpe.engagement_date = fbd.check_in_date
    WHERE fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      AND (destination_filter IS NULL OR CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) = destination_filter)
    GROUP BY dd.destination, dd.state_or_province, dd.country
  )
  SELECT 
    destination,
    total_views,
    total_clicks,
    total_bookings,
    (total_clicks / NULLIF(total_views, 0)) * 100 as view_to_click_rate,
    (total_bookings / NULLIF(total_clicks, 0)) * 100 as click_to_booking_rate,
    (total_bookings / NULLIF(total_views, 0)) * 100 as overall_conversion_rate,
    ((total_clicks / NULLIF(total_views, 0)) * 50 + 
     (total_bookings / NULLIF(total_clicks, 0)) * 50) as funnel_efficiency
  FROM funnel_data
  WHERE total_views > 0
  ORDER BY overall_conversion_rate DESC;

-- =============================================================================
-- TVF 3: get_traffic_source_analysis
-- Returns performance by referrer/source (simulated from clickstream)
-- =============================================================================

CREATE OR REPLACE FUNCTION get_traffic_source_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  property_type STRING COMMENT 'Property type category',
  total_views BIGINT COMMENT 'Total property views',
  unique_viewers BIGINT COMMENT 'Unique users viewing',
  total_clicks BIGINT COMMENT 'Total clicks',
  avg_time_on_page DECIMAL(10,2) COMMENT 'Average time viewing (seconds)',
  conversion_rate DECIMAL(5,2) COMMENT 'Conversion rate (%)',
  bookings_generated BIGINT COMMENT 'Total bookings'
)
COMMENT 'LLM: Returns engagement and conversion performance by property type (traffic source proxy).
Use this for: Property type performance, inventory optimization, marketing focus areas, user preference analysis.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Performance by property type" "Which property types convert best?" "Traffic source effectiveness"'
RETURN
  WITH source_data AS (
    SELECT 
      dp.property_type,
      SUM(fpe.view_count) as total_views,
      SUM(fpe.unique_user_views) as unique_viewers,
      SUM(fpe.click_count) as total_clicks,
      AVG(fpe.avg_time_on_page) as avg_time_on_page,
      AVG(fpe.conversion_rate) as conversion_rate,
      COUNT(DISTINCT fbd.booking_id) as bookings_generated
    FROM ${catalog}.${gold_schema}.fact_property_engagement fpe
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON fpe.property_id = dp.property_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON fpe.property_id = fbd.property_id 
      AND fpe.engagement_date = fbd.check_in_date
    WHERE fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY dp.property_type
  )
  SELECT 
    property_type,
    total_views,
    unique_viewers,
    total_clicks,
    avg_time_on_page,
    conversion_rate,
    bookings_generated
  FROM source_data
  WHERE total_views > 0
  ORDER BY bookings_generated DESC;

-- =============================================================================
-- TVF 4: get_engagement_trends
-- Returns daily/weekly engagement trends
-- =============================================================================

CREATE OR REPLACE FUNCTION get_engagement_trends(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  time_grain STRING DEFAULT 'day' COMMENT 'Aggregation grain: day or week'
)
RETURNS TABLE (
  period_start DATE COMMENT 'Start of period',
  period_name STRING COMMENT 'Human-friendly period label',
  total_views BIGINT COMMENT 'Total views in period',
  total_clicks BIGINT COMMENT 'Total clicks in period',
  avg_conversion_rate DECIMAL(5,2) COMMENT 'Average conversion rate',
  avg_time_on_page DECIMAL(10,2) COMMENT 'Average time on page (seconds)',
  unique_properties_viewed BIGINT COMMENT 'Number of properties viewed',
  engagement_index DECIMAL(10,2) COMMENT 'Composite engagement health score'
)
COMMENT 'LLM: Returns daily or weekly engagement trends with key metrics.
Use this for: Trend analysis, identifying seasonal patterns, campaign impact measurement, engagement health tracking.
Parameters: start_date, end_date (YYYY-MM-DD format), optional time_grain (default: day).
Example questions: "Show daily engagement trends" "Weekly engagement patterns" "How is engagement trending?"'
RETURN
  WITH period_data AS (
    SELECT 
      DATE_TRUNC(time_grain, fpe.engagement_date) AS period_start,
      CASE 
        WHEN time_grain = 'day' THEN DATE_FORMAT(fpe.engagement_date, 'yyyy-MM-dd')
        WHEN time_grain = 'week' THEN CONCAT('Week ', WEEKOFYEAR(fpe.engagement_date), ' ', YEAR(fpe.engagement_date))
        ELSE DATE_FORMAT(fpe.engagement_date, 'yyyy-MM-dd')
      END AS period_name,
      SUM(fpe.view_count) as total_views,
      SUM(fpe.click_count) as total_clicks,
      AVG(fpe.conversion_rate) as avg_conversion_rate,
      AVG(fpe.avg_time_on_page) as avg_time_on_page,
      COUNT(DISTINCT fpe.property_id) as unique_properties_viewed
    FROM ${catalog}.${gold_schema}.fact_property_engagement fpe
    WHERE fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY DATE_TRUNC(time_grain, fpe.engagement_date), period_name
  )
  SELECT 
    period_start,
    period_name,
    total_views,
    total_clicks,
    avg_conversion_rate,
    avg_time_on_page,
    unique_properties_viewed,
    ((total_clicks / NULLIF(total_views, 0)) * 40 + 
     (avg_conversion_rate / 5) * 30 + 
     (avg_time_on_page / 60) * 30) as engagement_index
  FROM period_data
  ORDER BY period_start;

-- =============================================================================
-- TVF 5: get_top_engaging_properties
-- Returns properties with highest engagement scores
-- =============================================================================

CREATE OR REPLACE FUNCTION get_top_engaging_properties(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top properties to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Property rank by engagement',
  property_id BIGINT COMMENT 'Property identifier',
  property_title STRING COMMENT 'Property title',
  destination STRING COMMENT 'Property location',
  total_views BIGINT COMMENT 'Total views',
  click_through_rate DECIMAL(5,2) COMMENT 'Click-through rate (%)',
  conversion_rate DECIMAL(5,2) COMMENT 'Conversion rate (%)',
  avg_time_on_page DECIMAL(10,2) COMMENT 'Average time on page (seconds)',
  engagement_score DECIMAL(10,2) COMMENT 'Composite engagement score',
  bookings_generated BIGINT COMMENT 'Number of bookings'
)
COMMENT 'LLM: Returns top N properties ranked by engagement score (clicks, time, conversions).
Use this for: Identifying best-performing listings, content optimization examples, marketing case studies.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 10).
Example questions: "Most engaging properties" "Top 10 by engagement" "Best performing listings"'
RETURN
  WITH property_engagement AS (
    SELECT 
      fpe.property_id,
      dp.title as property_title,
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      SUM(fpe.view_count) as total_views,
      (SUM(fpe.click_count) / NULLIF(SUM(fpe.view_count), 0)) * 100 as click_through_rate,
      AVG(fpe.conversion_rate) as conversion_rate,
      AVG(fpe.avg_time_on_page) as avg_time_on_page,
      ((SUM(fpe.click_count) / NULLIF(SUM(fpe.view_count), 0)) * 30 + 
       (AVG(fpe.conversion_rate) / 5) * 40 + 
       (AVG(fpe.avg_time_on_page) / 60) * 30) as engagement_score,
      COUNT(DISTINCT fbd.booking_id) as bookings_generated
    FROM ${catalog}.${gold_schema}.fact_property_engagement fpe
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON fpe.property_id = dp.property_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON dp.destination_id = dd.destination_id
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON fpe.property_id = fbd.property_id 
      AND fpe.engagement_date = fbd.check_in_date
    WHERE fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fpe.property_id, dp.title, dd.destination, dd.state_or_province, dd.country
  ),
  ranked_properties AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY engagement_score DESC) as rank,
      property_id,
      property_title,
      destination,
      total_views,
      click_through_rate,
      conversion_rate,
      avg_time_on_page,
      engagement_score,
      bookings_generated
    FROM property_engagement
  )
  SELECT * FROM ranked_properties
  WHERE rank <= top_n
  ORDER BY rank;

