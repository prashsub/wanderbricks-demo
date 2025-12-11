# Wanderbricks ML Models

This directory contains machine learning models for the Wanderbricks vacation rental platform. All models use MLflow 3.0 best practices, Unity Catalog Feature Store, and serverless model serving.

## 📋 Overview

Wanderbricks ML provides 5 production-ready models:

| Model | Type | Use Case | Target Metric |
|-------|------|----------|---------------|
| **Revenue Forecaster** | Time Series (Prophet) | Forecast revenue 30/60/90 days | MAPE < 15% |
| **Demand Predictor** | Regression (XGBoost) | Predict booking demand by property | RMSE < 3 bookings |
| **Conversion Predictor** | Classification (XGBoost) | Predict booking conversion probability | AUC-ROC > 0.75 |
| **Pricing Optimizer** | Regression (Gradient Boosting) | Recommend optimal property prices | Revenue Lift > 5% |
| **Customer LTV** | Regression (XGBoost) | Predict 12-month customer lifetime value | MAPE < 20% |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Gold Layer                              │
│   (fact_booking_daily, dim_property, dim_user, etc.)           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Feature Store (Unity Catalog)                  │
│  ┌───────────────────┐ ┌──────────────────┐ ┌─────────────────┐ │
│  │ property_features │ │  user_features   │ │ engagement_     │ │
│  │ • Attributes      │ │  • Demographics  │ │   features      │ │
│  │ • Bookings 30d    │ │  • Behavior      │ │ • Views/Clicks  │ │
│  │ • Revenue         │ │  • Transaction   │ │ • Conversion    │ │
│  │ • Engagement      │ │    History       │ │   Rate          │ │
│  └───────────────────┘ └──────────────────┘ └─────────────────┘ │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Training Pipelines                            │
│  ┌─────────────┐ ┌────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │   Revenue   │ │   Demand   │ │ Conversion  │ │  Pricing   │ │
│  │ Forecaster  │ │ Predictor  │ │  Predictor  │ │ Optimizer  │ │
│  └─────────────┘ └────────────┘ └─────────────┘ └────────────┘ │
│                         ┌──────────────┐                         │
│                         │ Customer LTV │                         │
│                         └──────────────┘                         │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│             Unity Catalog Model Registry (MLflow 3.0)           │
│         catalog.wanderbricks_ml.{model_name}                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Inference Layer                             │
│  ┌──────────────────────────┐  ┌──────────────────────────────┐ │
│  │  Batch Inference         │  │  Model Serving Endpoints     │ │
│  │  (Daily scheduled jobs)  │  │  (Real-time REST APIs)       │ │
│  └──────────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
src/wanderbricks_ml/
├── feature_store/
│   └── setup_feature_tables.py          # Feature table creation
├── models/
│   ├── revenue_forecaster/
│   │   └── train.py                     # Prophet time series model
│   ├── demand_predictor/
│   │   └── train.py                     # XGBoost regression
│   ├── conversion_predictor/
│   │   └── train.py                     # XGBoost classification
│   ├── pricing_optimizer/
│   │   └── train.py                     # Gradient Boosting
│   └── customer_ltv/
│       └── train.py                     # XGBoost regression
├── inference/
│   └── batch_inference.py               # Batch scoring pipeline
└── README.md                            # This file

resources/ml/
├── ml_feature_store_setup_job.yml       # Feature Store setup job
├── ml_training_orchestrator_job.yml     # Training orchestrator
├── ml_batch_inference_job.yml           # Batch inference job
└── ml_model_serving_endpoints.yml       # Serving endpoint configs
```

## 🚀 Quick Start

### 1. Setup Feature Store

```bash
# Deploy Feature Store setup job
databricks bundle deploy -t dev

# Run Feature Store setup
databricks bundle run -t dev ml_feature_store_setup_job
```

This creates 3 feature tables:
- `catalog.wanderbricks_ml.property_features`
- `catalog.wanderbricks_ml.user_features`
- `catalog.wanderbricks_ml.engagement_features`

### 2. Train Models

```bash
# Train all models (orchestrated)
databricks bundle run -t dev ml_training_orchestrator_job
```

This trains all 5 models in sequence and registers them in Unity Catalog Model Registry.

**Or train individual models:**

```bash
# Revenue Forecaster
databricks bundle run -t dev ml_training_orchestrator_job --task train_revenue_forecaster

