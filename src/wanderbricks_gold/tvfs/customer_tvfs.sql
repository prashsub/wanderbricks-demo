-- =============================================================================
-- Wanderbricks Gold Layer - Customer Domain TVFs for Genie
-- 
-- This file contains customer behavior and segmentation-focused Table-Valued
-- Functions optimized for Genie Spaces and customer analytics.
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
-- TVF 1: get_customer_segments
-- Returns customer segmentation based on booking behavior
-- =============================================================================

CREATE OR REPLACE FUNCTION get_customer_segments(
  start_date STRING COMMENT 'Start date for segment calculation (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date for segment calculation (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  segment_name STRING COMMENT 'Customer segment category',
  customer_count BIGINT COMMENT 'Number of customers in segment',
  total_bookings BIGINT COMMENT 'Total bookings from segment',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue from segment',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value',
  avg_bookings_per_customer DECIMAL(10,2) COMMENT 'Average bookings per customer',
  segment_revenue_share DECIMAL(5,2) COMMENT 'Percentage of total revenue',
  avg_nights_per_booking DECIMAL(10,2) COMMENT 'Average length of stay',
  cancellation_rate DECIMAL(5,2) COMMENT 'Cancellation rate (%)'
)
COMMENT 'LLM: Returns customer segment analysis based on booking behavior (frequency, value, recency).
Use this for: Customer segmentation, marketing targeting, loyalty programs, customer lifecycle management.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "What are our customer segments?" "Show segment performance" "Customer segmentation analysis"'
RETURN
  WITH customer_metrics AS (
    SELECT 
      du.user_id,
      COUNT(DISTINCT fbd.booking_id) as booking_count,
      SUM(fbd.total_amount) as total_revenue,
      MAX(fbd.created_at) as last_booking_date
    FROM ${catalog}.${gold_schema}.dim_user du
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON du.user_id = fbd.user_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE du.is_current = true
    GROUP BY du.user_id
  ),
  segmented_customers AS (
    SELECT 
      cm.user_id,
      CASE 
        WHEN cm.booking_count = 0 THEN 'Inactive'
        WHEN cm.booking_count = 1 THEN 'One-time Booker'
        WHEN cm.booking_count BETWEEN 2 AND 3 THEN 'Repeat Customer'
        WHEN cm.booking_count BETWEEN 4 AND 6 THEN 'Frequent Traveler'
        WHEN cm.booking_count >= 7 THEN 'VIP Customer'
        ELSE 'Unknown'
      END as segment_name,
      cm.booking_count,
      cm.total_revenue
    FROM customer_metrics cm
  ),
  segment_stats AS (
    SELECT 
      sc.segment_name,
      COUNT(DISTINCT sc.user_id) as customer_count,
      SUM(fbd_count.booking_count) as total_bookings,
      SUM(fbd_sum.revenue) as total_revenue,
      SUM(fbd_sum.revenue) / NULLIF(SUM(fbd_count.booking_count), 0) as avg_booking_value,
      SUM(fbd_count.booking_count) / NULLIF(COUNT(DISTINCT sc.user_id), 0) as avg_bookings_per_customer,
      AVG(fbd.nights_booked) as avg_nights_per_booking,
      (SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) / NULLIF(SUM(fbd_count.booking_count), 0)) * 100 as cancellation_rate
    FROM segmented_customers sc
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON sc.user_id = fbd.user_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    LEFT JOIN (
      SELECT user_id, COUNT(*) as booking_count
      FROM ${catalog}.${gold_schema}.fact_booking_detail
      WHERE check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      GROUP BY user_id
    ) fbd_count ON sc.user_id = fbd_count.user_id
    LEFT JOIN (
      SELECT user_id, SUM(total_amount) as revenue
      FROM ${catalog}.${gold_schema}.fact_booking_detail
      WHERE check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
      GROUP BY user_id
    ) fbd_sum ON sc.user_id = fbd_sum.user_id
    GROUP BY sc.segment_name
  ),
  total_revenue_calc AS (
    SELECT SUM(total_revenue) as grand_total_revenue FROM segment_stats
  )
  SELECT 
    ss.segment_name,
    ss.customer_count,
    ss.total_bookings,
    ss.total_revenue,
    ss.avg_booking_value,
    ss.avg_bookings_per_customer,
    (ss.total_revenue / NULLIF(tr.grand_total_revenue, 0)) * 100 as segment_revenue_share,
    ss.avg_nights_per_booking,
    ss.cancellation_rate
  FROM segment_stats ss
  CROSS JOIN total_revenue_calc tr
  ORDER BY 
    CASE segment_name
      WHEN 'VIP Customer' THEN 1
      WHEN 'Frequent Traveler' THEN 2
      WHEN 'Repeat Customer' THEN 3
      WHEN 'One-time Booker' THEN 4
      WHEN 'Inactive' THEN 5
    END;

