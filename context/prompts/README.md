# Databricks Medallion Architecture Framework - Reusable Prompts

## Overview

This directory contains **11 production-ready prompts** for building complete Databricks Medallion Architecture implementations. Each prompt is a **template** designed to work with any industry, domain, or use case.

**Proven in Production:** These prompts were created from real implementations and generalized to be reusable for:
- ✅ Retail / E-Commerce
- ✅ Healthcare / Clinical
- ✅ Finance / Banking
- ✅ Manufacturing
- ✅ Human Resources
- ✅ Supply Chain / Logistics
- ✅ Telecom / Media
- ✅ Any other domain

**📖 Each prompt now includes:**
- 🚀 **Quick Start** section (5 min - fast track commands and key decisions)
- 📋 **Requirements** section (detailed specifications to fill in)
- 📚 **Full Implementation Guide** (comprehensive step-by-step)

**Two ways to use:**
1. **Fast Track:** Read 🚀 Quick Start, run commands, iterate
2. **Deep Dive:** Fill 📋 Requirements, follow 📚 Full Guide

---

## 🚀 Quick Start (3 Steps)

### 1. Read the Guide
📚 **Start here:** [../docs/HOW_TO_USE_FRAMEWORK_PROMPTS.md](../docs/HOW_TO_USE_FRAMEWORK_PROMPTS.md)

This shows you exactly how to use these prompts with AI assistants.

### 2. Customize for Your Use Case
📝 **Reference:** [../docs/FRAMEWORK_CUSTOMIZATION_GUIDE.md](../docs/FRAMEWORK_CUSTOMIZATION_GUIDE.md)

Learn how to adapt prompts for retail, healthcare, finance, manufacturing, etc.

### 3. Start with Bronze
🥉 **Begin here:** [01-bronze-layer-prompt.md](./01-bronze-layer-prompt.md)

Fill in "Your Requirements" section, then generate code with AI.

---

## 📁 Prompt Catalog

### Core Architecture (Required)

#### [01-bronze-layer-prompt.md](./01-bronze-layer-prompt.md)
**Raw data ingestion with Unity Catalog compliance**
- Creates Bronze Delta tables with governance metadata
- Enables Change Data Feed for downstream processing
- Automatic liquid clustering for query optimization
- **Time:** 2-3 hours | **Tables:** 5-10

#### [02-silver-layer-prompt.md](./02-silver-layer-prompt.md)
**Data quality validation with Delta Live Tables**
- Centralized DQ rules (critical vs warning)
- Streaming ingestion from Bronze
- Quarantine pattern for invalid data
- DQ monitoring views
- **Time:** 2-4 hours | **Tables:** 5-10 + quarantine + monitoring

#### [03a-gold-layer-design-prompt.md](./03a-gold-layer-design-prompt.md) + [03b-gold-layer-implementation-prompt.md](./03b-gold-layer-implementation-prompt.md)
**Business-ready analytics tables (2-phase approach)**

**Phase 1: Design (03a)**
- ERD creation with Mermaid
- YAML schema definitions (single source of truth)
- Primary/Foreign key design
- Dual-purpose documentation (business + technical)
- **Time:** 2-3 hours | **Output:** ERD + YAML files

**Phase 2: Implementation (03b)**
- YAML-driven table creation (dynamic DDL generation)
- Delta MERGE scripts with deduplication
- Schema validation (DataFrame vs DDL)
- Grain validation (fact tables)
- **Time:** 3-4 hours | **Tables:** 3-5

---

### Semantic Layer & BI (Recommended)

#### [04-metric-views-prompt.md](./04-metric-views-prompt.md)
**Semantic layer for Genie AI and BI tools**
- LLM-friendly metric definitions
- Business measures with formatting
- Dimension joins with synonyms
- **Time:** 2 hours | **Views:** 2-3

#### [09-table-valued-functions-prompt.md](./09-table-valued-functions-prompt.md)
**Pre-built queries for Genie natural language**
- Parameterized SQL functions
- Top N queries, date ranges, filters
- Genie-compatible SQL patterns
- **Time:** 2-3 hours | **Functions:** 10-15

