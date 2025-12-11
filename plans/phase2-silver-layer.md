# Phase 2: Silver Layer - DLT Streaming & Data Quality

## Overview

**Status:** 🔧 In Progress  
**Schema:** `wanderbricks_silver`  
**Tables:** 8+ streaming tables  
**Dependencies:** Phase 1 (Bronze Layer)  
**Reference:** [Silver Layer Prompt](../context/prompts/02-silver-layer-prompt.md)

---

## Purpose

The Silver layer implements Delta Live Tables (DLT) streaming pipelines that:
1. Read incrementally from Bronze via Change Data Feed (CDF)
2. Apply data quality expectations with quarantine patterns
3. Deduplicate and clean records
4. Prepare validated data for Gold layer dimensional modeling

---

## Silver Tables Architecture

### Dimension Tables (5)

| Silver Table | Source Bronze | DQ Expectations | Quarantine |
|-------------|---------------|-----------------|------------|
| silver_user_dim | users | 5+ | Yes |
| silver_host_dim | hosts | 6+ | Yes |
| silver_property_dim | properties | 8+ | Yes |
| silver_destination_dim | destinations | 4+ | No |
| silver_date_dim | Generated | N/A | No |

### Fact Tables (3)

| Silver Table | Source Bronze | DQ Expectations | Quarantine |
|-------------|---------------|-----------------|------------|
| silver_bookings | bookings, booking_updates | 10+ | Yes |
| silver_payments | payments | 6+ | Yes |
| silver_engagement | clickstream, page_views | 5+ | Yes |

---

## DLT Pipeline Configuration

### Pipeline: Silver DLT Pipeline

```yaml
resources:
  pipelines:
    silver_dlt_pipeline:
      name: "[${bundle.target}] Wanderbricks Silver Pipeline"
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      root_path: ../src/wanderbricks_silver
      serverless: true
      photon: true
      edition: ADVANCED
      configuration:
        catalog: ${var.catalog}
        bronze_schema: ${var.bronze_schema}
        silver_schema: ${var.silver_schema}
```

### DLT Libraries

```
src/wanderbricks_silver/
├── silver_dimensions.py    # Dimension streaming tables
├── silver_bookings.py      # Booking fact streaming
├── silver_engagement.py    # Engagement fact streaming
├── dq_rules_loader.py      # Dynamic DQ rules
└── data_quality_monitoring.py  # DQ metrics tracking
```

---

## Data Quality Expectations

### 💰 Revenue Domain: silver_bookings

| Expectation | Rule | Action |
|-------------|------|--------|
| valid_booking_id | `booking_id IS NOT NULL` | DROP |
| valid_user_id | `user_id IS NOT NULL` | DROP |
| valid_property_id | `property_id IS NOT NULL` | DROP |
| valid_dates | `check_in < check_out` | QUARANTINE |
| positive_amount | `total_amount >= 0` | QUARANTINE |
| valid_status | `status IN ('pending', 'confirmed', 'cancelled')` | QUARANTINE |
| reasonable_guests | `guests_count BETWEEN 1 AND 50` | WARN |
| reasonable_nights | `DATEDIFF(check_out, check_in) BETWEEN 1 AND 365` | WARN |

### 👤 Host Domain: silver_host_dim

| Expectation | Rule | Action |
|-------------|------|--------|
| valid_host_id | `host_id IS NOT NULL` | DROP |
| valid_email | `email IS NOT NULL AND email LIKE '%@%.%'` | QUARANTINE |
| valid_rating | `rating BETWEEN 1.0 AND 5.0` | QUARANTINE |
| valid_country | `country IS NOT NULL` | WARN |

### 🏠 Property Domain: silver_property_dim

| Expectation | Rule | Action |
|-------------|------|--------|
| valid_property_id | `property_id IS NOT NULL` | DROP |
| valid_host_ref | `host_id IS NOT NULL` | DROP |
| valid_destination_ref | `destination_id IS NOT NULL` | DROP |
| positive_price | `base_price > 0` | QUARANTINE |
| reasonable_capacity | `max_guests BETWEEN 1 AND 100` | WARN |
| valid_coordinates | `property_latitude BETWEEN -90 AND 90` | WARN |

### 📊 Engagement Domain: silver_engagement

| Expectation | Rule | Action |
|-------------|------|--------|
| valid_property_ref | `property_id IS NOT NULL` | DROP |
| valid_timestamp | `timestamp IS NOT NULL` | DROP |
| valid_event_type | `event IN ('view', 'click', 'search', 'filter')` | QUARANTINE |
| valid_device | `metadata.device IS NOT NULL` | WARN |

