# Column-Level Lineage: Bronze → Silver → Gold

**Generated:** 2025-12-09 19:13:46  
**Project:** Wanderbricks  
**Total Tables:** 8  

## Purpose

This document provides complete column-level data lineage from Bronze through Gold layer, including transformation logic for every column. Use this as reference when implementing Gold merge scripts to prevent schema mismatches.

## Legend

| Emoji | Transformation Type |
|---|---|
| 📋 | Direct Copy (no transformation) |
| ✏️ | Rename (column name changed) |
| 🔄 | Cast (data type conversion) |
| ➕ | Aggregate SUM |
| ➕❓ | Aggregate SUM (conditional) |
| 🔢 | Aggregate COUNT |
| 🔢❓ | Aggregate COUNT (conditional) |
| 📊 | Aggregate AVG |
| 🧮 | Derived Calculation |
| 🔀 | Derived Conditional (CASE/WHEN) |
| 🔐 | MD5 Hash |
| 🔒 | SHA256 Hash |
| 🛡️ | Coalesce (null handling) |
| 📅 | Date Truncation |
| ⚙️ | Generated (not from source) |
| 🔍 | Lookup (from dimension join) |

---

## Table: `fact_booking_daily`
**Grain:** One row per property_id per check_in_date (daily aggregate)  
**Domain:** booking  
**Bronze Source:** bookings, payments (aggregated from fact_booking_detail)  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `property_id` | BIGINT | bronze_booking_fact.property_id | silver_booking_fact.property_id | 📋 DIRECT_COPY | `col('property_id')` | Part of daily aggregation grain |
| `destination_id` | BIGINT | bronze_property_dim.destination_id | silver_booking_fact (joined from dim_property).destination_id | 🔍 LOOKUP | `Retrieved via join with dim_property on property_id` | Denormalized from dimension for performance |
| `check_in_date` | DATE | bronze_booking_fact.check_in_timestamp | silver_booking_fact.check_in_timestamp | 📅 DATE_TRUNC | `date_trunc('day', col('check_in_timestamp')).cast('date')` | Part of daily aggregation grain, truncated from timestamp |
| `booking_count` | BIGINT | bronze_booking_fact.booking_id | silver_booking_fact.booking_id | 🔢 AGGREGATE_COUNT | `count('*')` |  |
| `confirmed_booking_count` | BIGINT | bronze_booking_fact.booking_id, status | silver_booking_fact.booking_id, status | 🔢❓ AGGREGATE_COUNT_CONDITIONAL | `spark_sum(when(col('status') == 'confirmed', 1).otherwise(0))` |  |
| `cancellation_count` | BIGINT | bronze_booking_fact.booking_id, status | silver_booking_fact.booking_id, status | 🔢❓ AGGREGATE_COUNT_CONDITIONAL | `spark_sum(when(col('status') == 'cancelled', 1).otherwise(0))` |  |
| `total_booking_value` | DECIMAL(18,2) | bronze_booking_fact.total_amount | silver_booking_fact.total_amount | ➕ AGGREGATE_SUM | `spark_sum('total_amount')` |  |
| `avg_booking_value` | DECIMAL(18,2) | bronze_booking_fact.total_amount | silver_booking_fact.total_amount | 📊 AGGREGATE_AVG | `avg('total_amount')` |  |
| `total_guests` | BIGINT | bronze_booking_fact.guests_count | silver_booking_fact.guests_count | ➕ AGGREGATE_SUM | `spark_sum('guests_count')` |  |
| `avg_nights_booked` | DECIMAL(10,2) | bronze_booking_fact.nights_booked | silver_booking_fact.nights_booked | 📊 AGGREGATE_AVG | `avg('nights_booked')` |  |
| `payment_completion_rate` | DECIMAL(5,2) | bronze_payment_fact.payment_amount | silver_booking_fact (joined from payment_fact).payment_amount | 🧮 DERIVED_CALCULATION | `(spark_sum(when(col('payment_amount').isNotNull(), 1).otherwise(0)) / count('*') * 100)` | Percentage calculation based on payment completion |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

### Aggregation Details

**Grain:** `GROUP BY (property_id, check_in_date)`

**Aggregated Measures:** `booking_count`, `confirmed_booking_count`, `cancellation_count`, `total_booking_value`, `avg_booking_value`, `total_guests`, `avg_nights_booked`

---

