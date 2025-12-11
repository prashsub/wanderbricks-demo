-- =============================================================================
-- Wanderbricks Gold Layer - Revenue Domain TVFs for Genie
-- 
-- This file contains revenue-focused Table-Valued Functions optimized for
-- Genie Spaces and natural language queries.
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
-- TVF 1: get_revenue_by_period
-- Returns revenue metrics aggregated by time period
-- =============================================================================

CREATE OR REPLACE FUNCTION get_revenue_by_period(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  time_grain STRING DEFAULT 'day' COMMENT 'Aggregation grain: day, week, month, quarter, year'
)
RETURNS TABLE (
  period_start DATE COMMENT 'Start date of the period',
  period_name STRING COMMENT 'Human-friendly period label',
  total_revenue DECIMAL(18,2) COMMENT 'Total booking revenue for period',
  booking_count BIGINT COMMENT 'Number of bookings',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average revenue per booking',
  confirmed_bookings BIGINT COMMENT 'Number of confirmed bookings',
  cancellation_count BIGINT COMMENT 'Number of cancelled bookings',
  cancellation_rate DECIMAL(5,2) COMMENT 'Cancellation rate as percentage',
  unique_properties BIGINT COMMENT 'Number of unique properties booked',
  unique_guests BIGINT COMMENT 'Number of unique guests'
)
COMMENT 'LLM: Returns revenue metrics aggregated by time period (day, week, month, quarter, year).
Use this for: Revenue trends, period-over-period comparisons, seasonal analysis, and financial reporting.
Parameters: start_date, end_date (YYYY-MM-DD format), optional time_grain (default: day).
Example questions: "What was revenue last month?" "Show me weekly booking trends" "Compare quarterly revenue"'
RETURN
  WITH period_data AS (
    SELECT 
      DATE_TRUNC(time_grain, fbd.check_in_date) AS period_start,
      CASE 
        WHEN time_grain = 'day' THEN DATE_FORMAT(fbd.check_in_date, 'yyyy-MM-dd')
        WHEN time_grain = 'week' THEN CONCAT('Week ', WEEKOFYEAR(fbd.check_in_date), ' ', YEAR(fbd.check_in_date))
        WHEN time_grain = 'month' THEN DATE_FORMAT(fbd.check_in_date, 'MMMM yyyy')
        WHEN time_grain = 'quarter' THEN CONCAT('Q', QUARTER(fbd.check_in_date), ' ', YEAR(fbd.check_in_date))
        WHEN time_grain = 'year' THEN CAST(YEAR(fbd.check_in_date) AS STRING)
        ELSE DATE_FORMAT(fbd.check_in_date, 'yyyy-MM-dd')
      END AS period_name,
      fbd.total_booking_value as total_revenue,
      fbd.booking_count,
      fbd.avg_booking_value,
      fbd.confirmed_booking_count as confirmed_bookings,
      fbd.cancellation_count
    FROM ${catalog}.${gold_schema}.fact_booking_daily fbd
    WHERE fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
  ),
  aggregated_periods AS (
    SELECT 
      pd.period_start,
      pd.period_name,
      SUM(pd.total_revenue) as total_revenue,
      SUM(pd.booking_count) as booking_count,
      SUM(pd.total_revenue) / NULLIF(SUM(pd.booking_count), 0) as avg_booking_value,
      SUM(pd.confirmed_bookings) as confirmed_bookings,
      SUM(pd.cancellation_count) as cancellation_count,
      (SUM(pd.cancellation_count) / NULLIF(SUM(pd.booking_count), 0)) * 100 as cancellation_rate,
      COUNT(DISTINCT fbd.property_id) as unique_properties,
      SUM(fbd.total_guests) as unique_guests
    FROM period_data pd
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_daily fbd
      ON DATE_TRUNC(time_grain, fbd.check_in_date) = pd.period_start
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY pd.period_start, pd.period_name
  )
  SELECT 
    period_start,
    period_name,
    total_revenue,
    booking_count,
    avg_booking_value,
    confirmed_bookings,
    cancellation_count,
    cancellation_rate,
    unique_properties,
    unique_guests
  FROM aggregated_periods
  ORDER BY period_start;

-- =============================================================================
-- TVF 2: get_top_properties_by_revenue
-- Returns top N properties by revenue for date range
-- =============================================================================

