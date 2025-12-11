# Phase 4 Addendum 4.3: Metric Views

## Overview

**Status:** ✅ Implemented  
**Implementation Date:** December 10, 2025  
**Dependencies:** Phase 3 (Gold Layer)  
**Artifact Count:** 5 Metric Views  
**Reference:** [Metric Views Patterns](../.cursor/rules/semantic-layer/14-metric-views-patterns.mdc)  
**Deployment Guide:** [Metric Views Deployment Guide](../docs/deployment/metric-views-deployment-guide.md)

---

## Purpose

Metric Views provide a semantic layer for:
1. **Self-service analytics** - Business users query without SQL
2. **AI/BI Dashboard integration** - Pre-defined dimensions and measures
3. **Genie natural language** - LLM-optimized metadata with synonyms
4. **Consistent metrics** - Single source of truth for KPI definitions

---

## Metric View Summary

| # | Metric View | Domain | Source Table | Dimensions | Measures |
|---|-------------|--------|--------------|------------|----------|
| 1 | revenue_analytics_metrics | 💰 Revenue | fact_booking_daily | 8 | 10 |
| 2 | engagement_analytics_metrics | 📊 Engagement | fact_property_engagement | 6 | 8 |
| 3 | property_analytics_metrics | 🏠 Property | dim_property + fact | 10 | 8 |
| 4 | host_analytics_metrics | 👤 Host | dim_host + fact | 8 | 8 |
| 5 | customer_analytics_metrics | 🎯 Customer | dim_user + fact | 7 | 8 |

---

## 💰 revenue_analytics_metrics

### YAML Definition

```yaml
version: "1.1"

- name: revenue_analytics_metrics
  comment: >
    Comprehensive revenue and booking analytics for vacation rental platform.
    Optimized for Genie natural language queries and AI/BI dashboards.
    Answers questions about revenue trends, booking volumes, and performance.
  
  source: ${catalog}.${gold_schema}.fact_booking_daily
  
  joins:
    - name: dim_property
      source: ${catalog}.${gold_schema}.dim_property
      'on': source.property_id = dim_property.property_id AND dim_property.is_current = true
    
    - name: dim_destination
      source: ${catalog}.${gold_schema}.dim_destination
      'on': source.destination_id = dim_destination.destination_id
    
    - name: dim_date
      source: ${catalog}.${gold_schema}.dim_date
      'on': source.check_in_date = dim_date.date
  
  dimensions:
    - name: check_in_date
      expr: source.check_in_date
      comment: Check-in date for the booking
      display_name: Check-in Date
      synonyms: [date, booking date, arrival date]
    
    - name: property_id
      expr: source.property_id
      comment: Property identifier
      display_name: Property ID
      synonyms: [property, listing]
    
    - name: property_title
      expr: dim_property.title
      comment: Property listing title
      display_name: Property Title
      synonyms: [property name, listing name]
    
    - name: property_type
      expr: dim_property.property_type
      comment: Type of property (house, apartment, etc.)
      display_name: Property Type
      synonyms: [type, listing type]
    
    - name: destination
      expr: dim_destination.destination
      comment: Destination city or location
      display_name: Destination
      synonyms: [city, location, market]
    
    - name: country
      expr: dim_destination.country
      comment: Country of the destination
      display_name: Country
      synonyms: [nation]
    
    - name: month_name
      expr: dim_date.month_name
      comment: Month name for time-based analysis
      display_name: Month
      synonyms: [month]
    
    - name: year
      expr: dim_date.year
      comment: Calendar year
      display_name: Year
      synonyms: [calendar year]
  
  measures:
    - name: total_revenue
      expr: SUM(source.total_booking_value)
      comment: Total booking revenue. Primary revenue KPI for business reporting.
      display_name: Total Revenue
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
        abbreviation: compact
      synonyms: [revenue, sales, income, booking value]
    
    - name: booking_count
      expr: SUM(source.booking_count)
      comment: Total number of bookings. Volume metric for demand analysis.
      display_name: Booking Count
      format:
        type: number
        abbreviation: compact
      synonyms: [bookings, reservations, orders]
    
    - name: avg_booking_value
      expr: AVG(source.avg_booking_value)
      comment: Average booking value. Pricing effectiveness indicator.
      display_name: Avg Booking Value
      format:
        type: currency
        currency_code: USD
        decimal_places:
          type: exact
          places: 2
      synonyms: [average booking, ticket size]
    
    - name: total_guests
      expr: SUM(source.total_guests)
      comment: Total guest count. Occupancy planning metric.
      display_name: Total Guests
      format:
        type: number
        abbreviation: compact
      synonyms: [guests, visitors, travelers]
    
    - name: avg_nights
      expr: AVG(source.avg_nights_booked)
      comment: Average length of stay in nights.
      display_name: Avg Nights
      format:
        type: number
        decimal_places:
          type: exact
          places: 1
      synonyms: [average stay, length of stay]
    
    - name: cancellation_count
      expr: SUM(source.cancellation_count)
      comment: Number of cancelled bookings.
      display_name: Cancellations
      format:
        type: number
      synonyms: [cancelled, cancelled bookings]
    
    - name: confirmed_count
      expr: SUM(source.confirmed_booking_count)
      comment: Number of confirmed bookings.
      display_name: Confirmed Bookings
      format:
        type: number
      synonyms: [confirmed, confirmed reservations]
    
    - name: cancellation_rate
      expr: SUM(source.cancellation_count) / NULLIF(SUM(source.booking_count), 0) * 100
      comment: Percentage of bookings cancelled.
      display_name: Cancellation Rate
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms: [cancel rate, cancellation percentage]
    
    - name: payment_rate
      expr: AVG(source.payment_completion_rate)
      comment: Average payment completion rate.
      display_name: Payment Rate
      format:
        type: percentage
        decimal_places:
          type: exact
          places: 1
      synonyms: [payment completion, payment success]
    
    - name: property_count
      expr: COUNT(DISTINCT source.property_id)
      comment: Number of unique properties with bookings.
      display_name: Property Count
      format:
        type: number
      synonyms: [properties, listings]
```

