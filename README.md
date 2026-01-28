# Wanderbricks: Vacation Rental Analytics Platform

**A production-ready Databricks Medallion Architecture implementation for vacation rental analytics**

[![Databricks](https://img.shields.io/badge/Platform-Databricks-FF3621?logo=databricks)](https://databricks.com)
[![Unity Catalog](https://img.shields.io/badge/Governance-Unity%20Catalog-00A972)](https://docs.databricks.com/data-governance/unity-catalog/index.html)
[![Delta Lake](https://img.shields.io/badge/Storage-Delta%20Lake-00ADD8)](https://delta.io)
[![Asset Bundles](https://img.shields.io/badge/IaC-Asset%20Bundles-077A9D)](https://docs.databricks.com/dev-tools/bundles/index.html)

---

## Overview

Wanderbricks is a comprehensive analytics platform for vacation rentals (similar to Airbnb), demonstrating best practices for building modern data lakehouses on Databricks. The platform includes:

- **Medallion Architecture** (Bronze → Silver → Gold)
- **Dimensional Modeling** (Star Schema with SCD Type 2)
- **Machine Learning** (5 production ML models)
- **Semantic Layer** (26 TVFs + 5 Metric Views)
- **Self-Service Analytics** (6 AI/BI Dashboards)
- **Data Quality & Monitoring** (5 Lakehouse Monitors with 20 custom metrics)

### Business Domains

| Domain | Icon | Focus Area | Key Use Cases |
|--------|------|------------|---------------|
| **Revenue** | 💰 | Booking revenue, payments, pricing | Revenue forecasting, pricing optimization |
| **Engagement** | 📊 | Views, clicks, conversions | Funnel analysis, marketing effectiveness |
| **Property** | 🏠 | Listings, inventory, availability | Portfolio management, capacity planning |
| **Host** | 👤 | Host performance, ratings, quality | Partner management, quality tracking |
| **Customer** | 🎯 | User behavior, segmentation, LTV | Customer analytics, segmentation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WANDERBRICKS PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │    BRONZE    │───▶│    SILVER    │───▶│     GOLD     │                  │
│  │  (Raw Data)  │    │  (Cleansed)  │    │ (Star Schema)│                  │
│  │   16 tables  │    │  17 tables   │    │   8 tables   │                  │
│  │              │    │  + 2 quarant │    │  (5 dim +    │                  │
│  │  CDF enabled │    │  DLT + DQ    │    │   3 fact)    │                  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘                  │
│                                                  │                          │
│  ┌───────────────────────────────────────────────┼───────────────────────┐  │
│  │                    SEMANTIC LAYER             │                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────┴──────┐                │  │
│  │  │     TVFs     │  │Metric Views  │  │ ML Models    │                │  │
│  │  │  26 funcs    │  │   5 views    │  │  5 models    │                │  │
│  │  │  Genie-ready │  │  YAML-based  │  │  MLflow 3.0  │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    ANALYTICS & MONITORING                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │  Dashboards  │  │  Lakehouse   │  │ Genie Spaces │                │  │
│  │  │  6 AI/BI     │  │  Monitors    │  │  (Planned)   │                │  │
│  │  │  68 widgets  │  │  5 monitors  │  │              │                │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Layers

| Layer | Schema | Tables | Technology | Features |
|-------|--------|--------|------------|----------|
| **Bronze** | `wanderbricks_bronze` | 16 | Delta Lake | CDF enabled, auto liquid clustering |
| **Silver** | `wanderbricks_silver` | 17 + 2 quarantine | Delta Live Tables | Streaming, DQ expectations, quarantine pattern |
| **Gold** | `wanderbricks_gold` | 8 | Delta Lake | Star schema, SCD2, PK/FK constraints |

---

## Quick Start

### Prerequisites

- Databricks CLI installed and configured
- Access to a Unity Catalog-enabled workspace
- Serverless SQL Warehouse

### Deploy in 5 Commands

```bash
# 1. Clone and navigate
git clone <repo-url>
cd Wanderbricks_Bundle

# 2. Validate bundle configuration
databricks bundle validate

# 3. Deploy all resources to dev
databricks bundle deploy -t dev

# 4. Initialize Silver layer (run DQ setup first!)
databricks bundle run silver_dq_setup_job -t dev
databricks pipelines start-update --pipeline-name "[dev] Wanderbricks Silver Layer Pipeline"

# 5. Initialize Gold layer
databricks bundle run gold_setup_job -t dev
databricks bundle run gold_merge_job -t dev
```

### Verify Deployment

```sql
-- Check Bronze layer
SHOW TABLES IN ${catalog}.${bronze_schema};

-- Check Silver layer (expect 17+ tables)
SHOW TABLES IN ${catalog}.${silver_schema};

-- Check Gold layer (expect 8 tables)
SHOW TABLES IN ${catalog}.${gold_schema};

-- Verify Gold layer data
SELECT COUNT(*) as bookings FROM ${catalog}.${gold_schema}.fact_booking_detail;
```

---

## Project Structure

```
Wanderbricks_Bundle/
├── databricks.yml              # Asset Bundle configuration
├── QUICKSTART.md               # Quick deployment commands
├── README.md                   # This file
│
├── resources/                  # Databricks Asset Bundle resources
│   ├── bronze/                 # Bronze layer jobs
│   ├── silver/                 # Silver DLT pipeline & jobs
│   ├── gold/                   # Gold layer setup & merge jobs
│   └── ml/                     # ML training & serving jobs
│
├── src/                        # Source code
│   ├── wanderbricks_silver/    # DLT pipeline code
│   ├── wanderbricks_gold/      # Gold layer merge scripts
│   └── wanderbricks_ml/        # ML model training code
│
├── gold_layer_design/          # Gold layer schema design
│   ├── yaml/                   # Table schema definitions (YAML)
│   │   ├── identity/           # dim_user, dim_host
│   │   ├── property/           # dim_property
│   │   ├── geography/          # dim_destination
│   │   ├── time/               # dim_date
│   │   ├── booking/            # fact_booking_*
│   │   ├── engagement/         # fact_property_engagement
│   │   └── weather/            # weather tables
│   ├── DESIGN_SUMMARY.md       # Design decisions
│   └── erd_complete.md         # Entity-relationship diagram
│
├── dashboards/                 # AI/BI Lakeview dashboards (JSON)
│   ├── wanderbricks_revenue_performance_dashboard.lvdash.json
│   ├── wanderbricks_engagement_conversion_dashboard.lvdash.json
│   ├── wanderbricks_property_portfolio_dashboard.lvdash.json
│   ├── wanderbricks_host_performance_dashboard.lvdash.json
│   ├── wanderbricks_customer_analytics_dashboard.lvdash.json
│   └── wanderbricks_lakehouse_monitoring_dashboard.lvdash.json
│
├── plans/                      # Project plans and roadmap
│   ├── phase1-use-cases.md     # Phase 1: Analytics artifacts
│   ├── phase2-agent-framework.md # Phase 2: AI Agents (planned)
│   └── phase3-frontend-app.md  # Phase 3: Frontend (planned)
│
├── docs/                       # Documentation
│   ├── deployment/             # Deployment guides
│   ├── ml/                     # ML documentation
│   ├── architecture/           # Architecture docs
│   ├── troubleshooting/        # Issue resolutions
│   └── reference/              # Reference materials
│
├── context/                    # AI context and prompts
│   └── prompts/                # Domain prompts for AI assistants
│
├── scripts/                    # Utility scripts
│   ├── validate_bundle.sh      # Bundle validation
│   └── validate_tvf_sql.sh     # TVF SQL validation
│
└── .cursor/                    # Cursor IDE rules
    └── rules/                  # AI assistant rules (30 rules)
```

---

## Key Features

### Data Quality

- **DLT Expectations**: 70+ data quality rules in Silver layer
- **Quarantine Pattern**: Invalid records captured, pipeline never fails
- **Runtime-Updateable Rules**: DQ rules stored in Delta table, update via SQL
- **Lakehouse Monitoring**: 20 custom business metrics across 5 monitors

### Governance

- **Unity Catalog**: All assets UC-managed with lineage tracking
- **PII Tagging**: Sensitive data classified and tagged
- **PK/FK Constraints**: Referential integrity declared (NOT ENFORCED)
- **Dual-Purpose Descriptions**: Business + technical documentation on all columns

### Performance

- **Automatic Liquid Clustering**: Enabled on all tables
- **Predictive Optimization**: Schema-level optimization enabled
- **Change Data Feed (CDF)**: Incremental propagation between layers
- **Serverless Compute**: Jobs run on serverless infrastructure

### Analytics

- **Self-Service TVFs**: 26 table-valued functions for Genie/SQL
- **Metric Views**: 5 semantic views with dimensions and measures
- **AI/BI Dashboards**: 6 executive dashboards with 68 widgets
- **ML Models**: 5 production models for forecasting and optimization

---

## Dimensional Model

### Dimensions (5 tables)

| Dimension | SCD Type | Business Key | PII | Purpose |
|-----------|----------|--------------|-----|---------|
| `dim_user` | Type 2 | user_id | Yes | Customer segmentation |
| `dim_host` | Type 2 | host_id | Yes | Host performance tracking |
| `dim_property` | Type 2 | property_id | Yes | Listing management |
| `dim_destination` | Type 1 | destination_id | No | Geographic reference |
| `dim_date` | Type 1 | date | No | Time dimension |

### Facts (3 tables)

| Fact | Grain | Update Frequency | Purpose |
|------|-------|------------------|---------|
| `fact_booking_detail` | booking_id (transaction) | Daily | Transaction-level bookings |
| `fact_booking_daily` | property-date | Daily | Aggregated daily metrics |
| `fact_property_engagement` | property-date | Daily | Engagement funnel metrics |

### Entity-Relationship Diagram

See [gold_layer_design/erd_complete.md](gold_layer_design/erd_complete.md) for the complete Mermaid ERD.

---

## ML Models

| Model | Type | Purpose | Target Metric |
|-------|------|---------|---------------|
| **Revenue Forecaster** | Time Series (Prophet) | Forecast revenue 30/60/90 days | MAPE < 15% |
| **Demand Predictor** | Regression (XGBoost) | Predict booking demand | RMSE < 3 |
| **Conversion Predictor** | Classification (XGBoost) | Predict booking conversion | AUC-ROC > 0.75 |
| **Pricing Optimizer** | Regression (GB) | Recommend optimal prices | Revenue Lift > 5% |
| **Customer LTV** | Regression (XGBoost) | Predict 12-month LTV | MAPE < 20% |

### ML Infrastructure

- **Feature Store**: Unity Catalog Feature Tables (3 tables)
- **Model Registry**: MLflow 3.0 with UC integration
- **Serving**: Serverless Model Serving endpoints
- **Training**: Weekly retraining schedule via Databricks Workflows

---

## Dashboards

| Dashboard | Pages | Widgets | Audience |
|-----------|-------|---------|----------|
| Revenue Performance | 4 | 12 | Finance, Leadership |
| Engagement & Conversion | 4 | 10 | Marketing |
| Property Portfolio | 4 | 10 | Operations |
| Host Performance | 4 | 10 | Partner Management |
| Customer Analytics | 4 | 11 | Growth, Product |
| Lakehouse Monitoring | 4 | 15 | Data Engineering |

**Total:** 6 dashboards, 24 pages, 68 widgets

Import dashboard JSON files from `dashboards/` into Databricks Lakeview. See [dashboards/README.md](dashboards/README.md) for details.

---

## Semantic Layer

### Table-Valued Functions (26 TVFs)

Organized by domain for Genie Space integration:

| Domain | TVFs | Example Functions |
|--------|------|-------------------|
| Revenue | 6 | `get_revenue_by_period()`, `get_top_properties_by_revenue()` |
| Engagement | 5 | `get_property_engagement()`, `get_conversion_funnel()` |
| Property | 5 | `get_property_performance()`, `get_pricing_analysis()` |
| Host | 5 | `get_host_performance()`, `get_host_quality_metrics()` |
| Customer | 5 | `get_customer_segments()`, `get_customer_ltv()` |

### Metric Views (5 views)

YAML-defined semantic views for AI/BI:

- `revenue_analytics_metrics` (8 dimensions, 10 measures)
- `engagement_analytics_metrics` (6 dimensions, 8 measures)
- `property_analytics_metrics` (10 dimensions, 8 measures)
- `host_analytics_metrics` (8 dimensions, 8 measures)
- `customer_analytics_metrics` (7 dimensions, 8 measures)

---

## Implementation Status

### Complete ✅

| Component | Count | Status |
|-----------|-------|--------|
| Bronze Tables | 16 | ✅ Complete |
| Silver Tables | 17 + 2 quarantine | ✅ Complete |
| Gold Tables | 8 (5 dim + 3 fact) | ✅ Complete |
| TVFs | 26 | ✅ Complete |
| Metric Views | 5 | ✅ Complete |
| AI/BI Dashboards | 6 | ✅ Complete |
| Lakehouse Monitors | 5 (20 custom metrics) | ✅ Complete |
| ML Models | 5 | ✅ Complete |

### Planned 📋

| Component | Count | Status |
|-----------|-------|--------|
| Genie Spaces | 5 | 📋 Planned |
| SQL Alerts | 21 | 📋 Planned |
| AI Agents (Phase 2) | 6 | 📋 Planned |
| Frontend App (Phase 3) | 1 | 📋 Planned |

---

## Configuration

### Environment Variables

Configure in `databricks.yml`:

```yaml
variables:
  catalog: your_catalog
  bronze_schema: wanderbricks_bronze
  silver_schema: wanderbricks_silver
  gold_schema: wanderbricks_gold
  ml_schema: wanderbricks_ml
  warehouse_id: "your-warehouse-id"
```

### Deployment Targets

| Target | Mode | Use Case |
|--------|------|----------|
| `dev` | development | Development and testing |
| `uat` | development | User acceptance testing |
| `prod` | production | Production deployment |

```bash
# Deploy to specific target
databricks bundle deploy -t dev
databricks bundle deploy -t prod
```

---

## Documentation

### Getting Started
- [QUICKSTART.md](QUICKSTART.md) - Fast deployment commands

### Design
- [gold_layer_design/DESIGN_SUMMARY.md](gold_layer_design/DESIGN_SUMMARY.md) - Design decisions
- [gold_layer_design/erd_complete.md](gold_layer_design/erd_complete.md) - ERD diagram

### Deployment
- [docs/deployment/DEPLOYMENT_GUIDE.md](docs/deployment/DEPLOYMENT_GUIDE.md) - Complete deployment guide

### ML
- [docs/ml/ml-models-guide.md](docs/ml/ml-models-guide.md) - ML model documentation

### Dashboards
- [dashboards/README.md](dashboards/README.md) - Dashboard inventory and import guide

### Project Plans
- [plans/README.md](plans/README.md) - Project roadmap and phases

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "dq_rules not found" | Run `silver_dq_setup_job` before DLT pipeline |
| High quarantine rate | Review quarantine reasons, adjust rules via SQL UPDATE |
| Bundle validation fails | Check YAML syntax in `databricks.yml` and `resources/*.yml` |
| Duplicate key errors | Silver source has duplicates; check deduplication logic |

### Validation Commands

```bash
# Validate bundle
databricks bundle validate

# Run Silver validation
databricks bundle run silver_validation_job -t dev

# Check deployment status
databricks bundle summary -t dev
```

---

## Contributing

### Development Workflow

1. Create feature branch from `main`
2. Make changes following [Cursor rules](.cursor/rules/)
3. Update YAML schemas if modifying Gold layer
4. Run bundle validation
5. Deploy to dev and test
6. Submit PR with description

### Schema Changes

Gold layer schemas are defined in `gold_layer_design/yaml/`. To modify:

1. Edit YAML file (single source of truth)
2. Regenerate DDL via setup scripts
3. Update downstream artifacts (TVFs, Metric Views)
4. Deploy and validate

---

## References

### Databricks Documentation
- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Unity Catalog](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Delta Live Tables](https://docs.databricks.com/workflows/delta-live-tables/index.html)
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/index.html)
- [AI/BI Dashboards](https://docs.databricks.com/dashboards/index.html)

### Design Methodology
- [Kimball Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/)
- [Medallion Architecture](https://docs.databricks.com/lakehouse/medallion.html)

---

## License

This project is for demonstration and educational purposes.

---

**Last Updated:** January 2026  
**Platform:** Databricks (Unity Catalog, Delta Lake, MLflow 3.0)  
**Deployment:** Databricks Asset Bundles
