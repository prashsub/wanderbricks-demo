# Phase 4 Addendum 4.2: Table-Valued Functions (TVFs)

## Overview

**Status:** ✅ Implemented  
**Dependencies:** Phase 3 (Gold Layer)  
**Artifact Count:** 26 TVFs  
**Reference:** [TVF Patterns](../.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc)

---

## Purpose

Table-Valued Functions (TVFs) provide:
1. **Parameterized queries** for Genie natural language interfaces
2. **Reusable analytics logic** for consistent metric calculations
3. **Row-level security** through parameter-based filtering
4. **LLM-friendly interfaces** with comprehensive function comments

---

## TVF Summary by Domain

| Domain | Icon | TVF Count | Primary Tables |
|--------|------|-----------|----------------|
| Revenue | 💰 | 6 | fact_booking_daily, fact_booking_detail |
| Engagement | 📊 | 5 | fact_property_engagement |
| Property | 🏠 | 5 | dim_property, fact_booking_daily |
| Host | 👤 | 5 | dim_host, fact_booking_detail |
| Customer | 🎯 | 5 | dim_user, fact_booking_detail |
| **Total** | | **26** | |

---

## 💰 Revenue Domain TVFs

### 1. get_revenue_by_period

**Purpose:** Return revenue metrics aggregated by time period

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_revenue_by_period(
    start_date STRING COMMENT 'Start date in YYYY-MM-DD format',
    end_date STRING COMMENT 'End date in YYYY-MM-DD format',
    time_grain STRING DEFAULT 'day' COMMENT 'Aggregation grain: day, week, month, quarter, year'
)
RETURNS TABLE (
    period_start DATE,
    period_name STRING,
    total_revenue DECIMAL(18,2),
    booking_count BIGINT,
    avg_booking_value DECIMAL(18,2),
    confirmed_bookings BIGINT,
    cancellation_count BIGINT,
    cancellation_rate DECIMAL(5,2)
)
COMMENT 'LLM: Returns revenue metrics aggregated by time period.
Use for: Revenue trends, period-over-period comparisons, seasonal analysis.
Example questions: "What was revenue last month?" "Show me weekly booking trends"'
RETURN
    SELECT 
        DATE_TRUNC(time_grain, check_in_date) AS period_start,
        -- Period name logic
        ...
    FROM ${catalog}.${gold_schema}.fact_booking_daily
    WHERE check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY 1
    ORDER BY 1;
```

### 2. get_top_properties_by_revenue

**Purpose:** Return top N properties by revenue

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_top_properties_by_revenue(
    start_date STRING COMMENT 'Start date in YYYY-MM-DD format',
    end_date STRING COMMENT 'End date in YYYY-MM-DD format',
    top_n INT DEFAULT 10 COMMENT 'Number of properties to return'
)
RETURNS TABLE (
    property_id BIGINT,
    property_title STRING,
    destination STRING,
    total_revenue DECIMAL(18,2),
    booking_count BIGINT,
    avg_revenue_per_booking DECIMAL(18,2),
    revenue_rank BIGINT
)
COMMENT 'LLM: Returns top performing properties by revenue.
Use for: Property performance analysis, revenue optimization.
Example questions: "Top 10 revenue generating properties" "Best performing listings"';
```

### 3. get_revenue_by_destination

**Purpose:** Revenue breakdown by destination/geography

### 4. get_payment_metrics

**Purpose:** Payment completion rates and method analysis

### 5. get_cancellation_analysis

**Purpose:** Cancellation patterns and revenue impact

### 6. get_revenue_forecast_inputs

**Purpose:** Historical data formatted for revenue forecasting ML model

---

## 📊 Engagement Domain TVFs

### 1. get_property_engagement