---

## 📊 engagement_analytics_metrics

### Key Dimensions

| Dimension | Source | Synonyms |
|-----------|--------|----------|
| engagement_date | source.engagement_date | date, activity date |
| property_id | source.property_id | property, listing |
| property_title | dim_property.title | property name |
| destination | dim_destination.destination | city, location |

### Key Measures

| Measure | Expression | Format | Synonyms |
|---------|------------|--------|----------|
| total_views | SUM(view_count) | number | views, impressions |
| unique_viewers | SUM(unique_user_views) | number | unique views, visitors |
| total_clicks | SUM(click_count) | number | clicks, interactions |
| conversion_rate | bookings/views*100 | percentage | conversion, convert rate |
| avg_time_on_page | AVG(avg_time_on_page) | number | time spent, engagement time |

---

## 🏠 property_analytics_metrics

### Key Dimensions

| Dimension | Source | Synonyms |
|-----------|--------|----------|
| property_id | source.property_id | property, listing |
| property_type | source.property_type | type, category |
| base_price | source.base_price | price, nightly rate |
| bedrooms | source.bedrooms | beds, rooms |
| max_guests | source.max_guests | capacity, guests allowed |
| destination | dim_destination.destination | city, location |
| host_name | dim_host.name | host, owner |

### Key Measures

| Measure | Expression | Format | Synonyms |
|---------|------------|--------|----------|
| property_count | COUNT(DISTINCT property_id) | number | properties, listings |
| avg_price | AVG(base_price) | currency | average price |
| total_capacity | SUM(max_guests) | number | capacity |
| avg_bedrooms | AVG(bedrooms) | number | average bedrooms |
| revenue | SUM(total_revenue) | currency | earnings |
| booking_count | SUM(booking_count) | number | bookings |

---

## 👤 host_analytics_metrics

### Key Dimensions

| Dimension | Source | Synonyms |
|-----------|--------|----------|
| host_id | source.host_id | host |
| host_name | source.name | host name, owner |
| is_verified | source.is_verified | verified, verification |
| rating | source.rating | host rating |
| country | source.country | host country, location |
| is_active | source.is_active | active, status |

### Key Measures

| Measure | Expression | Format | Synonyms |
|---------|------------|--------|----------|
| host_count | COUNT(DISTINCT host_id) | number | hosts, owners |
| verified_count | COUNT(CASE WHEN is_verified) | number | verified hosts |
| avg_rating | AVG(rating) | number | average rating |
| property_count | COUNT(DISTINCT property_id) | number | properties per host |
| total_revenue | SUM(revenue) | currency | host revenue, earnings |
| booking_count | SUM(bookings) | number | host bookings |

---

## 🎯 customer_analytics_metrics

### Key Dimensions

| Dimension | Source | Synonyms |
|-----------|--------|----------|
| user_id | source.user_id | customer, guest |
| country | source.country | customer country |
| user_type | source.user_type | type, account type |
| is_business | source.is_business | business, corporate |
| created_at | source.created_at | signup date, join date |

### Key Measures

