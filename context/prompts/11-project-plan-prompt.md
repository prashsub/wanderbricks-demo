# 11: Project Plan Prompt

**Create a comprehensive phased project plan for Databricks Medallion Architecture implementations**

---

## 🚀 Quick Start (5 Minutes)

### Fast Track: Create Your Project Plan

```bash
# 1. Understand your scope
#    - How many Bronze/Silver/Gold tables?
#    - What analytics use cases?
#    - What stakeholders need access?

# 2. Run this prompt with your project info:
"Create a phased project plan for {project_name} with:
- {n} Bronze tables from {source_system}
- {m} Gold tables (dimensions + facts)
- Use cases: {revenue analysis, marketing, operations, etc.}
- Target audience: {executives, analysts, data scientists}"

# 3. Output: Complete plan structure in plans/ folder
```

### Key Decisions (Answer These First)

| Decision | Options | Your Choice |
|----------|---------|-------------|
| Agent Domains | Define 4-6 business domains | __________ |
| Phase 4 Addendums | TVFs, Metric Views, Dashboards, Monitoring, Genie, Alerts, ML | __________ |
| Phase 5 Scope | AI Agents (optional) or skip | __________ |
| Artifact Counts | Min per domain: TVFs (4+), Alerts (4+), etc. | __________ |

---

## 📋 Your Requirements (Fill These In First)

### Project Information

| Field | Your Value |
|-------|------------|
| Project Name | {project_name} |
| Business Domain | {hospitality, retail, healthcare, finance, etc.} |
| Primary Use Cases | {revenue tracking, customer analytics, operations, etc.} |
| Target Stakeholders | {executives, analysts, data scientists, operations} |

### Data Layer Scope

| Layer | Count | Status |
|-------|-------|--------|
| Bronze Tables | {n} | {✅ Complete / 🔧 In Progress / 📋 Planned} |
| Silver Tables | {m} | {status} |
| Gold Dimensions | {d} | {status} |
| Gold Facts | {f} | {status} |

### Agent Domain Framework

Define your business domains (typically 4-6):

| Domain | Icon | Focus Area | Key Gold Tables |
|--------|------|------------|-----------------|
| {Domain 1} | {emoji} | {focus} | {tables} |
| {Domain 2} | {emoji} | {focus} | {tables} |
| {Domain 3} | {emoji} | {focus} | {tables} |
| {Domain 4} | {emoji} | {focus} | {tables} |
| {Domain 5} | {emoji} | {focus} | {tables} |

**Common Domain Patterns:**

| Industry | Domains |
|----------|---------|
| Hospitality | 💰 Revenue, 📊 Engagement, 🏠 Property, 👤 Host, 🎯 Customer |
| Retail | 💰 Sales, 📦 Inventory, 🏪 Store, 👤 Customer, 📊 Marketing |
| Healthcare | 👨‍⚕️ Clinical, 💰 Financial, 📊 Operations, 🏥 Facility, 👤 Patient |
| Finance | 💰 Revenue, 🔒 Risk, 📊 Compliance, 👤 Customer, ⚡ Operations |
| SaaS | 💰 Revenue, 📊 Product, 👤 Customer, ⚡ Performance, 🔒 Security |

### Phase 4 Addendum Selection

Select which addendums to include:

| # | Addendum | Include? | Artifact Count |
|---|----------|----------|----------------|
| 4.1 | ML Models | {Yes/No} | {count} |
| 4.2 | Table-Valued Functions | {Yes/No} | {count} |
| 4.3 | Metric Views | {Yes/No} | {count} |
| 4.4 | Lakehouse Monitoring | {Yes/No} | {count} |
| 4.5 | AI/BI Dashboards | {Yes/No} | {count} |
| 4.6 | Genie Spaces | {Yes/No} | {count} |
| 4.7 | Alerting Framework | {Yes/No} | {count} |

### Key Business Questions by Domain

List 5-10 key questions per domain that the solution must answer:

**{Domain 1}:**
1. {Question 1}
2. {Question 2}
3. {Question 3}
4. {Question 4}
5. {Question 5}

**{Domain 2}:**
1. {Question 1}
2. {Question 2}
...

---

## 📚 Full Implementation Guide

### Plan Structure Overview

A complete project plan follows this structure:

