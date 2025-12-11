# Phase 4 Addendum 4.4: Lakehouse Monitoring

## Overview

**Status:** ✅ Implemented  
**Dependencies:** Phase 3 (Gold Layer)  
**Artifact Count:** 5 Monitors with 19 Custom Metrics  
**Reference:** [Lakehouse Monitoring Patterns](../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

**Implementation Files:**
- `src/wanderbricks_gold/lakehouse_monitoring.py` - Monitor setup script (500+ lines)
- `resources/gold/lakehouse_monitoring_job.yml` - Asset Bundle job
- `src/wanderbricks_gold/monitoring_queries.sql` - Query examples
- `src/wanderbricks_gold/MONITORING_README.md` - Implementation documentation

---

## Purpose

Lakehouse Monitoring provides:
1. **Data quality tracking** - Automated profiling and drift detection
2. **Custom business metrics** - Domain-specific KPI monitoring
3. **Anomaly detection** - Statistical deviation alerts
4. **Data freshness** - SLA compliance monitoring

---

## Monitor Summary

| # | Monitor | Domain | Table | Custom Metrics |
|---|---------|--------|-------|----------------|
| 1 | revenue_monitor | 💰 Revenue | fact_booking_daily | 4 |
| 2 | engagement_monitor | 📊 Engagement | fact_property_engagement | 3 |
| 3 | property_monitor | 🏠 Property | dim_property | 3 |
| 4 | host_monitor | 👤 Host | dim_host | 3 |
| 5 | customer_monitor | 🎯 Customer | dim_user | 3 |

---

## 💰 Revenue Monitor

### Configuration

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import MonitorInferenceLog, MonitorTimeSeries

w = WorkspaceClient()

# Create revenue monitor
w.quality_monitors.create(
    table_name=f"{catalog}.{gold_schema}.fact_booking_daily",
    assets_dir=f"/Workspace/Users/shared/wanderbricks/monitors/revenue",
    output_schema_name=f"{catalog}.{gold_schema}",
    time_series=MonitorTimeSeries(
        timestamp_col="check_in_date",
        granularities=["1 day", "1 week"]
    ),
    slicing_exprs=["destination_id", "property_id"],
    baseline_table_name=f"{catalog}.{gold_schema}.fact_booking_daily_baseline",
    custom_metrics=[
        # Revenue KPIs
        {
            "name": "daily_revenue",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "SUM(total_booking_value)"
        },
        {
            "name": "avg_booking_value",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "AVG(avg_booking_value)"
        },
        {
            "name": "cancellation_rate",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) * 100"
        },
        {
            "name": "revenue_vs_baseline",
            "input_columns": [":table"],
            "type": "drift",
            "definition": "(SUM(total_booking_value) - {{baseline}}) / NULLIF({{baseline}}, 0) * 100"
        }
    ]
)
```

### Custom Metrics Detail

| Metric | Type | Definition | Threshold |
|--------|------|------------|-----------|
| daily_revenue | aggregate | SUM(total_booking_value) | Alert if <80% of baseline |
| avg_booking_value | aggregate | AVG(avg_booking_value) | Alert if deviation >20% |
| cancellation_rate | aggregate | cancellations/bookings*100 | Alert if >15% |
| revenue_vs_baseline | drift | % change from baseline | Alert if <-20% |

### Slicing Dimensions

- **destination_id** - Monitor revenue by destination
- **property_id** - Monitor individual property performance

---

## 📊 Engagement Monitor

### Configuration

```python
w.quality_monitors.create(
    table_name=f"{catalog}.{gold_schema}.fact_property_engagement",
    assets_dir=f"/Workspace/Users/shared/wanderbricks/monitors/engagement",
    output_schema_name=f"{catalog}.{gold_schema}",
    time_series=MonitorTimeSeries(
        timestamp_col="engagement_date",
        granularities=["1 day", "1 week"]
    ),
    slicing_exprs=["property_id"],
    custom_metrics=[
        {
            "name": "total_views",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "SUM(view_count)"
        },
        {
            "name": "conversion_rate",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "AVG(conversion_rate)"
        },
        {
            "name": "engagement_health",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "SUM(click_count) / NULLIF(SUM(view_count), 0) * 100"
        }
    ]
)
```

### Custom Metrics Detail

| Metric | Type | Definition | Threshold |
|--------|------|------------|-----------|
| total_views | aggregate | SUM(view_count) | Alert if <50% of baseline |
| conversion_rate | aggregate | AVG(conversion_rate) | Alert if deviation >30% |
| engagement_health | aggregate | clicks/views*100 | Alert if <5% |

---

## 🏠 Property Monitor

### Configuration

```python
w.quality_monitors.create(
    table_name=f"{catalog}.{gold_schema}.dim_property",
    assets_dir=f"/Workspace/Users/shared/wanderbricks/monitors/property",
    output_schema_name=f"{catalog}.{gold_schema}",
    snapshot=MonitorSnapshot(),  # Snapshot monitoring for dimension
    slicing_exprs=["property_type", "destination_id"],
    custom_metrics=[
        {
            "name": "active_listings",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "COUNT(CASE WHEN is_current = true THEN 1 END)"
        },
        {
            "name": "avg_price",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "AVG(CASE WHEN is_current = true THEN base_price END)"
        },
        {
            "name": "price_variance",
            "input_columns": ["base_price"],
            "type": "aggregate",
            "definition": "STDDEV(base_price)"
        }
    ]
)
```

### Custom Metrics Detail

| Metric | Type | Definition | Threshold |
|--------|------|------------|-----------|
| active_listings | aggregate | COUNT(is_current) | Alert if drops >10% |
| avg_price | aggregate | AVG(base_price) | Alert if deviation >15% |
| price_variance | aggregate | STDDEV(base_price) | Alert if variance doubles |

---

## 👤 Host Monitor

### Configuration

```python
w.quality_monitors.create(
    table_name=f"{catalog}.{gold_schema}.dim_host",
    assets_dir=f"/Workspace/Users/shared/wanderbricks/monitors/host",
    output_schema_name=f"{catalog}.{gold_schema}",
    snapshot=MonitorSnapshot(),
    slicing_exprs=["country", "is_verified"],
    custom_metrics=[
        {
            "name": "active_hosts",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "COUNT(CASE WHEN is_current = true AND is_active = true THEN 1 END)"
        },
        {
            "name": "avg_rating",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "AVG(CASE WHEN is_current = true THEN rating END)"
        },
        {
            "name": "verification_rate",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "SUM(CASE WHEN is_verified AND is_current THEN 1 ELSE 0 END) / NULLIF(COUNT(CASE WHEN is_current THEN 1 END), 0) * 100"
        }
    ]
)
```

---

## 🎯 Customer Monitor

### Configuration

```python
w.quality_monitors.create(
    table_name=f"{catalog}.{gold_schema}.dim_user",
    assets_dir=f"/Workspace/Users/shared/wanderbricks/monitors/customer",
    output_schema_name=f"{catalog}.{gold_schema}",
    snapshot=MonitorSnapshot(),
    slicing_exprs=["country", "user_type"],
    custom_metrics=[
        {
            "name": "total_customers",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "COUNT(CASE WHEN is_current = true THEN 1 END)"
        },
        {
            "name": "business_customer_rate",
            "input_columns": [":table"],
            "type": "aggregate",
            "definition": "SUM(CASE WHEN is_business AND is_current THEN 1 ELSE 0 END) / NULLIF(COUNT(CASE WHEN is_current THEN 1 END), 0) * 100"
        },
        {
            "name": "customer_growth",
            "input_columns": [":table"],
            "type": "drift",
            "definition": "COUNT(CASE WHEN is_current THEN 1 END)"
        }
    ]
)
```

---

## Monitor Output Tables

Each monitor creates these output tables:

| Table | Purpose | Refresh |
|-------|---------|---------|
| `{table}_profile_metrics` | Column-level statistics | Per run |
| `{table}_drift_metrics` | Drift detection results | Per run |
| `{table}_custom_metrics` | Custom metric values | Per run |

### Querying Monitor Results

```sql
-- Get latest revenue metrics
SELECT 
    window_start,
    window_end,
    slice_key,
    custom_metric_name,
    custom_metric_value
