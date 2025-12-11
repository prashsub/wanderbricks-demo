# Phase 1: Bronze Layer - Raw Data Ingestion

## Overview

**Status:** ✅ Complete  
**Schema:** `wanderbricks`  
**Tables:** 16  
**Dependencies:** None (source layer)  
**Reference:** [Bronze Layer Prompt](../context/prompts/01-bronze-layer-prompt.md)

---

## Purpose

The Bronze layer ingests raw data from the Wanderbricks vacation rental platform with minimal transformation. This layer preserves source fidelity and enables Change Data Feed (CDF) for downstream incremental processing.

---

## Bronze Tables Summary

### Core Entities (4 tables)

| Table | Primary Key | Rows | Description |
|-------|-------------|------|-------------|
| users | user_id | - | Guest/customer accounts |
| hosts | host_id | - | Property host accounts |
| properties | property_id | - | Vacation rental listings |
| destinations | destination_id | - | Travel destination reference data |

### Transactions (3 tables)

| Table | Primary Key | Rows | Description |
|-------|-------------|------|-------------|
| bookings | booking_id | - | Booking transactions |
| booking_updates | booking_update_id | - | Booking modification history |
| payments | payment_id | - | Payment transactions |

### Engagement (2 tables)

| Table | Primary Key | Rows | Description |
|-------|-------------|------|-------------|
| clickstream | (user_id, property_id, timestamp) | - | User interaction events |
| page_views | view_id | - | Property page view tracking |

### Reviews & Support (2 tables)

| Table | Primary Key | Rows | Description |
|-------|-------------|------|-------------|
| reviews | review_id | - | Guest reviews and ratings |
| customer_support_logs | ticket_id | - | Support ticket interactions |

### Reference Data (5 tables)

| Table | Primary Key | Rows | Description |
|-------|-------------|------|-------------|
| amenities | amenity_id | - | Amenity catalog |
| property_amenities | (property_id, amenity_id) | - | Property-amenity mapping |
| property_images | image_id | - | Property photo URLs |
| countries | country | - | Country reference data |
| employees | employee_id | - | Host employee records |

---

## Table Properties

All Bronze tables include:

```sql
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'layer' = 'bronze',
    'source_system' = 'Wanderbricks',
    'domain' = '<domain>'
)
CLUSTER BY AUTO
```

---

## Entity Relationship Overview

```
users ──────┬──── bookings ──── payments
            │         │
            │         ▼
hosts ──────┴─── properties ──── page_views
                     │              │
                     ├───────────── clickstream
                     │              │
                     ▼              ▼
              destinations      reviews
```

---

## Data Quality Baseline

### Volume Metrics

| Table | Expected Daily Volume | Peak Volume |
|-------|----------------------|-------------|
| bookings | 1,000-5,000 | 10,000+ |
| clickstream | 100,000-500,000 | 1,000,000+ |
| page_views | 50,000-200,000 | 500,000+ |
| payments | 1,000-5,000 | 10,000+ |

### Key Metrics to Track

- Record counts per table
- Null rate per column
- Unique key violations
- Late arriving data (timestamp drift)

---

## Implementation Checklist

### Schema Setup
- [x] Create `wanderbricks` schema
- [x] Enable Predictive Optimization
- [x] Apply governance tags

### Table Creation
- [x] Create all 16 Bronze tables
- [x] Enable Change Data Feed (CDF)
- [x] Enable automatic liquid clustering
- [x] Add table and column comments

### Data Loading
- [x] Initial data load complete
- [x] Verify record counts
- [x] Validate key uniqueness

### Governance
- [x] Apply PII tags where applicable
- [x] Set data classification
- [x] Document business ownership

---

## Next Phase

**→ [Phase 2: Silver Layer](./phase2-silver-layer.md)**

The Silver layer will:
1. Stream Bronze data via DLT
2. Apply data quality expectations
3. Deduplicate and validate records
4. Prepare clean data for Gold layer

---

## References

- [Bronze Layer Design Prompt](../context/prompts/01-bronze-layer-prompt.md)
- [Wanderbricks Schema CSV](../context/Wanderbricks_Schema.csv)
- [Change Data Feed](https://docs.databricks.com/delta/delta-change-data-feed.html)

