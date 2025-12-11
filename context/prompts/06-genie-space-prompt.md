# Genie Space Setup Prompt

## 🚀 Quick Start (1 hour)

**Goal:** Enable natural language queries for business users (no SQL required)

**Prerequisites:** ⚠️ Complete FIRST:
- ✅ Metric Views created (semantic layer)
- ✅ Table-Valued Functions created (common queries)
- ✅ Gold layer tables (with rich descriptions)

**What You'll Configure:**
1. **Trusted Assets** - Tables, views, and functions Genie can use
2. **Agent Instructions** - Business context and query patterns
3. **Benchmark Questions** - Test cases to validate Genie performance

**Fast Track (UI-Based):**
```
1. Navigate to: Databricks Workspace → Genie Spaces → Create New
2. Add Trusted Assets:
   - All Metric Views from Gold schema
   - All TVFs from Gold schema
   - Gold dimension/fact tables (if needed)
3. Configure Agent Instructions (comprehensive context)
4. Add 10-15 Benchmark Questions
5. Test queries: "Show top 10 stores by revenue last month"
```

**Agent Instructions Template:**
```markdown
# Data Assets
- Metric Views: sales_performance_metrics, inventory_metrics
- Key Dimensions: store, product, date
- Key Measures: revenue, units, transactions
- Functions: get_top_stores_by_revenue(), get_store_performance()

# Business Context
- [Your domain-specific context]

# Query Patterns
- [Common question patterns]
```

**Benchmark Questions (Test Cases):**
- Top N queries: "Top 10 stores by revenue"
- Trending: "Revenue trend last 90 days"
- Comparison: "Compare stores A vs B"
- Drill-down: "Product performance in California"

**Output:** Business users can query data via natural language

📖 **Full guide below** for detailed setup →

---

## Quick Reference

**Use this prompt when setting up a Databricks Genie Space for natural language queries.**

**Input Required:**
- Metric Views (already created)
- Table-Valued Functions (already created)
- Gold layer tables
- Common business questions

**Output:** Genie Space with trusted assets, agent instructions, and benchmark questions.

**Time Estimate:** 1-2 hours

---

## Core Philosophy: Natural Language Data Access

**⚠️ CRITICAL PRINCIPLE:**

Genie Spaces enable **business users to query data using natural language**:

- ✅ **Trusted Assets:** Curated tables, views, and functions
- ✅ **Agent Instructions:** Comprehensive context for query understanding
- ✅ **Benchmark Questions:** Test cases for validation
- ✅ **Metric Views:** Semantic layer with synonyms
- ✅ **Table-Valued Functions:** Pre-built common queries
- ❌ **No Raw Tables:** Use views and semantic layers

**Why This Matters:**
- Democratizes data access (no SQL knowledge required)
- Reduces repetitive analyst queries
- Ensures consistent metric definitions
- Captures business logic in natural language

---

## Step 1: Genie Space Setup (UI-Based)

### Create Genie Space

**Navigate to:** Databricks Workspace → Genie Spaces → Create New

1. **Space Name:** `{Project} Analytics Space`
2. **Description:** "Natural language interface for {project} sales, inventory, and product analytics"
3. **SQL Warehouse:** Select serverless SQL warehouse
4. **Permissions:** Grant access to business user groups

---

## Step 2: Add Trusted Assets

### Asset Selection Strategy

**Priority Order:**
1. **Metric Views** (highest priority - semantic layer)
2. **Table-Valued Functions** (common queries)
3. **Gold dimension tables** (for dimension lookups)
4. **Gold fact tables** (if needed, but prefer Metric Views)

### Assets to Add

```
Trusted Assets:
├── Metric Views (Primary)
│   ├── sales_performance_metrics
│   └── inventory_performance_metrics (if applicable)
│
├── Table-Valued Functions (Common Queries)
│   ├── get_sales_by_store(store_number, start_date, end_date)
│   ├── get_top_products(limit, start_date, end_date)
│   ├── get_store_performance(store_number, start_date, end_date)
│   └── ... (5-10 TVFs)
│
└── Gold Tables (Context)
    ├── dim_store (for store lookups)
    ├── dim_product (for product lookups)
    └── dim_date (for date context)
```