#### [10-aibi-dashboards-prompt.md](./10-aibi-dashboards-prompt.md)
**Lakeview AI/BI visual dashboards**
- KPIs, charts, tables, filters
- 6-column grid layout
- Global filters page
- **Time:** 2-4 hours | **Dashboards:** 1-2

---

### Observability & Quality (Recommended)

#### [05-monitoring-prompt.md](./05-monitoring-prompt.md)
**Lakehouse Monitoring for data quality**
- Profile metrics (row count, nulls, min/max)
- Custom business metrics
- Drift detection
- **Time:** 2 hours | **Monitors:** 2-5

#### [07-dqx-integration-prompt.md](./07-dqx-integration-prompt.md)
**Advanced DQ diagnostics with Databricks Labs DQX**
- Detailed failure insights
- Auto-profiling for rule discovery
- Flexible quarantine strategies
- **Time:** 3-4 hours | **Integration:** Hybrid DLT+DQX

---

### Development Tools (Optional)

#### [06-genie-space-prompt.md](./06-genie-space-prompt.md)
**Natural language query interface**
- Trusted assets configuration
- Agent instructions for LLM
- Benchmark questions
- **Time:** 1-2 hours | **Spaces:** 1

#### [08-exploration-notebook-prompt.md](./08-exploration-notebook-prompt.md)
**Ad-hoc data exploration notebook**
- Dual format (Databricks + Jupyter)
- Helper functions for common tasks
- Data quality checks
- **Time:** 1 hour | **Notebooks:** 1

---

### Project Planning (Strategic)

#### [11-project-plan-prompt.md](./11-project-plan-prompt.md)
**Comprehensive phased project planning**
- 5-phase plan structure (Bronze → Gold → Use Cases → Agents)
- Agent Domain Framework for artifact organization
- 7 Phase 4 addendums (ML, TVFs, Metric Views, Monitoring, Dashboards, Genie, Alerts)
- Templates for all plan documents
- **Time:** 2-4 hours | **Output:** Complete plans/ folder with 13+ documents

---

## 🎯 Usage Patterns

### Strategic Planning First (Recommended for Large Projects)
```
11-project-plan-prompt.md        (3 hours) ← Start here for complex projects
  ↓
01-bronze-layer-prompt.md        (2 hours)
  ↓
02-silver-layer-prompt.md        (3 hours)
  ↓
... continue with full stack
```
**Result:** Clear roadmap with 85+ artifacts planned across 5 phases

### Minimum Viable Product (10-15 hours)
```
01-bronze-layer-prompt.md        (2 hours)
  ↓
02-silver-layer-prompt.md        (3 hours)
  ↓
03a-gold-layer-design-prompt.md  (2 hours) ← Design phase
  ↓
03b-gold-layer-implementation-prompt.md (3 hours) ← Implementation phase
```
**Result:** Basic Medallion Architecture with DQ validation and proper schema governance

### Recommended Stack (12-16 hours)
```
MVP (above)
  ↓
04-metric-views-prompt.md     (2 hours)
  ↓
05-monitoring-prompt.md       (2 hours)
```
**Result:** + Semantic layer + Observability

### Full Stack (18-28 hours)
```
Recommended Stack (above)
  ↓
06-genie-space-prompt.md      (1 hour)
09-table-valued-functions-prompt.md (2 hours)
10-aibi-dashboards-prompt.md  (3 hours)
```
**Result:** + Natural language queries + Dashboards

### Advanced Quality (22-32 hours)
```
Full Stack (above)
  ↓
07-dqx-integration-prompt.md  (4 hours)
```
**Result:** + Advanced DQ diagnostics and compliance

---

## 📝 How to Use These Prompts

### Step 1: Fill "Your Requirements"
Each prompt starts with a **"Your Requirements"** section. Fill this in first!

