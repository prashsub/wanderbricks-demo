-- =============================================================================
-- Wanderbricks Gold Layer - Property Domain TVFs for Genie
-- 
-- This file contains property performance and inventory-focused Table-Valued
-- Functions optimized for Genie Spaces and property management analytics.
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
-- TVF 1: get_property_performance
-- Returns comprehensive property performance metrics
-- =============================================================================

CREATE OR REPLACE FUNCTION get_property_performance(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  destination_filter STRING DEFAULT NULL COMMENT 'Optional: Filter to destination name (NULL for all)'
)
RETURNS TABLE (
  property_id BIGINT COMMENT 'Property identifier',
  property_title STRING COMMENT 'Property listing title',
  property_type STRING COMMENT 'Property type (apartment, house, etc.)',
  destination STRING COMMENT 'Property location',
  base_price FLOAT COMMENT 'Property base price per night',
  total_bookings BIGINT COMMENT 'Total bookings in period',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue generated',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Occupancy rate as percentage',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average revenue per booking',
  total_nights BIGINT COMMENT 'Total nights booked',
  conversion_rate DECIMAL(5,2) COMMENT 'Views to bookings conversion rate (%)',
  total_views BIGINT COMMENT 'Total property views',
  property_score DECIMAL(10,2) COMMENT 'Composite property performance score'
)
COMMENT 'LLM: Returns comprehensive property performance metrics including revenue, occupancy, and conversion.
Use this for: Property portfolio analysis, pricing strategy, inventory management, property comparison.
Parameters: start_date, end_date (YYYY-MM-DD format), optional destination_filter (NULL for all destinations).
Example questions: "How are properties performing in Paris?" "Show property KPIs" "Property performance metrics"'
RETURN
  WITH property_metrics AS (
    SELECT 
      dp.property_id,
      dp.title as property_title,
      dp.property_type,
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      dp.base_price,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      (COUNT(DISTINCT fbd.booking_id) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)), 0)) * 100 as avg_occupancy_rate,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0) as avg_booking_value,
      SUM(fbd.nights_booked) as total_nights,
      AVG(fpe.conversion_rate) as conversion_rate,
      SUM(fpe.view_count) as total_views
    FROM ${catalog}.${gold_schema}.dim_property dp
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON dp.destination_id = dd.destination_id
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    LEFT JOIN ${catalog}.${gold_schema}.fact_property_engagement fpe 
      ON dp.property_id = fpe.property_id 
      AND fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dp.is_current = true
      AND (destination_filter IS NULL OR CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) = destination_filter)
    GROUP BY dp.property_id, dp.title, dp.property_type, dd.destination, dd.state_or_province, dd.country, dp.base_price
  )
  SELECT 
    property_id,
    property_title,
    property_type,
    destination,
    base_price,
    total_bookings,
    total_revenue,
    avg_occupancy_rate,
    avg_booking_value,
    total_nights,
    conversion_rate,
    total_views,
    ((total_revenue / NULLIF(100000, 0)) * 40 + 
     (avg_occupancy_rate / 100) * 30 + 
     (conversion_rate / 5) * 30) as property_score
  FROM property_metrics
  ORDER BY property_score DESC;

-- =============================================================================
-- TVF 2: get_availability_by_destination
-- Returns property inventory metrics by destination
-- =============================================================================

CREATE OR REPLACE FUNCTION get_availability_by_destination(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 20 COMMENT 'Number of top destinations to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Destination rank by property count',
  destination STRING COMMENT 'Destination (city, state, country)',
  total_properties BIGINT COMMENT 'Total properties available',
  active_properties BIGINT COMMENT 'Properties with bookings in period',
  total_bookings BIGINT COMMENT 'Total bookings in destination',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Average occupancy rate (%)',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue for destination',
  avg_price DECIMAL(18,2) COMMENT 'Average property price per night',
  inventory_utilization DECIMAL(5,2) COMMENT 'Percentage of properties with bookings'
)
COMMENT 'LLM: Returns property inventory and availability metrics by destination.
Use this for: Inventory management, market capacity analysis, destination portfolio planning, supply/demand analysis.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 20).
Example questions: "Property inventory by destination" "How many properties in each market?" "Destination capacity"'
RETURN
  WITH destination_inventory AS (
    SELECT 
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      COUNT(DISTINCT dp.property_id) as total_properties,
      COUNT(DISTINCT CASE WHEN fbd.booking_id IS NOT NULL THEN dp.property_id END) as active_properties,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      (COUNT(DISTINCT fbd.booking_id) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)) * COUNT(DISTINCT dp.property_id), 0)) * 100 as avg_occupancy_rate,
      SUM(fbd.total_amount) as total_revenue,
      AVG(dp.base_price) as avg_price,
      (COUNT(DISTINCT CASE WHEN fbd.booking_id IS NOT NULL THEN dp.property_id END) / NULLIF(COUNT(DISTINCT dp.property_id), 0)) * 100 as inventory_utilization
    FROM ${catalog}.${gold_schema}.dim_destination dd
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON dd.destination_id = dp.destination_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY dd.destination, dd.state_or_province, dd.country
  ),
  ranked_destinations AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY total_properties DESC) as rank,
      destination,
      total_properties,
      active_properties,
      total_bookings,
      avg_occupancy_rate,
      total_revenue,
      avg_price,
      inventory_utilization
    FROM destination_inventory
  )
  SELECT * FROM ranked_destinations
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 3: get_property_type_analysis
-- Returns performance breakdown by property type
-- =============================================================================

