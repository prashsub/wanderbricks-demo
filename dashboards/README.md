# Wanderbricks AI/BI Lakeview Dashboards

## Overview

This directory contains 6 production-ready Databricks Lakeview AI/BI dashboards for the Wanderbricks vacation rental analytics platform. Each dashboard provides executive visibility, self-service analytics, and AI-powered insights across key business domains.

---

## Dashboard Inventory

| # | Dashboard | Purpose | Key Metrics | Audience |
|---|-----------|---------|-------------|----------|
| 1 | **Revenue Performance** | Track revenue KPIs and booking trends | Revenue, Bookings, Avg Value, Cancellation Rate | Finance, Leadership |
| 2 | **Engagement & Conversion** | Monitor marketing funnel and property performance | Views, Clicks, Conversion Rate | Marketing |
| 3 | **Property Portfolio** | Manage inventory and pricing strategy | Property Count, Capacity, Price Distribution | Operations |
| 4 | **Host Performance** | Track host quality and partner management | Host Count, Ratings, Verification Status | Partner Management |
| 5 | **Customer Analytics** | Understand customer segments and behavior | Customer Count, Segments, CLV | Growth, Product |
| 6 | **Lakehouse Monitoring** | Monitor data quality and custom business metrics | 20 Custom Metrics, Drift Alerts, Quality KPIs | Data Engineering, Leadership |

---

## 📊 Dashboard 1: Revenue Performance

**File:** `wanderbricks_revenue_performance_dashboard.lvdash.json`

### Pages
1. **Executive Summary** - KPI cards, revenue trend, destination breakdown
2. **Revenue Deep Dive** - Property type revenue, lead time analysis, booking details
3. **Cancellation Analysis** - Cancellation rates and trends

### Key Datasets
- `executive_kpis` - Total revenue, bookings, avg value, cancellation rate
- `revenue_trend_monthly` - Monthly revenue and booking trends
- `revenue_by_destination` - Geographic revenue breakdown
- `booking_detail_table` - Transaction-level booking data

### KPIs
- Total Revenue (Sum of total_amount)
- Total Bookings (Count of booking_id)
- Avg Booking Value (Average total_amount)
- Cancellation Rate (%)

### Data Sources
- `fact_booking_detail` (primary)
- `dim_destination`, `dim_property`, `dim_user`

---

## 📈 Dashboard 2: Engagement & Conversion

**File:** `wanderbricks_engagement_conversion_dashboard.lvdash.json`

### Pages
1. **Funnel Overview** - Views, clicks, conversion metrics
2. **Property Engagement** - Top engaged properties, geographic engagement
3. **Optimization Insights** - Low conversion properties needing attention

### Key Datasets
- `engagement_kpis` - Total views, clicks, conversion rates
- `conversion_funnel` - Views → Clicks → Searches funnel
- `top_engaged_properties` - Highest engagement properties
- `low_conversion_properties` - Improvement opportunities

### KPIs
- Total Views (Sum of view_count)
- Total Clicks (Sum of click_count)
- Avg Conversion Rate (Average conversion_rate)

### Data Sources
- `fact_property_engagement` (primary)
- `dim_property`, `dim_destination`

---

## 🏠 Dashboard 3: Property Portfolio

**File:** `wanderbricks_property_portfolio_dashboard.lvdash.json`

### Pages
1. **Portfolio Overview** - Property count, capacity, geographic distribution
2. **Pricing Analysis** - Price distribution, amenities analysis
3. **Performance Ranking** - Top/bottom performing properties

### Key Datasets
- `portfolio_kpis` - Property count, capacity, avg price
- `properties_by_destination` - Geographic distribution
- `price_distribution` - Price range breakdown
- `top_performing_properties` - Highest revenue properties

### KPIs
- Total Properties (Count of property_id)
- Total Capacity (Sum of max_guests)
- Avg Base Price (Average base_price)

### Data Sources
- `dim_property` (primary)
- `dim_destination`, `fact_booking_detail`

---

## 👤 Dashboard 4: Host Performance

**File:** `wanderbricks_host_performance_dashboard.lvdash.json`

### Pages
1. **Host Overview** - Total hosts, verification %, rating distribution
2. **Performance Ranking** - Top hosts by revenue and rating
3. **Quality Analysis** - Verification impact, multi-property hosts