CREATE OR REPLACE FUNCTION get_top_properties_by_revenue(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 10 COMMENT 'Number of top properties to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Property rank by revenue',
  property_id BIGINT COMMENT 'Property identifier',
  property_title STRING COMMENT 'Property listing title',
  destination STRING COMMENT 'Property destination (city, state, country)',
  property_type STRING COMMENT 'Property type (apartment, house, etc.)',
  host_name STRING COMMENT 'Property owner name',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue for period',
  booking_count BIGINT COMMENT 'Number of bookings',
  avg_revenue_per_booking DECIMAL(18,2) COMMENT 'Average revenue per booking',
  total_nights BIGINT COMMENT 'Total nights booked',
  avg_occupancy_rate DECIMAL(5,2) COMMENT 'Occupancy rate as percentage'
)
COMMENT 'LLM: Returns top N properties ranked by revenue for a date range.
Use this for: Property performance analysis, revenue optimization, identifying best performers, property portfolio management.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 10).
Example questions: "Top 10 revenue generating properties" "Best performing listings" "Which properties made the most money?"'
RETURN
  WITH property_metrics AS (
    SELECT 
      fbd.property_id,
      dp.title as property_title,
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      dp.property_type,
      dh.name as host_name,
      SUM(fbd.total_booking_value) as total_revenue,
      SUM(fbd.booking_count) as booking_count,
      SUM(fbd.total_booking_value) / NULLIF(SUM(fbd.booking_count), 0) as avg_revenue_per_booking,
      SUM(fbd.avg_nights_booked * fbd.booking_count) as total_nights,
      (SUM(fbd.booking_count) / NULLIF(DATEDIFF(CAST(end_date AS DATE), CAST(start_date AS DATE)), 0)) * 100 as avg_occupancy_rate
    FROM ${catalog}.${gold_schema}.fact_booking_daily fbd
    LEFT JOIN ${catalog}.${gold_schema}.dim_property dp 
      ON fbd.property_id = dp.property_id 
      AND dp.is_current = true
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON fbd.destination_id = dd.destination_id
    LEFT JOIN ${catalog}.${gold_schema}.dim_host dh 
      ON dp.host_id = dh.host_id 
      AND dh.is_current = true
    WHERE fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fbd.property_id, dp.title, dd.destination, dd.state_or_province, dd.country, dp.property_type, dh.name
  ),
  ranked_properties AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank,
      property_id,
      property_title,
      destination,
      property_type,
      host_name,
      total_revenue,
      booking_count,
      avg_revenue_per_booking,
      total_nights,
      avg_occupancy_rate
    FROM property_metrics
  )
  SELECT * FROM ranked_properties
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 3: get_revenue_by_destination
-- Returns revenue breakdown by destination/geography
-- =============================================================================

CREATE OR REPLACE FUNCTION get_revenue_by_destination(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 20 COMMENT 'Number of top destinations to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Destination rank by revenue',
  destination_id BIGINT COMMENT 'Destination identifier',
  destination STRING COMMENT 'Destination city/area name',
  state_or_province STRING COMMENT 'Destination state/region',
  country STRING COMMENT 'Destination country',
  property_count BIGINT COMMENT 'Number of properties in destination',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue for destination',
  booking_count BIGINT COMMENT 'Number of bookings',
  avg_revenue_per_property DECIMAL(18,2) COMMENT 'Average revenue per property',
  unique_guests BIGINT COMMENT 'Number of unique guests'
)
COMMENT 'LLM: Returns revenue breakdown by geographic destination/market.
Use this for: Geographic market analysis, destination popularity tracking, regional performance comparisons, market expansion planning.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 20).
Example questions: "Revenue by destination" "Top performing cities" "Which markets generate most revenue?"'
RETURN
  WITH destination_metrics AS (
    SELECT 
      fbd.destination_id,
      dd.destination,
      dd.state_or_province,
      dd.country,
      COUNT(DISTINCT fbd.property_id) as property_count,
      SUM(fbd.total_booking_value) as total_revenue,
      SUM(fbd.booking_count) as booking_count,
      SUM(fbd.total_booking_value) / NULLIF(COUNT(DISTINCT fbd.property_id), 0) as avg_revenue_per_property,
      SUM(fbd.total_guests) as unique_guests
    FROM ${catalog}.${gold_schema}.fact_booking_daily fbd
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON fbd.destination_id = dd.destination_id
    WHERE fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY fbd.destination_id, dd.destination, dd.state_or_province, dd.country
  ),
  ranked_destinations AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank,
      destination_id,
      destination,
      state_or_province,
      country,
      property_count,
      total_revenue,
      booking_count,
      avg_revenue_per_property,
      unique_guests
    FROM destination_metrics
  )
  SELECT * FROM ranked_destinations
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 4: get_payment_metrics
-- Returns payment completion rates and method analysis
-- =============================================================================