```
plans/
├── README.md                              # Index and overview
├── phase1-bronze-ingestion.md             # Data ingestion layer
├── phase2-silver-layer.md                 # DLT streaming + DQ
├── phase3-gold-layer.md                   # Dimensional model
├── phase4-use-cases.md                    # Analytics artifacts (master)
│   ├── phase4-addendum-4.1-ml-models.md
│   ├── phase4-addendum-4.2-tvfs.md
│   ├── phase4-addendum-4.3-metric-views.md
│   ├── phase4-addendum-4.4-lakehouse-monitoring.md
│   ├── phase4-addendum-4.5-aibi-dashboards.md
│   ├── phase4-addendum-4.6-genie-spaces.md
│   └── phase4-addendum-4.7-alerting.md
└── phase5-ai-agents.md                    # AI agent framework (optional)
```

### Phase Dependencies

```
Phase 1 (Bronze) → Phase 2 (Silver) → Phase 3 (Gold) → Phase 4 (Use Cases) → Phase 5 (Agents)
                                                              ↓
                                                        All Addendums
```

---

## Phase Document Templates

### Phase 1: Bronze Layer Template

```markdown
# Phase 1: Bronze Layer - Raw Data Ingestion

## Overview

**Status:** {✅ Complete / 🔧 In Progress / 📋 Planned}
**Schema:** `{project}_bronze` or `{project}`
**Tables:** {n}
**Dependencies:** None (source layer)

---

## Purpose

{2-3 sentences explaining the Bronze layer's role}

---

## Bronze Tables Summary

### {Category 1} ({count} tables)

| Table | Primary Key | Description |
|-------|-------------|-------------|
| {table_1} | {pk} | {description} |
| {table_2} | {pk} | {description} |

### {Category 2} ({count} tables)

| Table | Primary Key | Description |
|-------|-------------|-------------|
| {table_3} | {pk} | {description} |

---

## Table Properties

All Bronze tables include:

```sql
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'layer' = 'bronze',
    'source_system' = '{source_system}',
    'domain' = '{domain}'
)
CLUSTER BY AUTO
```

---

## Implementation Checklist

- [ ] Create schema with Predictive Optimization
- [ ] Create all Bronze tables
- [ ] Enable Change Data Feed
- [ ] Enable automatic liquid clustering
- [ ] Apply governance tags
- [ ] Initial data load complete

---

## Next Phase

**→ [Phase 2: Silver Layer](./phase2-silver-layer.md)**
```

### Phase 2: Silver Layer Template

```markdown
# Phase 2: Silver Layer - DLT Streaming & Data Quality

## Overview

**Status:** {status}
**Schema:** `{project}_silver`
**Tables:** {n} streaming tables
**Dependencies:** Phase 1 (Bronze Layer)

---

## Purpose

{Explain DLT streaming, DQ expectations, quarantine pattern}

---

## Silver Tables Architecture

### Dimension Tables ({count})

| Silver Table | Source Bronze | DQ Expectations | Quarantine |
|-------------|---------------|-----------------|------------|
| silver_{entity}_dim | {entity} | {n}+ | Yes/No |

### Fact Tables ({count})

| Silver Table | Source Bronze | DQ Expectations | Quarantine |
|-------------|---------------|-----------------|------------|
| silver_{entity} | {entity} | {n}+ | Yes/No |

---

## Data Quality Expectations by Domain

### {Domain 1}: silver_{entity}

| Expectation | Rule | Action |
|-------------|------|--------|
| valid_{column} | `{column} IS NOT NULL` | DROP/QUARANTINE/WARN |

---

## DLT Pipeline Configuration

```yaml
resources:
  pipelines:
    silver_dlt_pipeline:
      name: "[${bundle.target}] {Project} Silver Pipeline"
      catalog: ${var.catalog}
      schema: ${var.silver_schema}
      root_path: ../src/{project}_silver
      serverless: true
      photon: true
      edition: ADVANCED
```

---

## Implementation Checklist

- [ ] Create DLT pipeline configuration
- [ ] Implement dimension streaming tables
- [ ] Implement fact streaming tables
- [ ] Configure DQ expectations
- [ ] Setup quarantine tables
- [ ] Create validation jobs

---

## Next Phase

**→ [Phase 3: Gold Layer](./phase3-gold-layer.md)**
```