## Table: `fact_booking_detail`
**Grain:** One row per booking_id (transaction level - individual booking)  
**Domain:** booking  
**Bronze Source:** bookings, payments, booking_updates  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `booking_id` | BIGINT | bronze_booking_fact.booking_id | silver_booking_fact.booking_id | 📋 DIRECT_COPY | `col('booking_id')` | Primary key, natural key from source |
| `user_id` | BIGINT | bronze_booking_fact.user_id | silver_booking_fact.user_id | 📋 DIRECT_COPY | `col('user_id')` |  |
| `host_id` | BIGINT | bronze_property_dim (joined).host_id | silver_booking_fact (joined from dim_property).host_id | 🔍 LOOKUP | `Retrieved via join with dim_property on property_id` | Denormalized from property for query simplicity |
| `property_id` | BIGINT | bronze_booking_fact.property_id | silver_booking_fact.property_id | 📋 DIRECT_COPY | `col('property_id')` |  |
| `destination_id` | BIGINT | bronze_property_dim (joined).destination_id | silver_booking_fact (joined from dim_property).destination_id | 🔍 LOOKUP | `Retrieved via join with dim_property on property_id` | Denormalized from property for query performance |
| `check_in_date` | DATE | bronze_booking_fact.check_in_timestamp | silver_booking_fact.check_in_timestamp | 🔄 CAST | `col('check_in_timestamp').cast('date')` |  |
| `check_out_date` | DATE | bronze_booking_fact.check_out_timestamp | silver_booking_fact.check_out_timestamp | 🔄 CAST | `col('check_out_timestamp').cast('date')` |  |
| `guests_count` | INT | bronze_booking_fact.guests_count | silver_booking_fact.guests_count | 📋 DIRECT_COPY | `col('guests_count')` |  |
| `nights_booked` | INT | bronze_booking_fact.check_in_timestamp, check_out_timestamp | silver_booking_fact.check_in_timestamp, check_out_timestamp | 🧮 DERIVED_CALCULATION | `datediff(col('check_out_timestamp').cast('date'), col('check_in_timestamp').cast('date'))` | Pre-calculated for performance |
| `total_amount` | DECIMAL(18,2) | bronze_booking_fact.total_amount | silver_booking_fact.total_amount | 📋 DIRECT_COPY | `col('total_amount')` |  |
| `payment_amount` | DECIMAL(18,2) | bronze_payment_fact.payment_amount | silver_booking_fact (joined from payment_fact).payment_amount | 🔍 LOOKUP | `Retrieved via left join with payment_fact on booking_id` | NULL for pending/unpaid bookings |
| `payment_method` | STRING | bronze_payment_fact.payment_method | silver_booking_fact (joined from payment_fact).payment_method | 🔍 LOOKUP | `Retrieved via left join with payment_fact on booking_id` | NULL for pending/unpaid bookings |
| `status` | STRING | bronze_booking_fact.status | silver_booking_fact.status | 📋 DIRECT_COPY | `col('status')` |  |
| `created_at` | TIMESTAMP | bronze_booking_fact.created_at | silver_booking_fact.created_at | 📋 DIRECT_COPY | `col('created_at')` |  |
| `updated_at` | TIMESTAMP | bronze_booking_updates.updated_at | silver_booking_fact.updated_at | 📋 DIRECT_COPY | `col('updated_at')` | Latest timestamp from booking_updates |
| `days_between_booking_and_checkin` | INT | N/A | N/A | 🧮 DERIVED_CALCULATION | `datediff(col('check_in_timestamp').cast('date'), col('created_at').cast('date'))` | Lead time metric, can be negative for same-day bookings |
| `is_cancelled` | BOOLEAN | bronze_booking_fact.status | silver_booking_fact.status | 🔀 DERIVED_CONDITIONAL | `when(col('status') == 'cancelled', True).otherwise(False)` | Boolean flag for cancellation filtering |
| `is_business_booking` | BOOLEAN | bronze_user_dim (joined).user_type | silver_booking_fact (joined from dim_user).is_business | 🔍 LOOKUP | `Retrieved via join with dim_user on user_id where is_current = true` | Denormalized from user dimension for query performance |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

---

