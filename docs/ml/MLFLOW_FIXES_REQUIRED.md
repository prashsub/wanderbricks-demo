# MLflow 3.1+ Fixes Required

**Status**: Experiments still showing "train", Dataset column empty  
**Root Cause**: Experiment setup happens inside run context, dataset logging missing  
**Solution**: Move experiment setup to main() before any runs, add dataset tracking

---

## Issue Analysis from Screenshot

**Problems Observed:**
1. ✅ Experiment name: "train" (should be descriptive like "conversion_predictor")
2. ❌ Dataset column: "-" (empty - should show training data reference)
3. ✅ Run names: Descriptive (good)
4. ✅ Models: Registered to Unity Catalog (good)

---

## Root Causes

### 1. Experiment Path Wrong
**Current (❌ Wrong)**:
```python
experiment_path = f"/Workspace/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/{model_name}"
```

**Should Be (✅ Correct)**:
```python
experiment_path = f"/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/{model_name}"
```

**Why**: Databricks managed MLflow uses `/Users/...` not `/Workspace/Users/...`

### 2. Experiment Setup Timing
**Current (❌ Wrong)**:
- Experiment set inside `log_model_with_mlflow()` function
- This happens INSIDE `mlflow.start_run()` context
- Too late - notebook already has default "train" experiment

**Should Be (✅ Correct)**:
- Set experiment in `main()` function BEFORE any `mlflow.start_run()`
- First thing after getting parameters

### 3. Dataset Tracking Missing
**Current (❌ Wrong)**:
- No `mlflow.log_input()` calls
- Dataset column shows "-"

**Should Be (✅ Correct)**:
```python
# After loading training data, before training
dataset = mlflow.data.from_spark(
    df=training_df_spark,
    table_name=f"{catalog}.{gold_schema}.fact_property_engagement",
    version="latest",
    targets="is_converted"
)
mlflow.log_input(dataset, context="training")
```

---

## Required Changes Per Model

### Template Pattern (Apply to ALL 4 Models)

```python
def main():
    """Main training pipeline."""
    
    # 1. Get parameters
    catalog, gold_schema, feature_schema, model_name = get_parameters()
    spark = SparkSession.builder.appName(f"{model_name} Training").getOrCreate()
    
    # =================================================================
    # 2. SET EXPERIMENT FIRST (before any MLflow operations)
    # =================================================================
    experiment_path = f"/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/{model_name}"
    
    try:
        experiment = mlflow.get_experiment_by_name(experiment_path)
        if experiment is None:
            mlflow.create_experiment(
                experiment_path,
                tags={
                    "project": "wanderbricks",
                    "model_name": model_name,
                    "mlflow_version": "3.1+"
                }
            )
        mlflow.set_experiment(experiment_path)
        print(f"✓ Experiment set: {experiment_path}")
    except Exception as e:
        print(f"❌ Failed to set experiment: {e}")
        raise  # Don't continue with default "train" experiment
    
    # =================================================================
    # 3. LOAD TRAINING DATA
    # =================================================================
    training_df_spark = spark.table(f"{catalog}.{gold_schema}.{SOURCE_TABLE}")
    
    # =================================================================
    # 4. LOG DATASET (for lineage tracking)
    # =================================================================
    try:
        dataset = mlflow.data.from_spark(
            df=training_df_spark,
            table_name=f"{catalog}.{gold_schema}.{SOURCE_TABLE}",
            version="latest",
            targets=TARGET_COLUMN
        )
        mlflow.log_input(dataset, context="training")
        print(f"✓ Logged training dataset")
    except Exception as e:
        print(f"⚠️  Dataset logging failed (non-critical): {e}")
    
    # =================================================================
    # 5. CONTINUE WITH TRAINING (existing logic)
    # =================================================================
    training_df = prepare_training_set(...)
    # ... rest of training logic
```

---

## Specific Changes Per Model

### 1. Conversion Predictor
**File**: `src/wanderbricks_ml/models/conversion_predictor/train.py`

**Add to main() after get_parameters():**
```python
# Set experiment
experiment_path = f"/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/conversion_predictor"
experiment = mlflow.get_experiment_by_name(experiment_path)
if experiment is None:
    mlflow.create_experiment(experiment_path, tags={"project": "wanderbricks"})
mlflow.set_experiment(experiment_path)

# Load and log dataset
training_df_spark = spark.table(f"{catalog}.{gold_schema}.fact_property_engagement")
dataset = mlflow.data.from_spark(
    df=training_df_spark,
    table_name=f"{catalog}.{gold_schema}.fact_property_engagement",
    version="latest",
    targets="is_converted"
)
mlflow.log_input(dataset, context="training")
```