Example:
```markdown
## 📋 Your Requirements (Fill These In First)

### Project Information
- **Project Name:** customer_analytics
- **Source System:** Salesforce CRM
- **Refresh Frequency:** Daily

### Entity List
| Entity | Type | Domain | PII | Classification |
|--------|------|--------|-----|----------------|
| customers | Dimension | sales | Yes | confidential |
| orders | Fact | sales | No | internal |
```

### Step 2: Replace Placeholders
When using code examples, replace:
- `{project}` → your_project
- `{source_system}` → Your Source Name
- `{entity}` → your_table_name
- `{domain}` → sales, healthcare, finance, etc.

### Step 3: Generate with AI
Use with your AI coding assistant:
```
Using prompt 01-bronze-layer-prompt.md, generate Bronze layer for:
- Project: customer_analytics
- Source: Salesforce CRM (daily batch)
- Entities: customers (dim), contacts (dim), opportunities (fact)
```

### Step 4: Deploy & Test
```bash
databricks bundle deploy -t dev
databricks bundle run bronze_setup_job
```

---

## 🌐 Domain Adaptation Examples

### Retail → Healthcare
```
store         → hospital / clinic
product       → medication / diagnosis
transaction   → encounter / admission
revenue       → cost / reimbursement
units_sold    → patient_count / procedures
```

### Retail → Finance
```
store         → branch / account
product       → financial_product
transaction   → transaction (same!)
revenue       → interest_income / fees
units_sold    → volume / balance
```

### Retail → Manufacturing
```
store         → facility / plant
product       → component / finished_good
transaction   → production_run / quality_check
revenue       → output_value / yield
units_sold    → production_volume
```

---

## ✅ What You Get

After using all prompts, you'll have:

### Infrastructure (Bronze → Silver → Gold)
- ✅ 5-10 Bronze tables (raw ingestion)
- ✅ 5-10 Silver tables (validated + streaming)
- ✅ 3-5 Gold tables (analytics-ready)
- ✅ Databricks Asset Bundles for deployment

### Data Quality
- ✅ 20-50 centralized DQ rules
- ✅ Quarantine tables for invalid data
- ✅ DQ monitoring views
- ✅ Lakehouse Monitors with custom metrics

### Semantic Layer & BI
- ✅ 2-3 Metric Views for Genie AI
- ✅ 10-15 Table-Valued Functions
- ✅ Genie Space with natural language queries
- ✅ Lakeview dashboards with KPIs

### Governance & Documentation
- ✅ Unity Catalog compliance (all tables)
- ✅ PII tagging and data classification
- ✅ Complete table/column descriptions
- ✅ PRIMARY KEY / FOREIGN KEY constraints

### Time Savings
- ⏱️ **Framework:** 18-28 hours total
- ⏱️ **From Scratch:** 80-120 hours
- 🚀 **Savings:** 60-90 hours (4-6x faster)

---

## 📚 Documentation Index

| Document | Purpose |
|----------|---------|
| [HOW_TO_USE_FRAMEWORK_PROMPTS.md](../docs/HOW_TO_USE_FRAMEWORK_PROMPTS.md) | Step-by-step usage guide with examples |
| [FRAMEWORK_CUSTOMIZATION_GUIDE.md](../docs/FRAMEWORK_CUSTOMIZATION_GUIDE.md) | Domain adaptation (retail, healthcare, etc.) |
| [FRAMEWORK_IMPLEMENTATION_STATUS.md](../docs/FRAMEWORK_IMPLEMENTATION_STATUS.md) | Development status and roadmap |
| [../examples/reference_implementation/](../examples/reference_implementation/) | Complete reference implementation |
| [../../.cursor/rules/](../../.cursor/rules/) | AI assistant patterns and rules |

---

## 🎓 Learning Path

### Week 0 (Optional but Recommended): Strategic Planning
- Day 1-2: Project Planning (Prompt 11) - Create comprehensive phased plan
- **Output:** Complete `plans/` folder with roadmap for entire implementation

### Week 1: Core Architecture
- Day 1-2: Bronze layer (Prompt 01)
- Day 3-4: Silver layer (Prompt 02)
- Day 5: Gold layer design (Prompt 03a)

