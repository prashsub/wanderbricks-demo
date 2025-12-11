# Semantic Layer Job Architecture

**Date:** 2025-12-09  
**Status:** ✅ Implemented  
**Pattern:** Modular Job Composition with `run_job_task`

---

## Architecture Overview

The Wanderbricks semantic layer uses a **modular job architecture** where standalone jobs are composed into higher-level orchestrator jobs.

```
┌─────────────────────────────────────────────────────────────────┐
│ semantic_setup_job (Orchestrator)                               │
│                                                                   │
│  Task 1: create_table_valued_functions                          │
│  ├── Type: notebook_task                                        │
│  ├── Script: src/wanderbricks_gold/create_all_tvfs.py          │
│  └── Creates: 26 TVFs across 5 domains                          │
│                                                                   │
│  Task 2: create_metric_views                                    │
│  ├── Type: run_job_task                                         │
│  ├── References: metric_views_job                               │
│  └── Depends on: Task 1                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ run_job_task
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ metric_views_job (Standalone)                                   │
│                                                                   │
│  Task: create_metric_views                                      │
│  ├── Type: notebook_task                                        │
│  ├── Script: src/wanderbricks_gold/semantic/create_metric_views.py │
│  └── Creates: 5 metric views from YAML                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Benefits

### 1. **Single Source of Truth**
- Metric views logic defined **once** in `metric_views_job`
- No code duplication between standalone and integrated execution
- Changes to metric views only need to be made in one place

### 2. **Flexible Execution**
```bash
# Option A: Run complete semantic layer (TVFs + Metric Views)
databricks bundle run semantic_setup_job -t dev

# Option B: Run metric views only (for testing/iteration)
databricks bundle run metric_views_job -t dev
```

### 3. **Proper Dependency Management**
- Metric views creation depends on TVFs completion
- `depends_on` ensures correct execution order
- Independent jobs have isolated environments

### 4. **Modular Design**
- Each job can be tested independently
- Easy to add more semantic layer components
- Clear separation of concerns

---

## Implementation Details

### Job Reference Pattern

**In `resources/gold/semantic_setup_job.yml`:**

```yaml
tasks:
  # Task 1: Create TVFs (direct notebook execution)
  - task_key: create_table_valued_functions
    environment_key: default
    notebook_task:
      notebook_path: ../../src/wanderbricks_gold/create_all_tvfs.py
      base_parameters:
        catalog: ${var.catalog}
        gold_schema: ${var.gold_schema}
  
  # Task 2: Call Metric Views Job (job reference)
  - task_key: create_metric_views
    depends_on:
      - task_key: create_table_valued_functions
    run_job_task:
      job_id: ${resources.jobs.metric_views_job.id}
```

**Key Points:**
- ✅ Use `run_job_task` (not `job_task`)
- ✅ Reference by ID: `${resources.jobs.metric_views_job.id}`
- ✅ No need to pass parameters (job has its own configuration)
- ✅ Called job uses its own environment and dependencies

---

## Execution Flows

### Flow 1: Complete Semantic Layer Setup

```bash
databricks bundle run semantic_setup_job -t dev
```

**Execution Timeline:**
```
[00:00] semantic_setup_job starts
[00:00] Task 1: create_table_valued_functions starts
[00:15] Task 1: create_table_valued_functions completes (26 TVFs created)
[00:15] Task 2: create_metric_views starts (triggers metric_views_job)
  [00:15] metric_views_job starts
  [00:15] Task: create_metric_views starts
  [00:17] Task: create_metric_views completes (5 views created)
  [00:17] metric_views_job completes
[00:17] Task 2: create_metric_views completes
[00:17] semantic_setup_job completes
```

**Total Time:** ~17 minutes

---

### Flow 2: Standalone Metric Views

```bash
databricks bundle run metric_views_job -t dev
```

**Execution Timeline:**
```
[00:00] metric_views_job starts
[00:00] Task: create_metric_views starts
[00:02] Task: create_metric_views completes (5 views created)
[00:02] metric_views_job completes
```

**Total Time:** ~2 minutes

---

## Use Cases

### Use Case 1: Initial Setup / Full Refresh
**Command:** `databricks bundle run semantic_setup_job -t dev`

**When to Use:**
- Initial deployment to new environment
- After Gold layer schema changes
- Complete semantic layer refresh
- Production deployments

**What It Does:**
1. Creates all 26 Table-Valued Functions
2. Creates all 5 Metric Views
3. Sets up complete semantic layer

---

### Use Case 2: Metric Views Iteration
**Command:** `databricks bundle run metric_views_job -t dev`

**When to Use:**
- Testing new metric view definitions
- Debugging metric view YAML
- Iterating on measures/dimensions
- Schema validation fixes

**What It Does:**
1. Creates/updates only metric views
2. Faster iteration cycle (~2 min vs ~17 min)
3. No need to recreate TVFs

---

### Use Case 3: CI/CD Pipeline
**Commands:**
```bash
# Stage 1: Deploy bundle
databricks bundle deploy -t prod

