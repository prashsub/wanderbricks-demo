# Phase 4: Use Cases - Analytics Artifacts

## Overview

**Status:** 📋 Planned  
**Dependencies:** Phase 3 (Gold Layer)  
**Estimated Effort:** 3-4 weeks  
**Reference:** [Project Plan Methodology](../.cursor/rules/planning/26-project-plan-methodology.mdc)

---

## Purpose

Phase 4 builds analytics artifacts on the Gold layer to enable:
1. **Self-service analytics** - Business users can query without SQL
2. **Natural language queries** - Genie Spaces for conversational analytics
3. **Executive dashboards** - Visual KPI tracking
4. **Proactive monitoring** - Alerts for anomalies and SLA violations
5. **Predictive capabilities** - ML models for forecasting

---

## Agent Domain Framework

All artifacts are organized by **Agent Domain**:

| Domain | Icon | Focus Area | Primary Tables |
|--------|------|------------|----------------|
| **Revenue** | 💰 | Booking revenue, payments, pricing | `fact_booking_daily`, `fact_booking_detail` |
| **Engagement** | 📊 | Views, clicks, conversions | `fact_property_engagement` |
| **Property** | 🏠 | Listings, inventory, pricing strategy | `dim_property` |
| **Host** | 👤 | Host performance, quality, retention | `dim_host` |
| **Customer** | 🎯 | User behavior, segmentation, CLV | `dim_user` |

---

## Addendum Index

| # | Addendum | Status | Artifacts Count |
|---|----------|--------|-----------------|
| 4.1 | [ML Models](./phase4-addendum-4.1-ml-models.md) | 📋 Planned | 5 models |
| 4.2 | [Table-Valued Functions](./phase4-addendum-4.2-tvfs.md) | 📋 Planned | 25+ TVFs |
| 4.3 | [Metric Views](./phase4-addendum-4.3-metric-views.md) | 📋 Planned | 5 metric views |
| 4.4 | [Lakehouse Monitoring](./phase4-addendum-4.4-lakehouse-monitoring.md) | 📋 Planned | 5 monitors |
| 4.5 | [AI/BI Dashboards](./phase4-addendum-4.5-aibi-dashboards.md) | 📋 Planned | 5 dashboards |
| 4.6 | [Genie Spaces](./phase4-addendum-4.6-genie-spaces.md) | 📋 Planned | 5 Genie Spaces |
| 4.7 | [Alerting Framework](./phase4-addendum-4.7-alerting.md) | 📋 Planned | 20+ alerts |

---

## Artifact Summary by Domain

### 💰 Revenue Domain

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| TVFs | 6 | `get_revenue_by_period`, `get_top_properties_by_revenue` |
| Metric Views | 1 | `revenue_analytics_metrics` |
| Dashboards | 1 | Revenue Performance Dashboard |
| Monitors | 1 | Revenue Data Quality Monitor |
| Alerts | 5 | Revenue drop, booking anomaly |
| ML Models | 2 | Revenue Forecaster, Demand Predictor |
| Genie Space | 1 | Revenue Intelligence |

### 📊 Engagement Domain

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| TVFs | 5 | `get_property_engagement`, `get_conversion_funnel` |
| Metric Views | 1 | `engagement_analytics_metrics` |
| Dashboards | 1 | Engagement & Conversion Dashboard |
| Monitors | 1 | Engagement Data Quality Monitor |
| Alerts | 4 | Conversion drop, view spike |
| ML Models | 1 | Conversion Predictor |
| Genie Space | 1 | Marketing Intelligence |

### 🏠 Property Domain

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| TVFs | 5 | `get_property_performance`, `get_availability_by_destination` |
| Metric Views | 1 | `property_analytics_metrics` |
| Dashboards | 1 | Property Portfolio Dashboard |
| Monitors | 1 | Property Data Quality Monitor |
| Alerts | 4 | Price anomaly, inventory alert |
| ML Models | 1 | Pricing Optimizer |
| Genie Space | 1 | Property Intelligence |

### 👤 Host Domain

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| TVFs | 4 | `get_host_performance`, `get_host_quality_metrics` |
| Metric Views | 1 | `host_analytics_metrics` |
| Dashboards | 1 | Host Performance Dashboard |
| Monitors | 1 | Host Data Quality Monitor |
| Alerts | 4 | Rating drop, inactive host |
| Genie Space | 1 | Host Intelligence |

### 🎯 Customer Domain

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| TVFs | 5 | `get_customer_segments`, `get_customer_ltv` |
| Metric Views | 1 | `customer_analytics_metrics` |
| Dashboards | 1 | Customer Analytics Dashboard |
| Monitors | 1 | Customer Data Quality Monitor |
| Alerts | 4 | Churn risk, behavior anomaly |
| ML Models | 1 | Customer Lifetime Value Predictor |
| Genie Space | 1 | Customer Intelligence |

---

## Artifact Totals

| Artifact Type | Count |
|--------------|-------|
| Table-Valued Functions (TVFs) | 25+ |
| Metric Views | 5 |
| AI/BI Dashboards | 5 |
| Lakehouse Monitors | 5 |
| SQL Alerts | 21 |
| ML Models | 5 |
| Genie Spaces | 5 |
| **Total Artifacts** | **66+** |

---

## Implementation Order

### Week 1: Foundation
1. ✅ Deploy Gold layer tables
2. Create TVFs (all domains)
3. Create Metric Views

