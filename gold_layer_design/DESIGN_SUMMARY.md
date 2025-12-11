# Wanderbricks Gold Layer Design Summary

## Project Context

- **Project Name:** Wanderbricks (Vacation Rental Analytics Platform)
- **Silver Schema:** wanderbricks_silver
- **Gold Schema:** wanderbricks_gold
- **Business Domain:** Hospitality, Vacation Rentals, Travel Analytics

## Design Goals

- **Primary Use Cases:** 
  - Booking performance analysis and revenue tracking
  - Property engagement and conversion metrics
  - Host performance and review analysis
  - Customer behavior and segmentation
  
- **Key Stakeholders:** 
  - Revenue Management Team
  - Property Operations
  - Marketing & Growth
  - Customer Success
  
- **Reporting Frequency:** Daily aggregations with historical tracking

---

## Dimensional Model Design

### Dimensions (5 tables)

| # | Dimension Name | Business Key | SCD Type | Source Silver Table | Contains PII | Rationale |
|---|---------------|--------------|----------|---------------------|--------------|-----------|
| 1 | dim_user | user_id | Type 2 | silver_user_dim | Yes | Track user status changes, country changes over time |
| 2 | dim_host | host_id | Type 2 | silver_host_dim | Yes | Track host verification status, ratings, active status changes |
| 3 | dim_property | property_id | Type 2 | silver_property_dim | Yes | Track property price changes, status updates, listing modifications |
| 4 | dim_destination | destination_id | Type 1 | silver_destination_dim | No | Reference data - destinations rarely change |
| 5 | dim_date | date | Type 1 | Generated | No | Standard date dimension for time-based analysis |

### Facts (3 tables)

| # | Fact Name | Grain | Source Silver Tables | Update Frequency |
|---|-----------|-------|---------------------|------------------|
| 1 | fact_booking_daily | property-date | silver_bookings, silver_booking_updates, silver_payments | Daily |
| 2 | fact_booking_detail | booking-transaction | silver_bookings, silver_payments | Daily |
| 3 | fact_property_engagement | property-date | silver_page_views, silver_clickstream | Daily |

---

## Grain Definitions

### fact_booking_daily
**Grain:** One row per property_id per date (check-in date)

**Aggregated from:** Individual bookings grouped by property and check-in date

**Measures:**
- booking_count - Number of bookings
- total_booking_value - Sum of booking amounts
- avg_booking_value - Average booking value
- total_guests - Total guest count
- avg_nights_booked - Average nights per booking
- cancellation_count - Number of cancelled bookings
- confirmed_booking_count - Number of confirmed bookings

### fact_booking_detail
**Grain:** One row per booking_id (transaction level)

**Not aggregated:** Individual booking transactions with full detail

**Measures:**
- total_amount - Booking amount
- guests_count - Number of guests
- nights_booked - Number of nights
- payment_amount - Payment received
- days_between_booking_and_checkin - Lead time metric

### fact_property_engagement
**Grain:** One row per property_id per date (engagement date)

**Aggregated from:** Page views and clickstream events grouped by property and date

**Measures:**
- view_count - Total property views
- unique_user_views - Distinct users viewing
- click_count - Total clicks
- search_count - Times property appeared in search
- conversion_rate - Bookings / Views ratio

---

## SCD Type Decision Matrix

### Type 2 (Track History) - Chosen For:

**dim_user:**
- **Why Type 2:** User country changes, business status changes need historical tracking for market analysis
- **Tracked Attributes:** country, user_type, is_business, company_name
- **Business Value:** Understand user segmentation over time, track market expansion

**dim_host:**
- **Why Type 2:** Host rating changes, verification status, active status critical for quality tracking
- **Tracked Attributes:** rating, is_verified, is_active, country
- **Business Value:** Monitor host quality trends, verify platform trust metrics