# Stage 2: Setup semantic layer
databricks bundle run semantic_setup_job -t prod
```

**Benefits:**
- Single command for complete setup
- Automated dependency management
- Consistent across environments

---

## Comparison: Before vs After

### Before (Duplicated Logic)

```yaml
# semantic_setup_job.yml
tasks:
  - task_key: create_tvfs
    notebook_task: ...
  
  - task_key: create_metric_views
    notebook_task:
      notebook_path: ../../src/.../create_metric_views.py  # Duplicated

# metric_views_job.yml
tasks:
  - task_key: create_metric_views
    notebook_task:
      notebook_path: ../../src/.../create_metric_views.py  # Duplicated
```

**Problems:**
- ❌ Logic defined in two places
- ❌ Changes need to be made twice
- ❌ Risk of inconsistency between jobs
- ❌ Harder to maintain

---

### After (Job Reference)

```yaml
# semantic_setup_job.yml
tasks:
  - task_key: create_tvfs
    notebook_task: ...
  
  - task_key: create_metric_views
    run_job_task:
      job_id: ${resources.jobs.metric_views_job.id}  # Reference

# metric_views_job.yml
tasks:
  - task_key: create_metric_views
    notebook_task:
      notebook_path: ../../src/.../create_metric_views.py  # Single definition
```

**Benefits:**
- ✅ Logic defined once
- ✅ Changes made in one place
- ✅ Guaranteed consistency
- ✅ Easier to maintain

---

## Related Patterns

### Pattern 1: Orchestrator with Multiple Job References

```yaml
# Hypothetical future pattern
tasks:
  - task_key: setup_tvfs
    run_job_task:
      job_id: ${resources.jobs.tvf_setup_job.id}
  
  - task_key: setup_metric_views
    depends_on: [setup_tvfs]
    run_job_task:
      job_id: ${resources.jobs.metric_views_job.id}
  
  - task_key: setup_genie_spaces
    depends_on: [setup_metric_views]
    run_job_task:
      job_id: ${resources.jobs.genie_setup_job.id}
```

**Use When:**
- Complex multi-stage workflows
- Each stage has independent job definition
- Need flexibility to run stages independently

---

### Pattern 2: Direct Notebook Execution

```yaml
tasks:
  - task_key: simple_task
    notebook_task:
      notebook_path: ../../src/script.py
      base_parameters:
        catalog: ${var.catalog}
```

**Use When:**
- Simple, single-purpose tasks
- No need for standalone execution
- No reuse across multiple jobs

---

## Monitoring & Debugging

### View Job Hierarchy

```bash
# List all jobs
databricks jobs list --profile wanderbricks | grep "Wanderbricks"

# Get semantic setup job details
databricks jobs get --job-id <semantic_setup_job_id> --profile wanderbricks

# Get metric views job details
databricks jobs get --job-id <metric_views_job_id> --profile wanderbricks
```

### Check Task Dependencies

In Databricks UI:
1. Navigate to **Workflows** → **Jobs**
2. Find `[dev] Wanderbricks Semantic Layer - Setup`
3. Click **Tasks** tab
4. View task graph showing:
   - `create_table_valued_functions` → `create_metric_views`
5. Click on `create_metric_views` task
6. See "Job Task" indicator showing it calls another job

### Debug Failures

```bash
# View semantic setup job runs
databricks jobs list-runs --job-id <semantic_setup_job_id> --limit 5

# View metric views job runs (includes runs triggered by semantic_setup_job)
databricks jobs list-runs --job-id <metric_views_job_id> --limit 5

