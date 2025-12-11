# Wanderbricks Table-Valued Functions (TVFs)

This directory contains SQL Table-Valued Functions optimized for Databricks Genie Spaces natural language queries.

---

## Directory Structure

```
src/wanderbricks_gold/tvfs/
├── README.md                    # This file
├── revenue_tvfs.sql            # Revenue & financial analysis (6 functions)
├── engagement_tvfs.sql         # Marketing & engagement (5 functions)
├── property_tvfs.sql           # Property performance (5 functions)
├── host_tvfs.sql               # Host management (5 functions)
└── customer_tvfs.sql           # Customer analytics (5 functions)
```

---

## SQL Compliance Patterns

All TVFs follow strict patterns for Genie compatibility:

### 1. STRING Date Parameters
```sql
-- ✅ CORRECT
start_date STRING COMMENT 'Start date (format: YYYY-MM-DD)'

-- ❌ WRONG
start_date DATE COMMENT 'Start date'
```

### 2. Parameter Ordering
```sql
-- ✅ CORRECT: Required first, optional last
FUNCTION name(
  start_date STRING,              -- Required
  end_date STRING,                -- Required
  top_n INT DEFAULT 10            -- Optional
)

-- ❌ WRONG: Optional before required
FUNCTION name(
  top_n INT DEFAULT 10,           -- Optional first
  start_date STRING               -- Required after optional
)
```

### 3. Top N Pattern
```sql
-- ✅ CORRECT: Use ROW_NUMBER + WHERE
WITH ranked AS (
  SELECT ROW_NUMBER() OVER (ORDER BY metric DESC) as rank, ...
)
SELECT * FROM ranked WHERE rank <= top_n

-- ❌ WRONG: LIMIT with parameter
SELECT * FROM data LIMIT top_n
```

### 4. Null Safety
```sql
-- ✅ CORRECT
revenue / NULLIF(bookings, 0) as avg_value

-- ❌ WRONG
revenue / bookings
```

---

## Function Naming Convention

All functions follow `get_{entity}_{metric/action}` pattern:

- `get_revenue_by_period` - Entity: revenue, Action: by period
- `get_top_properties_by_revenue` - Modifier: top, Entity: properties, Metric: revenue
- `get_host_performance` - Entity: host, Metric: performance

---

## Usage Examples

### Revenue Analysis
```sql
-- Monthly revenue trends
SELECT * FROM get_revenue_by_period('2024-01-01', '2024-12-31', 'month');

-- Top 10 revenue properties
SELECT * FROM get_top_properties_by_revenue('2024-01-01', '2024-12-31', 10);
```

### Engagement Analysis
```sql
-- Property engagement metrics
SELECT * FROM get_property_engagement('2024-01-01', '2024-12-31', NULL);

-- Conversion funnel by destination
SELECT * FROM get_conversion_funnel('2024-01-01', '2024-12-31', 'Paris');
```

### Host Management
```sql
-- All host performance
SELECT * FROM get_host_performance('2024-01-01', '2024-12-31', NULL);

-- Specific host details
SELECT * FROM get_host_performance('2024-01-01', '2024-12-31', 12345);
```

---

## LLM-Friendly Metadata

Every TVF includes rich metadata for Genie:

```sql
COMMENT 'LLM: [Brief description].
Use this for: [Use cases].
Parameters: [parameter list with formats].
Example questions: "[Question 1]" "[Question 2]"'
```

This enables Genie to understand when and how to use each function.

---

## Testing

```sql
-- List all TVFs
SHOW FUNCTIONS IN catalog.schema LIKE 'get_%';

-- View function details
DESCRIBE FUNCTION EXTENDED catalog.schema.get_revenue_by_period;

-- Test execution
SELECT * FROM catalog.schema.get_revenue_by_period(
  '2024-01-01', 
  '2024-12-31', 
  'month'
);
```

---

## Maintenance

### Adding New TVFs

1. Choose appropriate domain file (revenue, engagement, property, host, customer)
2. Follow naming convention: `get_{entity}_{metric/action}`
3. Apply all SQL compliance patterns
4. Add LLM-friendly metadata
5. Test thoroughly before deployment

### Modifying Existing TVFs

1. Update SQL logic
2. Preserve parameter signatures (breaking changes require version)
3. Update function COMMENT if behavior changes
4. Re-run deployment: `databricks bundle run gold_setup_job -t dev`

---

## Deployment

TVFs are automatically deployed via Asset Bundle:

```bash
# Deploy all TVFs
databricks bundle deploy -t dev
databricks bundle run gold_setup_job -t dev
```

The `create_all_tvfs.sql` master file sources all domain files during deployment.

---

## References

- [TVF Patterns Rule](../../../.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc)
- [TVF Prompt](../../../context/prompts/09-table-valued-functions-prompt.md)
- [Implementation Summary](../../../plans/IMPLEMENTATION_SUMMARY_TVFs.md)
- [Quick Start Guide](../../../plans/QUICKSTART_TVFs.md)
- [Databricks TVF Docs](https://docs.databricks.com/sql/language-manual/sql-ref-syntax-qry-select-tvf)

---

**Total Functions:** 26  
**Domains:** 5  
**Status:** ✅ Production-ready

