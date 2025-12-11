# Phase 4 Addendum 4.6: Genie Spaces

## Overview

**Status:** 📋 Planned  
**Dependencies:** Phase 3 (Gold Layer), 4.2 (TVFs)  
**Artifact Count:** 5 Genie Spaces  
**Reference:** [Genie Space Patterns](../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc)

---

## Purpose

Genie Spaces provide:
1. **Natural language analytics** - Ask questions in plain English
2. **Curated data access** - Pre-configured trusted assets
3. **Domain-specific intelligence** - Agent-like personas per domain
4. **Self-service discovery** - No SQL required

---

## Genie Space Summary

| # | Genie Space | Domain | Tables | TVFs | Sample Questions |
|---|-------------|--------|--------|------|------------------|
| 1 | Revenue Intelligence | 💰 Revenue | 2 | 6 | 10 |
| 2 | Marketing Intelligence | 📊 Engagement | 2 | 5 | 10 |
| 3 | Property Intelligence | 🏠 Property | 2 | 5 | 10 |
| 4 | Host Intelligence | 👤 Host | 2 | 4 | 10 |
| 5 | Customer Intelligence | 🎯 Customer | 2 | 5 | 10 |

---

## 💰 Revenue Intelligence

### Configuration

**Name:** Revenue Intelligence  
**Description:** Natural language interface for revenue and booking analytics

### Trusted Assets

#### Tables
- `${catalog}.${gold_schema}.fact_booking_daily`
- `${catalog}.${gold_schema}.fact_booking_detail`

#### TVFs
- `get_revenue_by_period(start_date, end_date, time_grain)`
- `get_top_properties_by_revenue(start_date, end_date, top_n)`
- `get_revenue_by_destination(start_date, end_date)`
- `get_payment_metrics(start_date, end_date)`
- `get_cancellation_analysis(start_date, end_date)`
- `get_revenue_forecast_inputs(start_date, end_date)`

### Agent Instructions

```
You are a Revenue Analytics Agent for Wanderbricks, a vacation rental platform.

Your expertise:
- Revenue trends and forecasting
- Booking volume analysis
- Pricing optimization insights
- Cancellation impact analysis
- Payment completion tracking

When answering questions:
1. Default to the last 90 days unless a specific date range is provided
2. Use the most specific TVF available for the question
3. Always include relevant context (comparisons, trends)
4. Format currency values appropriately ($X,XXX.XX)
5. When asked about "top" items, default to 10 unless specified

Key metrics you can provide:
- Total revenue by period (daily, weekly, monthly)
- Booking count and average booking value
- Cancellation rate and revenue impact
- Payment completion rate
- Revenue by destination/property/host
```

### Sample Questions

| # | Sample Question | TVF Used |
|---|-----------------|----------|
| 1 | What was total revenue last month? | get_revenue_by_period |
| 2 | Show me the top 10 revenue-generating properties | get_top_properties_by_revenue |
| 3 | Which destinations generate the most revenue? | get_revenue_by_destination |
| 4 | What is our cancellation rate? | get_cancellation_analysis |
| 5 | How are payment completions trending? | get_payment_metrics |
| 6 | Compare this month's revenue to last month | get_revenue_by_period |
| 7 | What is our average booking value? | get_revenue_by_period |
| 8 | Show weekly revenue trends for Q4 | get_revenue_by_period |
| 9 | Which properties had the most cancellations? | get_cancellation_analysis |
| 10 | What payment methods are most common? | get_payment_metrics |

---

## 📊 Marketing Intelligence

### Configuration

**Name:** Marketing Intelligence  
**Description:** Natural language interface for engagement and conversion analytics

### Trusted Assets

#### Tables
- `${catalog}.${gold_schema}.fact_property_engagement`
- `${catalog}.${gold_schema}.dim_property`

#### TVFs
- `get_property_engagement(start_date, end_date, property_id_filter)`
- `get_conversion_funnel(start_date, end_date)`
- `get_traffic_source_analysis(start_date, end_date)`
- `get_device_engagement(start_date, end_date)`
- `get_engagement_trends(start_date, end_date)`

### Agent Instructions

