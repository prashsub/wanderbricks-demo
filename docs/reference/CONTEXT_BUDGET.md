# Cursor Rules Context Budget

**Claude Opus Limit:** 200K tokens  
**Target Operating Budget:** 40-60K tokens  
**Maximum Rule Budget:** 80K tokens

---

## Token Budget Summary

### Total Rule Inventory: ~217K tokens (if ALL loaded)

⚠️ **This exceeds the 200K limit!** Rules MUST be loaded intelligently.

---

## Tiered Loading Architecture

### Tier 1: Always Loaded (~11K tokens)

| Rule | Bytes | Tokens |
|---|---|---|
| `00-rule-navigator.mdc` | 12,387 | ~3,097 |
| `01-databricks-expert-agent.mdc` | 22,833 | ~5,708 |
| `20-cursor-rules.mdc` | 1,675 | ~419 |
| `22-documentation-organization.mdc` | 8,366 | ~2,092 |
| **TOTAL TIER 1** | **45,261** | **~11,315** |

✅ This is a healthy baseline (~5.5% of context)

---

### Tier 2: Domain Indexes (~2K per domain)

Load ONLY the domain index summary when domain is detected.
Full detailed rules loaded only in Tier 3.

| Domain | Index Size | Full Domain Size |
|---|---|---|
| Semantic Layer | ~2K | ~44.5K |
| Gold Layer | ~2K | ~35.8K |
| Infrastructure | ~2K | ~35.6K |
| Monitoring | ~2K | ~34.2K |
| Silver Layer | ~1.5K | ~23.9K |
| Bronze Layer | ~1K | ~4.5K |
| ML | ~1K | ~16K |
| Planning | ~1K | ~8.5K |
| Exploration | ~1K | ~5K |

---

### Tier 3: Detailed Rules (Load ONE at a time)

**Large Rules (10K+ tokens) - Load sparingly:**

| Rule | Tokens | Domain |
|---|---|---|
| `27-mlflow-mlmodels-patterns.mdc` | ~15,914 | ML |
| `02-databricks-asset-bundles.mdc` | ~15,310 | Infrastructure |
| `17-lakehouse-monitoring-comprehensive.mdc` | ~14,505 | Monitoring |
| `29-genie-space-export-import-api.mdc` | ~14,494 | Semantic |
| `08-dqx-patterns.mdc` | ~13,107 | Silver |
| `18-databricks-aibi-dashboards.mdc` | ~12,205 | Monitoring |
| `14-metric-views-patterns.mdc` | ~11,228 | Semantic |
| `07-dlt-expectations-patterns.mdc` | ~10,748 | Silver |
| `16-genie-space-patterns.mdc` | ~10,486 | Semantic |
| `12-gold-layer-documentation.mdc` | ~10,355 | Gold |

**Medium Rules (5-10K tokens):**

| Rule | Tokens | Domain |
|---|---|---|
| `05-unity-catalog-constraints.mdc` | ~7,588 | Infrastructure |
| `19-sql-alerting-patterns.mdc` | ~7,478 | Monitoring |
| `21-self-improvement.mdc` | ~6,616 | Admin |
| `13-mermaid-erd-patterns.mdc` | ~5,999 | Gold |
| `exploration/22-adhoc-exploration-notebooks.mdc` | ~5,052 | Exploration |

**Small Rules (<5K tokens):**

| Rule | Tokens | Domain |
|---|---|---|
| `24-fact-table-grain-validation.mdc` | ~4,801 | Gold |
| `06-faker-data-generation.mdc` | ~4,477 | Bronze |
| `11-gold-delta-merge-deduplication.mdc` | ~4,284 | Gold |
| `23-gold-layer-schema-validation.mdc` | ~4,144 | Gold |
| `25-yaml-driven-gold-setup.mdc` | ~3,686 | Gold |
| `09-databricks-python-imports.mdc` | ~3,280 | Common |
| `10-gold-layer-merge-patterns.mdc` | ~2,579 | Gold |
| `04-databricks-table-properties.mdc` | ~2,177 | Infrastructure |
| `03-schema-management-patterns.mdc` | ~1,523 | Infrastructure |

---

## Context Zones

### 🟢 Green Zone (0-40K tokens)
- Normal operation
- Tier 1 + 1-2 domain indexes + 1-2 detailed rules
- Fast, focused responses

### 🟡 Yellow Zone (40-80K tokens)
- Heavy workload
- Multiple domains active
- May need to prioritize rules

### 🔴 Red Zone (80K+ tokens)
- Context constrained
- Reference docs instead of embedding
- Consider task splitting

---

## Loading Strategy Examples

### Simple Task: "Create metric view"
```
Tier 1 (always):     ~11K tokens
Semantic Index:      ~2K tokens
14-metric-views:     ~11K tokens
─────────────────────────────────
TOTAL:               ~24K tokens ✅ Green Zone
```

### Medium Task: "Deploy Gold layer with monitoring"
```
Tier 1 (always):     ~11K tokens
Gold Index:          ~2K tokens
Monitoring Index:    ~2K tokens
02-asset-bundles:    ~15K tokens
25-yaml-driven:      ~4K tokens
─────────────────────────────────
TOTAL:               ~34K tokens ✅ Green Zone
```

### Complex Task: "Full semantic layer setup"
```
Tier 1 (always):     ~11K tokens
Semantic Index:      ~2K tokens
14-metric-views:     ~11K tokens
15-tvfs:             ~8K tokens
16-genie-space:      ~10K tokens
─────────────────────────────────
TOTAL:               ~42K tokens 🟡 Yellow Zone
```

---

## Rules That Were Changed

### Removed from Always-Apply

| Rule | Reason | New Trigger |
|---|---|---|
| `21-self-improvement.mdc` | 6.6K tokens, meta-rule | `.cursor/rules/**/*.mdc` globs |

### Kept as Always-Apply (Tier 1)

| Rule | Tokens | Reason |
|---|---|---|
| `00-rule-navigator.mdc` | ~3K | Navigation system |
| `01-databricks-expert-agent.mdc` | ~5.7K | Core agent behavior |
| `20-cursor-rules.mdc` | ~0.4K | Rules management (tiny) |
| `22-documentation-organization.mdc` | ~2K | Doc standards |

---

## Maintenance Checklist

When adding/modifying rules:

- [ ] Calculate token size: `wc -c file.mdc / 4`
- [ ] If >10K tokens, consider splitting
- [ ] If always-apply, ensure total Tier 1 stays <15K
- [ ] Update domain index in navigator
- [ ] Add to appropriate tier in this document
- [ ] Set `alwaysApply: false` for domain-specific rules

---

## Commands

### Check individual rule size
```bash
wc -c .cursor/rules/path/to/rule.mdc | awk '{print $1/4 " tokens"}'
```

### Check folder totals
```bash
cat .cursor/rules/folder/*.mdc | wc -c | awk '{print $1/4 " tokens"}'
```

### Check always-apply total
```bash
cat .cursor/rules/00-rule-navigator.mdc \
    .cursor/rules/common/01-databricks-expert-agent.mdc \
    .cursor/rules/admin/20-cursor-rules.mdc \
    .cursor/rules/admin/22-documentation-organization.mdc \
    | wc -c | awk '{print $1/4 " tokens"}'
```
