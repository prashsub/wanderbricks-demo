# Phase 3: Gold Layer - Dimensional Model Implementation

## Overview

**Status:** 📋 Planned  
**Schema:** `wanderbricks_gold`  
**Tables:** 8 (5 dimensions + 3 facts)  
**Dependencies:** Phase 2 (Silver Layer)  
**Reference:** [Gold Layer Design](../gold_layer_design/README.md)

---

## Purpose

The Gold layer implements a star schema dimensional model that:
1. Provides business-ready, aggregated datasets
2. Tracks historical changes via SCD Type 2 dimensions
3. Enables fast analytics queries through pre-aggregation
4. Supports Unity Catalog PK/FK constraints for governance

---

## Dimensional Model Summary

### Dimensions (5)

| # | Table | SCD Type | Business Key | PII | Domain |
|---|-------|----------|--------------|-----|--------|
| 1 | dim_user | Type 2 | user_id | Yes | 🎯 Customer |
| 2 | dim_host | Type 2 | host_id | Yes | 👤 Host |
| 3 | dim_property | Type 2 | property_id | Yes | 🏠 Property |
| 4 | dim_destination | Type 1 | destination_id | No | 🏠 Property |
| 5 | dim_date | Type 1 | date | No | (Reference) |

### Facts (3)

| # | Table | Grain | Domain |
|---|-------|-------|--------|
| 1 | fact_booking_detail | booking_id (transaction) | 💰 Revenue |
| 2 | fact_booking_daily | property-date (aggregated) | 💰 Revenue |
| 3 | fact_property_engagement | property-date | 📊 Engagement |

---

## ERD Overview

```
                    ┌─────────────────┐
                    │    dim_user     │
                    │   (SCD Type 2)  │
                    └────────┬────────┘
                             │ user_id
                             ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    dim_host     │◄───│fact_booking_    │───►│  dim_property   │
│   (SCD Type 2)  │    │    detail       │    │   (SCD Type 2)  │
└─────────────────┘    └────────┬────────┘    └────────┬────────┘
                                │                      │
                                ▼                      │
                       ┌─────────────────┐             │
                       │fact_booking_    │◄────────────┤
                       │    daily        │             │
                       └────────┬────────┘             │
                                │                      ▼
┌─────────────────┐             │             ┌─────────────────┐
│  dim_destination│◄────────────┼─────────────│fact_property_   │
│   (Type 1)      │             │             │   engagement    │
└─────────────────┘             ▼             └────────┬────────┘
                       ┌─────────────────┐             │
                       │    dim_date     │◄────────────┘
                       │   (Type 1)      │
                       └─────────────────┘
```

Full ERD: [erd_complete.md](../gold_layer_design/erd_complete.md)

---

## Implementation Approach

### YAML-Driven Setup

Gold tables are created dynamically from YAML schema definitions:

```
gold_layer_design/yaml/
├── identity/
│   ├── dim_user.yaml
│   └── dim_host.yaml
├── property/
│   └── dim_property.yaml
├── geography/
│   └── dim_destination.yaml
├── time/
│   └── dim_date.yaml
├── booking/
│   ├── fact_booking_detail.yaml
│   └── fact_booking_daily.yaml
└── engagement/
    └── fact_property_engagement.yaml
```

### Setup Orchestration

```yaml
resources:
  jobs:
    gold_setup_orchestrator_job:
      name: "[${bundle.target}] Gold Layer Setup Orchestrator"
      tasks:
        - task_key: setup_all_tables
          notebook_task:
            notebook_path: ../src/wanderbricks_gold/create_gold_tables.py
            base_parameters:
              catalog: ${var.catalog}
              gold_schema: ${var.gold_schema}
        
        - task_key: add_fk_constraints
          depends_on:
            - task_key: setup_all_tables
          notebook_task:
            notebook_path: ../src/wanderbricks_gold/add_fk_constraints.py
```

---

## Table Specifications

### 🎯 dim_user (Customer Domain)

**SCD Type 2** - Track user changes over time

| Column | Type | Description |
|--------|------|-------------|
| user_key | STRING | Surrogate key (MD5 hash) |
| user_id | BIGINT | Business key |
| email | STRING | User email (PII) |
| name | STRING | User full name (PII) |
| country | STRING | Country of residence |
| user_type | STRING | individual/business |
| is_business | BOOLEAN | Business account flag |
| company_name | STRING | Company name if business |
| created_at | DATE | Account creation date |
| effective_from | TIMESTAMP | SCD2 version start |
| effective_to | TIMESTAMP | SCD2 version end (NULL=current) |
| is_current | BOOLEAN | Current version flag |

**Primary Key:** user_key  
**Business Key:** user_id

---