**In Genie UI:**
1. Click **"Add Trusted Assets"**
2. Search for each asset
3. Select and add
4. Repeat for all assets

---

## Step 3: Agent Instructions

### Comprehensive Instructions Template

```markdown
# {Project} Analytics Genie Agent Instructions

You are an expert data analyst for {Project Name}, helping users analyze sales, inventory, and product performance data. Follow these guidelines:

## Data Sources

### Primary Data Sources (Use These First)

**CUSTOMIZE THIS SECTION:** Replace with your actual metric view names and measures

1. **{your_primary_metric_view}** - {Description of what this metric view contains}
   - Use for: {Types of questions this answers}
   - Key measures: {List your actual measures - e.g., Total Revenue, Count, Average}
   - Dimensions: {List your actual dimensions - e.g., Location, Product, Customer, Date}

**Example (Retail):**
1. **sales_performance_metrics** - Comprehensive sales metrics
   - Use for: Revenue queries, sales trends, store performance
   - Key measures: Total Revenue, Total Units, Transaction Count
   - Dimensions: Store, Product, Date

**Example (Healthcare):**
1. **patient_outcomes_metrics** - Patient treatment outcomes and metrics
   - Use for: Treatment efficacy, readmission analysis
   - Key measures: Patient Count, Readmission Rate, Average Length of Stay
   - Dimensions: Provider, Diagnosis, Date

2. **Table-Valued Functions (TVFs)** - Pre-built queries for common analyses
   - `get_sales_by_store(store_number, start_date, end_date)` - Store-specific sales details
   - `get_top_products(limit, start_date, end_date)` - Top N products by revenue
   - `get_store_performance(store_number, start_date, end_date)` - Comprehensive store metrics
   - Use TVFs when they match the user's question exactly

### Dimension Tables (For Lookups)
- **dim_store** - Store details (name, address, city, state)
- **dim_product** - Product details (brand, category, UPC)
- **dim_date** - Calendar attributes (year, quarter, month, weekday, weekend)

## Query Guidelines

### Revenue Queries
- **Use:** `MEASURE(\`Total Revenue\`)` from sales_performance_metrics
- **Aggregation:** Already aggregated at daily grain, use SUM/AVG as needed
- **Filters:** Store name, city, state, brand, category, date ranges

### Unit/Volume Queries
- **Use:** `MEASURE(\`Total Units\`)` from sales_performance_metrics
- **Context:** Net units after returns
- **Analysis:** Trend analysis, store comparison, product performance

### Transaction Queries
- **Use:** `MEASURE(\`Transaction Count\`)` from sales_performance_metrics
- **Metrics:** Customer traffic, conversion, transaction velocity

### Store Performance
- **Best Approach:** Use `get_store_performance()` TVF for comprehensive view
- **Alternative:** Query sales_performance_metrics filtered by store
- **Dimensions:** Store name, city, state for grouping

### Product Analysis
- **Best Approach:** Use `get_top_products()` TVF for rankings
- **Alternative:** sales_performance_metrics grouped by brand/category
- **Metrics:** Revenue, units, transaction count per product

### Time-Based Analysis
- **Dimensions:** year, quarter, month_name, is_weekend from dim_date
- **Comparisons:** Use WHERE clause for date ranges (e.g., "last 30 days")
- **Trending:** Use ORDER BY transaction_date for time series

## Response Format

### For Tabular Results
- Return clean, formatted tables
- Include relevant columns only
- Sort by most relevant metric (usually revenue DESC)
- Limit to reasonable row count (10-20 for top N queries)

### For Summary Statistics
- Provide context (time period, filters applied)
- Show key metrics: Total Revenue, Total Units, Transaction Count
- Include comparisons when relevant (YoY, MoM)

### For Trends
- Use line charts when showing time-based data
- Include trend indicators (up/down, % change)
- Highlight anomalies or significant changes

## Common Query Patterns

### "Show me revenue by store"
```sql
SELECT 
  store_name,
  MEASURE(\`Total Revenue\`) as revenue
FROM sales_performance_metrics
GROUP BY store_name
ORDER BY revenue DESC
LIMIT 10
```

### "Top 10 products by sales"
```sql
SELECT * FROM get_top_products(10, CURRENT_DATE - INTERVAL 30 DAYS, CURRENT_DATE)
```

### "Store performance for Store 12345"
```sql
SELECT * FROM get_store_performance('12345', CURRENT_DATE - INTERVAL 90 DAYS, CURRENT_DATE)
```

### "Sales trend by month"
```sql
SELECT 
  month_name,
  year,
  MEASURE(\`Total Revenue\`) as revenue
FROM sales_performance_metrics
GROUP BY month_name, year
ORDER BY year, month_name
```

## Important Notes

- **Date Ranges:** Default to last 30 days if not specified
- **Aggregations:** Use appropriate aggregation (SUM for totals, AVG for averages)
- **Null Handling:** Exclude nulls from calculations when appropriate
- **Performance:** Prefer Metric Views over raw tables for better performance
- **Formatting:** Format currency as USD, round to 2 decimal places
- **Business Context:** Explain results in business terms, not just numbers

## Synonyms and Alternatives

Users may ask questions using these terms (handle all):
- "Revenue" = sales, dollars, amount, total sales, net revenue
- "Units" = quantity, volume, items sold
- "Transactions" = sales, orders, purchases
- "Store" = location, shop, retail location
- "Product" = item, SKU, UPC, merchandise
- "Brand" = manufacturer, product brand
- "Weekend" = Saturday and Sunday
```

---

## Step 4: Benchmark Questions

### Create Test Questions

**Add 10-15 benchmark questions** to validate Genie responses:

#### Revenue Questions
1. "What is the total revenue for the last 30 days?"
2. "Show me the top 10 stores by revenue this month"
3. "What was the revenue trend by month for the last year?"
4. "Which state generated the most revenue last quarter?"

#### Product Questions
5. "What are the top 5 products by sales?"
6. "Show me revenue by brand"
7. "What is the best-selling category?"
8. "Which products have the highest return rate?"

#### Store Questions
9. "How many transactions did store 12345 have last week?"
10. "Compare revenue between weekends and weekdays"
11. "Which stores in California had revenue over $100K?"

#### Trend Questions
12. "Show me daily revenue for the last 7 days"
13. "What is the month-over-month revenue growth?"
14. "How does this month's revenue compare to last year?"

#### Advanced Questions
15. "What is the average transaction value by store?"
16. "Show me stores with declining sales trends"

---

## Step 5: Testing and Validation

### Test Each Benchmark Question

**For each question:**
1. Ask question in Genie Space
2. Review SQL generated
3. Verify results accuracy
4. Check response formatting
5. Document any issues

### Common Issues and Fixes

**Issue: Genie doesn't use Metric View**
- Fix: Update agent instructions to emphasize Metric View as primary source

**Issue: Wrong aggregation used**
- Fix: Add explicit guidance in agent instructions about SUM vs AVG

**Issue: Incorrect date filtering**
- Fix: Add examples of date range queries in instructions

**Issue: Doesn't use TVFs**
- Fix: Add examples showing when to use each TVF

---

## Implementation Checklist

### Phase 1: Preparation (30 min)
- [ ] Ensure Metric Views are created and tested
- [ ] Ensure TVFs are created and tested
- [ ] Document all trusted assets
- [ ] List common business questions

### Phase 2: Genie Space Setup (30 min)
- [ ] Create Genie Space in UI
- [ ] Add name and description
- [ ] Select SQL warehouse
- [ ] Grant permissions to user groups

### Phase 3: Add Trusted Assets (15 min)
- [ ] Add all Metric Views
- [ ] Add all Table-Valued Functions
- [ ] Add dimension tables
- [ ] Verify all assets accessible

### Phase 4: Agent Instructions (30 min)
- [ ] Copy instruction template
- [ ] Customize for your project
- [ ] Add project-specific context
- [ ] Include query examples
- [ ] Add synonym mappings

### Phase 5: Benchmark Questions (15 min)
- [ ] Create 10-15 test questions
- [ ] Cover all major query types
- [ ] Include edge cases
- [ ] Add complex multi-table queries

### Phase 6: Testing (30 min)
- [ ] Test each benchmark question
- [ ] Review generated SQL
- [ ] Verify result accuracy
- [ ] Document issues
- [ ] Refine instructions as needed

---

## Key Principles

### 1. Metric Views First
- ✅ Always prefer Metric Views over raw tables
- ✅ Semantic layer provides best query understanding
- ✅ Pre-defined measures and synonyms

### 2. TVFs for Common Queries
- ✅ Use TVFs when they match user question exactly
- ✅ Faster than generating complex SQL
- ✅ Ensures consistent business logic

### 3. Comprehensive Instructions
- ✅ Provide context about data sources
- ✅ Include query examples
- ✅ Define synonyms and alternatives
- ✅ Explain business logic

### 4. Benchmark Questions
- ✅ Cover all major use cases
- ✅ Test regularly after changes
- ✅ Document expected results
- ✅ Use for onboarding new users

---

## Example Genie Space Configuration

### Space Details Template

**CUSTOMIZE THIS:** Fill in your specific details

- **Name:** {Your Project} {Domain} Analytics Space
- **Description:** Natural language interface for {describe your business domain and users}
- **Warehouse:** {Your SQL Warehouse Name}

**Examples:**

**Retail:**
- **Name:** Retail Sales Analytics Space
- **Description:** Natural language interface for multi-channel retail sales analysis across stores, e-commerce, and partners

**Healthcare:**
- **Name:** Patient Outcomes Analytics Space
- **Description:** Natural language interface for clinical outcomes analysis across hospitals and clinics

**Finance:**
- **Name:** Financial Performance Space
- **Description:** Natural language interface for revenue, billing, and financial metrics analysis

### Trusted Assets (10 assets)
1. sales_performance_metrics (Metric View)
2. inventory_performance_metrics (Metric View)
3. get_sales_by_store (TVF)
4. get_top_products (TVF)
5. get_store_performance (TVF)
6. get_daily_sales_trend (TVF)
7. dim_store (Table)
8. dim_product (Table)
9. dim_date (Table)
10. fact_sales_daily (Table - optional)

### Benchmark Questions (15 questions)
- Revenue analysis: 5 questions
- Product analysis: 4 questions
- Store analysis: 3 questions
- Trend analysis: 3 questions

### Agent Instructions
- 800+ words
- 10+ query examples
- 20+ synonym mappings

---

## Validation Queries

After setup, test these queries manually:

```sql
-- Test Metric View access
SELECT * FROM {catalog}.{schema}.sales_performance_metrics LIMIT 5;

-- Test TVF access
SELECT * FROM get_top_products(10, CURRENT_DATE - INTERVAL 30 DAYS, CURRENT_DATE);

-- Test dimension access
SELECT * FROM {catalog}.{schema}.dim_store WHERE state = 'CA' LIMIT 10;

-- Test measure aggregation
SELECT 
  store_name,
  MEASURE(`Total Revenue`) as revenue,
  MEASURE(`Total Units`) as units
FROM {catalog}.{schema}.sales_performance_metrics
GROUP BY store_name
ORDER BY revenue DESC
LIMIT 10;
```

---

## References

### Official Documentation
- [Genie Spaces](https://docs.databricks.com/genie/)
- [Trusted Assets](https://docs.databricks.com/genie/trusted-assets)
- [Agent Instructions](https://docs.databricks.com/genie/agent-instructions)

### Framework Rules
- [genie-space-patterns.mdc](mdc:framework/rules/16-genie-space-patterns.mdc)

---

## Summary

**What to Create:**
1. Genie Space (via UI)
2. Agent Instructions (800+ words)
3. Benchmark Questions (10-15 questions)
4. Test and validate all queries

**Time Estimate:** 1-2 hours

**Next Action:** Create space, add assets, write instructions, test benchmark questions