**dim_property:**
- **Why Type 2:** Property price changes, availability, listing modifications impact revenue analysis
- **Tracked Attributes:** base_price, property_type, max_guests, bedrooms, bathrooms, listing status
- **Business Value:** Track pricing strategies, property improvements, market positioning

### Type 1 (Overwrite) - Chosen For:

**dim_destination:**
- **Why Type 1:** Destination attributes (descriptions, locations) rarely change, history not needed
- **Business Value:** Reference data for geographic analysis

**dim_date:**
- **Why Type 1:** Standard date dimension, generated data doesn't change
- **Business Value:** Time-based reporting and trending

---

## Measures & Metrics by Fact Table

### fact_booking_daily

| Measure Name | Data Type | Calculation Logic | Business Purpose |
|---|---|---|---|
| booking_count | BIGINT | COUNT(booking_id) | Volume of bookings per property per day |
| total_booking_value | DECIMAL(18,2) | SUM(total_amount) | Revenue by property by day |
| avg_booking_value | DECIMAL(18,2) | AVG(total_amount) | Average booking size |
| total_guests | BIGINT | SUM(guests_count) | Occupancy planning |
| avg_nights_booked | DECIMAL(10,2) | AVG(nights_booked) | Average length of stay |
| cancellation_count | BIGINT | COUNT(CASE status='cancelled') | Cancellation tracking |
| confirmed_booking_count | BIGINT | COUNT(CASE status='confirmed') | Conversion success |
| payment_completion_rate | DECIMAL(5,2) | COUNT(payment)/COUNT(booking)*100 | Payment success rate |

### fact_booking_detail

| Measure Name | Data Type | Calculation Logic | Business Purpose |
|---|---|---|---|
| total_amount | DECIMAL(18,2) | total_amount from booking | Transaction value |
| guests_count | INT | guests_count from booking | Occupancy |
| nights_booked | INT | DATEDIFF(check_out, check_in) | Length of stay |
| payment_amount | DECIMAL(18,2) | amount from payments | Payment received |
| days_between_booking_and_checkin | INT | DATEDIFF(check_in, created_at) | Booking lead time |
| is_cancelled | BOOLEAN | status = 'cancelled' | Cancellation flag |
| is_business_booking | BOOLEAN | user.is_business | Business vs leisure |

### fact_property_engagement

| Measure Name | Data Type | Calculation Logic | Business Purpose |
|---|---|---|---|
| view_count | BIGINT | COUNT(view_id) | Property impressions |
| unique_user_views | BIGINT | COUNT(DISTINCT user_id) | Unique audience |
| click_count | BIGINT | COUNT(event='click') | Engagement level |
| search_count | BIGINT | COUNT(event='search') | Search visibility |
| conversion_rate | DECIMAL(5,2) | bookings/views*100 | Property conversion |
| avg_time_on_page | DECIMAL(10,2) | AVG(time_spent) | Engagement depth |

---

## Relationships (FK Constraints)

### fact_booking_daily

| Dimension | FK Column | PK Column | Relationship |
|---|---|---|---|
| dim_property | property_id | property_id | Many-to-One |
| dim_destination | destination_id | destination_id | Many-to-One |
| dim_date | check_in_date | date | Many-to-One |

### fact_booking_detail

| Dimension | FK Column | PK Column | Relationship |
|---|---|---|---|
| dim_user | user_id | user_id | Many-to-One |
| dim_host | host_id | host_id | Many-to-One |
| dim_property | property_id | property_id | Many-to-One |
| dim_destination | destination_id | destination_id | Many-to-One |
| dim_date | check_in_date | date | Many-to-One |

### fact_property_engagement

| Dimension | FK Column | PK Column | Relationship |
|---|---|---|---|
| dim_property | property_id | property_id | Many-to-One |
| dim_date | engagement_date | date | Many-to-One |

**Relationship Rules:**
- Facts → Dimensions: Always Many-to-One
- Use business keys for FK references (not surrogate keys for Type 2 dimensions)
- All FK constraints are `NOT ENFORCED` (informational only)

---