FROM ${catalog}.${gold_schema}.fact_booking_daily_custom_metrics
WHERE window_end >= DATE_ADD(CURRENT_DATE(), -7)
  AND custom_metric_name = 'daily_revenue'
ORDER BY window_start DESC;

-- Get drift alerts
SELECT *
FROM ${catalog}.${gold_schema}.fact_booking_daily_drift_metrics
WHERE is_anomaly = true
  AND window_end >= DATE_ADD(CURRENT_DATE(), -30);
```

---

## Baseline Configuration

### Creating Baselines

```python
# Create baseline from historical data
spark.sql(f"""
    CREATE OR REPLACE TABLE {catalog}.{gold_schema}.fact_booking_daily_baseline
    AS SELECT *
    FROM {catalog}.{gold_schema}.fact_booking_daily
    WHERE check_in_date BETWEEN 
        DATE_ADD(CURRENT_DATE(), -90) AND DATE_ADD(CURRENT_DATE(), -30)
""")
```

### Baseline Refresh Schedule

| Monitor | Baseline Period | Refresh Frequency |
|---------|-----------------|-------------------|
| Revenue | 60-day lookback | Monthly |
| Engagement | 30-day lookback | Monthly |
| Property | Previous snapshot | Weekly |
| Host | Previous snapshot | Weekly |
| Customer | Previous snapshot | Weekly |

---

## Alert Integration

### Alert Rules

| Monitor | Metric | Condition | Severity |
|---------|--------|-----------|----------|
| Revenue | daily_revenue | <80% baseline | Critical |
| Revenue | cancellation_rate | >15% | Warning |
| Engagement | total_views | <50% baseline | Critical |
| Engagement | conversion_rate | deviation >30% | Warning |
| Property | active_listings | drop >10% | Warning |
| Host | avg_rating | drop >0.5 | Warning |
| Customer | customer_growth | <0 | Warning |

### SQL Alert Example

```sql
-- Revenue drop alert
CREATE ALERT revenue_drop_alert
SCHEDULE EVERY 1 DAY
AS
SELECT 
    window_end as alert_time,
    custom_metric_value as current_revenue,
    baseline_value,
    (custom_metric_value - baseline_value) / baseline_value * 100 as pct_change
