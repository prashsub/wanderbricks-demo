# Wanderbricks Metric Views

**Phase:** 4.3 - Semantic Layer  
**Status:** ✅ Implemented  
**Purpose:** Enable natural language queries via Genie AI and power AI/BI dashboards

---

## Overview

This directory contains 5 metric view YAML definitions that provide a semantic layer for the Wanderbricks vacation rental platform. Each metric view follows the Databricks Metric View Specification v1.1 with comprehensive dimensions, measures, synonyms, and formatting.

---

## Metric Views

### 💰 revenue_analytics_metrics.yaml

**Source:** `fact_booking_daily`  
**Purpose:** Revenue trends, booking volumes, cancellation analysis

**Key Metrics:**
- Total Revenue, Booking Count, Avg Booking Value
- Total Guests, Avg Nights
- Cancellation Count/Rate, Confirmed Bookings
- Payment Completion Rate
- Property Count

**Use Cases:**
- "What was total revenue last month?"
- "Show me top destinations by booking count"
- "What's the cancellation rate in Paris?"

---

### 📊 engagement_analytics_metrics.yaml

**Source:** `fact_property_engagement`  
**Purpose:** View counts, click metrics, conversion rates, engagement time

**Key Metrics:**
- Total Views, Unique Viewers
- Total Clicks, Search Appearances
- Conversion Rate, Click-Through Rate
- Avg Time on Page

**Use Cases:**
- "Which properties have the highest conversion rate?"
- "Show me engagement trends over time"
- "What's the click-through rate by property type?"

---

### 🏠 property_analytics_metrics.yaml

**Source:** `dim_property`  
**Purpose:** Property inventory, pricing, capacity, portfolio analysis

**Key Metrics:**
- Property Count, Avg Base Price
- Total Capacity, Avg Bedrooms
- Total Revenue, Booking Count
- Revenue per Property, Bookings per Property

**Use Cases:**
- "How many properties do we have in each destination?"
- "What's the average price by property type?"
- "Show me property portfolio performance"

---

### 👤 host_analytics_metrics.yaml

**Source:** `dim_host`  
**Purpose:** Host performance, verification, ratings, earnings

**Key Metrics:**
- Host Count, Verified Hosts
- Avg Host Rating
- Property Count, Total Revenue
- Revenue per Host, Verification Rate

**Use Cases:**
- "Who are our top performing hosts?"
- "What's the average host rating?"
- "Show me verified vs unverified host performance"

---

### 🎯 customer_analytics_metrics.yaml

**Source:** `dim_user`  
**Purpose:** Customer behavior, segmentation, lifetime value

**Key Metrics:**
- Customer Count, Business Customers
- Booking Count, Total Spend
- Avg Booking Value
- Bookings per Customer, Spend per Customer (LTV)
- Business Rate

**Use Cases:**
- "What's the customer lifetime value?"
- "Show me customer segmentation by booking frequency"
- "Compare business vs leisure customers"

---

## YAML Structure

All metric views follow this v1.1 specification:

```yaml
version: "1.1"

- name: {metric_view_name}
  comment: > 
    Comprehensive description optimized for Genie AI...
  
  source: ${catalog}.${gold_schema}.{fact_table}
  
  joins:
    - name: {dim_alias}
      source: ${catalog}.${gold_schema}.{dim_table}
      'on': source.{fk} = {dim_alias}.{pk} AND {dim_alias}.is_current = true
  
  dimensions:
    - name: {dimension_name}
      expr: source.{column}
      comment: {Business description}
      display_name: {User-Friendly Name}
      synonyms: [alt1, alt2, alt3]
  
  measures:
    - name: {measure_name}
      expr: SUM(source.{column})
      comment: {Business description and calculation}
      display_name: {User-Friendly Name}
      format:
        type: currency  # or number, percentage
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms: [alt1, alt2, alt3]
```

---

## Deployment

### Step 1: Deploy Asset Bundle

```bash
databricks bundle deploy -t dev
```

### Step 2: Run Metric Views Job

```bash
databricks bundle run metric_views_job -t dev
```

### Step 3: Verify

```sql
-- Check view type
DESCRIBE EXTENDED prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.revenue_analytics_metrics;

-- Test query
SELECT 
  destination,
  MEASURE(`Total Revenue`) as revenue
FROM prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_gold.revenue_analytics_metrics
GROUP BY destination
ORDER BY revenue DESC
LIMIT 10;
```

---

## Key Features

### 1. v1.1 Specification Compliance