-- =============================================================================
-- TVF 2: get_customer_ltv
-- Returns customer lifetime value calculation
-- =============================================================================

CREATE OR REPLACE FUNCTION get_customer_ltv(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 100 COMMENT 'Number of top customers to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Customer rank by lifetime value',
  user_id BIGINT COMMENT 'Customer identifier',
  country STRING COMMENT 'Customer country',
  user_type STRING COMMENT 'User type (individual/business)',
  total_bookings BIGINT COMMENT 'Total bookings',
  lifetime_value DECIMAL(18,2) COMMENT 'Total revenue from customer',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value',
  first_booking_date DATE COMMENT 'Date of first booking',
  last_booking_date DATE COMMENT 'Date of most recent booking',
  days_since_last_booking INT COMMENT 'Recency metric (days)',
  customer_tenure_days INT COMMENT 'Days since first booking'
)
COMMENT 'LLM: Returns customer lifetime value (LTV) ranked by total revenue contribution.
Use this for: VIP customer identification, customer value analysis, retention strategies, loyalty program targeting.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 100).
Example questions: "Top customers by lifetime value" "Highest value customers" "Customer LTV analysis"'
RETURN
  WITH customer_ltv AS (
    SELECT 
      du.user_id,
      du.country,
      du.user_type,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as lifetime_value,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0) as avg_booking_value,
      MIN(fbd.check_in_date) as first_booking_date,
      MAX(fbd.check_in_date) as last_booking_date,
      DATEDIFF(CURRENT_DATE(), MAX(fbd.check_in_date)) as days_since_last_booking,
      DATEDIFF(MAX(fbd.check_in_date), MIN(fbd.check_in_date)) as customer_tenure_days
    FROM ${catalog}.${gold_schema}.dim_user du
    INNER JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON du.user_id = fbd.user_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE du.is_current = true
    GROUP BY du.user_id, du.country, du.user_type
  ),
  ranked_customers AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY lifetime_value DESC) as rank,
      user_id,
      country,
      user_type,
      total_bookings,
      lifetime_value,
      avg_booking_value,
      first_booking_date,
      last_booking_date,
      days_since_last_booking,
      customer_tenure_days
    FROM customer_ltv
  )
  SELECT * FROM ranked_customers
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 3: get_booking_frequency_analysis
-- Returns booking frequency distribution and patterns
-- =============================================================================