### 👤 dim_host (Host Domain)

**SCD Type 2** - Track host rating/status changes

| Column | Type | Description |
|--------|------|-------------|
| host_key | STRING | Surrogate key (MD5 hash) |
| host_id | BIGINT | Business key |
| name | STRING | Host full name (PII) |
| email | STRING | Host email (PII) |
| phone | STRING | Host phone (PII) |
| is_verified | BOOLEAN | Verification status |
| is_active | BOOLEAN | Active status |
| rating | FLOAT | Host rating (1.0-5.0) |
| country | STRING | Host country |
| joined_at | DATE | Platform join date |
| effective_from | TIMESTAMP | SCD2 version start |
| effective_to | TIMESTAMP | SCD2 version end |
| is_current | BOOLEAN | Current version flag |

**Primary Key:** host_key  
**Business Key:** host_id

---

### 🏠 dim_property (Property Domain)

**SCD Type 2** - Track property price/listing changes

| Column | Type | Description |
|--------|------|-------------|
| property_key | STRING | Surrogate key (MD5 hash) |
| property_id | BIGINT | Business key |
| host_id | BIGINT | FK → dim_host |
| destination_id | BIGINT | FK → dim_destination |
| title | STRING | Property listing title |
| description | STRING | Property description |
| base_price | FLOAT | Base nightly price |
| property_type | STRING | house, apartment, etc. |
| max_guests | INT | Maximum guests |
| bedrooms | INT | Number of bedrooms |
| bathrooms | INT | Number of bathrooms |
| property_latitude | FLOAT | Latitude |
| property_longitude | FLOAT | Longitude |
| created_at | DATE | Listing creation date |
| effective_from | TIMESTAMP | SCD2 version start |
| effective_to | TIMESTAMP | SCD2 version end |
| is_current | BOOLEAN | Current version flag |

**Primary Key:** property_key  
**Business Key:** property_id  
**Foreign Keys:** host_id → dim_host, destination_id → dim_destination

---

### 🏠 dim_destination (Property Domain)

**SCD Type 1** - Reference data (overwrite)

| Column | Type | Description |
|--------|------|-------------|
| destination_id | BIGINT | Primary key |
| destination | STRING | Destination name |
| country | STRING | Country name |
| state_or_province | STRING | State/province |
| state_or_province_code | STRING | State/province code |
| description | STRING | Destination description |

**Primary Key:** destination_id

---

### 📅 dim_date (Reference)

**SCD Type 1** - Generated date dimension

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Calendar date (PK) |
| year | INT | Calendar year |
| quarter | INT | Quarter (1-4) |
| month | INT | Month (1-12) |
| month_name | STRING | Month name |
| week_of_year | INT | ISO week (1-53) |
| day_of_week | INT | Day of week (1=Sunday) |
| day_of_week_name | STRING | Day name |
| day_of_month | INT | Day of month |
| day_of_year | INT | Day of year |
| is_weekend | BOOLEAN | Weekend indicator |
| is_holiday | BOOLEAN | Holiday indicator |

**Primary Key:** date

---

### 💰 fact_booking_detail (Revenue Domain)

**Grain:** One row per booking transaction

| Column | Type | Description |
|--------|------|-------------|
| booking_id | BIGINT | Primary key |
| user_id | BIGINT | FK → dim_user |
| host_id | BIGINT | FK → dim_host |
| property_id | BIGINT | FK → dim_property |
| destination_id | BIGINT | FK → dim_destination |
| check_in_date | DATE | FK → dim_date |
| check_out_date | DATE | Checkout date |
| guests_count | INT | Number of guests |
| nights_booked | INT | Number of nights |
| total_amount | DECIMAL(18,2) | Total booking amount |
| payment_amount | DECIMAL(18,2) | Payment received |
| payment_method | STRING | Payment method |
| status | STRING | Booking status |
| created_at | TIMESTAMP | Booking creation |
| days_between_booking_and_checkin | INT | Lead time |
| is_cancelled | BOOLEAN | Cancellation flag |
| is_business_booking | BOOLEAN | Business vs leisure |

**Primary Key:** booking_id  
**Foreign Keys:** user_id, host_id, property_id, destination_id, check_in_date

---

### 💰 fact_booking_daily (Revenue Domain)

**Grain:** One row per property per check-in date (aggregated)

| Column | Type | Description |
|--------|------|-------------|
| property_id | BIGINT | FK → dim_property |
| destination_id | BIGINT | FK → dim_destination |
| check_in_date | DATE | FK → dim_date |
| booking_count | BIGINT | Number of bookings |
| total_booking_value | DECIMAL(18,2) | Sum of amounts |
| avg_booking_value | DECIMAL(18,2) | Average amount |
| total_guests | BIGINT | Total guest count |
| avg_nights_booked | DECIMAL(10,2) | Avg nights |
| cancellation_count | BIGINT | Cancelled bookings |
| confirmed_booking_count | BIGINT | Confirmed bookings |
| payment_completion_rate | DECIMAL(5,2) | Payment success rate |