## Table: `fact_property_engagement`
**Grain:** One row per property_id per engagement_date (daily aggregate)  
**Domain:** engagement  
**Bronze Source:** page_views, clickstream  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `property_id` | BIGINT | bronze_page_views.property_id | silver_page_views.property_id | 📋 DIRECT_COPY | `col('property_id')` | Part of daily aggregation grain |
| `engagement_date` | DATE | bronze_page_views.event_timestamp | silver_page_views.event_timestamp | 📅 DATE_TRUNC | `date_trunc('day', col('event_timestamp')).cast('date')` | Part of daily aggregation grain, truncated from timestamp |
| `view_count` | BIGINT | bronze_page_views.view_id | silver_page_views.view_id | 🔢 AGGREGATE_COUNT | `count('*')` |  |
| `unique_user_views` | BIGINT | bronze_page_views.user_id | silver_page_views.user_id | 🔢 AGGREGATE_COUNT | `countDistinct('user_id')` |  |
| `click_count` | BIGINT | bronze_clickstream.event_id | silver_clickstream.event_id | 🔢❓ AGGREGATE_COUNT_CONDITIONAL | `spark_sum(when(col('event_type') == 'click', 1).otherwise(0))` |  |
| `search_count` | BIGINT | bronze_clickstream.event_id | silver_clickstream.event_id | 🔢❓ AGGREGATE_COUNT_CONDITIONAL | `spark_sum(when(col('event_type') == 'search', 1).otherwise(0))` |  |
| `conversion_rate` | DECIMAL(5,2) | N/A (derived from fact_booking_daily).N/A | N/A | 🧮 DERIVED_CALCULATION | `(bookings_count / NULLIF(view_count, 0)) * 100` | Calculated by joining with fact_booking_daily |
| `avg_time_on_page` | DECIMAL(10,2) | bronze_page_views.time_spent_seconds | silver_page_views.time_spent_seconds | 📊 AGGREGATE_AVG | `avg('time_spent_seconds')` | NULL values excluded from average |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

### Aggregation Details

**Grain:** `GROUP BY (property_id, engagement_date)`

**Aggregated Measures:** `view_count`, `unique_user_views`, `click_count`, `search_count`, `avg_time_on_page`

---

## Table: `dim_destination`
**Grain:** One row per destination (city/area within country)  
**Domain:** geography  
**Bronze Source:** destinations  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `destination_id` | BIGINT | bronze_destination_dim.destination_id | silver_destination_dim.destination_id | 📋 DIRECT_COPY | `col('destination_id')` |  |
| `destination` | STRING | bronze_destination_dim.destination | silver_destination_dim.destination | 📋 DIRECT_COPY | `col('destination')` |  |
| `country` | STRING | bronze_destination_dim.country | silver_destination_dim.country | 📋 DIRECT_COPY | `col('country')` |  |
| `state_or_province` | STRING | bronze_destination_dim.state_or_province | silver_destination_dim.state_or_province | 📋 DIRECT_COPY | `col('state_or_province')` |  |
| `state_or_province_code` | STRING | bronze_destination_dim.state_or_province_code | silver_destination_dim.state_or_province_code | 📋 DIRECT_COPY | `col('state_or_province_code')` |  |
| `description` | STRING | bronze_destination_dim.description | silver_destination_dim.description | 📋 DIRECT_COPY | `col('description')` |  |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

---

## Table: `dim_host`
**Grain:** One row per host_id per version (SCD Type 2)  
**Domain:** identity  
**Bronze Source:** hosts  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `host_key` | STRING | bronze_host_dim.host_id, processed_timestamp | silver_host_dim.host_id, processed_timestamp | 🔐 HASH_MD5 | `md5(concat_ws('||', col('host_id'), col('processed_timestamp')))` | Surrogate key for SCD Type 2, ensures uniqueness across versions |
| `host_id` | BIGINT | bronze_host_dim.host_id | silver_host_dim.host_id | 📋 DIRECT_COPY | `col('host_id')` | Business key, same across all versions |
| `name` | STRING | bronze_host_dim.name | silver_host_dim.name | 📋 DIRECT_COPY | `col('name')` |  |
| `email` | STRING | bronze_host_dim.email | silver_host_dim.email | 📋 DIRECT_COPY | `col('email')` |  |
| `phone` | STRING | bronze_host_dim.phone | silver_host_dim.phone | 📋 DIRECT_COPY | `col('phone')` |  |
| `is_verified` | BOOLEAN | bronze_host_dim.is_verified | silver_host_dim.is_verified | 📋 DIRECT_COPY | `col('is_verified')` |  |
| `is_active` | BOOLEAN | bronze_host_dim.is_active | silver_host_dim.is_active | 📋 DIRECT_COPY | `col('is_active')` |  |
| `rating` | FLOAT | bronze_host_dim.rating | silver_host_dim.rating | 📋 DIRECT_COPY | `col('rating')` |  |
| `country` | STRING | bronze_host_dim.country | silver_host_dim.country | 📋 DIRECT_COPY | `col('country')` |  |
| `joined_at` | DATE | bronze_host_dim.joined_at_timestamp | silver_host_dim.joined_at_timestamp | 🔄 CAST | `col('joined_at_timestamp').cast('date')` | Cast from timestamp to date, immutable across versions |
| `effective_from` | TIMESTAMP | bronze_host_dim.processed_timestamp | silver_host_dim.processed_timestamp | 📋 DIRECT_COPY | `col('processed_timestamp')` | SCD Type 2 field, marks version start |
| `effective_to` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `lit(None).cast('timestamp')` | SCD Type 2 field, NULL for current version, set when superseded |
| `is_current` | BOOLEAN | N/A | N/A | ⚙️ GENERATED | `lit(True)` | SCD Type 2 flag, TRUE for current version |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