CREATE OR REPLACE FUNCTION get_property_type_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  property_type STRING COMMENT 'Property type category',
  property_count BIGINT COMMENT 'Number of properties of this type',
  total_bookings BIGINT COMMENT 'Total bookings',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value',
  avg_nights_per_booking DECIMAL(10,2) COMMENT 'Average length of stay',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Occupancy rate (%)',
  conversion_rate DECIMAL(5,2) COMMENT 'Views to bookings conversion (%)',
  market_share_revenue DECIMAL(5,2) COMMENT 'Percentage of total revenue'
)
COMMENT 'LLM: Returns performance analysis by property type (apartment, house, villa, etc.).
Use this for: Property type strategy, inventory planning, pricing by type, market segmentation.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Performance by property type" "Which property types are most popular?" "Property type comparison"'
RETURN
  WITH type_metrics AS (
    SELECT 
      dp.property_type,
      COUNT(DISTINCT dp.property_id) as property_count,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0) as avg_booking_value,
      AVG(fbd.nights_booked) as avg_nights_per_booking,
      (COUNT(DISTINCT fbd.booking_id) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)) * COUNT(DISTINCT dp.property_id), 0)) * 100 as avg_occupancy_rate,
      AVG(fpe.conversion_rate) as conversion_rate
    FROM ${catalog}.${gold_schema}.dim_property dp
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    LEFT JOIN ${catalog}.${gold_schema}.fact_property_engagement fpe 
      ON dp.property_id = fpe.property_id 
      AND fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dp.is_current = true
    GROUP BY dp.property_type
  ),
  total_revenue_calc AS (
    SELECT SUM(total_revenue) as grand_total_revenue FROM type_metrics
  )
  SELECT 
    tm.property_type,
    tm.property_count,
    tm.total_bookings,
    tm.total_revenue,
    tm.avg_booking_value,
    tm.avg_nights_per_booking,
    tm.avg_occupancy_rate,
    tm.conversion_rate,
    (tm.total_revenue / NULLIF(tr.grand_total_revenue, 0)) * 100 as market_share_revenue
  FROM type_metrics tm
  CROSS JOIN total_revenue_calc tr
  ORDER BY total_revenue DESC;

-- =============================================================================
-- TVF 4: get_amenity_impact
-- Returns amenity correlation with booking performance
-- =============================================================================

