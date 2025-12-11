# Phase 4 Addendum 4.5: AI/BI Dashboards

## Overview

**Status:** 📋 Planned  
**Dependencies:** Phase 3 (Gold Layer), 4.2 (TVFs), 4.3 (Metric Views)  
**Artifact Count:** 5 Lakeview Dashboards  
**Reference:** [AI/BI Dashboard Patterns](../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)

---

## Purpose

AI/BI Dashboards (Lakeview) provide:
1. **Executive visibility** - Visual KPI tracking
2. **Self-service analytics** - Drag-and-drop exploration
3. **AI-powered insights** - Natural language dashboard interaction
4. **Scheduled distribution** - Automated report delivery

---

## Dashboard Summary

| # | Dashboard | Domain | Key Metrics | Audience |
|---|-----------|--------|-------------|----------|
| 1 | Revenue Performance | 💰 Revenue | Revenue, Bookings, Trends | Finance, Leadership |
| 2 | Engagement & Conversion | 📊 Engagement | Views, Clicks, Conversion | Marketing |
| 3 | Property Portfolio | 🏠 Property | Inventory, Pricing, Performance | Operations |
| 4 | Host Performance | 👤 Host | Ratings, Quality, Revenue | Partner Management |
| 5 | Customer Analytics | 🎯 Customer | Segments, CLV, Behavior | Growth, Product |

---

## 💰 Revenue Performance Dashboard

### Purpose
Track revenue KPIs, booking trends, and financial performance for executive reporting.

### Pages

| Page | Visualizations |
|------|----------------|
| Executive Summary | KPI Cards, Revenue Trend, Booking Funnel |
| Revenue Deep Dive | Revenue by Destination, Time Series, YoY Comparison |
| Booking Analysis | Booking Volume, Avg Value, Lead Time Distribution |
| Cancellation Analysis | Cancellation Rate, Revenue Impact, Trends |

### Key Visualizations

#### 1. Executive KPI Cards

| KPI | Metric | Comparison |
|-----|--------|------------|
| Total Revenue | SUM(total_booking_value) | vs Previous Period |
| Booking Count | SUM(booking_count) | vs Previous Period |
| Avg Booking Value | AVG(avg_booking_value) | vs Previous Period |
| Cancellation Rate | cancellations/bookings | vs Target |

#### 2. Revenue Trend (Line Chart)

```sql
SELECT 
    DATE_TRUNC('month', check_in_date) as month,
    SUM(total_booking_value) as revenue,
    SUM(booking_count) as bookings
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date >= DATE_ADD(CURRENT_DATE(), -365)
GROUP BY 1
ORDER BY 1
```

#### 3. Revenue by Destination (Bar Chart)

```sql
SELECT 
    d.destination,
    d.country,
    SUM(f.total_booking_value) as revenue,
    SUM(f.booking_count) as bookings
FROM ${catalog}.${gold_schema}.fact_booking_daily f
JOIN ${catalog}.${gold_schema}.dim_destination d 
    ON f.destination_id = d.destination_id
WHERE f.check_in_date >= DATE_ADD(CURRENT_DATE(), -90)
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 15
```

### Filters

| Filter | Type | Default |
|--------|------|---------|
| Date Range | Date Picker | Last 90 Days |
| Destination | Multi-Select | All |
| Property Type | Multi-Select | All |

---

## 📊 Engagement & Conversion Dashboard

### Purpose
Track marketing funnel performance, engagement metrics, and conversion optimization.

### Pages

| Page | Visualizations |
|------|----------------|
| Funnel Overview | View → Click → Book Funnel, Conversion Rates |
| Channel Analysis | Performance by Traffic Source, Device Breakdown |
| Property Engagement | Top Engaged Properties, Engagement Trends |
| Optimization Insights | Low Conversion Properties, Improvement Areas |

### Key Visualizations

#### 1. Conversion Funnel (Funnel Chart)

```sql
SELECT 
    'Views' as stage,
    1 as stage_order,
    SUM(view_count) as count
FROM ${catalog}.${gold_schema}.fact_property_engagement
WHERE engagement_date >= DATE_ADD(CURRENT_DATE(), -30)

UNION ALL

SELECT 
    'Clicks' as stage,
    2 as stage_order,
    SUM(click_count) as count
FROM ${catalog}.${gold_schema}.fact_property_engagement
WHERE engagement_date >= DATE_ADD(CURRENT_DATE(), -30)

UNION ALL

SELECT 
    'Bookings' as stage,
    3 as stage_order,
    SUM(booking_count) as count
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date >= DATE_ADD(CURRENT_DATE(), -30)

ORDER BY stage_order
```

