# Wanderbricks ML - Quick Reference

## 📋 Quick Commands

### Setup (One-Time)
```bash
# Deploy ML resources
databricks bundle deploy -t dev

# Create feature tables
databricks bundle run -t dev ml_feature_store_setup_job
```

### Train Models
```bash
# Train all models (1-2 hours)
databricks bundle run -t dev ml_training_orchestrator_job

# Train individual model
databricks bundle run -t dev ml_training_orchestrator_job --task train_revenue_forecaster
databricks bundle run -t dev ml_training_orchestrator_job --task train_demand_predictor
databricks bundle run -t dev ml_training_orchestrator_job --task train_conversion_predictor
databricks bundle run -t dev ml_training_orchestrator_job --task train_pricing_optimizer
databricks bundle run -t dev ml_training_orchestrator_job --task train_customer_ltv
```

### Batch Inference
```bash
# Score with all models
databricks bundle run -t dev ml_batch_inference_job

# Score individual model
databricks bundle run -t dev ml_batch_inference_job --task score_demand_predictions
databricks bundle run -t dev ml_batch_inference_job --task score_conversion_predictions
databricks bundle run -t dev ml_batch_inference_job --task score_pricing_recommendations
databricks bundle run -t dev ml_batch_inference_job --task score_customer_ltv
```

## 📊 Model Summary

| Model | Algorithm | Use Case | Target |
|-------|-----------|----------|--------|
| Revenue Forecaster | Prophet | Financial forecasting | MAPE < 15% |
| Demand Predictor | XGBoost | Inventory optimization | RMSE < 3 |
| Conversion Predictor | XGBoost | Marketing targeting | AUC > 0.75 |
| Pricing Optimizer | Gradient Boosting | Dynamic pricing | Lift > 5% |
| Customer LTV | XGBoost | Customer segmentation | MAPE < 20% |

## 🗂️ Feature Tables

```sql
-- Property features (15 features)
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.property_features;

-- User features (12 features)
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.user_features;

-- Engagement features (8 features)
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.engagement_features;
```

## 📈 Check Model Performance

```sql
-- View registered models
SELECT 
  model_name,
  version,
  creation_timestamp
FROM system.models.model_versions
WHERE model_name LIKE 'prashanth_subrahmanyam_catalog.wanderbricks_ml.%'
ORDER BY creation_timestamp DESC;

-- Check predictions
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.demand_predictions LIMIT 10;
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.conversion_predictions LIMIT 10;
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.pricing_recommendations LIMIT 10;
SELECT * FROM prashanth_subrahmanyam_catalog.wanderbricks_ml.customer_ltv_predictions LIMIT 10;
```

## 🔧 Common Tasks

### Update Features
```bash
# Refresh feature tables
databricks bundle run -t dev ml_feature_store_setup_job
```

### Check MLflow Experiments
Navigate to workspace:
- `/Wanderbricks/Revenue_Forecaster`
- `/Wanderbricks/Demand_Predictor`
- `/Wanderbricks/Conversion_Predictor`
- `/Wanderbricks/Pricing_Optimizer`
- `/Wanderbricks/Customer_LTV`

### Create Serving Endpoint
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.serving_endpoints.create(
    name="wanderbricks-demand-predictor",
    config={
        "served_models": [{
            "model_name": "prashanth_subrahmanyam_catalog.wanderbricks_ml.demand_predictor",
            "model_version": "1",
            "workload_size": "Small",
            "scale_to_zero_enabled": True
        }]
    }
)
```

### Test Endpoint
```bash
curl -X POST \
  https://<workspace>.databricks.com/serving-endpoints/wanderbricks-demand-predictor/invocations \
  -H "Authorization: Bearer <token>" \
  -d '{
    "dataframe_records": [{
      "property_id": "PROP001",
      "check_in_date": "2025-06-15"
    }]
  }'
```

## 📁 File Locations

### Code
- Feature Store: `src/wanderbricks_ml/feature_store/setup_feature_tables.py`
- Training: `src/wanderbricks_ml/models/*/train.py`
- Inference: `src/wanderbricks_ml/inference/batch_inference.py`

### Configuration
- Feature Store Setup: `resources/ml/ml_feature_store_setup_job.yml`
- Training Orchestrator: `resources/ml/ml_training_orchestrator_job.yml`
- Batch Inference: `resources/ml/ml_batch_inference_job.yml`
- Serving Endpoints: `resources/ml/ml_model_serving_endpoints.yml`

### Documentation
- Main README: `src/wanderbricks_ml/README.md`
- Implementation Summary: `plans/ML_IMPLEMENTATION_SUMMARY.md`
- This Quick Ref: `plans/ML_QUICK_REFERENCE.md`

## 🚨 Troubleshooting

### Feature table not found
```bash
# Run setup
databricks bundle run -t dev ml_feature_store_setup_job
```

### Model training timeout
```yaml
# Edit job YAML, increase timeout
timeout_seconds: 7200
```

### Predictions are NULL
```sql
-- Check feature freshness
SELECT MAX(feature_date) FROM wanderbricks_ml.property_features;
```

## 📚 Documentation Links

- [MLflow 3.0](https://learn.microsoft.com/en-us/azure/databricks/mlflow/mlflow-3-install)
- [Feature Store](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/uc/feature-tables-uc)
- [Model Serving](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/)
- [Main README](../src/wanderbricks_ml/README.md)

