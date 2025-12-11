# Lakehouse Monitoring - Two Workflow Approach

## Overview

The Wanderbricks monitoring implementation provides **two separate workflows** for managing Lakehouse Monitors:

1. **Initial Setup** - Creates monitors with deletion of existing (fresh start)
2. **Update** - Updates monitors without deletion (preserves data)

This separation ensures safe production operations while allowing flexibility for different scenarios.

---

## Why Two Workflows?

### Problem with Single Workflow

A single workflow that always deletes monitors has these issues:

1. ❌ **Data Loss Risk** - Every update loses historical monitoring data
2. ❌ **Long Downtime** - 15-20 minute initialization wait on every change
3. ❌ **No Rollback** - Can't revert to previous monitor configuration
4. ❌ **Production Unsafe** - Risky to update metrics in production

### Solution: Separate Workflows

| Scenario | Workflow | Impact |
|----------|----------|--------|
| First-time setup | Initial Setup | No data exists yet (safe) |
| Add new metric | Update | Historical data preserved |
| Change metric definition | Update | Historical data preserved |
| Update slicing | Update | Historical data preserved |
| Corrupted monitor | Initial Setup | Fresh start (intentional reset) |
| Major refactor | Initial Setup | Clean slate needed |

---

## Workflow 1: Initial Setup

### Purpose

Creates monitors from scratch. Deletes any existing monitors first.

### Files

- **Script:** `src/wanderbricks_gold/lakehouse_monitoring.py`
- **Job:** `resources/gold/lakehouse_monitoring_job.yml`
- **Bundle Command:** `databricks bundle run lakehouse_monitoring_job -t dev`

### Behavior

```python
def delete_existing_monitor(w: WorkspaceClient, table_name: str):
    """Delete existing monitor before creating new one."""
    try:
        existing = w.quality_monitors.get(table_name=table_name)
        if existing:
            w.quality_monitors.delete(table_name=table_name)
            time.sleep(5)  # Pause after deletion
    except Exception as e:
        pass  # Ignore "not found" errors

# Then creates new monitor
monitor_info = w.quality_monitors.create(...)
```

### When to Use

✅ **Use Initial Setup when:**
- Setting up monitors for the first time
- Monitors are corrupted or misconfigured
- Need a complete fresh start
- Don't care about historical monitoring data
- Testing/development environment

❌ **Don't use Initial Setup when:**
- Monitors already exist in production
- Need to preserve historical data
- Just adding or updating metrics
- Changing configuration only

### Timeline

| Step | Duration | Details |
|------|----------|---------|
| Bundle deploy | 1 min | Upload job config |
| Monitor creation | 3 min | Create 5 monitors |
| Initialization | 15-20 min | Async background process |
| **Total** | **~25 min** | **Including wait time** |

---

## Workflow 2: Update

### Purpose

Updates existing monitors without deletion. Preserves all historical data.

### Files

- **Script:** `src/wanderbricks_gold/update_lakehouse_monitoring.py`
- **Job:** `resources/gold/update_lakehouse_monitoring_job.yml`
- **Bundle Command:** `databricks bundle run update_lakehouse_monitoring_job -t dev`

### Behavior

```python
def update_monitor_with_custom_metrics(w: WorkspaceClient, table_name: str, ...):
    """Update existing monitor without deletion."""
    
    # Check if monitor exists
    existing = w.quality_monitors.get(table_name=table_name)
    if not existing:
        print("Monitor does not exist. Run setup first.")
        return None
    
    # Update (no deletion)
    monitor_info = w.quality_monitors.update(...)
    return monitor_info
```

### When to Use

✅ **Use Update when:**
- Monitors already exist
- Adding new custom metrics
- Updating metric definitions
- Changing slicing expressions
- Modifying time series configuration
- Production environment
- Need to preserve historical data

❌ **Don't use Update when:**
- Monitors don't exist yet (run Initial Setup first)
- Monitors are corrupted (use Initial Setup)
- Want a complete fresh start

### Timeline

| Step | Duration | Details |
|------|----------|---------|
| Bundle deploy | 1 min | Upload job config |
| Monitor update | 3 min | Update 5 monitors |
| Refresh | 2-5 min | Background refresh |
| **Total** | **~5 min** | **Much faster!** |

---

## Decision Tree