#### 2. Conversion by Property Type (Bar Chart)

```sql
SELECT 
    p.property_type,
    SUM(e.view_count) as views,
    SUM(b.booking_count) as bookings,
    (SUM(b.booking_count) / NULLIF(SUM(e.view_count), 0)) * 100 as conversion_rate
FROM ${catalog}.${gold_schema}.fact_property_engagement e
JOIN ${catalog}.${gold_schema}.dim_property p 
    ON e.property_id = p.property_id AND p.is_current = true
LEFT JOIN ${catalog}.${gold_schema}.fact_booking_daily b
    ON e.property_id = b.property_id AND e.engagement_date = b.check_in_date
GROUP BY 1
ORDER BY 4 DESC
```

---

## 🏠 Property Portfolio Dashboard

### Purpose
Manage property inventory, analyze pricing strategy, and track listing performance.

### Pages

| Page | Visualizations |
|------|----------------|
| Portfolio Overview | Property Count, Capacity, Geographic Distribution |
| Pricing Analysis | Price Distribution, Price vs Performance |
| Performance Ranking | Top/Bottom Properties, Occupancy Rates |
| Inventory Insights | Property Types, Amenity Analysis |

### Key Visualizations

#### 1. Geographic Distribution (Map)

```sql
SELECT 
    d.destination,
    d.country,
    COUNT(DISTINCT p.property_id) as property_count,
    AVG(p.base_price) as avg_price,
    SUM(f.booking_count) as bookings
FROM ${catalog}.${gold_schema}.dim_property p
JOIN ${catalog}.${gold_schema}.dim_destination d 
    ON p.destination_id = d.destination_id
LEFT JOIN ${catalog}.${gold_schema}.fact_booking_daily f
    ON p.property_id = f.property_id
WHERE p.is_current = true
GROUP BY 1, 2
```

#### 2. Price vs Performance Scatter Plot

```sql
SELECT 
    p.property_id,
    p.title,
    p.base_price,
    p.property_type,
    SUM(f.total_booking_value) as total_revenue,
    SUM(f.booking_count) as booking_count
FROM ${catalog}.${gold_schema}.dim_property p
LEFT JOIN ${catalog}.${gold_schema}.fact_booking_daily f
    ON p.property_id = f.property_id
WHERE p.is_current = true
  AND f.check_in_date >= DATE_ADD(CURRENT_DATE(), -90)
GROUP BY 1, 2, 3, 4
```

---

## 👤 Host Performance Dashboard

### Purpose
Track host quality metrics, identify top performers, and support partner management.

### Pages

| Page | Visualizations |
|------|----------------|
| Host Overview | Total Hosts, Verified %, Rating Distribution |
| Performance Ranking | Top Hosts by Revenue, Top Hosts by Rating |
| Quality Analysis | Verification Impact, Rating Trends |
| Geographic Distribution | Hosts by Country, Market Coverage |

### Key Visualizations

#### 1. Host Rating Distribution (Histogram)

```sql
SELECT 
    FLOOR(rating * 2) / 2 as rating_bucket,  -- 0.5 increments
    COUNT(*) as host_count
FROM ${catalog}.${gold_schema}.dim_host
WHERE is_current = true
  AND is_active = true
GROUP BY 1
ORDER BY 1
```

#### 2. Verification Impact (Comparison Chart)

```sql
SELECT 
    CASE WHEN h.is_verified THEN 'Verified' ELSE 'Not Verified' END as status,
    COUNT(DISTINCT h.host_id) as host_count,
    AVG(h.rating) as avg_rating,
    SUM(f.total_booking_value) / COUNT(DISTINCT h.host_id) as revenue_per_host
FROM ${catalog}.${gold_schema}.dim_host h
LEFT JOIN ${catalog}.${gold_schema}.dim_property p 
    ON h.host_id = p.host_id AND p.is_current = true
LEFT JOIN ${catalog}.${gold_schema}.fact_booking_daily f
    ON p.property_id = f.property_id
WHERE h.is_current = true
GROUP BY 1
```

---

## 🎯 Customer Analytics Dashboard

### Purpose
Understand customer segments, track behavior patterns, and optimize customer experience.

### Pages