**Remove from log_model_with_mlflow():**
- Remove experiment setup code (lines 368-379)
- Experiment should already be set

---

### 2. Pricing Optimizer
**File**: `src/wanderbricks_ml/models/pricing_optimizer/train.py`

**Add to main():**
```python
experiment_path = f"/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/pricing_optimizer"
experiment = mlflow.get_experiment_by_name(experiment_path)
if experiment is None:
    mlflow.create_experiment(experiment_path, tags={"project": "wanderbricks"})
mlflow.set_experiment(experiment_path)

training_df_spark = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
dataset = mlflow.data.from_spark(
    df=training_df_spark,
    table_name=f"{catalog}.{gold_schema}.fact_booking_daily",
    version="latest",
    targets="avg_booking_value"
)
mlflow.log_input(dataset, context="training")
```

---

### 3. Customer LTV
**File**: `src/wanderbricks_ml/models/customer_ltv/train.py`

**Add to main():**
```python
experiment_path = f"/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/customer_ltv_predictor"
experiment = mlflow.get_experiment_by_name(experiment_path)
if experiment is None:
    mlflow.create_experiment(experiment_path, tags={"project": "wanderbricks"})
mlflow.set_experiment(experiment_path)

training_df_spark = spark.table(f"{catalog}.{gold_schema}.dim_user")
dataset = mlflow.data.from_spark(
    df=training_df_spark,
    table_name=f"{catalog}.{gold_schema}.dim_user",
    version="latest",
    targets="total_spend"  # Or appropriate LTV proxy
)
mlflow.log_input(dataset, context="training")
```

---

### 4. Demand Predictor
**File**: `src/wanderbricks_ml/models/demand_predictor/train.py`

**Already has some fixes, but verify:**
- Experiment path uses `/Users/` ✓
- Dataset logging present ✓

**If missing, add:**
```python
experiment_path = f"/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/demand_predictor_seasonal_regional"
experiment = mlflow.get_experiment_by_name(experiment_path)
if experiment is None:
    mlflow.create_experiment(experiment_path, tags={"project": "wanderbricks"})
mlflow.set_experiment(experiment_path)

# Dataset logging (already added in recent changes)
```

---

## Verification Steps

After making changes, retrain models and verify:

### 1. Check Experiment Names
```sql
-- Query MLflow experiments
SELECT 
  experiment_id,
  name,
  lifecycle_stage
FROM system.mlflow.experiments
WHERE name LIKE '%wanderbricks_ml%'
ORDER BY creation_time DESC
```

**Expected**:
- `/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/conversion_predictor`
- `/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/pricing_optimizer`
- `/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/customer_ltv_predictor`
- `/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/demand_predictor_seasonal_regional`

### 2. Check Dataset Column
Navigate to MLflow UI → Runs → Should see:
- **Dataset column**: `training_data (hash)` ✅
- NOT: `-` ❌

### 3. Check Run Tags
Click any run → Tags should include:
- `mlflow.datasets.0.context`: training
- `mlflow.datasets.0.name`: {catalog}.{schema}.{table}
- `project`: wanderbricks
- `model_name`: {model_name}

---

## Quick Fix Script

Run this to update all training scripts:

```bash
cd /path/to/wanderbricks

# Update conversion predictor
sed -i 's|/Workspace/Users|/Users|g' src/wanderbricks_ml/models/conversion_predictor/train.py

# Update pricing optimizer
sed -i 's|/Workspace/Users|/Users|g' src/wanderbricks_ml/models/pricing_optimizer/train.py

# Update customer LTV
sed -i 's|/Workspace/Users|/Users|g' src/wanderbricks_ml/models/customer_ltv/train.py
```

---

## Reference Documentation

- [MLflow on Databricks](https://docs.databricks.com/aws/en/mlflow/)
- [MLflow 3.1 End-to-End Example](https://docs.databricks.com/aws/en/notebooks/source/mlflow/mlflow-classic-ml-e2e-mlflow-3.html)
- [Dataset Tracking](https://mlflow.org/docs/latest/python_api/mlflow.data.html)
- [Experiment Management](https://mlflow.org/docs/latest/tracking.html#organizing-runs-in-experiments)

---

## Impact

**Before Fixes**:
- Experiment name: "train" ❌
- Dataset tracking: None ❌
- Discoverability: Poor

**After Fixes**:
- Experiment name: "conversion_predictor" ✅
- Dataset tracking: Full lineage ✅
- Discoverability: Excellent

---

## Next Actions

1. Apply changes to 3 models (conversion, pricing, customer_ltv)
2. Retrain models: `databricks bundle run -t dev ml_training_orchestrator_job`
3. Verify in MLflow UI
4. Update demand_predictor if weather data available