### Phase 3: Gold Layer Template

```markdown
# Phase 3: Gold Layer - Dimensional Model Implementation

## Overview

**Status:** {status}
**Schema:** `{project}_gold`
**Tables:** {n} ({d} dimensions + {f} facts)
**Dependencies:** Phase 2 (Silver Layer)

---

## Purpose

{Explain star schema, SCD Type 2, business-ready aggregates}

---

## Dimensional Model Summary

### Dimensions ({d})

| # | Table | SCD Type | Business Key | PII | Domain |
|---|-------|----------|--------------|-----|--------|
| 1 | dim_{entity} | Type 1/2 | {key} | Yes/No | {domain} |

### Facts ({f})

| # | Table | Grain | Domain |
|---|-------|-------|--------|
| 1 | fact_{entity} | {grain description} | {domain} |

---

## ERD Overview

```
{Include Mermaid ERD or link to ERD file}
```

---

## Implementation Approach

Gold tables are created dynamically from YAML schema definitions:

```
gold_layer_design/yaml/
├── {domain1}/
│   ├── dim_{entity}.yaml
│   └── fact_{entity}.yaml
├── {domain2}/
│   └── ...
```

---

## Implementation Checklist

- [ ] Create schema with Predictive Optimization
- [ ] Create all dimension tables
- [ ] Create all fact tables
- [ ] Apply PRIMARY KEY constraints
- [ ] Apply FOREIGN KEY constraints
- [ ] Implement MERGE scripts
- [ ] Validate data population

---

## Next Phase

**→ [Phase 4: Use Cases](./phase4-use-cases.md)**
```

### Phase 4: Use Cases Master Template

```markdown
# Phase 4: Use Cases - Analytics Artifacts

## Overview

**Status:** {status}
**Dependencies:** Phase 3 (Gold Layer)
**Estimated Effort:** {weeks}

---

## Purpose

{Explain TVFs, Metric Views, Dashboards, Monitoring, Genie, Alerts}

---

## Agent Domain Framework

| Domain | Icon | Focus Area | Primary Tables |
|--------|------|------------|----------------|
| {Domain 1} | {emoji} | {focus} | {tables} |

---

## Addendum Index

| # | Addendum | Status | Artifacts |
|---|----------|--------|-----------|
| 4.1 | ML Models | {status} | {count} |
| 4.2 | TVFs | {status} | {count} |
| 4.3 | Metric Views | {status} | {count} |
| 4.4 | Lakehouse Monitoring | {status} | {count} |
| 4.5 | AI/BI Dashboards | {status} | {count} |
| 4.6 | Genie Spaces | {status} | {count} |
| 4.7 | Alerting | {status} | {count} |

---

## Artifact Summary by Domain

### {Domain 1}

| Artifact Type | Count | Examples |
|--------------|-------|----------|
| TVFs | {n} | `get_{metric}_by_{dimension}` |
| Metric Views | {n} | `{domain}_analytics_metrics` |
| Dashboards | {n} | {Domain} Performance Dashboard |
| Monitors | {n} | {Domain} Data Quality Monitor |
| Alerts | {n} | {metric} drop, {anomaly} |
| ML Models | {n} | {Type} Predictor/Forecaster |
| Genie Space | 1 | {Domain} Intelligence |

---

## Key Business Questions by Domain

### {Domain 1}

1. {Question 1}?
2. {Question 2}?
...

---

## Implementation Order

### Week 1: Foundation
1. Deploy Gold layer tables
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
12. Integrate predictions

---

## Success Criteria

| Metric | Target |
|--------|--------|
| TVFs deployed and functional | {count} |
| Metric Views queryable | {count} |
| Dashboards published | {count} |
| Monitors with baselines | {count} |
| Alerts configured | {count} |
| Genie Spaces responding | {count} |
```

---

## Addendum Templates

### Phase 4 Addendum 4.2: TVFs Template

