# TVF Schema Mapping Reference

**Source of Truth:** `gold_layer_design/yaml/**/*.yaml`

This document maps the actual Gold layer schema to guide TVF development.

---

## Dimensions

### dim_destination
```yaml
Columns:
  - destination_id (BIGINT, PK)
  - destination (STRING) # City/area name
  - country (STRING)
  - state_or_province (STRING, nullable)
  - state_or_province_code (STRING, nullable)
  - description (STRING, nullable)
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)
```

**Key Notes:**
- ❌ NO `city` column → Use `destination`
- ❌ NO `state` column → Use `state_or_province`
- SCD Type 1 (no is_current, effective_from/to)

### dim_property
```yaml
Columns:
  - property_key (STRING, PK - surrogate)
  - property_id (BIGINT, business key)
  - host_id (BIGINT, FK)
  - destination_id (BIGINT, FK)
  - title (STRING)
  - property_type (STRING)
  - base_price (FLOAT)
  - bedrooms (INT)
  - bathrooms (INT)
  - max_guests (INT)
  - property_latitude (DOUBLE, nullable)
  - property_longitude (DOUBLE, nullable)
  - description (STRING, nullable)
  - effective_from (TIMESTAMP)
  - effective_to (TIMESTAMP, nullable)
  - is_current (BOOLEAN)
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)
```

**Key Notes:**
- SCD Type 2 (has is_current, effective_from/to)
- Join on `property_id` with `is_current = true` filter

### dim_host
```yaml
Columns:
  - host_key (STRING, PK - surrogate)
  - host_id (BIGINT, business key)
  - name (STRING)
  - email (STRING)
  - phone (STRING, nullable)
  - country (STRING)
  - is_verified (BOOLEAN)
  - is_active (BOOLEAN)
  - rating (FLOAT)
  - joined_at (TIMESTAMP)
  - effective_from (TIMESTAMP)
  - effective_to (TIMESTAMP, nullable)
  - is_current (BOOLEAN)
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)
```

**Key Notes:**
- SCD Type 2 (has is_current, effective_from/to)
- Join on `host_id` with `is_current = true` filter

### dim_user
```yaml
Columns:
  - user_key (STRING, PK - surrogate)
  - user_id (BIGINT, business key)
  - email (STRING)
  - name (STRING)
  - country (STRING)
  - user_type (STRING)
  - is_business (BOOLEAN)
  - company_name (STRING, nullable)
  - joined_at (TIMESTAMP)
  - effective_from (TIMESTAMP)
  - effective_to (TIMESTAMP, nullable)
  - is_current (BOOLEAN)
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)
```

**Key Notes:**
- SCD Type 2 (has is_current, effective_from/to)
- Join on `user_id` with `is_current = true` filter

### dim_date
```yaml
Columns:
  - date (DATE, PK)
  - year (INT)
  - quarter (INT)
  - month (INT)
  - month_name (STRING)
  - week_of_year (INT)
  - day_of_month (INT)
  - day_of_week (INT)
  - day_of_week_name (STRING)
  - day_of_year (INT)
  - is_weekend (BOOLEAN)
  - is_holiday (BOOLEAN)
```

**Key Notes:**
- Type 1 (no is_current)
- Standard date dimension

---

## Facts

### fact_booking_daily
```yaml
Columns:
  - property_id (BIGINT, PK1, FK)
  - destination_id (BIGINT, FK)
  - check_in_date (DATE, PK2, FK)
  - booking_count (BIGINT)
  - confirmed_booking_count (BIGINT)
  - cancellation_count (BIGINT)
  - total_booking_value (DECIMAL(18,2))
  - avg_booking_value (DECIMAL(18,2))
  - total_guests (BIGINT)
  - avg_nights_booked (DECIMAL(10,2))
  - payment_completion_rate (DECIMAL(5,2))
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)

Grain: One row per property_id per check_in_date (daily aggregate)
Primary Key: (property_id, check_in_date) composite
```

**Key Notes:**
- ❌ NO `status` column - This is aggregated data
- ❌ NO `host_id` - Must join through dim_property
- Pre-aggregated metrics already calculated

