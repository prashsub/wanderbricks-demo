# Semantic Layer Setup Refactoring

**Date:** December 10, 2025  
**Change Type:** Job Reorganization  
**Impact:** Low (deployment pattern change only, no code changes)

---

## Summary

Refactored Gold layer setup to separate **data layer** (tables/constraints) from **semantic layer** (TVFs/metric views) into distinct jobs for better organizational clarity.

---

## Changes Made

### 1. Created New Job: `semantic_setup_job`

**File:** `resources/gold/semantic_setup_job.yml`

**Purpose:** Unified semantic layer setup combining:
- Table-Valued Functions (TVFs) for Genie natural language queries
- Unity Catalog Metric Views for semantic metadata

**Tasks:**
1. `create_table_valued_functions` - Creates 26 TVFs across 5 domains (Revenue, Engagement, Property, Host, Customer)
2. `create_metric_views` - Creates UC Metric Views from YAML definitions

**Dependencies:**
- Requires Gold layer tables to exist (run `gold_setup_job` first)
- Tasks run sequentially: TVFs → Metric Views

**Configuration:**
```yaml
resources:
  jobs:
    semantic_setup_job:
      name: "[${bundle.target}] Wanderbricks Semantic Layer - Setup"
      
      environments:
        - environment_key: default
          spec:
            environment_version: "4"
            dependencies:
              - "PyYAML>=6.0"
      
      tasks:
        - task_key: create_table_valued_functions
          notebook_task:
            notebook_path: ../../src/wanderbricks_gold/create_all_tvfs.py
          timeout_seconds: 1200
        
        - task_key: create_metric_views
          depends_on:
            - task_key: create_table_valued_functions
          notebook_task:
            notebook_path: ../../src/wanderbricks_gold/semantic/create_metric_views.py
          timeout_seconds: 1800
      
      timeout_seconds: 3600  # 1 hour total
      
      tags:
        layer: semantic
        phase: "4.2-4.3"
        artifact_type: tvfs_and_metric_views
```

---

### 2. Updated Job: `gold_setup_job`

**File:** `resources/gold/gold_setup_job.yml`

**Changes:**
- ❌ Removed `create_table_valued_functions` task
- ✅ Now focused solely on table and constraint creation
- ✅ Updated documentation to reference semantic_setup_job

**Current Tasks:**
1. `setup_all_tables` - Create Gold tables from YAML schemas
2. `add_fk_constraints` - Apply foreign key constraints

**Updated Description:**
```
Creates Gold layer tables from YAML schema definitions with constraints.

Note: Semantic layer (TVFs, Metric Views) are created by semantic_setup_job
```

---

### 3. Deprecated Job: `metric_views_job`

**File:** `resources/gold/metric_views_job.yml`

**Status:** ⚠️ Deprecated (functionality moved to semantic_setup_job)

**Recommendation:** 
- Keep file for reference
- Can be deleted after confirming semantic_setup_job works in all environments
- Update any documentation/runbooks referencing this job

---

## Deployment Order

### Complete Fresh Setup
```bash
# 1. Gold layer tables and constraints
databricks bundle run gold_setup_job -t dev

# 2. Semantic layer (TVFs + Metric Views)
databricks bundle run semantic_setup_job -t dev
```

### Update Semantic Layer Only
```bash
# Run after Gold layer tables exist
databricks bundle run semantic_setup_job -t dev
```

---

## Benefits of This Refactoring

### 1. **Clearer Separation of Concerns**
- **Data Layer (gold_setup_job):** Physical tables and constraints
- **Semantic Layer (semantic_setup_job):** Virtual assets for analytics (TVFs, Metric Views)

### 2. **Better Development Workflow**
- Can update semantic layer independently without recreating tables
- Faster iteration during TVF/Metric View development
- Reduced risk of accidentally dropping tables

### 3. **Logical Grouping**
- TVFs and Metric Views both serve Genie/AI-BI use cases
- Natural coupling: Metric Views often reference tables that TVFs also query
- Single job to update all semantic layer assets

### 4. **Easier Maintenance**
- Clear job boundaries make troubleshooting simpler
- Can run semantic setup multiple times without affecting data
- Better aligned with phase-based project structure (Phase 4.2 + 4.3)

---

## Migration Guide

### For Existing Deployments

If you previously ran jobs separately:

**OLD:**
```bash
databricks bundle run gold_setup_job -t dev       # Included TVFs
databricks bundle run metric_views_job -t dev     # Separate
```

**NEW:**
```bash
databricks bundle run gold_setup_job -t dev       # Tables only
databricks bundle run semantic_setup_job -t dev   # TVFs + Metric Views
```

### For CI/CD Pipelines

Update workflow files to use new job name:

**Before:**
```yaml
- name: Setup Gold Layer
  run: databricks bundle run gold_setup_job -t prod
- name: Create Metric Views
  run: databricks bundle run metric_views_job -t prod
```

