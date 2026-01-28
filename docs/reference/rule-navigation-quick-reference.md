# Rule Navigation System: Quick Reference Card

**Version:** 1.0 | **Date:** January 26, 2026

---

## What Changed?

| Before | After |
|---|---|
| 30 rules always loaded (~120K tokens) | 5 universal + 25 intelligent (~20-40K tokens) |
| All patterns in context | Domain-specific patterns on demand |
| Slower responses | 30-50% faster responses |
| Manual rule discovery | Automatic routing by keywords & files |

---

## Always Loaded Rules (5)

✅ These rules are **ALWAYS** active:

1. `00-rule-navigator.mdc` - **NEW** Navigation system
2. `01-databricks-expert-agent.mdc` - Core agent behavior
3. `20-cursor-rules.mdc` - Rules management
4. `21-self-improvement.mdc` - Continuous improvement
5. `22-documentation-organization.mdc` - Documentation standards

---

## Intelligently Loaded Rules (25)

📚 These rules load **ON DEMAND** based on task detection:

### Semantic Layer (4)
- `14-metric-views-patterns.mdc`
- `15-databricks-table-valued-functions.mdc`
- `16-genie-space-patterns.mdc`
- `29-genie-space-export-import-api.mdc`

### Gold Layer (7)
- `10-gold-layer-merge-patterns.mdc`
- `11-gold-delta-merge-deduplication.mdc`
- `12-gold-layer-documentation.mdc`
- `13-mermaid-erd-patterns.mdc`
- `23-gold-layer-schema-validation.mdc`
- `24-fact-table-grain-validation.mdc`
- `25-yaml-driven-gold-setup.mdc`

### Infrastructure (4)
- `02-databricks-asset-bundles.mdc`
- `03-schema-management-patterns.mdc`
- `04-databricks-table-properties.mdc`
- `05-unity-catalog-constraints.mdc`

### Monitoring & Quality (4)
- `17-lakehouse-monitoring-comprehensive.mdc`
- `18-databricks-aibi-dashboards.mdc`
- `19-sql-alerting-patterns.mdc`
- `08-dqx-patterns.mdc`

### Silver Layer (2)
- `07-dlt-expectations-patterns.mdc`
- `08-dqx-patterns.mdc`

### Bronze Layer (1)
- `06-faker-data-generation.mdc`

### ML (1)
- `27-mlflow-mlmodels-patterns.mdc`

### Exploration (1)
- `22-adhoc-exploration-notebooks.mdc`

### Planning (1)
- `26-project-plan-methodology.mdc`

### Common/Utilities (1)
- `09-databricks-python-imports.mdc`

---

## Quick Detection Patterns

| Say This | Loads These Rules |
|---|---|
| "metric view" | 14-metric-views-patterns |
| "TVF" or "table-valued function" | 15-databricks-table-valued-functions |
| "Genie Space" | 16-genie-space-patterns |
| "Gold merge" | 10-gold-layer-merge-patterns |
| "duplicate key" | 11-gold-delta-merge-deduplication |
| "Asset Bundle" or "deploy" | 02-databricks-asset-bundles |
| "table properties" | 04-databricks-table-properties |
| "Lakehouse Monitoring" | 17-lakehouse-monitoring-comprehensive |
| "MLflow" or "model training" | 27-mlflow-mlmodels-patterns |

---

## Explicit Rule Requests

Want a specific rule regardless of detection?

```
@rule-name.mdc [your request]
```

**Example:**
```
@15-databricks-table-valued-functions.mdc help me create a TVF for top destinations
```

---

## File Pattern Triggers

Rules automatically load when working with matching files:

| File Pattern | Triggers Rule |
|---|---|
| `resources/**/*.yml` | 02-databricks-asset-bundles |
| `src/**/*metric*view*.yaml` | 14-metric-views-patterns |
| `src/**/*gold*/merge*.py` | 10-gold-layer-merge-patterns |
| `src/**/*setup*.py` | 04-databricks-table-properties |
| `src/wanderbricks_ml/**` | 27-mlflow-mlmodels-patterns |

---

## Priority Levels

| Priority | When Loads | Example Use |
|---|---|---|
| **HIGH** | Always when keywords match | Critical patterns, blocking errors |
| **MEDIUM** | If context allows | Best practices, helpful context |
| **LOW** | Only if explicitly requested | Reference material |

---

## Token Budget Impact

```
Old System (All Rules Always):
┌────────────────────────────────┐
│ ████████████████████ 100K      │  Full context every time
└────────────────────────────────┘

New System (Smart Loading):
┌────────────────────────────────┐
│ ████████ 40K                   │  Metric view task
│ ██████ 30K                     │  Gold merge task  
│ ████ 20K                       │  Simple deployment
└────────────────────────────────┘
```

**Result:** 60-80% token reduction, faster responses

---

## Common Workflows

### Creating Metric Views
```
Keywords: "metric view", "semantic layer"
Rules loaded:
✅ 14-metric-views-patterns (HIGH)
✅ 12-gold-layer-documentation (MEDIUM)
Tokens: ~25K
```

### Gold Layer Merge Debugging
```
Keywords: "merge", "duplicate key", "fact_booking"
Rules loaded:
✅ 10-gold-layer-merge-patterns (HIGH)
✅ 11-gold-delta-merge-deduplication (HIGH)
✅ 23-gold-layer-schema-validation (HIGH)
Tokens: ~40K
```

### Asset Bundle Deployment
```
Keywords: "deploy", "job", "Asset Bundle"
Files: resources/**/*.yml
Rules loaded:
✅ 02-databricks-asset-bundles (HIGH)
✅ 03-schema-management-patterns (MEDIUM)
Tokens: ~30K
```

### ML Model Training
```
Keywords: "MLflow", "model training"
Files: src/wanderbricks_ml/**
Rules loaded:
✅ 27-mlflow-mlmodels-patterns (HIGH)
✅ 09-databricks-python-imports (MEDIUM)
Tokens: ~35K
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Rule not loading | Add keywords from detection table |
| Wrong rules loading | Be more specific in request |
| Too many rules loading | Split into smaller tasks |
| Need specific rule | Use `@rule-name.mdc` syntax |

---

## Benefits Summary

✅ **60-80% fewer tokens** per request  
✅ **30-50% faster** responses  
✅ **Better accuracy** through focused context  
✅ **Unlimited scalability** (add rules without bloat)  
✅ **Backward compatible** (no workflow changes needed)  

---

## No Action Required!

The navigation system works automatically:
- ✅ Agent detects task domain
- ✅ Agent loads relevant rules
- ✅ Agent applies appropriate patterns
- ✅ You get focused, accurate responses

**Just keep working as before!**

---

## Learn More

📖 Full documentation: [docs/reference/rule-navigation-system.md](rule-navigation-system.md)  
🔍 Navigation rule: [.cursor/rules/00-rule-navigator.mdc](../../.cursor/rules/00-rule-navigator.mdc)  
📋 Rules management: [.cursor/rules/admin/20-cursor-rules.mdc](../../.cursor/rules/admin/20-cursor-rules.mdc)

---

**Questions?** The navigation system is self-documenting. Just ask!