```
You are a Marketing Analytics Agent for Wanderbricks, a vacation rental platform.

Your expertise:
- Engagement funnel analysis (views → clicks → bookings)
- Conversion rate optimization
- Traffic source analysis
- Device and channel performance
- Content effectiveness

When answering questions:
1. Default to the last 30 days unless specified
2. Always express conversion rates as percentages
3. Compare against benchmarks when available
4. Identify low-performing properties proactively
5. Suggest optimization opportunities

Key metrics you can provide:
- View count and unique visitors
- Click-through rate (CTR)
- View-to-booking conversion rate
- Traffic source breakdown
- Device type engagement
```

### Sample Questions

| # | Sample Question | TVF Used |
|---|-----------------|----------|
| 1 | What is our conversion rate? | get_conversion_funnel |
| 2 | Which properties have the highest engagement? | get_property_engagement |
| 3 | Show the view-to-booking funnel | get_conversion_funnel |
| 4 | How is traffic distributed by source? | get_traffic_source_analysis |
| 5 | Compare mobile vs desktop conversion | get_device_engagement |
| 6 | What are the engagement trends this month? | get_engagement_trends |
| 7 | Which properties have low conversion? | get_property_engagement |
| 8 | How many views did we get last week? | get_engagement_trends |
| 9 | What is our click-through rate? | get_conversion_funnel |
| 10 | Which traffic sources convert best? | get_traffic_source_analysis |

---

## 🏠 Property Intelligence

### Configuration

**Name:** Property Intelligence  
**Description:** Natural language interface for property portfolio analytics

### Trusted Assets

#### Tables
- `${catalog}.${gold_schema}.dim_property`
- `${catalog}.${gold_schema}.fact_booking_daily`

#### TVFs
- `get_property_performance(start_date, end_date, destination_filter)`
- `get_availability_by_destination(start_date, end_date)`
- `get_property_type_analysis(start_date, end_date)`
- `get_amenity_impact(start_date, end_date)`
- `get_pricing_analysis(start_date, end_date)`

### Agent Instructions

```
You are a Property Analytics Agent for Wanderbricks, a vacation rental platform.

Your expertise:
- Property portfolio management
- Pricing strategy analysis
- Inventory and capacity planning
- Property type performance
- Amenity correlation analysis

When answering questions:
1. Default to current active listings unless specified
2. Include property type and destination context
3. Compare prices against market averages
4. Identify underperforming properties
5. Provide actionable pricing recommendations

Key metrics you can provide:
- Total properties by destination
- Property distribution by type
- Average and range of prices
- Occupancy rates
- Revenue per property
```

### Sample Questions

| # | Sample Question | TVF Used |
|---|-----------------|----------|
| 1 | How many properties do we have? | get_property_performance |
| 2 | What is the average price by destination? | get_pricing_analysis |
| 3 | Which property types perform best? | get_property_type_analysis |
| 4 | Show properties in Paris | get_property_performance |
| 5 | What is our inventory by city? | get_availability_by_destination |
| 6 | Which amenities correlate with bookings? | get_amenity_impact |
| 7 | What is the price range for apartments? | get_pricing_analysis |
| 8 | Compare house vs apartment performance | get_property_type_analysis |
| 9 | Which properties are underperforming? | get_property_performance |
| 10 | What is our total capacity? | get_availability_by_destination |

---

## 👤 Host Intelligence

### Configuration

**Name:** Host Intelligence  
**Description:** Natural language interface for host performance analytics

### Trusted Assets

#### Tables
- `${catalog}.${gold_schema}.dim_host`
- `${catalog}.${gold_schema}.fact_booking_detail`

#### TVFs
- `get_host_performance(start_date, end_date, host_id_filter)`
- `get_host_quality_metrics(start_date, end_date)`
- `get_host_retention_analysis(start_date, end_date)`
- `get_host_geographic_distribution()`

### Agent Instructions

```
You are a Host Analytics Agent for Wanderbricks, a vacation rental platform.

Your expertise:
- Host performance tracking
- Quality and rating analysis
- Host retention and churn
- Verification program impact
- Partner management insights

When answering questions:
1. Focus on active hosts by default
2. Highlight verification status impact
3. Compare against platform averages
4. Identify at-risk hosts
5. Recommend host success interventions

Key metrics you can provide:
- Host count and growth
- Average host rating
- Verification rate
- Revenue per host
- Properties per host
```

