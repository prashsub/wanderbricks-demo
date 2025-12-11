# Wanderbricks Gold Layer Design Package

**Complete dimensional model design for Wanderbricks vacation rental analytics platform.**

---

## 📦 Contents

### Design Documentation
- **[DESIGN_SUMMARY.md](./DESIGN_SUMMARY.md)** - Complete design decisions, rationale, and implementation plan
- **[erd_complete.md](./erd_complete.md)** - Mermaid ERD diagram with all dimensions, facts, and relationships
- **README.md** (this file) - Navigation guide

### Implementation Documentation ✨ NEW
- **[IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)** - Complete deployment guide, validation, and troubleshooting
- **[QUICKSTART.md](./QUICKSTART.md)** - Quick 4-command deployment reference

### YAML Schema Files

#### Dimensions (5 tables)
```
yaml/
├── identity/
│   ├── dim_user.yaml          # User dimension (SCD Type 2)
│   └── dim_host.yaml          # Host dimension (SCD Type 2)
├── property/
│   └── dim_property.yaml      # Property dimension (SCD Type 2)
├── geography/
│   └── dim_destination.yaml   # Destination dimension (Type 1)
└── time/
    └── dim_date.yaml          # Date dimension (Type 1)
```

#### Facts (3 tables)
```
yaml/
├── booking/
│   ├── fact_booking_detail.yaml    # Transaction-level bookings
│   └── fact_booking_daily.yaml     # Daily aggregated bookings
└── engagement/
    └── fact_property_engagement.yaml  # Daily engagement metrics
```

---

## 🎯 Quick Start

### Step 1: Review Design
1. Read [DESIGN_SUMMARY.md](./DESIGN_SUMMARY.md) for complete context
2. Review [erd_complete.md](./erd_complete.md) for visual model
3. Understand grain and SCD strategy decisions

### Step 2: Review YAML Schemas
- **Dimensions:** Start with `yaml/time/dim_date.yaml` (simplest)
- **Facts:** Start with `yaml/booking/fact_booking_daily.yaml` (dashboard KPIs)

### Step 3: Get Stakeholder Approval
- Share DESIGN_SUMMARY.md with business stakeholders
- Review ERD diagram in team meetings
- Confirm measures and grain definitions
- Sign off on design (section at bottom of DESIGN_SUMMARY.md)

### Step 4: Proceed to Implementation
Once design is approved, use **03b-gold-layer-implementation-prompt.md** to:
1. Generate DDL from YAML schemas
2. Create table setup scripts
3. Create MERGE scripts for data population
4. Deploy via Databricks Asset Bundles

---

## 📊 Dimensional Model Summary

### Dimensions (5)
| Dimension | SCD Type | Business Key | Contains PII | Purpose |
|---|---|---|---|---|
| dim_user | Type 2 | user_id | Yes | Customer segmentation and behavior analysis |
| dim_host | Type 2 | host_id | Yes | Host performance and quality tracking |
| dim_property | Type 2 | property_id | Yes | Listing management and pricing strategy |
| dim_destination | Type 1 | destination_id | No | Geographic market reference data |
| dim_date | Type 1 | date | No | Time-based analysis and trending |

### Facts (3)
| Fact | Grain | Source | Update Frequency |
|---|---|---|---|
| fact_booking_detail | booking_id (transaction) | silver_bookings, silver_payments | Daily |
| fact_booking_daily | property-date (daily) | fact_booking_detail (aggregated) | Daily |
| fact_property_engagement | property-date (daily) | silver_clickstream, silver_page_views | Daily |

---

## 🔑 Key Design Decisions

### 1. SCD Type 2 for User, Host, Property
**Why:** Track historical changes for pricing analysis, host quality trends, and user behavior evolution.

**Example Use Cases:**
- Analyze booking revenue at historical property prices
- Track host rating improvements over time
- Understand user country migrations and market expansion

### 2. Two Booking Facts (Detail + Daily)
**Why:** Balance query performance with analytical flexibility.