| Measure | Expression | Format | Synonyms |
|---------|------------|--------|----------|
| customer_count | COUNT(DISTINCT user_id) | number | customers, users, guests |
| business_count | COUNT(CASE WHEN is_business) | number | business customers |
| booking_count | SUM(booking_count) | number | customer bookings |
| total_spend | SUM(total_amount) | currency | customer spend, revenue |
| avg_booking_value | AVG(booking_value) | currency | average spend |
| booking_frequency | bookings/customers | number | frequency |

---

## Implementation

### Python Script Structure

```python
# src/wanderbricks_gold/semantic/create_metric_views.py

import yaml
from pathlib import Path

def create_metric_view(spark, catalog, schema, metric_view):
    """Create a single metric view from YAML definition."""
    view_name = metric_view['name']
    fqn = f"{catalog}.{schema}.{view_name}"
    
    # Drop existing view/table to avoid conflicts
    try:
        spark.sql(f"DROP VIEW IF EXISTS {fqn}")
        spark.sql(f"DROP TABLE IF EXISTS {fqn}")
    except:
        pass
    
    # Convert YAML to string
    yaml_str = yaml.dump(metric_view, default_flow_style=False)
    
    # Create metric view
    create_sql = f"""
    CREATE VIEW {fqn}
    WITH METRICS
    LANGUAGE YAML
    COMMENT '{metric_view.get('comment', '')}'
    AS $$
{yaml_str}
    $$
    """
    
    spark.sql(create_sql)
    print(f"✓ Created metric view: {view_name}")
```

### YAML File Location

```
src/wanderbricks_gold/semantic/metric_views/
├── revenue_analytics_metrics.yaml
├── engagement_analytics_metrics.yaml
├── property_analytics_metrics.yaml
├── host_analytics_metrics.yaml
└── customer_analytics_metrics.yaml
```

---

## Implementation Status

### ✅ Artifacts Created

| Artifact | Location | Status |
|----------|----------|--------|
| Revenue Analytics YAML | `src/wanderbricks_gold/semantic/metric_views/revenue_analytics_metrics.yaml` | ✅ Complete |
| Engagement Analytics YAML | `src/wanderbricks_gold/semantic/metric_views/engagement_analytics_metrics.yaml` | ✅ Complete |
| Property Analytics YAML | `src/wanderbricks_gold/semantic/metric_views/property_analytics_metrics.yaml` | ✅ Complete |
| Host Analytics YAML | `src/wanderbricks_gold/semantic/metric_views/host_analytics_metrics.yaml` | ✅ Complete |
| Customer Analytics YAML | `src/wanderbricks_gold/semantic/metric_views/customer_analytics_metrics.yaml` | ✅ Complete |
| Python Deployment Script | `src/wanderbricks_gold/semantic/create_metric_views.py` | ✅ Complete |
| Asset Bundle Job | `resources/gold/metric_views_job.yml` | ✅ Complete |
| Deployment Guide | `docs/deployment/metric-views-deployment-guide.md` | ✅ Complete |

### Implementation Checklist

- [x] revenue_analytics_metrics (💰 Revenue)
- [x] engagement_analytics_metrics (📊 Engagement)
- [x] property_analytics_metrics (🏠 Property)
- [x] host_analytics_metrics (👤 Host)
- [x] customer_analytics_metrics (🎯 Customer)
- [x] Python deployment script with v1.1 syntax
- [x] Asset Bundle job configuration
- [x] YAML file sync in databricks.yml
- [x] Comprehensive error handling
- [x] Deployment guide and documentation

---

## Validation

### Verify Metric View Type

```sql
DESCRIBE EXTENDED ${catalog}.${gold_schema}.revenue_analytics_metrics;
-- Expect: Type = METRIC_VIEW
```

### Test Queries

```sql
-- Basic aggregation
SELECT 
    destination,
    MEASURE(total_revenue) as revenue,
    MEASURE(booking_count) as bookings
FROM ${catalog}.${gold_schema}.revenue_analytics_metrics
GROUP BY destination
ORDER BY revenue DESC;

-- Time-based analysis
SELECT 
    month_name,
    year,
    MEASURE(total_revenue) as revenue
FROM ${catalog}.${gold_schema}.revenue_analytics_metrics
WHERE year = 2024
GROUP BY month_name, year
ORDER BY revenue DESC;
```

---

## References

- [Metric Views YAML Reference](https://docs.databricks.com/metric-views/yaml-ref)
- [Metric Views Semantic Metadata](https://docs.databricks.com/metric-views/semantic-metadata)
- [Metric Views Patterns Rule](../.cursor/rules/semantic-layer/14-metric-views-patterns.mdc)