✅ No unsupported fields (time_dimension, window_measures)  
✅ Correct join structure (name, source, 'on')  
✅ Proper column references (source., join_alias.)

### 2. Comprehensive Synonyms

Each dimension and measure has 3-5 synonyms for natural language recognition:

```yaml
synonyms:
  - revenue
  - sales
  - income
  - total sales
```

### 3. Professional Formatting

- **Currency:** USD with 2 decimal places, compact abbreviation (1.5M)
- **Numbers:** Compact with all decimals or exact places
- **Percentages:** 1-2 decimal places (45.3%)

### 4. LLM-Optimized Comments

```yaml
comment: >
  Total booking revenue aggregated across all bookings. Primary revenue KPI
  for business reporting, financial analysis, and executive dashboards.
  Represents total value of confirmed and completed bookings.
```

---

## Usage with Genie AI

After deployment, these metric views can be queried using natural language:

**Example Queries:**
- "What was total revenue last month?"
- "Show me top 10 properties by booking count"
- "What's the cancellation rate in Paris?"
- "Which hosts have the highest ratings?"
- "Customer lifetime value by segment"

Genie AI will:
1. Parse natural language query
2. Map to appropriate metric view
3. Use synonyms to identify dimensions/measures
4. Generate SQL with MEASURE() function
5. Execute and return results

---

## Usage with AI/BI Dashboards

Metric views provide semantic layer for Lakeview dashboards:

```sql
-- Revenue dashboard
SELECT 
  destination,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Booking Count`) as bookings
FROM revenue_analytics_metrics
WHERE year = 2024
GROUP BY destination
ORDER BY revenue DESC;

-- Engagement funnel
SELECT 
  property_type,
  MEASURE(`Total Views`) as views,
  MEASURE(`Total Clicks`) as clicks,
  MEASURE(`Conversion Rate`) as conversion_rate
FROM engagement_analytics_metrics
GROUP BY property_type;
```

---

## Modification Guidelines

### Adding a New Dimension

```yaml
dimensions:
  - name: new_dimension
    expr: source.new_column  # or join_alias.new_column
    comment: Business description for LLM understanding
    display_name: User-Friendly Name
    synonyms:
      - alternative1
      - alternative2
      - alternative3
```

### Adding a New Measure

```yaml
measures:
  - name: new_measure
    expr: SUM(source.new_column)  # or AVG, COUNT, etc.
    comment: Business description and calculation logic
    display_name: User-Friendly Name
    format:
      type: currency  # or number, percentage
      currency_code: USD
      decimal_places:
        type: exact
        places: 2
      abbreviation: compact
    synonyms:
      - alternative1
      - alternative2
```

### Adding a New Join

```yaml
joins:
  - name: new_dim_alias
    source: ${catalog}.${gold_schema}.new_dim_table
    'on': source.fk_column = new_dim_alias.pk_column AND new_dim_alias.is_current = true
```

---

## Troubleshooting

### View Created as VIEW instead of METRIC_VIEW

**Cause:** Not using WITH METRICS syntax in Python script

**Fix:** Verify `create_metric_views.py` uses:
```python
CREATE VIEW {name}
WITH METRICS
LANGUAGE YAML
AS $$
{yaml}
$$
```

### Unrecognized Field Error

**Cause:** Using unsupported v1.1 fields

**Fix:** Remove `time_dimension`, `window_measures`, `join_type`

### Missing Required Property Error

**Cause:** Join missing `name`, `source`, or `'on'` field

**Fix:** Ensure all three fields present and `'on'` is quoted

---

## References

### Documentation
- [Deployment Guide](../../../../docs/deployment/metric-views-deployment-guide.md)
- [Test Queries](../../../../docs/deployment/metric-views-test-queries.sql)
- [Implementation Summary](../../../../docs/deployment/metric-views-implementation-summary.md)

### Official Databricks Docs
- [Metric Views v1.1](https://docs.databricks.com/metric-views/yaml-ref)
- [Semantic Metadata](https://docs.databricks.com/metric-views/semantic-metadata)
- [Measure Formats](https://docs.databricks.com/metric-views/measure-formats)

### Framework Rules
- [Metric Views Patterns](.cursor/rules/semantic-layer/14-metric-views-patterns.mdc)

---

**Status:** ✅ Production Ready  
**Deployment:** Automated via Asset Bundles  
**Monitoring:** Phase 4.4 (Lakehouse Monitoring)  
**Integration:** Phase 4.5 (AI/BI Dashboards), Phase 4.6 (Genie Spaces)