- **fact_booking_detail:** Transaction-level for detailed analysis
- **fact_booking_daily:** Pre-aggregated for fast dashboard queries

### 3. Separate Engagement Fact
**Why:** Different grain (engagement vs transaction), high volume, distinct stakeholder needs.

**Business Value:**
- Marketing team analyzes views → clicks → bookings funnel
- Property optimization based on conversion rates
- SEO and content effectiveness tracking

---

## 📈 Primary Use Cases

### Revenue Management
- Daily booking value and volume tracking
- Property-level revenue analysis
- Host performance and commission calculations
- Payment completion rate monitoring

### Marketing & Growth
- Property engagement funnel (views → clicks → bookings)
- Conversion rate optimization
- Campaign effectiveness tracking
- SEO and search visibility metrics

### Operations
- Geographic market analysis (destination performance)
- Occupancy and capacity planning
- Host quality and verification tracking
- Cancellation pattern analysis

### Customer Analytics
- User segmentation and behavior analysis
- Customer lifetime value calculations
- Booking patterns and preferences
- Lead time analysis

---

## 📋 YAML Schema Structure

Each YAML file follows this standard structure:

```yaml
# Table metadata
table_name: <name>
domain: <domain>
bronze_source: <source_tables>

# Dual-purpose description (business + technical)
description: >
  [Layer] [Type] [Purpose]. Business: [use cases]. Technical: [implementation].

# Grain definition (explicit)
grain: "One row per <what>"

# SCD strategy (1 or 2)
scd_type: <1|2>

# Primary key
primary_key:
  columns: [<column_list>]
  composite: <true|false>

# Business key (for SCD Type 2)
business_key:
  columns: [<column_list>]

# Foreign keys (applied via ALTER TABLE)
foreign_keys:
  - columns: [<fk_column>]
    references: <parent_table>(<pk_column>)
    nullable: <true|false>

# Column definitions (dual-purpose descriptions)
columns:
  - name: <column_name>
    type: <data_type>
    nullable: <true|false>
    description: >
      [Definition]. Business: [purpose, use cases, rules]. 
      Technical: [data type, format, calculation, source, constraints].

# Table properties (governance metadata)
table_properties:
  contains_pii: <true|false>
  data_classification: <confidential|internal|public>
  business_owner: <team>
  technical_owner: Data Engineering
  update_frequency: <Daily|Weekly|Static>
  retention_policy: <duration>
```

---

## 🔍 Column Description Standards

All column descriptions follow **dual-purpose format**:

**Pattern:**
```
[Natural description]. Business: [business context and use cases]. Technical: [implementation details].
```

**Example:**
```yaml
- name: net_revenue
  description: >
    Net revenue after subtracting returns from gross revenue.
    Business: The actual revenue realized from sales, primary KPI for financial reporting.
    Technical: gross_revenue - return_amount, represents true daily sales value.
```

**Benefits:**
- Business users understand purpose and use cases
- Technical users understand implementation and constraints
- LLM-friendly for AI/BI and Genie natural language queries

---

## 🎨 ERD Visualization

The complete ERD diagram shows:
- All 5 dimensions and 3 facts
- All relationships with cardinality (1:N)
- Primary keys (PK), foreign keys (FK), unique keys (UK)
- SCD Type 2 columns (effective_from, effective_to, is_current)
- Composite primary keys for aggregated facts

**View the diagram:** [erd_complete.md](./erd_complete.md)

---

## 📐 Grain Validation

### Fact Grains Defined

| Fact Table | Primary Key | Grain | Example |
|---|---|---|---|
| fact_booking_detail | booking_id | One row per booking transaction | booking_id=12345 |
| fact_booking_daily | (property_id, check_in_date) | One row per property per check-in date | property_id=789, check_in_date=2024-12-15 |
| fact_property_engagement | (property_id, engagement_date) | One row per property per engagement date | property_id=789, engagement_date=2024-12-15 |