### fact_booking_detail
```yaml
Columns:
  - booking_id (BIGINT, PK)
  - user_id (BIGINT, FK)
  - host_id (BIGINT, FK)
  - property_id (BIGINT, FK)
  - destination_id (BIGINT, FK)
  - check_in_date (DATE, FK)
  - check_out_date (DATE)
  - guests_count (INT)
  - nights_booked (INT)
  - total_amount (DECIMAL(18,2))
  - payment_amount (DECIMAL(18,2), nullable)
  - payment_method (STRING, nullable)
  - status (STRING) # 'pending', 'confirmed', 'cancelled', 'completed'
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)
  - days_between_booking_and_checkin (INT)
  - is_cancelled (BOOLEAN)
  - is_business_booking (BOOLEAN)
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)

Grain: One row per booking_id (transaction level)
Primary Key: booking_id
```

**Key Notes:**
- Has `status` column for booking lifecycle
- Has `host_id` denormalized for query performance
- Has `is_cancelled` boolean flag

### fact_property_engagement
```yaml
Columns:
  - property_id (BIGINT, PK1, FK)
  - engagement_date (DATE, PK2, FK)
  - view_count (BIGINT)
  - unique_user_views (BIGINT)
  - click_count (BIGINT)
  - search_count (BIGINT)
  - conversion_rate (DECIMAL(5,2))
  - avg_time_on_page (DECIMAL(10,2), nullable)
  - record_created_timestamp (TIMESTAMP)
  - record_updated_timestamp (TIMESTAMP)

Grain: One row per property_id per engagement_date (daily aggregate)
Primary Key: (property_id, engagement_date) composite
```

---

## Common TVF Join Patterns

### Get Property with Destination
```sql
FROM fact_booking_daily fbd
LEFT JOIN dim_property dp 
  ON fbd.property_id = dp.property_id 
  AND dp.is_current = true
LEFT JOIN dim_destination dd 
  ON fbd.destination_id = dd.destination_id

-- Access:
dp.title -- property name
dp.property_type
dd.destination -- city/area name (NOT dd.city)
dd.state_or_province -- state (NOT dd.state)
dd.country
```

### Get Booking with All Dimensions
```sql
FROM fact_booking_detail fbd
LEFT JOIN dim_user du 
  ON fbd.user_id = du.user_id 
  AND du.is_current = true
LEFT JOIN dim_host dh 
  ON fbd.host_id = dh.host_id 
  AND dh.is_current = true
LEFT JOIN dim_property dp 
  ON fbd.property_id = dp.property_id 
  AND dp.is_current = true
LEFT JOIN dim_destination dd 
  ON fbd.destination_id = dd.destination_id

-- Access:
fbd.status -- booking status (detail table only)
fbd.is_cancelled -- boolean flag
du.name -- user name
dh.name -- host name
dp.title -- property name
dd.destination, dd.state_or_province, dd.country
```

---

## TVF Corrections Needed

### Replace These Patterns:

```sql
# ❌ WRONG
dd.city
dd.state
CONCAT(dd.city, ', ', dd.state, ', ', dd.country)

# ✅ CORRECT
dd.destination
dd.state_or_province
CONCAT(dd.destination, ', ', dd.state_or_province, ', ', dd.country)
```

```sql
# ❌ WRONG (fact_booking_daily doesn't have status)
fbd.status FROM fact_booking_daily

# ✅ CORRECT (use fact_booking_detail for status)
fbd.status FROM fact_booking_detail
```

---

## Validation Queries

```sql
-- Verify dimension columns
DESCRIBE TABLE dim_destination;
DESCRIBE TABLE dim_property;
DESCRIBE TABLE dim_host;
DESCRIBE TABLE dim_user;

-- Verify fact columns
DESCRIBE TABLE fact_booking_daily;
DESCRIBE TABLE fact_booking_detail;
DESCRIBE TABLE fact_property_engagement;
```

---

**Last Updated:** December 2025  
**Source:** gold_layer_design/yaml/**/*.yaml