---

## Table: `dim_user`
**Grain:** One row per user_id per version (SCD Type 2)  
**Domain:** identity  
**Bronze Source:** users  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `user_key` | STRING | bronze_user_dim.user_id, processed_timestamp | silver_user_dim.user_id, processed_timestamp | 🔐 HASH_MD5 | `md5(concat_ws('||', col('user_id'), col('processed_timestamp')))` | Surrogate key for SCD Type 2, ensures uniqueness across versions |
| `user_id` | BIGINT | bronze_user_dim.user_id | silver_user_dim.user_id | 📋 DIRECT_COPY | `col('user_id')` | Business key, same across all versions |
| `email` | STRING | bronze_user_dim.email | silver_user_dim.email | 📋 DIRECT_COPY | `col('email')` |  |
| `name` | STRING | bronze_user_dim.name | silver_user_dim.name | 📋 DIRECT_COPY | `col('name')` |  |
| `country` | STRING | bronze_user_dim.country | silver_user_dim.country | 📋 DIRECT_COPY | `col('country')` |  |
| `user_type` | STRING | bronze_user_dim.user_type | silver_user_dim.user_type | 📋 DIRECT_COPY | `col('user_type')` |  |
| `is_business` | BOOLEAN | bronze_user_dim.user_type | silver_user_dim.user_type | 🔀 DERIVED_CONDITIONAL | `when(col('user_type') == 'business', True).otherwise(False)` | Derived boolean flag from user_type enumeration |
| `company_name` | STRING | bronze_user_dim.company_name | silver_user_dim.company_name | 📋 DIRECT_COPY | `col('company_name')` |  |
| `created_at` | DATE | bronze_user_dim.created_at_timestamp | silver_user_dim.created_at_timestamp | 🔄 CAST | `col('created_at_timestamp').cast('date')` | Cast from timestamp to date, immutable across versions |
| `effective_from` | TIMESTAMP | bronze_user_dim.processed_timestamp | silver_user_dim.processed_timestamp | 📋 DIRECT_COPY | `col('processed_timestamp')` | SCD Type 2 field, marks version start |
| `effective_to` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `lit(None).cast('timestamp')` | SCD Type 2 field, NULL for current version, set when superseded |
| `is_current` | BOOLEAN | N/A | N/A | ⚙️ GENERATED | `lit(True)` | SCD Type 2 flag, TRUE for current version |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

---