### Key Datasets
- `host_kpis` - Total hosts, verified %, avg rating
- `host_rating_distribution` - Rating distribution (0.5 buckets)
- `top_hosts_by_revenue` - Highest earning hosts
- `verification_impact` - Verified vs non-verified comparison

### KPIs
- Total Hosts (Count of host_id)
- Verified % (Percentage is_verified)
- Avg Rating (Average rating)

### Data Sources
- `dim_host` (primary)
- `dim_property`, `fact_booking_detail`

---

## 🎯 Dashboard 5: Customer Analytics

**File:** `wanderbricks_customer_analytics_dashboard.lvdash.json`

### Pages
1. **Customer Overview** - Total customers, segments, geographic distribution
2. **Segment Analysis** - Business vs leisure, booking frequency
3. **Behavior Patterns** - Top customers, lead time analysis

### Key Datasets
- `customer_kpis` - Total customers, business %
- `customer_segments` - VIP, Loyal, Returning, New segments
- `business_vs_leisure` - B2B vs B2C comparison
- `top_customers_by_spend` - Highest value customers

### KPIs
- Total Customers (Count of user_id)
- Business % (Percentage is_business)
- Customer Segments (VIP, Loyal, Returning, New)

### Data Sources
- `dim_user` (primary)
- `fact_booking_detail`, `dim_destination`

---

## 🔍 Dashboard 6: Lakehouse Monitoring

**File:** `wanderbricks_lakehouse_monitoring_dashboard.lvdash.json`  
**Guide:** `LAKEHOUSE_MONITORING_DASHBOARD_GUIDE.md`

### Pages
1. **Monitoring Overview** - 6 KPI counters across all monitors, unified alerts table
2. **Revenue Monitoring** - Revenue metrics, drift detection, cancellation analysis
3. **Engagement Monitoring** - Property views, clicks, conversion health
4. **Dimension Monitors** - Property, host, and customer dimension quality metrics

### Key Datasets
- `revenue_kpis` - Daily revenue, avg booking value, cancellation rate
- `revenue_drift_alerts` - Period-over-period revenue change detection
- `engagement_kpis` - Views, clicks, conversion rate, engagement health
- `property_kpis` - Active listings, avg price, price variance
- `host_kpis` - Active hosts, verification rate, avg rating
- `customer_kpis` - Total customers, business customer rate
- `all_alerts` - Unified alert view across all 5 monitors

### Custom Metrics (20 Total)

**Revenue Monitor (6 metrics):**
- `daily_revenue` - Total booking value per day (AGGREGATE)
- `avg_booking_value` - Average booking amount (AGGREGATE)
- `total_bookings` - Sum of booking count (AGGREGATE)
- `total_cancellations` - Sum of cancellation count (AGGREGATE)
- `cancellation_rate` - Derived: cancellations/bookings * 100 (DERIVED)
- `revenue_vs_baseline` - Period-over-period revenue change (DRIFT)

**Engagement Monitor (4 metrics):**
- `total_views` - Sum of property views (AGGREGATE)
- `total_clicks` - Sum of property clicks (AGGREGATE)
- `avg_conversion` - Average conversion rate (AGGREGATE)
- `engagement_health` - Derived: clicks/views * 100 (DERIVED)

**Property Monitor (3 metrics):**
- `active_listings` - Count of current active properties (AGGREGATE)
- `avg_price` - Average base price of active listings (AGGREGATE)
- `price_variance` - Standard deviation of prices (AGGREGATE)

**Host Monitor (4 metrics):**
- `active_hosts` - Count of active current hosts (AGGREGATE)
- `total_current_hosts` - Count of all current hosts (AGGREGATE)
- `avg_rating` - Average host rating (AGGREGATE)
- `verification_rate` - Derived: verified/total * 100 (DERIVED)

**Customer Monitor (3 metrics):**
- `total_customers` - Count of current customers (AGGREGATE)
- `business_customers` - Count of business customers (AGGREGATE)
- `business_customer_rate` - Derived: business/total * 100 (DERIVED)
- `customer_growth` - Period-over-period customer growth (DRIFT)

### Alert Thresholds
| Alert Type | Condition | Severity |
|---|---|---|
| Revenue Drop | `pct_change < -20%` | Critical |
| High Cancellation | `cancellation_rate > 15%` | Warning |
| Low Engagement | `engagement_health < 5%` | Warning |
| Listing Drop | `>10% decrease` | Warning |