FROM ${catalog}.${gold_schema}.fact_booking_daily_custom_metrics
WHERE custom_metric_name = 'daily_revenue'
  AND window_end = CURRENT_DATE()
  AND custom_metric_value < baseline_value * 0.8;
```

---

## Implementation Checklist

- [x] Revenue Monitor
  - [x] Create monitor with time series config
  - [x] Add 6 custom metrics (4 AGGREGATE, 1 DERIVED, 1 DRIFT)
  - [ ] Create baseline table (optional - will auto-generate)
  - [ ] Configure SQL alerts (next phase)

- [x] Engagement Monitor
  - [x] Create monitor with time series config
  - [x] Add 4 custom metrics (3 AGGREGATE, 1 DERIVED)
  - [ ] Configure SQL alerts (next phase)

- [x] Property Monitor
  - [x] Create monitor with snapshot config
  - [x] Add 3 custom metrics (3 AGGREGATE)
  - [ ] Configure SQL alerts (next phase)

- [x] Host Monitor
  - [x] Create monitor with snapshot config
  - [x] Add 5 custom metrics (4 AGGREGATE, 1 DERIVED)
  - [ ] Configure SQL alerts (next phase)

- [x] Customer Monitor
  - [x] Create monitor with snapshot config
  - [x] Add 4 custom metrics (2 AGGREGATE, 1 DERIVED, 1 DRIFT)
  - [ ] Configure SQL alerts (next phase)

**Implementation Complete:** All monitors created with production-ready configuration. Alert configuration will be handled in Phase 4 Addendum 4.7 (Alerting).

---

## References

- [Lakehouse Monitoring Documentation](https://docs.databricks.com/lakehouse-monitoring/)
- [Custom Metrics](https://docs.databricks.com/lakehouse-monitoring/custom-metrics)
- [Monitoring Patterns Rule](../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)