**Grain Validation Rule:** If you can't uniquely identify a row using the grain, the grain is wrong.

---

## 🚀 Implementation Checklist

### Phase 1: Design Approval ✅
- [x] Dimensional model designed
- [x] ERD created
- [x] YAML schemas defined
- [ ] Stakeholder review completed
- [ ] Design sign-off obtained

### Phase 2: Implementation ✅ COMPLETE
- [x] Generate DDL from YAML (YAML-driven pattern)
- [x] Create table setup scripts (`setup_tables.py`, `add_fk_constraints.py`)
- [x] Create MERGE scripts (`merge_gold_tables.py`)
- [x] Create Asset Bundle jobs (`gold_setup_job.yml`, `gold_merge_job.yml`)
- [ ] Deploy and test in dev environment

**📖 See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for complete deployment instructions**  
**🚀 See [QUICKSTART.md](./QUICKSTART.md) for 4-command deployment**

### Phase 3: Semantic Layer
- [ ] Create Table-Valued Functions (TVFs)
- [ ] Create Metric Views
- [ ] Setup Lakehouse Monitoring
- [ ] Create AI/BI Dashboards
- [ ] Create Genie Spaces

---

## 📚 References

### Design Guides
- [03a-gold-layer-design-prompt.md](../../context/prompts/03a-gold-layer-design-prompt.md) - This design's source template
- [03b-gold-layer-implementation-prompt.md](../../context/prompts/03b-gold-layer-implementation-prompt.md) - Next step: implementation

### Framework Rules
- [12-gold-layer-documentation.mdc](mdc:.cursor/rules/gold/12-gold-layer-documentation.mdc) - Documentation standards
- [13-mermaid-erd-patterns.mdc](mdc:.cursor/rules/gold/13-mermaid-erd-patterns.mdc) - ERD patterns
- [24-fact-table-grain-validation.mdc](mdc:.cursor/rules/gold/24-fact-table-grain-validation.mdc) - Grain validation
- [25-yaml-driven-gold-setup.mdc](mdc:.cursor/rules/gold/25-yaml-driven-gold-setup.mdc) - YAML-driven implementation

### Official Documentation
- [Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
- [Unity Catalog Constraints](https://docs.databricks.com/data-governance/unity-catalog/constraints.html)
- [Delta Lake](https://docs.databricks.com/delta/index.html)

---

## 💡 Tips for Implementation

### YAML = Single Source of Truth
- All schema changes go through YAML first
- DDL generated from YAML at runtime
- Schema changes = YAML edits only (no code changes)
- Version control YAML files for schema versioning

### Grain First
- Always define grain explicitly before writing queries
- Validate grain with stakeholders
- Ensure primary key enforces grain uniqueness
- Test grain with sample data queries

### Dual-Purpose Documentation
- Write descriptions for both business and technical audiences
- Business section: Why? What for? Business rules?
- Technical section: How? Data type? Source? Constraints?
- No "LLM:" prefix (natural dual-purpose format)

### SCD Type 2 Best Practices
- Use surrogate keys (MD5 hash)
- Always include: effective_from, effective_to, is_current
- Facts reference business keys (not surrogate keys)
- Point-in-time joins use is_current or effective_from/to

---

## 🤝 Contributors

**Design Created:** [Date]

**Design Approved:** [Pending]

**Stakeholders:**
- Revenue Management: _________________ (Date: _____)
- Property Operations: _________________ (Date: _____)
- Data Engineering Lead: _________________ (Date: _____)
- Analytics Team Lead: _________________ (Date: _____)

---

## 📞 Support

For questions about this design:
- **Business Questions:** Contact Revenue Management Team
- **Technical Questions:** Contact Data Engineering Team
- **Schema Changes:** Submit PR to YAML files with business justification

---

**Next Step:** Use [03b-gold-layer-implementation-prompt.md](../../context/prompts/03b-gold-layer-implementation-prompt.md) to implement this design.