### Week 2: Gold Implementation & Semantic Layer
- Day 1-2: Gold layer implementation (Prompt 03b)
- Day 3-4: Metric Views (Prompt 04)
- Day 5: Table-Valued Functions (Prompt 09)

### Week 3: Genie & Observability
- Day 1-2: Genie Space (Prompt 06)
- Day 3-4: Lakehouse Monitoring (Prompt 05)
- Day 5: DQX Integration intro (Prompt 07)

### Week 4: Advanced Quality & Visualization
- Day 1-3: DQX Integration advanced (Prompt 07)
- Day 4-5: AI/BI Dashboards (Prompt 10)

### Week 5: Exploration & Polish
- Day 1: Exploration Notebooks (Prompt 08)
- Day 2-5: Polish, optimize, and document

---

## 🛠️ Requirements

### Technical Prerequisites
- Databricks workspace (AWS, Azure, or GCP)
- Unity Catalog enabled
- SQL Warehouse (serverless recommended)
- Databricks CLI installed
- Git for version control

### Knowledge Prerequisites
- Basic SQL knowledge
- Understanding of dimensional modeling
- Familiarity with Delta Lake concepts
- Experience with AI coding assistants (helpful)

---

## 💡 Pro Tips

1. **Start Small:** Begin with 3-5 tables, not 50
2. **Test with Faker:** Generate sample data before connecting real sources
3. **Use Git:** Version control everything from day 1
4. **Deploy to Dev First:** Test thoroughly before production
5. **Customize, Don't Copy:** Adapt examples to your specific needs
6. **Leverage AI:** These prompts are optimized for AI assistants
7. **Read the Docs:** Each prompt links to official Databricks documentation

---

## 🐛 Troubleshooting

### "I don't know what my domain is"
**Answer:** Use: sales, inventory, product, clinical, patient, finance, etc. It's just a tag for organization.

### "My data doesn't fit the examples"
**Answer:** All prompts are templates. The examples show patterns - adapt column names, data types, and business logic for your data.

### "I'm not in retail"
**Answer:** See [FRAMEWORK_CUSTOMIZATION_GUIDE.md](../docs/FRAMEWORK_CUSTOMIZATION_GUIDE.md) for healthcare, finance, manufacturing, and other domain mappings.

### "I need help with a specific prompt"
**Answer:** Each prompt has:
- Quick Reference at the top
- Step-by-step instructions
- Complete examples
- Common mistakes to avoid
- References to official docs

---

## 📞 Support

### Self-Service Resources
1. Read prompt-specific documentation
2. Check [HOW_TO_USE_FRAMEWORK_PROMPTS.md](../docs/HOW_TO_USE_FRAMEWORK_PROMPTS.md)
3. Review [../examples/reference_implementation/](../examples/reference_implementation/) for working code
4. Consult Databricks official docs (links in each prompt)

### Framework Evolution
These prompts are maintained and improved based on:
- Real production implementations
- User feedback and use cases
- Databricks platform updates
- Best practice evolution

---

## 🎯 Success Metrics

After completing the framework, you should have:
- ✅ End-to-end data pipeline (Bronze → Silver → Gold)
- ✅ Data quality monitoring and alerting
- ✅ Self-service analytics for business users
- ✅ Natural language query capability
- ✅ Production-grade governance and compliance
- ✅ 20x faster than building from scratch
- ✅ Reusable patterns for future projects

---

## 🚀 Get Started Now

1. **Read:** [HOW_TO_USE_FRAMEWORK_PROMPTS.md](../docs/HOW_TO_USE_FRAMEWORK_PROMPTS.md)
2. **Customize:** [FRAMEWORK_CUSTOMIZATION_GUIDE.md](../docs/FRAMEWORK_CUSTOMIZATION_GUIDE.md)
3. **Build:** Start with [01-bronze-layer-prompt.md](./01-bronze-layer-prompt.md)

**Time to first deployment: 10-15 hours (includes proper design phase)**  
**Complete framework: 20-30 hours**

Good luck building your Medallion Architecture! 🏗️✨