**After:**
```yaml
- name: Setup Gold Layer
  run: databricks bundle run gold_setup_job -t prod
- name: Setup Semantic Layer
  run: databricks bundle run semantic_setup_job -t prod
```

---

## Testing Validation

### Tested Scenarios

- [x] Bundle validation passes
- [x] Deployment succeeds in dev environment
- [x] gold_setup_job creates tables without TVF task
- [x] semantic_setup_job creates both TVFs and metric views
- [x] Task dependencies work correctly (TVFs → Metric Views)
- [x] No duplicate resource definitions

### Verification Commands

```bash
# Verify gold_setup_job structure
databricks bundle run gold_setup_job -t dev --dry-run

# Verify semantic_setup_job structure
databricks bundle run semantic_setup_job -t dev --dry-run

# List all TVFs after semantic setup
databricks sql -e "
  SELECT routine_name 
  FROM prashanth_subrahmanyam_catalog.information_schema.routines 
  WHERE routine_schema = 'dev_prashanth_subrahmanyam_wanderbricks_gold'
  AND routine_type = 'FUNCTION'
  ORDER BY routine_name
"

# Count metric views
databricks sql -e "
  SELECT COUNT(*) as metric_view_count
  FROM prashanth_subrahmanyam_catalog.information_schema.tables
  WHERE table_schema = 'dev_prashanth_subrahmanyam_wanderbricks_gold'
  AND table_type = 'METRIC_VIEW'
"
```

---

## Rollback Plan

If issues occur, rollback is simple:

### Option 1: Use Previous Jobs
```bash
# Restore old pattern (if needed)
databricks bundle run gold_setup_job -t dev  # Tables + constraints (no TVFs)
databricks bundle run metric_views_job -t dev  # Just metric views

# Then manually create TVFs using old gold_setup_job or run script directly
databricks workspace import \
  ../../src/wanderbricks_gold/create_all_tvfs.py \
  /tmp/create_tvfs.py
databricks jobs run-now --notebook-path /tmp/create_tvfs.py
```

### Option 2: Revert Bundle Configuration
```bash
git revert <commit_hash>
databricks bundle deploy -t dev
```

---

## Related Documentation

- **TVF Implementation:** `docs/troubleshooting/2025-12-10-tvf-deployment-postmortem.md`
- **Schema-First Development:** `docs/development/SCHEMA_FIRST_DEVELOPMENT.md`
- **Phase 4.2 Plan:** `plans/phase4-addendum-4.2-tvfs.md`
- **Phase 4.3 Plan:** `plans/phase4-addendum-4.3-metric-views.md`
- **TVF Patterns Rule:** `.cursor/rules/semantic-layer/15-databricks-table-valued-functions.mdc`

---

## Future Enhancements

### Potential Additions to semantic_setup_job

1. **Genie Space Configuration** (Phase 4.6)
   - Create/update Genie Spaces with TVFs and Metric Views
   - Configure benchmark questions

2. **AI/BI Dashboard Deployment** (Phase 4.5)
   - Deploy standard dashboards using Metric Views
   - Link to Genie Spaces

3. **Semantic Validation**
   - Validate TVF signatures match Gold schema
   - Verify Metric View references exist
   - Check for broken cross-references

---

## Change Log

### v1.0 - December 10, 2025

**Added:**
- Created `semantic_setup_job.yml` combining TVF and Metric View creation
- Moved `create_table_valued_functions` task from gold_setup_job
- Integrated `create_metric_views` task from metric_views_job

**Modified:**
- Updated `gold_setup_job.yml` to focus on tables/constraints only
- Updated job descriptions and documentation

**Deprecated:**
- `metric_views_job.yml` (functionality moved to semantic_setup_job)

---

## Lessons Learned

### 1. Tag Value Validation
**Issue:** Initial deployment failed with error about invalid tag character (comma).

**Solution:** Changed `phase: "4.2,4.3"` to `phase: "4.2-4.3"`

**Lesson:** Databricks tags must match regex `^[\d \w\+\-=\.:/@]*$` - no commas allowed.

### 2. Job Dependency Planning
**Decision:** Made TVF and Metric View tasks sequential (not parallel).

**Rationale:** 
- Metric Views may reference same tables as TVFs
- Ensures consistent schema state
- Minimal performance impact (both are metadata operations)

### 3. Job Naming Convention
**Choice:** Used `semantic_setup_job` instead of `tvf_and_metric_views_job`

**Rationale:**
- "Semantic layer" is the recognized term in data architecture
- More scalable (can add more semantic assets later)
- Aligns with Databricks documentation terminology

---

**Status:** ✅ Successfully deployed and validated  
**Next Steps:** Update orchestrator workflows and CI/CD pipelines to use new job structure

