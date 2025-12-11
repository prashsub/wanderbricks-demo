-- =============================================================================
-- Wanderbricks Gold Layer - Host Domain TVFs for Genie
-- 
-- This file contains host performance and quality-focused Table-Valued
-- Functions optimized for Genie Spaces and partner management analytics.
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
-- TVF 1: get_host_performance
-- Returns comprehensive host performance metrics
-- =============================================================================

CREATE OR REPLACE FUNCTION get_host_performance(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  host_id_filter BIGINT DEFAULT NULL COMMENT 'Optional: Filter to specific host (NULL for all)'
)
RETURNS TABLE (
  host_id BIGINT COMMENT 'Host identifier',
  host_name STRING COMMENT 'Host name',
  country STRING COMMENT 'Host country',
  is_verified BOOLEAN COMMENT 'Host verification status',
  rating FLOAT COMMENT 'Host average rating',
  property_count BIGINT COMMENT 'Number of properties managed',
  total_bookings BIGINT COMMENT 'Total bookings across all properties',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue generated',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average revenue per booking',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Average occupancy rate (%)',
  cancellation_rate DECIMAL(5,2) COMMENT 'Percentage of bookings cancelled',
  host_performance_score DECIMAL(10,2) COMMENT 'Composite host quality score'
)
COMMENT 'LLM: Returns comprehensive host performance metrics including revenue, bookings, and quality indicators.
Use this for: Host quality analysis, partner management, commission calculations, host comparison.
Parameters: start_date, end_date (YYYY-MM-DD format), optional host_id_filter (NULL for all hosts).
Example questions: "Who are top performing hosts?" "Show host KPIs" "Host performance metrics"'
RETURN
  WITH host_metrics AS (
    SELECT 
      dh.host_id,
      dh.name as host_name,
      dh.country,
      dh.is_verified,
      dh.rating,
      COUNT(DISTINCT dp.property_id) as property_count,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0) as avg_booking_value,
      (COUNT(DISTINCT fbd.booking_id) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)) * COUNT(DISTINCT dp.property_id), 0)) * 100 as avg_occupancy_rate,
      (SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0)) * 100 as cancellation_rate
    FROM ${catalog}.${gold_schema}.dim_host dh
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON dh.host_id = dp.host_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dh.is_current = true
      AND (host_id_filter IS NULL OR dh.host_id = host_id_filter)
    GROUP BY dh.host_id, dh.name, dh.country, dh.is_verified, dh.rating
  )
  SELECT 
    host_id,
    host_name,
    country,
    is_verified,
    rating,
    property_count,
    total_bookings,
    total_revenue,
    avg_booking_value,
    avg_occupancy_rate,
    cancellation_rate,
    ((rating / 5) * 30 + 
     (total_revenue / NULLIF(50000, 0)) * 40 + 
     (avg_occupancy_rate / 100) * 20 + 
     ((100 - cancellation_rate) / 100) * 10) as host_performance_score
  FROM host_metrics
  ORDER BY host_performance_score DESC;

-- =============================================================================
-- TVF 2: get_host_quality_metrics
-- Returns host rating and verification analysis
-- =============================================================================