# Get specific run output
databricks jobs get-run-output --run-id <run_id>
```

---

## Configuration Files

### Primary Configuration
- **`resources/gold/semantic_setup_job.yml`** - Orchestrator job with job reference
- **`resources/gold/metric_views_job.yml`** - Standalone metric views job

### Scripts
- **`src/wanderbricks_gold/create_all_tvfs.py`** - TVF creation logic
- **`src/wanderbricks_gold/semantic/create_metric_views.py`** - Metric views creation logic

### YAML Definitions
- **`src/wanderbricks_gold/semantic/metric_views/*.yaml`** - 5 metric view definitions

---

## Best Practices

### 1. **Always Use Job References for Reusable Components**
```yaml
# ✅ GOOD: Reusable job
run_job_task:
  job_id: ${resources.jobs.metric_views_job.id}

# ❌ BAD: Duplicated notebook task
notebook_task:
  notebook_path: ../../src/.../create_metric_views.py
```

### 2. **Keep Standalone Jobs Simple**
```yaml
# ✅ GOOD: Single-purpose standalone job
metric_views_job:
  tasks:
    - task_key: create_metric_views
      notebook_task: ...

# ❌ BAD: Complex standalone job with dependencies
metric_views_job:
  tasks:
    - task_key: setup
    - task_key: create_views
      depends_on: [setup]
    - task_key: validate
      depends_on: [create_views]
```

### 3. **Use Dependencies for Order Control**
```yaml
# ✅ GOOD: Explicit dependency
- task_key: create_metric_views
  depends_on:
    - task_key: create_table_valued_functions

# ❌ BAD: Implicit ordering (undefined behavior)
- task_key: create_metric_views
- task_key: create_table_valued_functions
```

### 4. **Document Job Architecture**
- Maintain architecture diagrams
- Document execution flows
- Explain when to use each job
- Keep this document updated

---

## Testing

### Test Standalone Job
```bash
# 1. Deploy
databricks bundle deploy -t dev

# 2. Run standalone
databricks bundle run metric_views_job -t dev

# 3. Verify
databricks sql "SHOW VIEWS IN dev_prashanth_subrahmanyam_wanderbricks_gold LIKE '*_metrics'"
```

**Expected:** 5 metric views created

---

### Test Orchestrator Job
```bash
# 1. Deploy
databricks bundle deploy -t dev

# 2. Run orchestrator
databricks bundle run semantic_setup_job -t dev

# 3. Verify TVFs
databricks sql "SHOW FUNCTIONS IN dev_prashanth_subrahmanyam_wanderbricks_gold LIKE 'get_*'"

# 4. Verify Metric Views
databricks sql "SHOW VIEWS IN dev_prashanth_subrahmanyam_wanderbricks_gold LIKE '*_metrics'"
```

**Expected:** 
- 26 TVFs created
- 5 metric views created

---

## Future Enhancements

### Potential Improvements

1. **Add Genie Spaces Setup Job**
   ```yaml
   tasks:
     - task_key: setup_genie_spaces
       depends_on: [create_metric_views]
       run_job_task:
         job_id: ${resources.jobs.genie_setup_job.id}
   ```

2. **Add AI/BI Dashboard Deployment**
   ```yaml
   tasks:
     - task_key: deploy_dashboards
       depends_on: [setup_genie_spaces]
       run_job_task:
         job_id: ${resources.jobs.dashboard_deploy_job.id}
   ```

3. **Parameterized Job Calls**
   ```yaml
   run_job_task:
     job_id: ${resources.jobs.metric_views_job.id}
     job_parameters:
       refresh_mode: "incremental"
   ```

---

## Troubleshooting

### Issue: "Job not found" error

**Symptom:**
```
Error: job_id ${resources.jobs.metric_views_job.id} not found
```

**Solution:**
```bash
# Ensure metric_views_job is defined in bundle
databricks bundle validate -t dev

# Check resource reference
grep -r "metric_views_job:" resources/
```

---

### Issue: Circular dependency

**Symptom:**
```
Error: Circular dependency detected
```

**Solution:**
- Ensure no job references itself
- Check `depends_on` chains don't form loops
- Use `databricks bundle validate` to detect

---

### Issue: Parameters not passed to called job

**Symptom:**
Called job fails with missing parameter errors

**Solution:**
- Called job should get parameters from its own configuration
- Don't rely on parent job parameters
- If needed, use `job_parameters` in `run_job_task`

---

## References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/)
- [Run Job Task Reference](https://docs.databricks.com/workflows/jobs/jobs-tasks.html#run-a-job-task)
- [Job Dependencies](https://docs.databricks.com/workflows/jobs/jobs-tasks.html#task-dependencies)
- [Semantic Layer Setup Guide](../deployment/metric-views-deployment-success.md)

---

**Last Updated:** 2025-12-09  
**Architecture Status:** ✅ Production-ready  
**Validated:** Yes (bundle validate + deployment successful)