CREATE OR REPLACE FUNCTION get_payment_metrics(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  payment_method STRING COMMENT 'Payment method used',
  booking_count BIGINT COMMENT 'Number of bookings with this payment method',
  total_payment_amount DECIMAL(18,2) COMMENT 'Total payments processed',
  avg_payment_amount DECIMAL(18,2) COMMENT 'Average payment amount',
  payment_completion_rate DECIMAL(5,2) COMMENT 'Percentage of bookings with completed payments',
  total_booking_value DECIMAL(18,2) COMMENT 'Total booking value (including unpaid)'
)
COMMENT 'LLM: Returns payment completion rates and payment method analysis.
Use this for: Payment method preference analysis, payment success rates, payment processing optimization, financial reconciliation.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Payment completion rates" "Most popular payment methods" "Payment method performance"'
RETURN
  WITH payment_data AS (
    SELECT 
      COALESCE(payment_method, 'Unpaid/Pending') as payment_method,
      COUNT(*) as booking_count,
      SUM(COALESCE(payment_amount, 0)) as total_payment_amount,
      SUM(COALESCE(payment_amount, 0)) / NULLIF(COUNT(*), 0) as avg_payment_amount,
      (SUM(CASE WHEN payment_amount IS NOT NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100 as payment_completion_rate,
      SUM(total_amount) as total_booking_value
    FROM ${catalog}.${gold_schema}.fact_booking_detail
    WHERE check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY COALESCE(payment_method, 'Unpaid/Pending')
  )
  SELECT 
    payment_method,
    booking_count,
    total_payment_amount,
    avg_payment_amount,
    payment_completion_rate,
    total_booking_value
  FROM payment_data
  ORDER BY total_payment_amount DESC;

-- =============================================================================
-- TVF 5: get_cancellation_analysis
-- Returns cancellation patterns and revenue impact
-- =============================================================================

CREATE OR REPLACE FUNCTION get_cancellation_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  destination STRING COMMENT 'Destination (city, state, country)',
  total_bookings BIGINT COMMENT 'Total bookings (confirmed + cancelled)',
  confirmed_bookings BIGINT COMMENT 'Number of confirmed bookings',
  cancelled_bookings BIGINT COMMENT 'Number of cancelled bookings',
  cancellation_rate DECIMAL(5,2) COMMENT 'Cancellation rate as percentage',
  potential_revenue DECIMAL(18,2) COMMENT 'Total booking value including cancelled',
  actual_revenue DECIMAL(18,2) COMMENT 'Revenue from confirmed bookings only',
  lost_revenue DECIMAL(18,2) COMMENT 'Revenue lost to cancellations'
)
COMMENT 'LLM: Returns cancellation patterns and revenue impact by destination.
Use this for: Cancellation trend analysis, risk assessment, revenue forecasting, destination-specific cancellation patterns.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Cancellation rates by destination" "How much revenue lost to cancellations?" "Which markets have highest cancellations?"'
RETURN
  WITH cancellation_data AS (
    SELECT 
      CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country) as destination,
      COUNT(*) as total_bookings,
      SUM(CASE WHEN fbd.status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_bookings,
      SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) as cancelled_bookings,
      (SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100 as cancellation_rate,
      SUM(fbd.total_amount) as potential_revenue,
      SUM(CASE WHEN fbd.status = 'confirmed' THEN fbd.total_amount ELSE 0 END) as actual_revenue,
      SUM(CASE WHEN fbd.is_cancelled THEN fbd.total_amount ELSE 0 END) as lost_revenue
    FROM ${catalog}.${gold_schema}.fact_booking_detail fbd
    LEFT JOIN ${catalog}.${gold_schema}.dim_destination dd 
      ON fbd.destination_id = dd.destination_id
    WHERE fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY dd.destination, dd.state_or_province, dd.country
  )
  SELECT 
    destination,
    total_bookings,
    confirmed_bookings,
    cancelled_bookings,
    cancellation_rate,
    potential_revenue,
    actual_revenue,
    lost_revenue
  FROM cancellation_data
  WHERE total_bookings > 0
  ORDER BY lost_revenue DESC;

-- =============================================================================
-- TVF 6: get_revenue_forecast_inputs
-- Returns historical data formatted for revenue forecasting ML models
-- =============================================================================

CREATE OR REPLACE FUNCTION get_revenue_forecast_inputs(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  property_id_filter BIGINT DEFAULT NULL COMMENT 'Optional: Filter to specific property (NULL for all)'
)
RETURNS TABLE (
  ds DATE COMMENT 'Date (Prophet-compatible column name)',
  property_id BIGINT COMMENT 'Property identifier for grouping',
  y DECIMAL(18,2) COMMENT 'Daily revenue (Prophet-compatible target variable)',
  booking_count BIGINT COMMENT 'Number of bookings (feature)',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value (feature)',
  day_of_week INT COMMENT 'Day of week (1=Sunday, feature)',
  is_weekend BOOLEAN COMMENT 'Weekend indicator (feature)',
  month INT COMMENT 'Month number (feature)',
  quarter INT COMMENT 'Quarter number (feature)'
)
COMMENT 'LLM: Returns historical revenue data formatted for ML forecasting models (Prophet-compatible).
Use this for: Revenue forecasting, demand prediction, ML model training, time series analysis.
Parameters: start_date, end_date (YYYY-MM-DD format), optional property_id_filter (NULL for all properties).
Example questions: "Get data for revenue forecasting" "Historical revenue for ML model" "Time series data for predictions"'
RETURN
  SELECT 
    fbd.check_in_date as ds,
    fbd.property_id,
    fbd.total_booking_value as y,
    fbd.booking_count,
    fbd.avg_booking_value,
    DAYOFWEEK(fbd.check_in_date) as day_of_week,
    dd.is_weekend,
    MONTH(fbd.check_in_date) as month,
    QUARTER(fbd.check_in_date) as quarter
  FROM ${catalog}.${gold_schema}.fact_booking_daily fbd
  LEFT JOIN ${catalog}.${gold_schema}.dim_date dd 
    ON fbd.check_in_date = dd.date
  WHERE fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    AND (property_id_filter IS NULL OR fbd.property_id = property_id_filter)
  ORDER BY ds, property_id;