```
┌─────────────────────────────────┐
│ Do monitors exist?              │
└────────┬───────────────┬────────┘
         │               │
         ▼               ▼
    ┌────────┐      ┌────────┐
    │   NO   │      │  YES   │
    └───┬────┘      └───┬────┘
        │               │
        ▼               ▼
  ┌──────────────┐  ┌──────────────────────┐
  │ Initial      │  │ Do you need to       │
  │ Setup        │  │ preserve data?       │
  └──────────────┘  └──────┬───────────┬───┘
                           │           │
                           ▼           ▼
                      ┌────────┐  ┌──────────────┐
                      │  YES   │  │     NO       │
                      └───┬────┘  └──────┬───────┘
                          │              │
                          ▼              ▼
                    ┌──────────┐  ┌──────────────┐
                    │ Update   │  │ Initial      │
                    │ Workflow │  │ Setup        │
                    └──────────┘  └──────────────┘
```

---

## Example Scenarios

### Scenario 1: First-Time Setup

**Context:** Gold layer just deployed, no monitors exist

**Workflow:** Initial Setup

**Commands:**
```bash
databricks bundle deploy -t dev
databricks bundle run lakehouse_monitoring_job -t dev
# Wait 20 minutes for initialization
```

**Outcome:** 5 monitors created, ready to use

---

### Scenario 2: Add New Metric

**Context:** Monitors running in production, need to add "avg_nights_per_booking" metric

**Workflow:** Update

**Steps:**
1. Edit `update_lakehouse_monitoring.py`
2. Add new metric to `custom_metrics` list:
   ```python
   {
       "type": "AGGREGATE",
       "name": "avg_nights_per_booking",
       "input_columns": [":table"],
       "definition": "AVG(nights_stayed)",
       "output_data_type": "double"
   }
   ```
3. Deploy and run:
   ```bash
   databricks bundle deploy -t dev
   databricks bundle run update_lakehouse_monitoring_job -t dev
   ```

**Outcome:** New metric added, historical data preserved, ~5 min total

---

### Scenario 3: Monitor Corrupted

**Context:** Monitor showing errors, dashboards not loading

**Workflow:** Initial Setup (fresh start)

**Commands:**
```bash
databricks bundle run lakehouse_monitoring_job -t dev
# Wait 20 minutes
```

**Outcome:** Clean monitors, historical data lost (acceptable for recovery)

---

### Scenario 4: Change Metric Definition

**Context:** Need to change how "cancellation_rate" is calculated

**Workflow:** Update

**Steps:**
1. Edit `update_lakehouse_monitoring.py`
2. Modify metric definition:
   ```python
   # OLD
   "definition": "({{total_cancellations}} / NULLIF({{total_bookings}}, 0)) * 100"
   
   # NEW (exclude no-shows)
   "definition": "({{confirmed_cancellations}} / NULLIF({{total_bookings}}, 0)) * 100"
   ```
3. Deploy and run:
   ```bash
   databricks bundle deploy -t dev
   databricks bundle run update_lakehouse_monitoring_job -t dev
   ```

**Outcome:** Updated calculation, historical data trends preserved

---

## File Organization

```
src/wanderbricks_gold/
├── lakehouse_monitoring.py          # Initial Setup (with deletion)
│   └── Functions: delete_existing_monitor() + create_*_monitor()
│
├── update_lakehouse_monitoring.py   # Update (without deletion)
│   └── Functions: update_monitor_with_custom_metrics() + update_*_monitor()
│
├── monitoring_queries.sql           # Query examples (same for both)
├── MONITORING_README.md             # Full documentation
├── MONITORING_QUICKSTART.md         # Quick deployment guide
└── MONITORING_WORKFLOWS.md          # This file

resources/gold/
├── lakehouse_monitoring_job.yml     # Initial Setup job
└── update_lakehouse_monitoring_job.yml # Update job
```

---

## Code Differences

### Initial Setup Script

```python
def create_revenue_monitor(w: WorkspaceClient, catalog: str, schema: str):
    """Create monitor (deletes existing first)."""
    
    # 1. Delete if exists
    delete_existing_monitor(w, table_name)
    
    # 2. Create new
    monitor_info = w.quality_monitors.create(
        table_name=table_name,
        custom_metrics=custom_metrics,
        ...
    )
    
    return monitor_info
```

### Update Script