### Data Sources
- `{catalog}.{schema}__tables__fact_booking_daily_profile_metrics`
- `{catalog}.{schema}__tables__fact_booking_daily_drift_metrics`
- `{catalog}.{schema}__tables__fact_property_engagement_profile_metrics`
- `{catalog}.{schema}__tables__dim_property_profile_metrics`
- `{catalog}.{schema}__tables__dim_host_profile_metrics`
- `{catalog}.{schema}__tables__dim_user_profile_metrics`
- `{catalog}.{schema}__tables__dim_user_drift_metrics`

**⚠️ Prerequisites:**
1. Lakehouse Monitoring setup complete (`lakehouse_monitoring.py`)
2. Monitors have initialized (15-20 minutes after creation)
3. Output tables exist with custom metrics as columns

**📘 Deployment:** See `LAKEHOUSE_MONITORING_DASHBOARD_GUIDE.md` for complete setup instructions.

---

## 🎨 Design Standards

### Grid System
- **6-column grid layout** (NOT 12!)
- Widget widths: 1, 2, 3, 4, or 6 columns
- Standard heights: 2 (KPIs), 6 (charts), 6+ (tables)

### Widget Versions
| Widget Type | Version |
|-------------|---------|
| KPI Counter | 2 |
| Bar Chart | 3 |
| Line Chart | 3 |
| Pie Chart | 3 |
| Table | 1 |
| Filter | 2 |

### Color Palette
```
Primary:    #077A9D (Blue)
Secondary:  #00A972 (Green)
Warning:    #FFAB00 (Amber)
Alert:      #FF3621 (Red)
```

### Date Parameters
- Type: `DATE` (not DATETIME)
- Default range: 2024-01-01 to 2024-12-31
- Format: Static date strings (not dynamic expressions)

---

## 📦 Deployment

### Prerequisites
1. Gold layer tables deployed:
   - `fact_booking_detail`
   - `fact_booking_daily`
   - `fact_property_engagement`
   - `dim_user`, `dim_host`, `dim_property`, `dim_destination`, `dim_date`

2. Unity Catalog access:
   - Catalog: `${catalog}`
   - Schema: `${gold_schema}`

### Import Steps

1. **Navigate to Databricks Workspace:**
   ```
   Workspace → Dashboards → Create AI/BI Dashboard
   ```

2. **Import Dashboard JSON:**
   - Click "Import" or "Create from JSON"
   - Upload one of the 5 dashboard JSON files
   - Databricks will validate the JSON structure

3. **Configure Variables:**
   - Replace `${catalog}` with your catalog name (e.g., `prashanth_subrahmanyam_catalog`)
   - Replace `${gold_schema}` with your Gold schema name (e.g., `wanderbricks_gold`)

4. **Test Queries:**
   - Navigate to each page
   - Verify datasets execute without errors
   - Adjust date parameters if needed

5. **Set Permissions:**
   - Share dashboard with appropriate groups
   - Set view/edit permissions

6. **Configure Auto-Refresh:**
   - Set refresh schedule (e.g., Daily at 2 AM)
   - Enable notifications on failure

---

## 🔄 Auto-Refresh Schedule

### Recommended Schedule

| Dashboard | Frequency | Time (UTC) | Rationale |
|-----------|-----------|------------|-----------|
| Revenue Performance | Daily | 02:00 | After overnight booking batch |
| Engagement & Conversion | Daily | 03:00 | After clickstream aggregation |
| Property Portfolio | Weekly | Sunday 04:00 | Inventory changes weekly |
| Host Performance | Weekly | Sunday 05:00 | Host metrics update weekly |
| Customer Analytics | Daily | 06:00 | After customer dimension refresh |
| Lakehouse Monitoring | Daily | 08:00 | After monitor refresh completion |

---

## 🔍 Query Optimization Tips

### Performance Best Practices

1. **Use Date Filters:**
   - Always include `:start_date` and `:end_date` parameters
   - Default to 90-day window for performance

2. **Limit Result Sets:**
   - Use `LIMIT` clauses (typically 15-20 for charts, 100 for tables)
   - Aggregate before joining large tables

3. **SCD2 Handling:**
   - Always filter `is_current = true` for current state
   - Use point-in-time joins for historical analysis

4. **Aggregation Strategy:**
   - Pre-aggregate in datasets, not in widget queries
   - Use `fact_booking_daily` for daily aggregates

5. **JOIN Optimization:**
   - Join fact tables to dimensions (not vice versa)
   - Use LEFT JOIN for optional relationships