**Purpose:** Engagement metrics for properties

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_property_engagement(
    start_date STRING COMMENT 'Start date in YYYY-MM-DD format',
    end_date STRING COMMENT 'End date in YYYY-MM-DD format',
    property_id_filter BIGINT DEFAULT NULL COMMENT 'Optional: Filter to specific property'
)
RETURNS TABLE (
    property_id BIGINT,
    property_title STRING,
    total_views BIGINT,
    unique_viewers BIGINT,
    total_clicks BIGINT,
    search_appearances BIGINT,
    conversion_rate DECIMAL(5,2),
    avg_time_on_page DECIMAL(10,2)
)
COMMENT 'LLM: Returns engagement metrics for properties.
Use for: Marketing analysis, content optimization, funnel analysis.
Example questions: "Which properties have highest engagement?" "Show conversion rates"';
```

### 2. get_conversion_funnel

**Purpose:** View → Click → Book funnel analysis

### 3. get_traffic_source_analysis

**Purpose:** Performance by referrer/source

### 4. get_device_engagement

**Purpose:** Engagement breakdown by device type

### 5. get_engagement_trends

**Purpose:** Daily/weekly engagement trends

---

## 🏠 Property Domain TVFs

### 1. get_property_performance

**Purpose:** Comprehensive property performance metrics

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_property_performance(
    start_date STRING COMMENT 'Start date in YYYY-MM-DD format',
    end_date STRING COMMENT 'End date in YYYY-MM-DD format',
    destination_filter STRING DEFAULT NULL COMMENT 'Optional: Filter to destination name'
)
RETURNS TABLE (
    property_id BIGINT,
    property_title STRING,
    property_type STRING,
    destination STRING,
    base_price FLOAT,
    total_bookings BIGINT,
    total_revenue DECIMAL(18,2),
    avg_occupancy_rate DECIMAL(5,2),
    avg_review_rating FLOAT,
    conversion_rate DECIMAL(5,2)
)
COMMENT 'LLM: Returns comprehensive property performance metrics.
Use for: Property portfolio analysis, pricing strategy, inventory management.
Example questions: "How are properties performing in Paris?" "Show property KPIs"';
```

### 2. get_availability_by_destination

**Purpose:** Property inventory by destination

### 3. get_property_type_analysis

**Purpose:** Performance by property type

### 4. get_amenity_impact

**Purpose:** Amenity correlation with performance

### 5. get_pricing_analysis

**Purpose:** Price distribution and optimization insights

---

## 👤 Host Domain TVFs

### 1. get_host_performance

**Purpose:** Host performance metrics

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_host_performance(
    start_date STRING COMMENT 'Start date in YYYY-MM-DD format',
    end_date STRING COMMENT 'End date in YYYY-MM-DD format',
    host_id_filter BIGINT DEFAULT NULL COMMENT 'Optional: Filter to specific host'
)
RETURNS TABLE (
    host_id BIGINT,
    host_name STRING,
    country STRING,
    is_verified BOOLEAN,
    rating FLOAT,
    property_count BIGINT,
    total_bookings BIGINT,
    total_revenue DECIMAL(18,2),
    avg_booking_value DECIMAL(18,2),
    cancellation_rate DECIMAL(5,2)
)
COMMENT 'LLM: Returns host performance metrics.
Use for: Host quality analysis, partner management, commission calculations.
Example questions: "Who are top performing hosts?" "Show host KPIs"';
```

### 2. get_host_quality_metrics

**Purpose:** Host rating and verification analysis

### 3. get_host_retention_analysis

**Purpose:** Active vs churned hosts

### 4. get_host_geographic_distribution

**Purpose:** Host distribution by country

---

## 🎯 Customer Domain TVFs

### 1. get_customer_segments

**Purpose:** Customer segmentation analysis

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_customer_segments(
    start_date STRING COMMENT 'Start date for segment calculation',
    end_date STRING COMMENT 'End date for segment calculation'
)
RETURNS TABLE (
    segment_name STRING,
    customer_count BIGINT,
    total_bookings BIGINT,
    total_revenue DECIMAL(18,2),
    avg_booking_value DECIMAL(18,2),
    avg_bookings_per_customer DECIMAL(10,2),
    segment_revenue_share DECIMAL(5,2)
)
COMMENT 'LLM: Returns customer segment analysis based on booking behavior.
Use for: Customer segmentation, marketing targeting, loyalty programs.
Example questions: "What are our customer segments?" "Show segment performance"';
```

### 2. get_customer_ltv

**Purpose:** Customer lifetime value calculation