### Sample Questions

| # | Sample Question | TVF Used |
|---|-----------------|----------|
| 1 | Who are our top hosts? | get_host_performance |
| 2 | What is the average host rating? | get_host_quality_metrics |
| 3 | How many verified hosts do we have? | get_host_quality_metrics |
| 4 | Show host distribution by country | get_host_geographic_distribution |
| 5 | What is the impact of verification? | get_host_quality_metrics |
| 6 | Which hosts are at risk of churning? | get_host_retention_analysis |
| 7 | Compare verified vs non-verified hosts | get_host_quality_metrics |
| 8 | How many properties per host on average? | get_host_performance |
| 9 | What is host revenue distribution? | get_host_performance |
| 10 | Show inactive host trends | get_host_retention_analysis |

---

## 🎯 Customer Intelligence

### Configuration

**Name:** Customer Intelligence  
**Description:** Natural language interface for customer behavior analytics

### Trusted Assets

#### Tables
- `${catalog}.${gold_schema}.dim_user`
- `${catalog}.${gold_schema}.fact_booking_detail`

#### TVFs
- `get_customer_segments(start_date, end_date)`
- `get_customer_ltv(start_date, end_date)`
- `get_booking_frequency_analysis(start_date, end_date)`
- `get_customer_geographic_analysis()`
- `get_business_vs_leisure_analysis(start_date, end_date)`

### Agent Instructions

```
You are a Customer Analytics Agent for Wanderbricks, a vacation rental platform.

Your expertise:
- Customer segmentation
- Lifetime value analysis
- Booking behavior patterns
- Business vs leisure analysis
- Customer retention insights

When answering questions:
1. Segment customers by booking behavior
2. Calculate and explain CLV methodology
3. Compare business vs leisure patterns
4. Identify high-value customers
5. Recommend retention strategies

Key metrics you can provide:
- Customer count and growth
- Customer segments and distribution
- Average bookings per customer
- Customer lifetime value
- Business customer percentage
```

### Sample Questions

| # | Sample Question | TVF Used |
|---|-----------------|----------|
| 1 | What are our customer segments? | get_customer_segments |
| 2 | Who are our most valuable customers? | get_customer_ltv |
| 3 | How often do customers book? | get_booking_frequency_analysis |
| 4 | Where are our customers from? | get_customer_geographic_analysis |
| 5 | Compare business vs leisure customers | get_business_vs_leisure_analysis |
| 6 | What is the average customer LTV? | get_customer_ltv |
| 7 | How many repeat customers do we have? | get_booking_frequency_analysis |
| 8 | Which countries have the most customers? | get_customer_geographic_analysis |
| 9 | What percentage are business customers? | get_business_vs_leisure_analysis |
| 10 | Show customer segment performance | get_customer_segments |

---

## Implementation Checklist

- [ ] Revenue Intelligence Genie Space
  - [ ] Configure trusted assets (tables + TVFs)
  - [ ] Write agent instructions
  - [ ] Add sample questions
  - [ ] Test with 10+ queries

- [ ] Marketing Intelligence Genie Space
  - [ ] Configure trusted assets
  - [ ] Write agent instructions
  - [ ] Add sample questions
  - [ ] Test with 10+ queries

- [ ] Property Intelligence Genie Space
  - [ ] Configure trusted assets
  - [ ] Write agent instructions
  - [ ] Add sample questions
  - [ ] Test with 10+ queries

- [ ] Host Intelligence Genie Space
  - [ ] Configure trusted assets
  - [ ] Write agent instructions
  - [ ] Add sample questions
  - [ ] Test with 10+ queries

- [ ] Customer Intelligence Genie Space
  - [ ] Configure trusted assets
  - [ ] Write agent instructions
  - [ ] Add sample questions
  - [ ] Test with 10+ queries

---

## References

- [Genie Spaces Documentation](https://docs.databricks.com/genie/)
- [Trusted Assets](https://docs.databricks.com/genie/trusted-assets.html)
- [Genie Space Patterns Rule](../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc)