```markdown
# Phase 4 Addendum 4.2: Table-Valued Functions (TVFs)

## Overview

**Status:** {status}
**Dependencies:** Phase 3 (Gold Layer)
**Artifact Count:** {n} TVFs

---

## TVF Summary by Domain

| Domain | Icon | TVF Count | Primary Tables |
|--------|------|-----------|----------------|
| {Domain 1} | {emoji} | {n} | {tables} |

---

## {Domain 1} TVFs

### 1. get_{metric}_by_{dimension}

**Purpose:** {description}

```sql
CREATE OR REPLACE FUNCTION ${catalog}.${gold_schema}.get_{metric}_by_{dimension}(
    start_date STRING COMMENT 'Start date in YYYY-MM-DD format',
    end_date STRING COMMENT 'End date in YYYY-MM-DD format',
    filter_param {TYPE} DEFAULT NULL COMMENT 'Optional filter'
)
RETURNS TABLE (
    {column_1} {TYPE},
    {column_2} {TYPE},
    {measure_1} {TYPE}
)
COMMENT 'LLM: {Description for Genie}.
Use for: {use cases}.
Example questions: "{Question 1}" "{Question 2}"'
RETURN
    SELECT 
        ...
    FROM ${catalog}.${gold_schema}.{fact_table}
    WHERE {date_column} BETWEEN CAST(start_date AS DATE) AND CAST(end_date AS DATE)
    GROUP BY ...
    ORDER BY ...;
```

---

## TVF Design Standards

### Parameter Requirements

```sql
-- ✅ CORRECT: STRING dates for Genie compatibility
start_date STRING COMMENT 'Start date in YYYY-MM-DD format'

-- ❌ WRONG: DATE type breaks Genie
start_date DATE
```

### Comment Structure

```sql
COMMENT 'LLM: [One-line description].
Use for: [Use cases separated by commas].
Example questions: "[Question 1]" "[Question 2]"'
```

---

## Implementation Checklist

### {Domain 1} TVFs
- [ ] get_{metric1}_by_{dimension}
- [ ] get_{metric2}_by_{dimension}
- [ ] get_top_{entities}_by_{metric}
```

### Phase 4 Addendum 4.7: Alerting Template

```markdown
# Phase 4 Addendum 4.7: Alerting Framework

## Overview

**Status:** {status}
**Dependencies:** Phase 3 (Gold Layer), 4.4 (Lakehouse Monitoring)
**Artifact Count:** {n} SQL Alerts

---

## Alert Summary by Domain

| Domain | Icon | Alert Count | Critical | Warning | Info |
|--------|------|-------------|----------|---------|------|
| {Domain 1} | {emoji} | {n} | {c} | {w} | {i} |

---

## Alert ID Convention

```
<DOMAIN>-<NUMBER>-<SEVERITY>
```

Examples:
- `{DOM}-001-CRIT` - {Domain} critical alert #1
- `{DOM}-002-WARN` - {Domain} warning alert #2

---

## {Domain 1} Alerts

### {DOM}-001-CRIT: {Alert Name}

**Severity:** 🔴 Critical
**Frequency:** {Daily/Hourly/Weekly}
**Condition:** {Description}

```sql
SELECT 
    CURRENT_DATE() as alert_date,
    {metric} as current_value,
    {threshold} as threshold,
    '{message}' as alert_message
FROM ${catalog}.${gold_schema}.{table}
WHERE {condition}
```

**Actions:**
- Email: {recipients}
- Slack: #{channel}

---

## Implementation Checklist

### {Domain 1} Alerts
- [ ] {DOM}-001-CRIT: {Alert Name}
- [ ] {DOM}-002-WARN: {Alert Name}
- [ ] {DOM}-003-INFO: {Alert Name}
```

---

## README.md Template

