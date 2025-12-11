# Phase 4 Addendum 4.7: Alerting Framework

## Overview

**Status:** 📋 Planned  
**Dependencies:** Phase 3 (Gold Layer), 4.4 (Lakehouse Monitoring)  
**Artifact Count:** 21 SQL Alerts  
**Reference:** [Databricks SQL Alerts](https://docs.databricks.com/sql/user/alerts/)

---

## Purpose

The Alerting Framework provides:
1. **Proactive monitoring** - Catch issues before they impact business
2. **SLA compliance** - Ensure data freshness and quality
3. **Business anomaly detection** - Flag unusual patterns
4. **Automated notifications** - Email/Slack integration

---

## Alert Summary by Domain

| Domain | Icon | Alert Count | Critical | Warning | Info |
|--------|------|-------------|----------|---------|------|
| Revenue | 💰 | 5 | 2 | 2 | 1 |
| Engagement | 📊 | 4 | 1 | 2 | 1 |
| Property | 🏠 | 4 | 1 | 2 | 1 |
| Host | 👤 | 4 | 1 | 2 | 1 |
| Customer | 🎯 | 4 | 1 | 2 | 1 |
| **Total** | | **21** | **6** | **10** | **5** |

---

## Alert ID Convention

```
<DOMAIN>-<NUMBER>-<SEVERITY>
```

Examples:
- `REV-001-CRIT` - Revenue critical alert #1
- `ENG-003-WARN` - Engagement warning alert #3
- `PROP-002-INFO` - Property info alert #2

---

## 💰 Revenue Domain Alerts

### REV-001-CRIT: Revenue Drop Alert

**Severity:** 🔴 Critical  
**Frequency:** Daily at 6 AM  
**Condition:** Daily revenue <80% of 7-day average

```sql
-- Alert: Revenue Drop
SELECT 
    CURRENT_DATE() as alert_date,
    yesterday_revenue,
    avg_7d_revenue,
    ROUND((yesterday_revenue - avg_7d_revenue) / avg_7d_revenue * 100, 1) as pct_change,
    'CRITICAL: Revenue dropped ' || 
        ROUND((avg_7d_revenue - yesterday_revenue) / avg_7d_revenue * 100, 1) || 
        '% below 7-day average' as alert_message
FROM (
    SELECT
        SUM(CASE WHEN check_in_date = DATE_ADD(CURRENT_DATE(), -1) 
            THEN total_booking_value ELSE 0 END) as yesterday_revenue,
        AVG(CASE WHEN check_in_date BETWEEN DATE_ADD(CURRENT_DATE(), -8) 
            AND DATE_ADD(CURRENT_DATE(), -2) 
            THEN daily_total ELSE NULL END) as avg_7d_revenue
    FROM (
        SELECT check_in_date, SUM(total_booking_value) as daily_total
        FROM ${catalog}.${gold_schema}.fact_booking_daily
        WHERE check_in_date >= DATE_ADD(CURRENT_DATE(), -8)
        GROUP BY 1
    )
)
WHERE yesterday_revenue < avg_7d_revenue * 0.8
```

**Actions:**
- Email: Finance team, Revenue Management
- Slack: #revenue-alerts channel

---

### REV-002-CRIT: High Cancellation Rate

**Severity:** 🔴 Critical  
**Frequency:** Daily at 7 AM  
**Condition:** Cancellation rate >15%

```sql
SELECT 
    check_in_date,
    SUM(cancellation_count) as cancellations,
    SUM(booking_count) as bookings,
    ROUND(SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) * 100, 1) as cancellation_rate,
    'CRITICAL: Cancellation rate at ' || 
        ROUND(SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) * 100, 1) || '%' as alert_message
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date = DATE_ADD(CURRENT_DATE(), -1)
GROUP BY 1
HAVING SUM(cancellation_count) / NULLIF(SUM(booking_count), 0) > 0.15
```

---

### REV-003-WARN: Booking Volume Anomaly

**Severity:** 🟡 Warning  
**Frequency:** Hourly  
**Condition:** Booking count deviation >2 std from mean

```sql
SELECT 
    CURRENT_TIMESTAMP() as alert_time,
    today_bookings,
    avg_bookings,
    stddev_bookings,
    'WARNING: Booking volume anomaly - ' || 
        ROUND((today_bookings - avg_bookings) / stddev_bookings, 1) || 
        ' std deviations from mean' as alert_message
FROM (
    SELECT
        SUM(CASE WHEN check_in_date = CURRENT_DATE() 
            THEN booking_count ELSE 0 END) as today_bookings,
        AVG(daily_bookings) as avg_bookings,
        STDDEV(daily_bookings) as stddev_bookings
    FROM (
        SELECT check_in_date, SUM(booking_count) as daily_bookings
        FROM ${catalog}.${gold_schema}.fact_booking_daily
        WHERE check_in_date BETWEEN DATE_ADD(CURRENT_DATE(), -30) AND CURRENT_DATE()
        GROUP BY 1
    )
)
WHERE ABS(today_bookings - avg_bookings) > 2 * stddev_bookings
```

---

### REV-004-WARN: Payment Completion Drop

**Severity:** 🟡 Warning  
**Frequency:** Daily at 8 AM  
**Condition:** Payment completion rate <90%

```sql
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as date,
    AVG(payment_completion_rate) as payment_rate,
    'WARNING: Payment completion rate at ' || 
        ROUND(AVG(payment_completion_rate), 1) || '%' as alert_message
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date = DATE_ADD(CURRENT_DATE(), -1)
HAVING AVG(payment_completion_rate) < 90
```

---

### REV-005-INFO: Daily Revenue Summary

**Severity:** 🟢 Info  
**Frequency:** Daily at 9 AM  
**Condition:** Always (informational)

```sql
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as date,
    SUM(total_booking_value) as total_revenue,
    SUM(booking_count) as total_bookings,
    ROUND(AVG(avg_booking_value), 2) as avg_booking_value,
    'Daily Summary: $' || FORMAT_NUMBER(SUM(total_booking_value), 2) || 
        ' revenue from ' || SUM(booking_count) || ' bookings' as summary
FROM ${catalog}.${gold_schema}.fact_booking_daily
WHERE check_in_date = DATE_ADD(CURRENT_DATE(), -1)
```

---

## 📊 Engagement Domain Alerts

### ENG-001-CRIT: Traffic Crash

**Severity:** 🔴 Critical  
**Frequency:** Hourly  
**Condition:** Views <50% of same time yesterday

```sql
SELECT 
    CURRENT_TIMESTAMP() as alert_time,
    today_views,
    yesterday_views,
    ROUND((yesterday_views - today_views) / yesterday_views * 100, 1) as pct_drop,
    'CRITICAL: Traffic down ' || 
        ROUND((yesterday_views - today_views) / yesterday_views * 100, 1) || 
        '% vs yesterday' as alert_message
FROM (
    SELECT
        SUM(CASE WHEN engagement_date = CURRENT_DATE() 
            THEN view_count ELSE 0 END) as today_views,
        SUM(CASE WHEN engagement_date = DATE_ADD(CURRENT_DATE(), -1) 
            THEN view_count ELSE 0 END) as yesterday_views
    FROM ${catalog}.${gold_schema}.fact_property_engagement
)
WHERE today_views < yesterday_views * 0.5
```

---

### ENG-002-WARN: Conversion Rate Drop

**Severity:** 🟡 Warning  
**Frequency:** Daily  
**Condition:** Conversion rate <2%

```sql
SELECT 
    DATE_ADD(CURRENT_DATE(), -1) as date,
    AVG(conversion_rate) as avg_conversion,
    'WARNING: Conversion rate at ' || 
        ROUND(AVG(conversion_rate), 2) || '%' as alert_message
FROM ${catalog}.${gold_schema}.fact_property_engagement
WHERE engagement_date = DATE_ADD(CURRENT_DATE(), -1)
HAVING AVG(conversion_rate) < 2
```

---

### ENG-003-WARN: Low Engagement Property Alert

**Severity:** 🟡 Warning  
**Frequency:** Weekly  
**Condition:** Properties with <10 views in 7 days

```sql
SELECT 
    p.property_id,
    p.title,
    COALESCE(SUM(e.view_count), 0) as weekly_views,
    'WARNING: Property "' || p.title || '" has only ' || 
        COALESCE(SUM(e.view_count), 0) || ' views this week' as alert_message
FROM ${catalog}.${gold_schema}.dim_property p
LEFT JOIN ${catalog}.${gold_schema}.fact_property_engagement e
    ON p.property_id = e.property_id
    AND e.engagement_date >= DATE_ADD(CURRENT_DATE(), -7)
WHERE p.is_current = true
GROUP BY p.property_id, p.title
HAVING COALESCE(SUM(e.view_count), 0) < 10
```

---

### ENG-004-INFO: Weekly Engagement Summary

**Severity:** 🟢 Info  
**Frequency:** Weekly (Monday)  
**Condition:** Always

---

## 🏠 Property Domain Alerts

### PROP-001-CRIT: Inventory Drop

**Severity:** 🔴 Critical  
**Condition:** Active listings drop >10% WoW

### PROP-002-WARN: Price Anomaly

**Severity:** 🟡 Warning  
**Condition:** Price deviation >3 std from mean

### PROP-003-WARN: Zero Booking Properties

**Severity:** 🟡 Warning  
**Condition:** Properties with 0 bookings in 30 days

### PROP-004-INFO: Property Portfolio Summary

**Severity:** 🟢 Info  
**Frequency:** Weekly

---

## 👤 Host Domain Alerts

### HOST-001-CRIT: Host Rating Crash

**Severity:** 🔴 Critical  
**Condition:** Host rating drops >0.5 in 7 days

### HOST-002-WARN: Unverified Host with High Bookings

**Severity:** 🟡 Warning  
**Condition:** Unverified host with >10 bookings

### HOST-003-WARN: Inactive Host Alert

**Severity:** 🟡 Warning  
**Condition:** Hosts with no activity in 30 days

### HOST-004-INFO: Host Performance Summary

**Severity:** 🟢 Info  
**Frequency:** Weekly

---

## 🎯 Customer Domain Alerts

### CUST-001-CRIT: New Customer Drop

**Severity:** 🔴 Critical  
**Condition:** New signups <50% of average

### CUST-002-WARN: High Value Customer Churn

**Severity:** 🟡 Warning  
**Condition:** VIP customer no activity in 90 days

### CUST-003-WARN: Business Customer Decline

**Severity:** 🟡 Warning  
**Condition:** Business bookings down >20%

### CUST-004-INFO: Customer Growth Summary

**Severity:** 🟢 Info  
**Frequency:** Weekly

---

## Alert Configuration Template

```yaml
# Alert configuration (YAML representation)
alert:
  name: <ALERT-ID>-<SEVERITY>: <Alert Name>
  query_id: <query_uuid>
  owner_user_name: data-engineering@wanderbricks.com
  options:
    column: alert_message  # Column to check
    op: ">"                # Operator
    value: 0               # Threshold
    custom_body: |
      Alert: {{ALERT_NAME}}
      Time: {{ALERT_TIME}}
      Status: {{ALERT_STATUS}}
      
      {{QUERY_RESULT_VALUE}}
    custom_subject: "[{{ALERT_STATUS}}] {{ALERT_NAME}}"
  rearm: 1800  # 30 minutes cooldown
```

---

## Notification Configuration

### Email Recipients by Severity

| Severity | Recipients |
|----------|------------|
| Critical | Leadership, On-call, Domain owners |
| Warning | Domain owners, Data Engineering |
| Info | Subscribed stakeholders |

### Slack Channels

| Domain | Channel |
|--------|---------|
| Revenue | #revenue-alerts |
| Engagement | #marketing-alerts |
| Property | #operations-alerts |
| Host | #partner-alerts |
| Customer | #growth-alerts |
| All Critical | #platform-critical |

---

## Implementation Checklist

### Revenue Alerts
- [ ] REV-001-CRIT: Revenue Drop Alert
- [ ] REV-002-CRIT: High Cancellation Rate
- [ ] REV-003-WARN: Booking Volume Anomaly
- [ ] REV-004-WARN: Payment Completion Drop
- [ ] REV-005-INFO: Daily Revenue Summary

### Engagement Alerts
- [ ] ENG-001-CRIT: Traffic Crash
- [ ] ENG-002-WARN: Conversion Rate Drop
- [ ] ENG-003-WARN: Low Engagement Property Alert
- [ ] ENG-004-INFO: Weekly Engagement Summary

### Property Alerts
- [ ] PROP-001-CRIT: Inventory Drop
- [ ] PROP-002-WARN: Price Anomaly
- [ ] PROP-003-WARN: Zero Booking Properties
- [ ] PROP-004-INFO: Property Portfolio Summary

### Host Alerts
- [ ] HOST-001-CRIT: Host Rating Crash
- [ ] HOST-002-WARN: Unverified Host with High Bookings
- [ ] HOST-003-WARN: Inactive Host Alert
- [ ] HOST-004-INFO: Host Performance Summary

### Customer Alerts
- [ ] CUST-001-CRIT: New Customer Drop
- [ ] CUST-002-WARN: High Value Customer Churn
- [ ] CUST-003-WARN: Business Customer Decline
- [ ] CUST-004-INFO: Customer Growth Summary

---

## References

- [Databricks SQL Alerts](https://docs.databricks.com/sql/user/alerts/)
- [Alert Notifications](https://docs.databricks.com/sql/user/alerts/index.html#notifications)

