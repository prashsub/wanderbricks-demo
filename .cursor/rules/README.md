# Cursor Rules: Tiered Context Loading System

This folder contains 30 cursor rules organized with a **tiered loading architecture** to stay within Claude Opus's 200K token context limit.

---

## Quick Summary

| Category | Rules | Tokens | Loading |
|---|---|---|---|
| **Tier 1: Core** | 4 rules | ~11K | Always loaded |
| **Tier 2: Indexes** | 9 domains | ~2K each | On domain detection |
| **Tier 3: Detailed** | 26 rules | ~206K total | On specific task |

**Total Rule Inventory:** ~217K tokens (if ALL loaded - but we never load all!)

---

## Tier 1: Always Loaded (~11K tokens)

These rules load for EVERY interaction:

```
.cursor/rules/
├── 00-rule-navigator.mdc          # Navigation system (~3K)
├── common/
│   └── 01-databricks-expert-agent.mdc  # Core agent (~5.7K)
└── admin/
    ├── 20-cursor-rules.mdc        # Rules management (~0.4K)
    └── 22-documentation-organization.mdc  # Docs standards (~2K)
```

---

## Tier 2 & 3: Domain-Specific Rules

### Semantic Layer (~44.5K tokens total)
```
.cursor/rules/semantic-layer/
├── 14-metric-views-patterns.mdc         # ~11K tokens
├── 15-databricks-table-valued-functions.mdc  # ~8K tokens
├── 16-genie-space-patterns.mdc          # ~10.5K tokens
└── 29-genie-space-export-import-api.mdc # ~14.5K tokens
```
**Triggers:** "metric view", "TVF", "Genie", "semantic layer"

---

### Gold Layer (~35.8K tokens total)
```
.cursor/rules/gold/
├── 10-gold-layer-merge-patterns.mdc     # ~2.5K tokens
├── 11-gold-delta-merge-deduplication.mdc  # ~4K tokens
├── 12-gold-layer-documentation.mdc      # ~10K tokens
├── 13-mermaid-erd-patterns.mdc          # ~6K tokens
├── 23-gold-layer-schema-validation.mdc  # ~4K tokens
├── 24-fact-table-grain-validation.mdc   # ~5K tokens
└── 25-yaml-driven-gold-setup.mdc        # ~3.5K tokens
```
**Triggers:** "Gold layer", "merge", "fact table", "dimension", "SCD2"

---

### Infrastructure (~35.6K tokens total)
```
.cursor/rules/common/
├── 02-databricks-asset-bundles.mdc      # ~15K tokens ⚠️ LARGE
├── 03-schema-management-patterns.mdc    # ~1.5K tokens
├── 04-databricks-table-properties.mdc   # ~2K tokens
├── 05-unity-catalog-constraints.mdc     # ~7.5K tokens
└── 09-databricks-python-imports.mdc     # ~3K tokens
```
**Triggers:** "deploy", "Asset Bundle", "job", "schema", "constraints"

---

### Monitoring (~34.2K tokens total)
```
.cursor/rules/monitoring/
├── 17-lakehouse-monitoring-comprehensive.mdc  # ~14.5K tokens ⚠️ LARGE
├── 18-databricks-aibi-dashboards.mdc    # ~12K tokens ⚠️ LARGE
└── 19-sql-alerting-patterns.mdc         # ~7.5K tokens
```
**Triggers:** "monitoring", "dashboard", "alert", "AI/BI"

---

### Silver Layer (~23.9K tokens total)
```
.cursor/rules/silver/
├── 07-dlt-expectations-patterns.mdc     # ~11K tokens ⚠️ LARGE
└── 08-dqx-patterns.mdc                  # ~13K tokens ⚠️ LARGE
```
**Triggers:** "DLT", "Silver layer", "expectations", "DQX"

---

### Bronze Layer (~4.5K tokens total)
```
.cursor/rules/bronze/
└── 06-faker-data-generation.mdc         # ~4.5K tokens
```
**Triggers:** "Bronze", "Faker", "synthetic data"

---

### Machine Learning (~16K tokens total)
```
.cursor/rules/ml/
└── 27-mlflow-mlmodels-patterns.mdc      # ~16K tokens ⚠️ LARGE
```
**Triggers:** "MLflow", "model training", "ML pipeline"

---

### Exploration (~5K tokens total)
```
.cursor/rules/exploration/
└── 22-adhoc-exploration-notebooks.mdc   # ~5K tokens
```
**Triggers:** "exploration notebook", "Databricks Connect", "ad-hoc"

---

### Planning (~8.5K tokens total)
```
.cursor/rules/planning/
└── 26-project-plan-methodology.mdc      # ~8.5K tokens
```
**Triggers:** "project plan", "roadmap", "phase planning"

---

### Admin (~6.6K additional tokens)
```
.cursor/rules/admin/
└── 21-self-improvement.mdc              # ~6.6K tokens
```
**Triggers:** "improve rules", `.cursor/rules/**/*.mdc` files

---

## How Tiered Loading Works

### Step 1: Core Always Active (~11K)
```
Every interaction starts with Tier 1 rules loaded.
```

### Step 2: Domain Detection (~13-15K total)
```
Navigator detects keywords → Loads domain INDEX (summary, not full rules)
Example: "metric view" → Loads Semantic Layer Index (~2K)
```

### Step 3: Task-Specific Loading (~25-40K total)
```
Specific task identified → Loads ONE detailed rule
Example: "create metric view" → Loads 14-metric-views-patterns.mdc (~11K)
```

### Step 4: Deep Dive (if needed, ~60K max)
```
Complex task → May load 2-3 related rules
Monitor total context - stays under 80K for rules
```

---

## ⚠️ Large Rules (10K+ tokens)

Load only ONE of these at a time:

| Rule | Tokens | Domain |
|---|---|---|
| `27-mlflow-mlmodels-patterns` | ~16K | ML |
| `02-databricks-asset-bundles` | ~15K | Infrastructure |
| `17-lakehouse-monitoring-comprehensive` | ~14.5K | Monitoring |
| `29-genie-space-export-import-api` | ~14.5K | Semantic |
| `08-dqx-patterns` | ~13K | Silver |
| `18-databricks-aibi-dashboards` | ~12K | Monitoring |
| `14-metric-views-patterns` | ~11K | Semantic |
| `07-dlt-expectations-patterns` | ~11K | Silver |
| `16-genie-space-patterns` | ~10.5K | Semantic |
| `12-gold-layer-documentation` | ~10K | Gold |

---

## Key Files

| File | Purpose |
|---|---|
| `00-rule-navigator.mdc` | Main navigation system with indexes |
| `CONTEXT_BUDGET.md` | Detailed token budget analysis |
| `README.md` | This overview |

---

## Explicit Rule Loading

To explicitly load a specific rule:
```
@14-metric-views-patterns.mdc help me create a metric view
```

---

## Adding New Rules

1. Calculate size: `wc -c new-rule.mdc / 4` = tokens
2. Place in appropriate domain folder
3. Set `alwaysApply: false` in frontmatter
4. Add globs for file pattern triggers
5. Update navigator's domain index
6. Update `CONTEXT_BUDGET.md`
7. If >10K tokens, add to "Large Rules" list

---

## Benefits

- ✅ **80% token reduction** vs loading all rules
- ✅ **Stays under 200K limit** even with large rule inventory
- ✅ **Scalable** - can add unlimited rules
- ✅ **Fast responses** - less context to process
- ✅ **Accurate** - focused, relevant patterns