CREATE OR REPLACE FUNCTION get_amenity_impact(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  bedrooms INT COMMENT 'Number of bedrooms',
  bathrooms INT COMMENT 'Number of bathrooms',
  max_guests INT COMMENT 'Maximum guests capacity',
  property_count BIGINT COMMENT 'Number of properties with this configuration',
  avg_booking_count DECIMAL(10,2) COMMENT 'Average bookings per property',
  avg_revenue_per_property DECIMAL(18,2) COMMENT 'Average revenue per property',
  avg_price DECIMAL(18,2) COMMENT 'Average base price',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Occupancy rate (%)',
  performance_score DECIMAL(10,2) COMMENT 'Composite performance score'
)
COMMENT 'LLM: Returns performance analysis by property amenities (bedrooms, bathrooms, capacity).
Use this for: Amenity optimization, pricing strategy, property development decisions, capacity planning.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Impact of amenities on performance" "Best performing property configurations" "Amenity analysis"'
RETURN
  WITH amenity_metrics AS (
    SELECT 
      dp.bedrooms,
      dp.bathrooms,
      dp.max_guests,
      COUNT(DISTINCT dp.property_id) as property_count,
      COUNT(DISTINCT fbd.booking_id) / NULLIF(COUNT(DISTINCT dp.property_id), 0) as avg_booking_count,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT dp.property_id), 0) as avg_revenue_per_property,
      AVG(dp.base_price) as avg_price,
      (COUNT(DISTINCT fbd.booking_id) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)) * COUNT(DISTINCT dp.property_id), 0)) * 100 as avg_occupancy_rate
    FROM ${catalog}.${gold_schema}.dim_property dp
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dp.is_current = true
    GROUP BY dp.bedrooms, dp.bathrooms, dp.max_guests
  )
  SELECT 
    bedrooms,
    bathrooms,
    max_guests,
    property_count,
    avg_booking_count,
    avg_revenue_per_property,
    avg_price,
    avg_occupancy_rate,
    ((avg_revenue_per_property / NULLIF(10000, 0)) * 50 + 
     (avg_occupancy_rate / 100) * 50) as performance_score
  FROM amenity_metrics
  WHERE property_count >= 3
  ORDER BY performance_score DESC;

-- =============================================================================
-- TVF 5: get_pricing_analysis
-- Returns price distribution and optimization insights
-- =============================================================================

CREATE OR REPLACE FUNCTION get_pricing_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  price_bucket STRING COMMENT 'Price range bucket',
  property_count BIGINT COMMENT 'Number of properties in bucket',
  total_bookings BIGINT COMMENT 'Total bookings',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Occupancy rate (%)',
  avg_conversion_rate DECIMAL(5,2) COMMENT 'Conversion rate (%)',
  revenue_per_property DECIMAL(18,2) COMMENT 'Average revenue per property',
  price_efficiency_score DECIMAL(10,2) COMMENT 'Price point efficiency score'
)
COMMENT 'LLM: Returns pricing analysis with performance by price bucket.
Use this for: Pricing optimization, competitive analysis, revenue management, price elasticity studies.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Pricing analysis" "Optimal price points" "Revenue by price range"'
RETURN
  WITH price_buckets AS (
    SELECT 
      CASE 
        WHEN dp.base_price < 100 THEN '$0-$99'
        WHEN dp.base_price BETWEEN 100 AND 199 THEN '$100-$199'
        WHEN dp.base_price BETWEEN 200 AND 299 THEN '$200-$299'
        WHEN dp.base_price BETWEEN 300 AND 499 THEN '$300-$499'
        ELSE '$500+'
      END as price_bucket,
      dp.property_id,
      dp.base_price,
      COUNT(DISTINCT fbd.booking_id) as booking_count,
      SUM(fbd.total_amount) as revenue,
      AVG(fpe.conversion_rate) as conversion_rate
    FROM ${catalog}.${gold_schema}.dim_property dp
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON dp.property_id = fbd.property_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    LEFT JOIN ${catalog}.${gold_schema}.fact_property_engagement fpe 
      ON dp.property_id = fpe.property_id 
      AND fpe.engagement_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE dp.is_current = true
    GROUP BY dp.property_id, dp.base_price
  ),
  bucket_metrics AS (
    SELECT 
      price_bucket,
      COUNT(DISTINCT property_id) as property_count,
      SUM(booking_count) as total_bookings,
      SUM(revenue) as total_revenue,
      (SUM(booking_count) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)) * COUNT(DISTINCT property_id), 0)) * 100 as avg_occupancy_rate,
      AVG(conversion_rate) as avg_conversion_rate,
      SUM(revenue) / NULLIF(COUNT(DISTINCT property_id), 0) as revenue_per_property
    FROM price_buckets
    GROUP BY price_bucket
  )
  SELECT 
    price_bucket,
    property_count,
    total_bookings,
    total_revenue,
    avg_occupancy_rate,
    avg_conversion_rate,
    revenue_per_property,
    ((revenue_per_property / NULLIF(10000, 0)) * 60 + 
     (avg_occupancy_rate / 100) * 40) as price_efficiency_score
  FROM bucket_metrics
  ORDER BY 
    CASE price_bucket
      WHEN '$0-$99' THEN 1
      WHEN '$100-$199' THEN 2
      WHEN '$200-$299' THEN 3
      WHEN '$300-$499' THEN 4
      WHEN '$500+' THEN 5
    END;