# Demand Predictor
databricks bundle run -t dev ml_training_orchestrator_job --task train_demand_predictor
```

### 3. Batch Inference

```bash
# Run batch inference for all models
databricks bundle run -t dev ml_batch_inference_job
```

Predictions are saved to:
- `catalog.wanderbricks_ml.demand_predictions`
- `catalog.wanderbricks_ml.conversion_predictions`
- `catalog.wanderbricks_ml.pricing_recommendations`
- `catalog.wanderbricks_ml.customer_ltv_predictions`

### 4. Real-Time Serving

Model serving endpoints must be created via UI or API after models are registered.

**Via UI:**
1. Go to **Serving** in Databricks workspace
2. Click **Create Serving Endpoint**
3. Select model: `catalog.wanderbricks_ml.{model_name}`
4. Choose **Small** workload size
5. Enable **Scale to zero**

**Via API:**
```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
w.serving_endpoints.create(
    name="wanderbricks-demand-predictor",
    config={
        "served_models": [{
            "model_name": "catalog.wanderbricks_ml.demand_predictor",
            "model_version": "1",
            "workload_size": "Small",
            "scale_to_zero_enabled": True
        }]
    }
)
```

**Test endpoint:**
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

## 🎯 Model Details

### 1. Revenue Forecaster

**Algorithm:** Prophet (Facebook's time series forecasting)  
**Purpose:** Forecast revenue for financial planning  
**Features:**
- Historical daily revenue
- Seasonality (yearly, weekly)
- Custom regressors (booking count, day of week)

**Training:**
```python
# Uses MLflow Prophet flavor
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    seasonality_mode='multiplicative'
)
mlflow.prophet.log_model(model, "model")
```

**Performance Target:** MAPE < 15%

### 2. Demand Predictor

**Algorithm:** XGBoost Regressor  
**Purpose:** Predict booking demand by property/date  
**Features:** (from Feature Store)
- Property: type, bedrooms, price, location
- Historical: bookings_30d, revenue_30d
- Engagement: views, clicks, conversion rate

**Training:**
```python
# Uses Feature Engineering Client
training_set = fe.create_training_set(
    df=labels,
    feature_lookups=[...],
    label="booking_count"
)
model = XGBRegressor(...)
fe.log_model(model, training_set=training_set)
```

**Performance Target:** RMSE < 3 bookings

### 3. Conversion Predictor

**Algorithm:** XGBoost Classifier  
**Purpose:** Predict probability of engagement converting to booking  
**Features:**
- Engagement: view_count, click_count
- Property: price, ratings, photos
- User: repeat customer, country

**Output:**
```python
{
    "conversion_probability": 0.23,
    "predicted_conversion": 0,  # 1 if > 0.5
}
```

**Performance Target:** AUC-ROC > 0.75

### 4. Pricing Optimizer

**Algorithm:** Gradient Boosting Regressor  
**Purpose:** Recommend optimal prices for revenue maximization  
**Features:**
- Property attributes
- Demand forecasts
- Seasonal factors
- Competitive pricing

**Output:**
```python
{
    "recommended_price": 180.50,
    "current_price": 150.00,
    "expected_revenue_lift": "+12.5%"
}
```

**Performance Target:** Revenue Lift > 5%

### 5. Customer LTV Predictor

**Algorithm:** XGBoost Regressor  
**Purpose:** Predict 12-month forward customer lifetime value  
**Features:**
- Demographics: country, user_type
- Behavior: booking frequency, cancellation rate
- Transaction: total bookings, avg booking value
- Recency: days since last booking

**Output:**
```python
{
    "predicted_ltv_12m": 2500.00,
    "ltv_segment": "High Value",  # Low/Medium/High/VIP
    "churn_risk": "Low"
}
```

**Performance Target:** MAPE < 20%

## 🔄 Retraining Schedule

| Model | Frequency | Schedule | Reason |
|-------|-----------|----------|--------|
| Revenue Forecaster | Weekly | Sunday 2 AM | New booking data |
| Demand Predictor | Weekly | Sunday 2 AM | Seasonality changes |
| Conversion Predictor | Weekly | Sunday 2 AM | User behavior shifts |
| Pricing Optimizer | Weekly | Sunday 2 AM | Market dynamics |
| Customer LTV | Monthly | 1st Sunday 2 AM | Slower behavior changes |

**Automatic retraining:**
```bash
# Enable schedule in production
# Edit resources/ml/ml_training_orchestrator_job.yml
schedule:
  pause_status: UNPAUSED  # Change from PAUSED
```

## 📊 Monitoring

### Model Performance Tracking

**Via MLflow Experiments:**
```python
import mlflow

# View experiment runs
experiment = mlflow.get_experiment_by_name("/Wanderbricks/Demand_Predictor")
runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])

# Compare metrics
runs[['metrics.val_rmse', 'metrics.val_r2', 'params.n_estimators']]
```

**Via Unity Catalog:**
```sql
-- Model version metrics
SELECT 
  model_name,
  version,
  creation_timestamp,
  tags
FROM system.models.model_versions
WHERE model_name LIKE 'wanderbricks_ml.%'
ORDER BY creation_timestamp DESC;
```

### Inference Monitoring

**Batch inference results:**
```sql
-- Check prediction quality
SELECT 
  scoring_date,
  COUNT(*) as predictions_count,
  AVG(predicted_bookings) as avg_predicted_bookings,
  MIN(predicted_bookings) as min_prediction,
  MAX(predicted_bookings) as max_prediction