| Page | Visualizations |
|------|----------------|
| Customer Overview | Total Customers, New vs Returning, Geographic |
| Segment Analysis | Customer Segments, Segment Performance |
| Behavior Patterns | Booking Frequency, Lead Time, Preferences |
| Business vs Leisure | Comparison Analysis, Trends |

### Key Visualizations

#### 1. Customer Segments (Pie Chart)

```sql
SELECT 
    CASE 
        WHEN booking_count >= 5 THEN 'VIP (5+ bookings)'
        WHEN booking_count >= 3 THEN 'Loyal (3-4 bookings)'
        WHEN booking_count >= 2 THEN 'Returning (2 bookings)'
        ELSE 'New (1 booking)'
    END as segment,
    COUNT(DISTINCT user_id) as customer_count,
    SUM(total_spend) as total_revenue
FROM (
    SELECT 
        f.user_id,
        COUNT(*) as booking_count,
        SUM(f.total_amount) as total_spend
    FROM ${catalog}.${gold_schema}.fact_booking_detail f
    GROUP BY 1
) customer_summary
GROUP BY 1
ORDER BY 2 DESC
```

#### 2. Business vs Leisure (Comparison)

```sql
SELECT 
    CASE WHEN u.is_business THEN 'Business' ELSE 'Leisure' END as segment,
    COUNT(DISTINCT f.booking_id) as bookings,
    SUM(f.total_amount) as revenue,
    AVG(f.total_amount) as avg_booking_value,
    AVG(f.nights_booked) as avg_stay_length
FROM ${catalog}.${gold_schema}.fact_booking_detail f
JOIN ${catalog}.${gold_schema}.dim_user u 
    ON f.user_id = u.user_id AND u.is_current = true
GROUP BY 1
```

---

## Dashboard Design Standards

### Layout Grid

```
┌─────────────────────────────────────────┐
│           Dashboard Title               │
├──────────┬──────────┬──────────┬────────┤
│   KPI    │   KPI    │   KPI    │  KPI   │
├──────────┴──────────┴──────────┴────────┤
│         Primary Visualization           │
├────────────────────┬────────────────────┤
│  Secondary Viz 1   │  Secondary Viz 2   │
├────────────────────┴────────────────────┤
│              Detail Table               │
└─────────────────────────────────────────┘
```

### Color Palette

| Purpose | Color | Usage |
|---------|-------|-------|
| Primary | #1E88E5 | Main metrics, positive trends |
| Secondary | #43A047 | Secondary metrics, comparisons |
| Warning | #FFC107 | Threshold warnings |
| Alert | #E53935 | Negative trends, alerts |
| Neutral | #757575 | Supporting text, axes |

### KPI Card Format

| Element | Specification |
|---------|--------------|
| Title | 14px, Bold, Gray |
| Value | 32px, Bold, Primary |
| Comparison | 14px, Green/Red with arrow |
| Sparkline | Optional, 50px height |

---

## Implementation Checklist

- [ ] Revenue Performance Dashboard
  - [ ] Executive Summary page
  - [ ] Revenue Deep Dive page
  - [ ] Booking Analysis page
  - [ ] Cancellation Analysis page

- [ ] Engagement & Conversion Dashboard
  - [ ] Funnel Overview page
  - [ ] Channel Analysis page
  - [ ] Property Engagement page
  - [ ] Optimization Insights page

- [ ] Property Portfolio Dashboard
  - [ ] Portfolio Overview page
  - [ ] Pricing Analysis page
  - [ ] Performance Ranking page
  - [ ] Inventory Insights page

- [ ] Host Performance Dashboard
  - [ ] Host Overview page
  - [ ] Performance Ranking page
  - [ ] Quality Analysis page
  - [ ] Geographic Distribution page

- [ ] Customer Analytics Dashboard
  - [ ] Customer Overview page
  - [ ] Segment Analysis page
  - [ ] Behavior Patterns page
  - [ ] Business vs Leisure page

---

## Scheduled Distribution

### Report Schedule

| Dashboard | Frequency | Recipients | Format |
|-----------|-----------|------------|--------|
| Revenue Performance | Daily | Leadership | PDF |
| Engagement | Weekly | Marketing | PDF |
| Property Portfolio | Weekly | Operations | PDF |
| Host Performance | Monthly | Partner Mgmt | PDF |
| Customer Analytics | Weekly | Growth | PDF |

---

## References

- [Lakeview Dashboards](https://docs.databricks.com/dashboards/lakeview.html)
- [AI/BI Dashboard Patterns](../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)
- [Dashboard Prompt](../context/prompts/10-aibi-dashboards-prompt.md)