```markdown
# {Project Name} Project Plans

**Complete phased implementation plan for {Project Description}**

---

## 📋 Plan Index

### Core Phases

| Phase | Document | Status | Description |
|-------|----------|--------|-------------|
| 1 | [Phase 1: Bronze Layer](./phase1-bronze-ingestion.md) | {status} | Raw data ingestion ({n} tables) |
| 2 | [Phase 2: Silver Layer](./phase2-silver-layer.md) | {status} | DLT streaming with DQ |
| 3 | [Phase 3: Gold Layer](./phase3-gold-layer.md) | {status} | Dimensional model ({n} tables) |
| 4 | [Phase 4: Use Cases](./phase4-use-cases.md) | {status} | Analytics artifacts |
| 5 | [Phase 5: AI Agents](./phase5-ai-agents.md) | {status} | Natural language agents |

### Phase 4 Addendums

| # | Addendum | Status | Artifacts |
|---|----------|--------|-----------|
| 4.1 | [ML Models](./phase4-addendum-4.1-ml-models.md) | {status} | {count} |
| 4.2 | [TVFs](./phase4-addendum-4.2-tvfs.md) | {status} | {count} |
...

---

## 🎯 Agent Domain Framework

| Domain | Icon | Focus Area | Key Gold Tables |
|--------|------|------------|-----------------|
| {Domain 1} | {emoji} | {focus} | {tables} |

---

## 📊 Project Scope Summary

### Data Layers

| Layer | Schema | Tables | Status |
|-------|--------|--------|--------|
| Bronze | `{schema}` | {n} | {status} |
| Silver | `{schema}` | {n} | {status} |
| Gold | `{schema}` | {n} | {status} |

---

## 📈 Success Metrics

| Phase | Criteria | Target |
|-------|----------|--------|
| Silver | DQ expectations passing | >95% |
| Gold | All tables deployed | {n} tables |
| Use Cases | TVFs deployed | {n}+ |
| Use Cases | Dashboards created | {n}+ |
```

---

## ✅ Validation Checklist

### Plan Structure
- [ ] README.md with index and overview
- [ ] Phase 1-5 documents created
- [ ] All Phase 4 addendums included
- [ ] Cross-references between documents

### Content Quality
- [ ] Agent Domains defined consistently
- [ ] All artifacts tagged with domain
- [ ] Business questions documented per domain
- [ ] Implementation checklists in each phase
- [ ] Success criteria tables included

### Completeness
- [ ] All domains covered (4-6 minimum)
- [ ] Minimum artifact counts per domain:
  - [ ] TVFs: 4+ per domain
  - [ ] Alerts: 4+ per domain  
  - [ ] Dashboard pages: 2+ per domain
- [ ] Key business questions answered

---

## 🎯 Example: Hospitality (Wanderbricks)

### Agent Domains

| Domain | Icon | Focus Area | Key Tables |
|--------|------|------------|------------|
| Revenue | 💰 | Booking revenue, payments | fact_booking_daily, fact_booking_detail |
| Engagement | 📊 | Views, clicks, conversions | fact_property_engagement |
| Property | 🏠 | Listings, pricing | dim_property |
| Host | 👤 | Host performance | dim_host |
| Customer | 🎯 | User behavior, CLV | dim_user |

### Artifact Totals

| Artifact Type | Count |
|--------------|-------|
| Gold Tables | 8 |
| TVFs | 25+ |
| Metric Views | 5 |
| Dashboards | 5 |
| Monitors | 5 |
| Alerts | 21 |
| ML Models | 5 |
| Genie Spaces | 5 |
| AI Agents | 6 |
| **Total** | **85+** |

---

## 📚 References

### Related Prompts
- [01-bronze-layer-prompt.md](./01-bronze-layer-prompt.md) - Bronze implementation
- [02-silver-layer-prompt.md](./02-silver-layer-prompt.md) - Silver implementation
- [03a-gold-layer-design-prompt.md](./03a-gold-layer-design-prompt.md) - Gold design
- [03b-gold-layer-implementation-prompt.md](./03b-gold-layer-implementation-prompt.md) - Gold implementation
- [04-metric-views-prompt.md](./04-metric-views-prompt.md) - Metric Views
- [05-monitoring-prompt.md](./05-monitoring-prompt.md) - Lakehouse Monitoring
- [09-table-valued-functions-prompt.md](./09-table-valued-functions-prompt.md) - TVFs
- [10-aibi-dashboards-prompt.md](./10-aibi-dashboards-prompt.md) - Dashboards

### Cursor Rules
- [26-project-plan-methodology.mdc](../.cursor/rules/planning/26-project-plan-methodology.mdc) - Full methodology

### Official Documentation
- [Databricks Docs](https://docs.databricks.com/)
- [Unity Catalog](https://docs.databricks.com/unity-catalog/)
- [Delta Live Tables](https://docs.databricks.com/dlt/)
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/)
- [Metric Views](https://docs.databricks.com/metric-views/)
- [Genie Spaces](https://docs.databricks.com/genie/)