FROM wanderbricks_ml.demand_predictions
GROUP BY scoring_date
ORDER BY scoring_date DESC;
```

**Serving endpoint metrics:**
- Available in **Serving UI > Endpoint > Metrics**
- Latency percentiles (p50, p95, p99)
- Request rate
- Error rate
- Model drift (if enabled)

## 🛠️ Development Workflow

### 1. Feature Engineering

```python
# Add new features to Feature Store
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Update existing feature table
fe.write_table(
    name="catalog.wanderbricks_ml.property_features",
    df=updated_features_df,
    mode="merge"  # Incremental update
)
```

### 2. Experiment Tracking

```python
import mlflow

mlflow.set_experiment("/Wanderbricks/My_Experiment")

with mlflow.start_run():
    # Log parameters
    mlflow.log_params({"learning_rate": 0.1, "max_depth": 6})
    
    # Train model
    model = train_model(...)
    
    # Log metrics
    mlflow.log_metrics({"rmse": 2.5, "r2": 0.85})
    
    # Log model
    mlflow.xgboost.log_model(model, "model")
```

### 3. Model Versioning

```python
# Register new version
model_info = mlflow.register_model(
    model_uri="runs:/<run_id>/model",
    name="catalog.wanderbricks_ml.demand_predictor"
)

# Transition to production
client = mlflow.tracking.MlflowClient()
client.set_registered_model_alias(
    name="catalog.wanderbricks_ml.demand_predictor",
    alias="Production",
    version=model_info.version
)
```

### 4. A/B Testing

```python
# Deploy multiple model versions
w.serving_endpoints.update_config(
    name="wanderbricks-demand-predictor",
    served_models=[
        {
            "model_name": "catalog.wanderbricks_ml.demand_predictor",
            "model_version": "1",
            "workload_size": "Small",
            "scale_to_zero_enabled": True,
            "traffic_percentage": 90  # Champion
        },
        {
            "model_name": "catalog.wanderbricks_ml.demand_predictor",
            "model_version": "2",
            "workload_size": "Small",
            "scale_to_zero_enabled": True,
            "traffic_percentage": 10  # Challenger
        }
    ]
)
```

## 🔧 Troubleshooting

### Issue: Feature lookup fails during training

**Error:** `Feature table not found: catalog.wanderbricks_ml.property_features`

**Solution:**
```bash
# Run Feature Store setup
databricks bundle run -t dev ml_feature_store_setup_job
```

### Issue: Model training times out

**Error:** `Task exceeded timeout of 3600 seconds`

**Solution:** Increase timeout in job YAML:
```yaml
tasks:
  - task_key: train_model
    timeout_seconds: 7200  # 2 hours
```

### Issue: Prediction results are NULL

**Cause:** Feature values missing for scoring records

**Solution:** Check feature freshness:
```sql
SELECT 
  MAX(feature_date) as latest_features
FROM wanderbricks_ml.property_features;
```

Refresh features if stale:
```bash
databricks bundle run -t dev ml_feature_store_setup_job
```

## 📚 References

### MLflow 3.0
- [MLflow 3.0 Overview](https://learn.microsoft.com/en-us/azure/databricks/mlflow/mlflow-3-install)
- [Logged Models](https://learn.microsoft.com/en-us/azure/databricks/mlflow/logged-model)
- [Model Registry](https://learn.microsoft.com/en-us/azure/databricks/mlflow/model-registry-3)

### Feature Store
- [Feature Engineering Client](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/uc/feature-tables-uc)
- [Train Models with Feature Store](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/train-models-with-feature-store)
- [Online Feature Store](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/online-feature-store)

### Model Serving
- [Model Serving Overview](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/)
- [Serverless Model Serving](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/serverless-optimized-deployments)
- [Query Endpoints](https://learn.microsoft.com/en-us/azure/databricks/machine-learning/model-serving/score-custom-model-endpoints)

## 💡 Next Steps

1. **Enable Production Deployment**
   ```bash
   databricks bundle deploy -t prod
   ```

2. **Enable Automatic Retraining**
   - Edit `resources/ml/ml_training_orchestrator_job.yml`
   - Set `pause_status: UNPAUSED`

3. **Set Up Model Monitoring**
   - Enable inference tables in serving endpoints
   - Create AI/BI dashboards for model performance
   - Set up alerting for degraded performance

4. **Integrate with Applications**
   - Use model predictions in recommendation engine
   - Feed pricing recommendations to dynamic pricing system
   - Use LTV segments for targeted marketing

5. **Expand ML Capabilities**
   - Add property similarity model (embeddings)
   - Build churn prediction model
   - Create dynamic pricing rules engine

