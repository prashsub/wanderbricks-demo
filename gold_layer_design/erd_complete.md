# Wanderbricks Gold Layer - Entity Relationship Diagram

## Complete Dimensional Model

This ERD shows the complete Wanderbricks Gold layer dimensional model with all dimensions, facts, and relationships.

```mermaid
erDiagram
    dim_user ||--o{ fact_booking_detail : "user_id"
    dim_host ||--o{ fact_booking_detail : "host_id"
    dim_property ||--o{ fact_booking_detail : "property_id"
    dim_property ||--o{ fact_booking_daily : "property_id"
    dim_property ||--o{ fact_property_engagement : "property_id"
    dim_destination ||--o{ fact_booking_detail : "destination_id"
    dim_destination ||--o{ fact_booking_daily : "destination_id"
    dim_destination ||--o{ dim_property : "destination_id"
    dim_date ||--o{ fact_booking_detail : "check_in_date"
    dim_date ||--o{ fact_booking_daily : "check_in_date"
    dim_date ||--o{ fact_property_engagement : "engagement_date"
    
    dim_user {
        string user_key PK "Surrogate key (SCD Type 2)"
        bigint user_id UK "Business key"
        string email "User email address"
        string name "User full name"
        string country "Country of residence"
        string user_type "individual or business"
        boolean is_business "Business account flag"
        string company_name "Company name if business"
        date created_at "Account creation date"
        timestamp effective_from "SCD Type 2 start"
        timestamp effective_to "SCD Type 2 end (NULL = current)"
        boolean is_current "Current version flag"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
    
    dim_host {
        string host_key PK "Surrogate key (SCD Type 2)"
        bigint host_id UK "Business key"
        string name "Host full name"
        string email "Host email address"
        string phone "Host phone number"
        boolean is_verified "Verification status"
        boolean is_active "Active status"
        float rating "Host rating (1.0-5.0)"
        string country "Host country"
        date joined_at "Platform join date"
        timestamp effective_from "SCD Type 2 start"
        timestamp effective_to "SCD Type 2 end (NULL = current)"
        boolean is_current "Current version flag"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
    
    dim_property {
        string property_key PK "Surrogate key (SCD Type 2)"
        bigint property_id UK "Business key"
        bigint host_id FK "→ dim_host"
        bigint destination_id FK "→ dim_destination"
        string title "Property listing title"
        string description "Property description"
        float base_price "Base nightly price"
        string property_type "house, apartment, etc."
        int max_guests "Maximum guests allowed"
        int bedrooms "Number of bedrooms"
        int bathrooms "Number of bathrooms"
        float property_latitude "Latitude coordinates"
        float property_longitude "Longitude coordinates"
        date created_at "Listing creation date"
        timestamp effective_from "SCD Type 2 start"
        timestamp effective_to "SCD Type 2 end (NULL = current)"
        boolean is_current "Current version flag"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
    
    dim_destination {
        bigint destination_id PK "Primary key"
        string destination "Destination name"
        string country "Country name"
        string state_or_province "State or province"
        string state_or_province_code "State/province code"
        string description "Destination description"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
    
    dim_date {
        date date PK "Calendar date"
        int year "Calendar year (YYYY)"
        int quarter "Calendar quarter (1-4)"
        int month "Calendar month (1-12)"
        string month_name "Month name (January, etc.)"
        int week_of_year "ISO week of year (1-53)"
        int day_of_week "Day of week (1=Sunday)"
        string day_of_week_name "Day name (Monday, etc.)"
        int day_of_month "Day of month (1-31)"
        int day_of_year "Day of year (1-366)"
        boolean is_weekend "Weekend indicator"
        boolean is_holiday "Holiday indicator"
    }
    
    fact_booking_detail {
        bigint booking_id PK "Primary key"
        bigint user_id FK "→ dim_user"
        bigint host_id FK "→ dim_host"
        bigint property_id FK "→ dim_property"
        bigint destination_id FK "→ dim_destination"
        date check_in_date FK "→ dim_date"
        date check_out_date "Checkout date"
        int guests_count "Number of guests"
        int nights_booked "Number of nights"
        decimal total_amount "Total booking amount"
        decimal payment_amount "Payment received"
        string payment_method "Payment method"
        string status "Booking status"
        timestamp created_at "Booking creation timestamp"
        timestamp updated_at "Last update timestamp"
        int days_between_booking_and_checkin "Lead time metric"
        boolean is_cancelled "Cancellation flag"
        boolean is_business_booking "Business vs leisure flag"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
    
    fact_booking_daily {
        bigint property_id FK "→ dim_property"
        bigint destination_id FK "→ dim_destination"
        date check_in_date FK "→ dim_date"
        bigint booking_count "Number of bookings"
        decimal total_booking_value "Sum of booking amounts"
        decimal avg_booking_value "Average booking value"
        bigint total_guests "Total guest count"
        decimal avg_nights_booked "Average nights per booking"
        bigint cancellation_count "Cancelled bookings"
        bigint confirmed_booking_count "Confirmed bookings"
        decimal payment_completion_rate "Payment success rate"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
    
    fact_property_engagement {
        bigint property_id FK "→ dim_property"
        date engagement_date FK "→ dim_date"
        bigint view_count "Total property views"
        bigint unique_user_views "Distinct users viewing"
        bigint click_count "Total clicks"
        bigint search_count "Search appearances"
        decimal conversion_rate "Bookings / Views ratio"
        decimal avg_time_on_page "Average engagement time"
        timestamp record_created_timestamp "Gold audit field"
        timestamp record_updated_timestamp "Gold audit field"
    }
```