---

## DQ Rules Storage Pattern

### Rules Table: `silver_dq_rules`

```sql
CREATE TABLE ${catalog}.${silver_schema}.silver_dq_rules (
    rule_id STRING NOT NULL,
    table_name STRING NOT NULL,
    column_name STRING,
    rule_type STRING NOT NULL,  -- 'not_null', 'range', 'regex', 'referential'
    expectation_sql STRING NOT NULL,
    action STRING NOT NULL,  -- 'DROP', 'QUARANTINE', 'WARN'
    severity STRING NOT NULL,  -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Dynamic Rules Loading

```python
def load_dq_rules(spark, table_name):
    """Load active DQ rules for a table."""
    return spark.sql(f"""
        SELECT rule_id, expectation_sql, action
        FROM {catalog}.{silver_schema}.silver_dq_rules
        WHERE table_name = '{table_name}'
          AND is_active = true
        ORDER BY severity
    """).collect()
```

---

## Quarantine Pattern

### Quarantine Tables

| Quarantine Table | Source | Retention |
|-----------------|--------|-----------|
| silver_bookings_quarantine | silver_bookings | 90 days |
| silver_hosts_quarantine | silver_host_dim | 90 days |
| silver_properties_quarantine | silver_property_dim | 90 days |
| silver_engagement_quarantine | silver_engagement | 30 days |

### Quarantine Flow

```
Bronze Table
     │
     ▼
DLT Streaming Read
     │
     ├── PASS ──────► Silver Table (clean data)
     │
     └── FAIL ──────► Quarantine Table + Error Details
                            │
                            ▼
                     Manual Review / Auto-Retry
```

---

## DQ Metrics Tracking

### Metrics Table: `silver_dq_metrics`

```sql
CREATE TABLE ${catalog}.${silver_schema}.silver_dq_metrics (
    metric_id STRING NOT NULL,
    table_name STRING NOT NULL,
    rule_id STRING NOT NULL,
    execution_timestamp TIMESTAMP NOT NULL,
    total_records BIGINT,
    passed_records BIGINT,
    failed_records BIGINT,
    pass_rate DECIMAL(5,2),
    processing_time_ms BIGINT
)
```

### Success Criteria

| Metric | Target | Critical |
|--------|--------|----------|
| Overall Pass Rate | >99% | <95% |
| Drop Rate | <0.1% | >1% |
| Quarantine Rate | <1% | >5% |
| Pipeline Latency | <5 min | >30 min |

---

## Implementation Status

### Completed ✅

- [x] DLT pipeline configuration
- [x] Dimension streaming tables (silver_dimensions.py)
- [x] Booking streaming with DQ (silver_bookings.py)
- [x] Engagement streaming (silver_engagement.py)
- [x] DQ rules loader pattern

### In Progress 🔧

- [ ] Quarantine table setup
- [ ] DQ metrics tracking
- [ ] Validation job deployment
- [ ] Monitoring dashboards

### Planned 📋

- [ ] Auto-retry from quarantine
- [ ] Alerting on DQ degradation
- [ ] Historical DQ trending

---

## Validation Jobs

### Silver Validation Job

```yaml
resources:
  jobs:
    silver_validation_job:
      name: "[${bundle.target}] Silver Layer Validation"
      tasks:
        - task_key: validate_table_counts
          notebook_task:
            notebook_path: ../src/wanderbricks_silver/validation/validate_table_counts.py
        
        - task_key: validate_referential_integrity
          depends_on:
            - task_key: validate_table_counts
          notebook_task:
            notebook_path: ../src/wanderbricks_silver/validation/validate_referential_integrity.py
        
        - task_key: analyze_quarantine
          notebook_task:
            notebook_path: ../src/wanderbricks_silver/validation/analyze_quarantine.py
```

---

## Next Phase

**→ [Phase 3: Gold Layer](./phase3-gold-layer.md)**

The Gold layer will:
1. Read validated Silver data
2. Apply dimensional modeling (SCD Type 2)
3. Pre-aggregate facts for performance
4. Enable PK/FK constraints

---

## References

- [Silver Layer Prompt](../context/prompts/02-silver-layer-prompt.md)
- [DQX Patterns](../.cursor/rules/silver/08-dqx-patterns.mdc)
- [DLT Expectations](https://docs.databricks.com/aws/en/dlt/expectations)
- [DLT Pipeline Resource](../resources/silver/silver_dlt_pipeline.yml)