CREATE OR REPLACE FUNCTION get_host_quality_metrics(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 20 COMMENT 'Number of top hosts to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Host rank by quality score',
  host_id BIGINT COMMENT 'Host identifier',
  host_name STRING COMMENT 'Host name',
  is_verified BOOLEAN COMMENT 'Verification status',
  rating FLOAT COMMENT 'Average rating',
  property_count BIGINT COMMENT 'Number of properties',
  total_bookings BIGINT COMMENT 'Total bookings',
  response_rate DECIMAL(5,2) COMMENT 'Simulated response rate (%)',
  cancellation_by_host_rate DECIMAL(5,2) COMMENT 'Host-initiated cancellation rate (%)',
  quality_score DECIMAL(10,2) COMMENT 'Composite quality score'
)
COMMENT 'LLM: Returns top N hosts ranked by quality metrics (rating, verification, reliability).
Use this for: Host quality assessment, partner certification, identifying top hosts, quality benchmarking.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 20).
Example questions: "Top quality hosts" "Best rated hosts" "Most reliable hosts"'
RETURN
  WITH host_quality AS (
    SELECT 
      dh.host_id,
      dh.name as host_name,
      dh.is_verified,
      dh.rating,
      COUNT(DISTINCT dp.property_id) as property_count,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      CASE WHEN dh.is_verified THEN 95.0 ELSE 85.0 END as response_rate,
      (SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0)) * 100 as cancellation_by_host_rate
    FROM ${catalog}.${gold_schema}.dim_host dh
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON dh.host_id = dp.host_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dh.is_current = true
    GROUP BY dh.host_id, dh.name, dh.is_verified, dh.rating
  ),
  ranked_hosts AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY 
        ((rating / 5) * 40 + 
         (response_rate / 100) * 30 + 
         ((100 - cancellation_by_host_rate) / 100) * 20 + 
         (CASE WHEN is_verified THEN 10 ELSE 0 END)) DESC
      ) as rank,
      host_id,
      host_name,
      is_verified,
      rating,
      property_count,
      total_bookings,
      response_rate,
      cancellation_by_host_rate,
      ((rating / 5) * 40 + 
       (response_rate / 100) * 30 + 
       ((100 - cancellation_by_host_rate) / 100) * 20 + 
       (CASE WHEN is_verified THEN 10 ELSE 0 END)) as quality_score
    FROM host_quality
  )
  SELECT * FROM ranked_hosts
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 3: get_host_retention_analysis
-- Returns active vs churned host analysis
-- =============================================================================

CREATE OR REPLACE FUNCTION get_host_retention_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  host_status STRING COMMENT 'Host activity status',
  host_count BIGINT COMMENT 'Number of hosts',
  total_properties BIGINT COMMENT 'Total properties managed',
  total_bookings BIGINT COMMENT 'Total bookings',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_properties_per_host DECIMAL(10,2) COMMENT 'Average properties per host',
  avg_revenue_per_host DECIMAL(18,2) COMMENT 'Average revenue per host',
  avg_rating DECIMAL(3,2) COMMENT 'Average host rating'
)
COMMENT 'LLM: Returns host retention and activity analysis (active vs inactive hosts).
Use this for: Host retention tracking, churn analysis, host engagement strategies, partner lifecycle management.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Active vs inactive hosts" "Host retention metrics" "Host churn analysis"'
RETURN
  WITH host_activity AS (
    SELECT 
      dh.host_id,
      dh.is_active,
      CASE 
        WHEN dh.is_active AND COUNT(DISTINCT fbd.booking_id) > 0 THEN 'Active with Bookings'
        WHEN dh.is_active AND COUNT(DISTINCT fbd.booking_id) = 0 THEN 'Active without Bookings'
        ELSE 'Inactive/Churned'
      END as host_status,
      COUNT(DISTINCT dp.property_id) as property_count,
      COUNT(DISTINCT fbd.booking_id) as booking_count,
      SUM(fbd.total_amount) as revenue,
      dh.rating
    FROM ${catalog}.${gold_schema}.dim_host dh
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON dh.host_id = dp.host_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dh.is_current = true
    GROUP BY dh.host_id, dh.is_active, dh.rating
  )
  SELECT 
    host_status,
    COUNT(DISTINCT host_id) as host_count,
    SUM(property_count) as total_properties,
    SUM(booking_count) as total_bookings,
    SUM(revenue) as total_revenue,
    SUM(property_count) / NULLIF(COUNT(DISTINCT host_id), 0) as avg_properties_per_host,
    SUM(revenue) / NULLIF(COUNT(DISTINCT host_id), 0) as avg_revenue_per_host,
    AVG(rating) as avg_rating
  FROM host_activity
  GROUP BY host_status
  ORDER BY 
    CASE host_status
      WHEN 'Active with Bookings' THEN 1
      WHEN 'Active without Bookings' THEN 2
      WHEN 'Inactive/Churned' THEN 3
    END;

-- =============================================================================
-- TVF 4: get_host_geographic_distribution
-- Returns host distribution and performance by country
-- =============================================================================