---

## 📊 Common Queries Reference

### Revenue Last 30 Days
```sql
SELECT SUM(total_amount) as revenue
FROM ${catalog}.${gold_schema}.fact_booking_detail
WHERE check_in_date >= CURRENT_DATE() - INTERVAL 30 DAYS
```

### Top 10 Properties by Revenue
```sql
SELECT p.title, SUM(f.total_amount) as revenue
FROM ${catalog}.${gold_schema}.fact_booking_detail f
JOIN ${catalog}.${gold_schema}.dim_property p 
  ON f.property_id = p.property_id AND p.is_current = true
WHERE f.check_in_date >= :start_date
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10
```

### Conversion Rate by Property Type
```sql
SELECT p.property_type, AVG(e.conversion_rate) as avg_conversion
FROM ${catalog}.${gold_schema}.fact_property_engagement e
JOIN ${catalog}.${gold_schema}.dim_property p 
  ON e.property_id = p.property_id AND p.is_current = true
WHERE e.engagement_date >= :start_date
GROUP BY 1
ORDER BY 2 DESC
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Widget Not Rendering
- **Cause:** Width exceeds 6 columns
- **Fix:** Adjust `position.width` to be between 1-6

#### 2. Query Timeout
- **Cause:** Missing date filters or inefficient join
- **Fix:** Add WHERE clause with date range, optimize joins

#### 3. Empty Dataset
- **Cause:** No data in date range or table doesn't exist
- **Fix:** Verify table exists, check date parameter defaults

#### 4. Schema Mismatch
- **Cause:** Column names in query don't match Gold layer
- **Fix:** Review Gold layer YAML schemas, update column references

#### 5. Parameter Not Recognized
- **Cause:** Parameter keyword mismatch
- **Fix:** Ensure `:start_date` and `:end_date` match parameter definitions

---

## 📚 References

### Official Documentation
- [Lakeview Dashboards](https://docs.databricks.com/dashboards/lakeview.html)
- [AI/BI Dashboard Patterns](../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)
- [Dashboard Prompt](../context/prompts/10-aibi-dashboards-prompt.md)
- [Phase 4 Addendum 4.5](../plans/phase4-addendum-4.5-aibi-dashboards.md)

### Project Documentation
- [Gold Layer Design](../gold_layer_design/README.md)
- [Schema Definitions](../gold_layer_design/yaml/)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)

---

## ✅ Implementation Status

| Dashboard | Status | Pages | Widgets | Last Updated |
|-----------|--------|-------|---------|--------------|
| 1. Revenue Performance | ✅ Complete | 4 | 12 | 2024-12-10 |
| 2. Engagement & Conversion | ✅ Complete | 4 | 10 | 2024-12-10 |
| 3. Property Portfolio | ✅ Complete | 4 | 10 | 2024-12-10 |
| 4. Host Performance | ✅ Complete | 4 | 10 | 2024-12-10 |
| 5. Customer Analytics | ✅ Complete | 4 | 11 | 2024-12-10 |
| 6. Lakehouse Monitoring | ✅ Complete | 4 | 15 | 2024-12-11 |

**Total:** 6 dashboards, 24 pages, 68 widgets

---

## 🎯 Next Steps

1. **Import Dashboards:**
   - Import all 5 JSON files into Databricks workspace
   - Configure catalog and schema variables

2. **Test Queries:**
   - Verify all datasets execute successfully
   - Adjust date ranges as needed

3. **Set Permissions:**
   - Share with appropriate teams
   - Configure view/edit access

4. **Configure Auto-Refresh:**
   - Set refresh schedules per recommendations
   - Enable failure notifications

5. **User Training:**
   - Document dashboard navigation
   - Create user guides for self-service analytics

6. **Monitor Usage:**
   - Track dashboard views and query performance
   - Optimize slow-running queries

---

## 📞 Support

For questions or issues:
- **Technical:** Refer to [AI/BI Dashboard Patterns](../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)
- **Data Quality:** Check [Gold Layer Documentation](../gold_layer_design/README.md)
- **Schema Changes:** Update YAML schemas and regenerate dashboards

---

**Implementation Date:** December 10-11, 2024  
**Framework Version:** Databricks Lakeview AI/BI  
**Compliance:** Unity Catalog, 6-column grid, Databricks theme  
**Monitoring:** 5 Lakehouse Monitors with 20 custom business metrics