CREATE OR REPLACE FUNCTION get_booking_frequency_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  booking_frequency_bucket STRING COMMENT 'Frequency bucket (1, 2-3, 4-6, 7+)',
  customer_count BIGINT COMMENT 'Number of customers in bucket',
  total_bookings BIGINT COMMENT 'Total bookings from bucket',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue from bucket',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value',
  customer_percentage DECIMAL(5,2) COMMENT 'Percentage of total customers',
  revenue_percentage DECIMAL(5,2) COMMENT 'Percentage of total revenue'
)
COMMENT 'LLM: Returns booking frequency distribution showing customer behavior patterns.
Use this for: Frequency analysis, repeat purchase behavior, customer loyalty assessment, engagement strategies.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Booking frequency distribution" "How often do customers book?" "Repeat booking patterns"'
RETURN
  WITH customer_frequency AS (
    SELECT 
      du.user_id,
      CASE 
        WHEN COUNT(DISTINCT fbd.booking_id) = 1 THEN '1 Booking'
        WHEN COUNT(DISTINCT fbd.booking_id) BETWEEN 2 AND 3 THEN '2-3 Bookings'
        WHEN COUNT(DISTINCT fbd.booking_id) BETWEEN 4 AND 6 THEN '4-6 Bookings'
        WHEN COUNT(DISTINCT fbd.booking_id) >= 7 THEN '7+ Bookings'
        ELSE 'No Bookings'
      END as booking_frequency_bucket,
      COUNT(DISTINCT fbd.booking_id) as booking_count,
      SUM(fbd.total_amount) as revenue
    FROM ${catalog}.${gold_schema}.dim_user du
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON du.user_id = fbd.user_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE du.is_current = true
    GROUP BY du.user_id
  ),
  frequency_stats AS (
    SELECT 
      booking_frequency_bucket,
      COUNT(DISTINCT user_id) as customer_count,
      SUM(booking_count) as total_bookings,
      SUM(revenue) as total_revenue,
      SUM(revenue) / NULLIF(SUM(booking_count), 0) as avg_booking_value
    FROM customer_frequency
    GROUP BY booking_frequency_bucket
  ),
  totals AS (
    SELECT 
      SUM(customer_count) as total_customers,
      SUM(total_revenue) as grand_total_revenue
    FROM frequency_stats
  )
  SELECT 
    fs.booking_frequency_bucket,
    fs.customer_count,
    fs.total_bookings,
    fs.total_revenue,
    fs.avg_booking_value,
    (fs.customer_count / NULLIF(t.total_customers, 0)) * 100 as customer_percentage,
    (fs.total_revenue / NULLIF(t.grand_total_revenue, 0)) * 100 as revenue_percentage
  FROM frequency_stats fs
  CROSS JOIN totals t
  ORDER BY 
    CASE booking_frequency_bucket
      WHEN '7+ Bookings' THEN 1
      WHEN '4-6 Bookings' THEN 2
      WHEN '2-3 Bookings' THEN 3
      WHEN '1 Booking' THEN 4
      WHEN 'No Bookings' THEN 5
    END;

-- =============================================================================
-- TVF 4: get_customer_geographic_analysis
-- Returns customer distribution and behavior by country
-- =============================================================================

CREATE OR REPLACE FUNCTION get_customer_geographic_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)',
  top_n INT DEFAULT 20 COMMENT 'Number of top countries to return'
)
RETURNS TABLE (
  rank BIGINT COMMENT 'Country rank by customer count',
  country STRING COMMENT 'Customer country',
  customer_count BIGINT COMMENT 'Number of customers',
  total_bookings BIGINT COMMENT 'Total bookings',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_bookings_per_customer DECIMAL(10,2) COMMENT 'Average bookings per customer',
  avg_revenue_per_customer DECIMAL(18,2) COMMENT 'Average revenue per customer',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value',
  cancellation_rate DECIMAL(5,2) COMMENT 'Cancellation rate (%)'
)
COMMENT 'LLM: Returns customer geographic distribution and behavior by country.
Use this for: Geographic customer analysis, market segmentation, international marketing, regional strategies.
Parameters: start_date, end_date (YYYY-MM-DD format), optional top_n (default: 20).
Example questions: "Customers by country" "Geographic customer distribution" "Which countries have most customers?"'
RETURN
  WITH country_metrics AS (
    SELECT 
      du.country,
      COUNT(DISTINCT du.user_id) as customer_count,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      COUNT(DISTINCT fbd.booking_id) / NULLIF(COUNT(DISTINCT du.user_id), 0) as avg_bookings_per_customer,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT du.user_id), 0) as avg_revenue_per_customer,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0) as avg_booking_value,
      (SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0)) * 100 as cancellation_rate
    FROM ${catalog}.${gold_schema}.dim_user du
    LEFT JOIN ${catalog}.${gold_schema}.fact_booking_detail fbd 
      ON du.user_id = fbd.user_id 
      AND fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    WHERE du.is_current = true
    GROUP BY du.country
  ),
  ranked_countries AS (
    SELECT 
      ROW_NUMBER() OVER (ORDER BY customer_count DESC) as rank,
      country,
      customer_count,
      total_bookings,
      total_revenue,
      avg_bookings_per_customer,
      avg_revenue_per_customer,
      avg_booking_value,
      cancellation_rate
    FROM country_metrics
  )
  SELECT * FROM ranked_countries
  WHERE rank <= top_n
  ORDER BY rank;