CREATE OR REPLACE FUNCTION get_host_geographic_distribution(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 20 COMMENT 'Number of top countries to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Country rank by host count',
  country STRING COMMENT 'Host country',
  host_count BIGINT COMMENT 'Number of hosts',
  verified_host_count BIGINT COMMENT 'Number of verified hosts',
  verification_rate DECIMAL(5,2) COMMENT 'Percentage of hosts verified',
  total_properties BIGINT COMMENT 'Total properties',
  total_bookings BIGINT COMMENT 'Total bookings',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_rating DECIMAL(3,2) COMMENT 'Average host rating',
  avg_revenue_per_host DECIMAL(18,2) COMMENT 'Average revenue per host'
)
COMMENT 'LLM: Returns host geographic distribution and performance by country.
Use this for: Geographic host analysis, market expansion planning, regional partner strategies, international growth.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 20).
Example questions: "Hosts by country" "Geographic host distribution" "Which countries have most hosts?"'
RETURN
  WITH country_metrics AS (
    SELECT 
      dh.country,
      COUNT(DISTINCT dh.host_id) as host_count,
      SUM(CASE WHEN dh.is_verified THEN 1 ELSE 0 END) as verified_host_count,
      (SUM(CASE WHEN dh.is_verified THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT dh.host_id), 0)) * 100 as verification_rate,
      COUNT(DISTINCT dp.property_id) as total_properties,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      AVG(dh.rating) as avg_rating,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT dh.host_id), 0) as avg_revenue_per_host
    FROM ${catalog}.${gold_schema}.dim_host dh
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON dh.host_id = dp.host_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dh.is_current = true
    GROUP BY dh.country
  ),
  ranked_countries AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY host_count DESC) as rank,
      country,
      host_count,
      verified_host_count,
      verification_rate,
      total_properties,
      total_bookings,
      total_revenue,
      avg_rating,
      avg_revenue_per_host
    FROM country_metrics
  )
  SELECT * FROM ranked_countries
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 5: get_multi_property_hosts
-- Returns analysis of hosts managing multiple properties
-- =============================================================================

CREATE OR REPLACE FUNCTION get_multi_property_hosts(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  min_properties INT DEFAULT 3 COMMENT 'Minimum number of properties for inclusion'
)
RETURNS TABLE (
  host_id BIGINT COMMENT 'Host identifier',
  host_name STRING COMMENT 'Host name',
  country STRING COMMENT 'Host country',
  property_count BIGINT COMMENT 'Number of properties managed',
  total_bookings BIGINT COMMENT 'Total bookings across all properties',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_revenue_per_property DECIMAL(18,2) COMMENT 'Average revenue per property',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Average occupancy rate',
  portfolio_performance_score DECIMAL(10,2) COMMENT 'Portfolio quality score'
)
COMMENT 'LLM: Returns analysis of hosts managing multiple properties (property portfolios).
Use this for: Multi-property host management, professional host identification, portfolio optimization, scalability analysis.
Parameters: start_date, end_date (YYYY-MM-DD format), optional min_properties (default: 3).
Example questions: "Multi-property hosts" "Professional hosts" "Hosts with multiple listings"'
RETURN
  WITH multi_property_metrics AS (
    SELECT 
      dh.host_id,
      dh.name as host_name,
      dh.country,
      COUNT(DISTINCT dp.property_id) as property_count,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT dp.property_id), 0) as avg_revenue_per_property,
      (COUNT(DISTINCT fbd.booking_id) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)) * COUNT(DISTINCT dp.property_id), 0)) * 100 as avg_occupancy_rate
    FROM ${catalog}.${gold_schema}.dim_host dh
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON dh.host_id = dp.host_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dh.is_current = true
    GROUP BY dh.host_id, dh.name, dh.country
    HAVING COUNT(DISTINCT dp.property_id) >= min_properties
  )
  SELECT 
    host_id,
    host_name,
    country,
    property_count,
    total_bookings,
    total_revenue,
    avg_revenue_per_property,
    avg_occupancy_rate,
    ((total_revenue / NULLIF(100000, 0)) * 50 + 
     (avg_occupancy_rate / 100) * 30 + 
     (property_count / NULLIF(10, 0)) * 20) as portfolio_performance_score
  FROM multi_property_metrics
  ORDER BY portfolio_performance_score DESC;