### 3. get_booking_frequency_analysis

**Purpose:** Booking frequency distribution

### 4. get_customer_geographic_analysis

**Purpose:** Customer distribution by country

### 5. get_business_vs_leisure_analysis

**Purpose:** Business vs leisure booking patterns

---

## TVF Design Standards

### Parameter Requirements

```sql
-- ✅ CORRECT: STRING dates for Genie compatibility
start_date STRING COMMENT 'Start date in YYYY-MM-DD format'

-- ❌ WRONG: DATE type breaks Genie
start_date DATE
```

### Comment Structure

```sql
COMMENT 'LLM: [One-line description].
Use for: [Use cases separated by commas].
Example questions: "[Question 1]" "[Question 2]"'
```

### Return Table Structure

```sql
RETURNS TABLE (
    -- 1. Dimension keys first
    property_id BIGINT,
    -- 2. Dimension attributes second  
    property_title STRING,
    -- 3. Measures last
    total_revenue DECIMAL(18,2)
)
```

### SQL Patterns

```sql
-- Use CAST for date parameters
WHERE check_in_date BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)

-- Use COALESCE for optional filters
WHERE (destination_filter IS NULL OR destination = destination_filter)

-- Use LIMIT with parameters
ORDER BY total_revenue DESC
LIMIT COALESCE(top_n, 10)
```

---

## Implementation Checklist

### Revenue TVFs
- [x] get_revenue_by_period
- [x] get_top_properties_by_revenue
- [x] get_revenue_by_destination
- [x] get_payment_metrics
- [x] get_cancellation_analysis
- [x] get_revenue_forecast_inputs

### Engagement TVFs
- [x] get_property_engagement
- [x] get_conversion_funnel
- [x] get_traffic_source_analysis
- [x] get_top_engaging_properties
- [x] get_engagement_trends

### Property TVFs
- [x] get_property_performance
- [x] get_availability_by_destination
- [x] get_property_type_analysis
- [x] get_amenity_impact
- [x] get_pricing_analysis

### Host TVFs
- [x] get_host_performance
- [x] get_host_quality_metrics
- [x] get_host_retention_analysis
- [x] get_host_geographic_distribution
- [x] get_multi_property_hosts

### Customer TVFs
- [x] get_customer_segments
- [x] get_customer_ltv
- [x] get_booking_frequency_analysis
- [x] get_customer_geographic_analysis
- [x] get_business_vs_leisure_analysis

---

## Deployment

### SQL File Structure

```
src/wanderbricks_gold/semantic/
├── tvfs/
│   ├── revenue_tvfs.sql
│   ├── engagement_tvfs.sql
│   ├── property_tvfs.sql
│   ├── host_tvfs.sql
│   └── customer_tvfs.sql
└── create_all_tvfs.sql
```

### Asset Bundle Job

```yaml
resources:
  jobs:
    create_tvfs_job:
      name: "[${bundle.target}] Create TVFs"
      tasks:
        - task_key: create_all_tvfs
          sql_task:
            warehouse_id: ${var.warehouse_id}
            file:
              path: ../src/wanderbricks_gold/semantic/create_all_tvfs.sql
            parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
```

---

## Testing & Validation

### Test Queries

```sql
-- Test revenue TVF
SELECT * FROM ${catalog}.${gold_schema}.get_revenue_by_period(
    '2024-01-01', '2024-12-31', 'month'
);

-- Test with optional filter
SELECT * FROM ${catalog}.${gold_schema}.get_property_performance(
    '2024-01-01', '2024-12-31', 'Paris'
);
```

### Validation Criteria

| Criteria | Target |
|----------|--------|
| All TVFs created without errors | 25/25 |
| Genie can invoke TVFs | Yes |
| Response time < 30 seconds | All |
| Results match direct SQL | 100% |

---

## References

- [TVF Patterns Rule](../.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc)
- [TVFs Prompt](../context/prompts/09-table-valued-functions-prompt.md)
- [Databricks TVF Documentation](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-ddl-create-sql-function.html)
- [Genie Trusted Assets](https://docs.databricks.com/genie/trusted-assets.html)