## Design Decisions & Rationale

### 1. SCD Type 2 for User, Host, Property

**Decision:** Track historical changes for these dimensions

**Rationale:**
- **User:** Country migrations, business status changes affect market segmentation
- **Host:** Rating and verification changes critical for trust and quality metrics
- **Property:** Price changes, listing updates essential for revenue optimization analysis

**Alternative Considered:** Type 1 (overwrite)
- **Rejected because:** Historical analysis of pricing strategies, host quality trends, user behavior evolution would be lost

### 2. Two Booking Facts (Daily + Detail)

**Decision:** Create both aggregated and transaction-level facts

**Rationale:**
- **fact_booking_daily:** Fast queries for dashboard KPIs, pre-aggregated metrics
- **fact_booking_detail:** Detailed transaction analysis, customer journey, payment tracking

**Alternative Considered:** Single fact at transaction level
- **Rejected because:** Daily aggregate queries would be slow, dashboards would scan millions of rows

### 3. Separate Engagement Fact

**Decision:** Create dedicated fact for property engagement metrics

**Rationale:**
- High-volume clickstream data (different grain than bookings)
- Marketing team needs engagement analysis separate from revenue
- Enables funnel analysis (views → clicks → bookings)

**Alternative Considered:** Combine with booking facts
- **Rejected because:** Different grain (engagement vs transaction), different update frequency

### 4. Property as Type 2 (Not Snapshot)

**Decision:** Track property changes as Type 2, not daily snapshots

**Rationale:**
- Properties don't change daily (prices/listings updated occasionally)
- Type 2 preserves exact change history with timestamps
- More storage-efficient than daily snapshots

**Alternative Considered:** Daily property snapshot table
- **Rejected because:** 99% of days would be duplicates, wasted storage, harder to query changes

### 5. Destination as Type 1

**Decision:** Don't track destination history

**Rationale:**
- Destination descriptions, locations extremely stable
- Reference data that rarely changes
- No business use case for historical destination attributes

**Alternative Considered:** Type 2 destination
- **Rejected because:** Unnecessary complexity, no business value

---

## Data Classification & Governance

### Confidential (Contains PII)
- dim_user - Contains email, name, personal information
- dim_host - Contains email, name, phone, personal information
- dim_property - Contains address, location coordinates
- fact_booking_detail - Contains user behavior, payment information

### Internal (No PII)
- dim_destination - Public reference data
- dim_date - Generated data
- fact_booking_daily - Aggregated metrics without personal identifiers
- fact_property_engagement - Anonymized engagement metrics

---

## Implementation Order

1. **Phase 1: Core Dimensions**
   - dim_date (generated, no dependencies)
   - dim_destination (reference data)

2. **Phase 2: Entity Dimensions**
   - dim_user (depends on: dim_date for joined_at)
   - dim_host (depends on: dim_date for joined_at)
   - dim_property (depends on: dim_destination, dim_host)

3. **Phase 3: Fact Tables**
   - fact_booking_detail (depends on: all dimensions)
   - fact_booking_daily (depends on: fact_booking_detail or direct from Silver)
   - fact_property_engagement (depends on: dim_property, dim_date)

---

## Next Steps

1. ✅ Review and approve dimensional model design
2. ⏭️ Create YAML schema files for each table
3. ⏭️ Generate Mermaid ERD diagram
4. ⏭️ Implement table creation scripts
5. ⏭️ Implement MERGE scripts for data population
6. ⏭️ Create Table-Valued Functions (TVFs) for Genie
7. ⏭️ Create Metric Views for AI/BI dashboards
8. ⏭️ Setup Lakehouse Monitoring

---

## Stakeholder Sign-off

- [ ] Revenue Management Team - Approved by: _________________ Date: _______
- [ ] Property Operations - Approved by: _________________ Date: _______
- [ ] Data Engineering Lead - Approved by: _________________ Date: _______
- [ ] Analytics Team Lead - Approved by: _________________ Date: _______