-- =============================================================================
-- TVF 5: get_business_vs_leisure_analysis
-- Returns business vs leisure booking pattern comparison
-- =============================================================================

CREATE OR REPLACE FUNCTION get_business_vs_leisure_analysis(
  start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)',
  end_date STRING COMMENT 'End date (format: YYYY-MM-DD)'
)
RETURNS TABLE (
  booking_type STRING COMMENT 'Booking type (Business/Leisure)',
  customer_count BIGINT COMMENT 'Number of customers',
  total_bookings BIGINT COMMENT 'Total bookings',
  total_revenue DECIMAL(18,2) COMMENT 'Total revenue',
  avg_booking_value DECIMAL(18,2) COMMENT 'Average booking value',
  avg_nights_booked DECIMAL(10,2) COMMENT 'Average length of stay',
  avg_lead_time_days DECIMAL(10,2) COMMENT 'Average booking lead time (days)',
  cancellation_rate DECIMAL(5,2) COMMENT 'Cancellation rate (%)',
  payment_completion_rate DECIMAL(5,2) COMMENT 'Payment completion rate (%)'
)
COMMENT 'LLM: Returns comparison of business vs leisure booking patterns and behaviors.
Use this for: B2B vs B2C segmentation, corporate account targeting, booking pattern analysis, pricing strategies.
Parameters: start_date, end_date (YYYY-MM-DD format).
Example questions: "Business vs leisure bookings" "Corporate booking patterns" "B2B vs B2C comparison"'
RETURN
  WITH booking_type_metrics AS (
    SELECT 
      CASE 
        WHEN fbd.is_business_booking THEN 'Business'
        ELSE 'Leisure'
      END as booking_type,
      COUNT(DISTINCT du.user_id) as customer_count,
      COUNT(DISTINCT fbd.booking_id) as total_bookings,
      SUM(fbd.total_amount) as total_revenue,
      SUM(fbd.total_amount) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0) as avg_booking_value,
      AVG(fbd.nights_booked) as avg_nights_booked,
      AVG(fbd.days_between_booking_and_checkin) as avg_lead_time_days,
      (SUM(CASE WHEN fbd.is_cancelled THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0)) * 100 as cancellation_rate,
      (SUM(CASE WHEN fbd.payment_amount IS NOT NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT fbd.booking_id), 0)) * 100 as payment_completion_rate
    FROM ${catalog}.${gold_schema}.fact_booking_detail fbd
    LEFT JOIN ${catalog}.${gold_schema}.dim_user du 
      ON fbd.user_id = du.user_id 
      AND du.is_current = true
    WHERE fbd.check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY CASE WHEN fbd.is_business_booking THEN 'Business' ELSE 'Leisure' END
  )
  SELECT 
    booking_type,
    customer_count,
    total_bookings,
    total_revenue,
    avg_booking_value,
    avg_nights_booked,
    avg_lead_time_days,
    cancellation_rate,
    payment_completion_rate
  FROM booking_type_metrics
  ORDER BY 
    CASE booking_type
      WHEN 'Business' THEN 1
      WHEN 'Leisure' THEN 2
    END;