### Week 2: Monitoring
4. Setup Lakehouse Monitors
5. Create Alerting Framework
6. Validate data quality baselines

### Week 3: Visualization
7. Build AI/BI Dashboards
8. Configure Genie Spaces
9. Document business usage guides

### Week 4: Intelligence
10. Train ML Models
11. Deploy model endpoints
12. Integrate predictions into dashboards

---

## Success Criteria

| Metric | Target |
|--------|--------|
| TVFs deployed and functional | 25+ |
| Metric Views queryable | 5 |
| Dashboards published | 5 |
| Monitors with baselines | 5 |
| Alerts configured | 20+ |
| Genie Spaces responding to NL queries | 5 |
| ML Models with acceptable accuracy | 80%+ |

---

## Key Business Questions by Domain

### 💰 Revenue

1. What is our total booking revenue by destination/month?
2. Which properties generate the most revenue?
3. What is the average booking value trend?
4. How does cancellation rate impact revenue?
5. What is the payment completion rate?

### 📊 Engagement

1. Which properties have the highest conversion rate?
2. What is the view-to-booking funnel performance?
3. Which traffic sources drive the most bookings?
4. How does device type affect engagement?
5. What is the optimal property page content?

### 🏠 Property

1. What is the inventory utilization by destination?
2. Which property types perform best?
3. How does pricing affect bookings?
4. What amenities correlate with higher ratings?
5. Which destinations are trending?

### 👤 Host

1. Who are the top-performing hosts?
2. How does verification status affect bookings?
3. What is the host rating distribution?
4. Which hosts have the fastest response time?
5. What predicts host churn?

### 🎯 Customer

1. What are the key customer segments?
2. Which customers have the highest lifetime value?
3. What is the booking frequency distribution?
4. How does business vs leisure booking differ?
5. What predicts customer churn?

---

## Technical Architecture

### Data Flow

```
Gold Layer Tables
        │
        ├──► TVFs (Parameterized Queries)
        │         │
        │         └──► Genie Spaces
        │
        ├──► Metric Views
        │         │
        │         └──► AI/BI Dashboards
        │
        ├──► Lakehouse Monitors
        │         │
        │         └──► Alerts
        │
        └──► Feature Store
                  │
                  └──► ML Models
```

### Deployment Strategy

```yaml
# Asset Bundle job for semantic layer setup
resources:
  jobs:
    semantic_layer_setup_job:
      name: "[${bundle.target}] Semantic Layer Setup"
      tasks:
        - task_key: create_tvfs
          sql_task:
            file:
              path: ../src/wanderbricks_gold/semantic/create_tvfs.sql

        - task_key: create_metric_views
          depends_on:
            - task_key: create_tvfs
          notebook_task:
            notebook_path: ../src/wanderbricks_gold/semantic/create_metric_views.py

        - task_key: setup_lakehouse_monitoring
          depends_on:
            - task_key: create_metric_views
          notebook_task:
            notebook_path: ../src/wanderbricks_gold/monitoring/setup_monitors.py
```

---

## Cross-Addendum Dependencies

```
4.2 TVFs ────────────────────► 4.6 Genie Spaces
    │                               │
    │                               ▼
    └──────────────────────────► 4.5 Dashboards
                                    ▲
4.3 Metric Views ──────────────────┘
    │
    └──► 4.4 Lakehouse Monitoring ──► 4.7 Alerting

4.1 ML Models (independent, uses Gold directly)
```

---

## Next Phase

**→ [Phase 5: AI Agents](./phase5-ai-agents.md)**

Phase 5 will create AI agents that use the semantic layer:
1. Revenue Agent (financial analysis)
2. Engagement Agent (marketing optimization)
3. Property Agent (inventory management)
4. Host Agent (host success)
5. Customer Agent (customer success)

---

## References

### Addendum Documents
- [4.1 ML Models](./phase4-addendum-4.1-ml-models.md)
- [4.2 TVFs](./phase4-addendum-4.2-tvfs.md)
- [4.3 Metric Views](./phase4-addendum-4.3-metric-views.md)
- [4.4 Lakehouse Monitoring](./phase4-addendum-4.4-lakehouse-monitoring.md)
- [4.5 AI/BI Dashboards](./phase4-addendum-4.5-aibi-dashboards.md)
- [4.6 Genie Spaces](./phase4-addendum-4.6-genie-spaces.md)
- [4.7 Alerting](./phase4-addendum-4.7-alerting.md)

### Cursor Rules
- [TVF Patterns](../.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc)
- [Genie Space Patterns](../.cursor/rules/semantic-layer/16-genie-space-patterns.mdc)
- [Lakehouse Monitoring](../.cursor/rules/monitoring/17-lakehouse-monitoring-comprehensive.mdc)
- [AI/BI Dashboards](../.cursor/rules/monitoring/18-databricks-aibi-dashboards.mdc)

### Context Prompts
- [TVFs Prompt](../context/prompts/09-table-valued-functions-prompt.md)
- [Metric Views Prompt](../context/prompts/04-metric-views-prompt.md)
- [Monitoring Prompt](../context/prompts/05-monitoring-prompt.md)
- [Genie Space Prompt](../context/prompts/06-genie-space-prompt.md)
- [Dashboards Prompt](../context/prompts/10-aibi-dashboards-prompt.md)