```python
def update_revenue_monitor(w: WorkspaceClient, catalog: str, schema: str):
    """Update monitor (no deletion)."""
    
    # 1. Check exists
    existing = w.quality_monitors.get(table_name=table_name)
    if not existing:
        print("Monitor does not exist")
        return None
    
    # 2. Update (no deletion)
    monitor_info = w.quality_monitors.update(
        table_name=table_name,
        custom_metrics=custom_metrics,
        ...
    )
    
    return monitor_info
```

**Key Difference:** `create()` vs `update()` SDK method

---

## Best Practices

### For Development

1. ✅ Use Initial Setup freely (data loss acceptable)
2. ✅ Test metric changes with Update workflow first
3. ✅ Iterate quickly with Update (no 20-min wait)

### For Production

1. ✅ **ALWAYS use Update workflow** for changes
2. ⚠️ Only use Initial Setup for:
   - Absolute first-time setup
   - Disaster recovery (corrupted monitors)
   - Intentional complete refresh
3. ✅ Test changes in dev first
4. ✅ Plan downtime if using Initial Setup

### For Metric Changes

| Change Type | Workflow | Example |
|------------|----------|---------|
| Add metric | Update | New "revenue_per_guest" metric |
| Remove metric | Update | Remove unused "test_metric" |
| Change definition | Update | Fix calculation error |
| Rename metric | Initial Setup | Requires recreation |
| Change input_columns | Initial Setup | Structural change |

---

## Rollback Strategy

### If Update Breaks Something

**Option 1: Quick Fix**
```bash
# Edit script to fix issue
databricks bundle deploy -t dev
databricks bundle run update_lakehouse_monitoring_job -t dev
```

**Option 2: Revert to Previous**
```bash
# Git revert to previous working version
git revert HEAD
databricks bundle deploy -t dev
databricks bundle run update_lakehouse_monitoring_job -t dev
```

### If Initial Setup Needed

```bash
# Complete refresh (loses historical data)
databricks bundle run lakehouse_monitoring_job -t dev
# Wait 20 minutes
```

---

## Validation Checklist

After running either workflow:

### Immediate Checks
- [ ] Job completed successfully (no errors)
- [ ] All 5 monitors listed in output
- [ ] No monitors in "failed" list

### After Initialization (Initial Setup only)
- [ ] Monitor status = ACTIVE (check UI)
- [ ] Dashboards auto-generated
- [ ] Metrics tables populated

### After Update
- [ ] Monitor status still ACTIVE
- [ ] New metrics appear in dashboards
- [ ] Historical trends preserved
- [ ] Queries return new metrics

---

## Troubleshooting

### "Monitor does not exist" during Update

**Cause:** Trying to update non-existent monitor

**Solution:** Run Initial Setup first
```bash
databricks bundle run lakehouse_monitoring_job -t dev
```

---

### Update completes but metrics not showing

**Cause:** Refresh delay (2-5 minutes)

**Solution:** Wait and check dashboard again

---

### Want to change from Setup to Update

**Already ran Initial Setup accidentally?**

No problem! Historical data is already gone. Just note for next time:
- Development: Either workflow works
- Production: Always use Update

---

## Summary

| Aspect | Initial Setup | Update |
|--------|--------------|--------|
| **Use When** | First time / Recovery | Changes / Updates |
| **Deletes Data** | ✅ Yes | ❌ No |
| **Wait Time** | ⏱️ 20 min | ⚡ 5 min |
| **Risk Level** | ⚠️ High | ✅ Low |
| **Production** | Rare | Common |
| **Command** | `lakehouse_monitoring_job` | `update_lakehouse_monitoring_job` |

**Golden Rule:**
- **Development:** Use whichever is faster for your workflow
- **Production:** Almost always use Update (preserves data)

---

## References

### Implementation Files
- Initial Setup: `src/wanderbricks_gold/lakehouse_monitoring.py`
- Update: `src/wanderbricks_gold/update_lakehouse_monitoring.py`
- Jobs: `resources/gold/*.yml`

### Documentation
- Full Guide: `MONITORING_README.md`
- Quick Start: `MONITORING_QUICKSTART.md`
- Workflows: `MONITORING_WORKFLOWS.md` (this file)

### Databricks SDK
- [Create Monitor](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/quality_monitors.html#databricks.sdk.service.catalog.QualityMonitorsAPI.create)
- [Update Monitor](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/quality_monitors.html#databricks.sdk.service.catalog.QualityMonitorsAPI.update)

---

**Last Updated:** December 10, 2025  
**Version:** 1.0 - Two Workflow Approach