**Primary Key:** (property_id, check_in_date)  
**Foreign Keys:** property_id, destination_id, check_in_date

---

### 📊 fact_property_engagement (Engagement Domain)

**Grain:** One row per property per engagement date

| Column | Type | Description |
|--------|------|-------------|
| property_id | BIGINT | FK → dim_property |
| engagement_date | DATE | FK → dim_date |
| view_count | BIGINT | Total views |
| unique_user_views | BIGINT | Distinct users |
| click_count | BIGINT | Total clicks |
| search_count | BIGINT | Search appearances |
| conversion_rate | DECIMAL(5,2) | Bookings / Views |
| avg_time_on_page | DECIMAL(10,2) | Avg engagement time |

**Primary Key:** (property_id, engagement_date)  
**Foreign Keys:** property_id, engagement_date

---

## Table Properties Standard

```sql
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.enableRowTracking' = 'true',
    'delta.enableDeletionVectors' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'layer' = 'gold',
    'source_layer' = 'silver',
    'domain' = '<domain>',
    'entity_type' = '<dimension|fact>',
    'contains_pii' = '<true|false>',
    'data_classification' = '<confidential|internal>',
    'business_owner' = '<team>',
    'technical_owner' = 'Data Engineering'
)
CLUSTER BY AUTO
```

---

## Implementation Checklist

### Schema Setup
- [ ] Create `wanderbricks_gold` schema
- [ ] Enable Predictive Optimization
- [ ] Apply governance tags

### Table Creation (Phase 1: Dimensions)
- [ ] Create dim_date (no dependencies)
- [ ] Create dim_destination (no dependencies)
- [ ] Create dim_user (depends on Silver)
- [ ] Create dim_host (depends on Silver)
- [ ] Create dim_property (depends on dim_host, dim_destination)

### Table Creation (Phase 2: Facts)
- [ ] Create fact_booking_detail (depends on all dimensions)
- [ ] Create fact_booking_daily (depends on dim_property, dim_date)
- [ ] Create fact_property_engagement (depends on dim_property, dim_date)

### Constraints (Phase 3)
- [ ] Apply PRIMARY KEY constraints
- [ ] Apply FOREIGN KEY constraints (after all PKs exist)

### Data Population
- [ ] Populate dim_date (generate 5-year range)
- [ ] Merge dim_destination from Silver
- [ ] Merge dim_user with SCD Type 2
- [ ] Merge dim_host with SCD Type 2
- [ ] Merge dim_property with SCD Type 2
- [ ] Merge fact_booking_detail
- [ ] Aggregate fact_booking_daily
- [ ] Aggregate fact_property_engagement

### Validation
- [ ] Verify record counts
- [ ] Validate PK/FK integrity
- [ ] Test SCD Type 2 versioning
- [ ] Verify aggregation accuracy

---

## Asset Bundle Jobs

### Gold Setup Orchestrator

Runs once to create tables and constraints:

```yaml
resources:
  jobs:
    gold_setup_orchestrator_job:
      name: "[${bundle.target}] Gold Setup Orchestrator"
      schedule:
        pause_status: PAUSED  # Manual trigger only
```

### Gold Refresh Orchestrator

Runs daily to update Gold data:

```yaml
resources:
  jobs:
    gold_refresh_orchestrator_job:
      name: "[${bundle.target}] Gold Refresh Orchestrator"
      schedule:
        quartz_cron_expression: "0 0 3 * * ?"  # 3 AM daily
        pause_status: PAUSED
```

---

## Next Phase

**→ [Phase 4: Use Cases](./phase4-use-cases.md)**

Phase 4 will build analytics artifacts on the Gold layer:
1. Table-Valued Functions (TVFs) for Genie
2. Metric Views for self-service analytics
3. AI/BI Dashboards
4. Lakehouse Monitoring
5. Genie Spaces
6. Alerting Framework

---

## References

- [Gold Layer Design](../gold_layer_design/README.md)
- [ERD Complete](../gold_layer_design/erd_complete.md)
- [Design Summary](../gold_layer_design/DESIGN_SUMMARY.md)
- [YAML Schemas](../gold_layer_design/yaml/)
- [Gold Layer Documentation Rule](../.cursor/rules/gold/12-gold-layer-documentation.mdc)
- [YAML-Driven Setup Rule](../.cursor/rules/gold/25-yaml-driven-gold-setup.mdc)