## Table: `dim_property`
**Grain:** One row per property_id per version (SCD Type 2)  
**Domain:** property  
**Bronze Source:** properties  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `property_key` | STRING | bronze_property_dim.property_id, processed_timestamp | silver_property_dim.property_id, processed_timestamp | 🔐 HASH_MD5 | `md5(concat_ws('||', col('property_id'), col('processed_timestamp')))` | Surrogate key for SCD Type 2, ensures uniqueness across versions |
| `property_id` | BIGINT | bronze_property_dim.property_id | silver_property_dim.property_id | 📋 DIRECT_COPY | `col('property_id')` | Business key, same across all versions |
| `host_id` | BIGINT | bronze_property_dim.host_id | silver_property_dim.host_id | 📋 DIRECT_COPY | `col('host_id')` |  |
| `destination_id` | BIGINT | bronze_property_dim.destination_id | silver_property_dim.destination_id | 📋 DIRECT_COPY | `col('destination_id')` |  |
| `title` | STRING | bronze_property_dim.title | silver_property_dim.title | 📋 DIRECT_COPY | `col('title')` |  |
| `description` | STRING | bronze_property_dim.description | silver_property_dim.description | 📋 DIRECT_COPY | `col('description')` |  |
| `base_price` | FLOAT | bronze_property_dim.base_price | silver_property_dim.base_price | 📋 DIRECT_COPY | `col('base_price')` |  |
| `property_type` | STRING | bronze_property_dim.property_type | silver_property_dim.property_type | 📋 DIRECT_COPY | `col('property_type')` |  |
| `max_guests` | INT | bronze_property_dim.max_guests | silver_property_dim.max_guests | 📋 DIRECT_COPY | `col('max_guests')` |  |
| `bedrooms` | INT | bronze_property_dim.bedrooms | silver_property_dim.bedrooms | 📋 DIRECT_COPY | `col('bedrooms')` |  |
| `bathrooms` | INT | bronze_property_dim.bathrooms | silver_property_dim.bathrooms | 📋 DIRECT_COPY | `col('bathrooms')` |  |
| `property_latitude` | FLOAT | bronze_property_dim.latitude | silver_property_dim.latitude | 📋 DIRECT_COPY | `col('latitude')` |  |
| `property_longitude` | FLOAT | bronze_property_dim.longitude | silver_property_dim.longitude | 📋 DIRECT_COPY | `col('longitude')` |  |
| `created_at` | DATE | bronze_property_dim.created_at_timestamp | silver_property_dim.created_at_timestamp | 🔄 CAST | `col('created_at_timestamp').cast('date')` | Cast from timestamp to date, immutable across versions |
| `effective_from` | TIMESTAMP | bronze_property_dim.processed_timestamp | silver_property_dim.processed_timestamp | 📋 DIRECT_COPY | `col('processed_timestamp')` | SCD Type 2 field, marks version start |
| `effective_to` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `lit(None).cast('timestamp')` | SCD Type 2 field, NULL for current version, set when superseded |
| `is_current` | BOOLEAN | N/A | N/A | ⚙️ GENERATED | `lit(True)` | SCD Type 2 flag, TRUE for current version |
| `record_created_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Generated during Gold MERGE INSERT, never updated |
| `record_updated_timestamp` | TIMESTAMP | N/A | N/A | ⚙️ GENERATED | `current_timestamp()` | Updated on every MERGE operation |

---

## Table: `dim_date`
**Grain:** One row per calendar date  
**Domain:** time  
**Bronze Source:** generated  

| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |
|---|---|---|---|---|---|---|
| `date` | DATE | N/A | N/A | ⚙️ GENERATED | `SEQUENCE(start_date, end_date, INTERVAL 1 DAY)` | Primary key generated from date sequence |
| `year` | INT | N/A | N/A | ⚙️ GENERATED | `YEAR(date)` |  |
| `quarter` | INT | N/A | N/A | ⚙️ GENERATED | `QUARTER(date)` |  |
| `month` | INT | N/A | N/A | ⚙️ GENERATED | `MONTH(date)` |  |
| `month_name` | STRING | N/A | N/A | ⚙️ GENERATED | `DATE_FORMAT(date, 'MMMM')` |  |
| `week_of_year` | INT | N/A | N/A | ⚙️ GENERATED | `WEEKOFYEAR(date)` |  |
| `day_of_week` | INT | N/A | N/A | ⚙️ GENERATED | `DAYOFWEEK(date)` |  |
| `day_of_week_name` | STRING | N/A | N/A | ⚙️ GENERATED | `DATE_FORMAT(date, 'EEEE')` |  |
| `day_of_month` | INT | N/A | N/A | ⚙️ GENERATED | `DAY(date)` |  |
| `day_of_year` | INT | N/A | N/A | ⚙️ GENERATED | `DAYOFYEAR(date)` |  |
| `is_weekend` | BOOLEAN | N/A | N/A | ⚙️ GENERATED | `CASE WHEN DAYOFWEEK(date) IN (1, 7) THEN true ELSE false END` |  |
| `is_holiday` | BOOLEAN | N/A | N/A | ⚙️ GENERATED | `false` | Default to false, can be updated from holiday calendar lookup |

---