## Relationship Summary

### One-to-Many Relationships

| Parent (One) | Child (Many) | Foreign Key | Cardinality |
|---|---|---|---|
| dim_user | fact_booking_detail | user_id | 1:N |
| dim_host | fact_booking_detail | host_id | 1:N |
| dim_host | dim_property | host_id | 1:N |
| dim_property | fact_booking_detail | property_id | 1:N |
| dim_property | fact_booking_daily | property_id | 1:N |
| dim_property | fact_property_engagement | property_id | 1:N |
| dim_destination | fact_booking_detail | destination_id | 1:N |
| dim_destination | fact_booking_daily | destination_id | 1:N |
| dim_destination | dim_property | destination_id | 1:N |
| dim_date | fact_booking_detail | check_in_date | 1:N |
| dim_date | fact_booking_daily | check_in_date | 1:N |
| dim_date | fact_property_engagement | engagement_date | 1:N |

### Key Observations

1. **dim_property is central** - Referenced by all three fact tables
2. **dim_date enables time-based analysis** - All facts have date FK
3. **dim_destination appears twice** - Both in facts and as property attribute
4. **Type 2 dimensions use surrogate keys** - But facts reference business keys
5. **fact_booking_daily is derived** - Can be computed from fact_booking_detail

## Grain Validation

### fact_booking_detail
- **Primary Key:** booking_id
- **Grain:** One row per individual booking transaction
- **Uniqueness:** Each booking_id appears exactly once

### fact_booking_daily
- **Composite Primary Key:** (property_id, check_in_date)
- **Grain:** One row per property per check-in date
- **Uniqueness:** Each property-date combination appears exactly once

### fact_property_engagement
- **Composite Primary Key:** (property_id, engagement_date)
- **Grain:** One row per property per engagement date
- **Uniqueness:** Each property-date combination appears exactly once

## Design Notes

### SCD Type 2 Implementation

**Surrogate Keys (for facts):**
- dim_user.user_key (MD5 hash of user_id + effective_from)
- dim_host.host_key (MD5 hash of host_id + effective_from)
- dim_property.property_key (MD5 hash of property_id + effective_from)

**Business Keys (for facts):**
- Facts reference business keys (user_id, host_id, property_id)
- Simplifies queries: no need to join on surrogate keys
- Point-in-time joins use is_current flag or effective_from/to

### Degenerate Dimensions

Some attributes stored directly in facts (not separate dimensions):
- **status** (in fact_booking_detail) - Booking status changes frequently
- **payment_method** (in fact_booking_detail) - Low cardinality, not analyzed independently

### Derived Metrics

Pre-calculated in fact tables for performance:
- **nights_booked** = DATEDIFF(check_out_date, check_in_date)
- **days_between_booking_and_checkin** = DATEDIFF(check_in_date, created_at)
- **conversion_rate** = bookings / views * 100

## Query Patterns

### Revenue by Destination
```sql
SELECT 
  d.destination,
  d.country,
  SUM(f.total_booking_value) as total_revenue,
  SUM(f.booking_count) as total_bookings
FROM fact_booking_daily f
JOIN dim_destination d ON f.destination_id = d.destination_id
JOIN dim_date dt ON f.check_in_date = dt.date
WHERE dt.year = 2024
GROUP BY d.destination, d.country
ORDER BY total_revenue DESC;
```

### Host Performance
```sql
SELECT 
  h.name as host_name,
  h.rating,
  h.is_verified,
  COUNT(DISTINCT f.booking_id) as total_bookings,
  SUM(f.total_amount) as total_revenue
FROM fact_booking_detail f
JOIN dim_host h ON f.host_id = h.host_id AND h.is_current = true
GROUP BY h.name, h.rating, h.is_verified
ORDER BY total_revenue DESC;
```

### Property Engagement Funnel
```sql
SELECT 
  p.title as property_title,
  SUM(e.view_count) as total_views,
  SUM(e.click_count) as total_clicks,
  COUNT(DISTINCT b.booking_id) as total_bookings,
  (COUNT(DISTINCT b.booking_id) / NULLIF(SUM(e.view_count), 0)) * 100 as view_to_booking_rate
FROM fact_property_engagement e
JOIN dim_property p ON e.property_id = p.property_id AND p.is_current = true
LEFT JOIN fact_booking_detail b ON e.property_id = b.property_id
GROUP BY p.title
ORDER BY total_views DESC;
```

