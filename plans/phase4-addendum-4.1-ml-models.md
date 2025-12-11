# Phase 4 Addendum 4.1: ML Models

## Overview

**Status:** 📋 Planned  
**Dependencies:** Phase 3 (Gold Layer)  
**Artifact Count:** 5 ML Models  
**Reference:** [MLflow Documentation](https://docs.databricks.com/mlflow/)

---

## Purpose

ML Models provide:
1. **Predictive analytics** - Forecast future trends
2. **Optimization** - Data-driven pricing recommendations
3. **Segmentation** - Automated customer clustering
4. **Anomaly detection** - Identify unusual patterns
5. **Personalization** - Improve user experience

---

## Model Summary

| # | Model | Domain | Use Case | Type |
|---|-------|--------|----------|------|
| 1 | Revenue Forecaster | 💰 Revenue | Predict future revenue | Time Series |
| 2 | Demand Predictor | 💰 Revenue | Predict booking demand | Regression |
| 3 | Conversion Predictor | 📊 Engagement | Predict booking conversion | Classification |
| 4 | Pricing Optimizer | 🏠 Property | Recommend optimal prices | Regression |
| 5 | Customer LTV Predictor | 🎯 Customer | Predict customer lifetime value | Regression |

---

## 💰 Revenue Forecaster

### Purpose
Forecast revenue for the next 30/60/90 days to support financial planning.

### Model Details

| Attribute | Value |
|-----------|-------|
| Algorithm | Prophet / XGBoost |
| Training Data | fact_booking_daily (2+ years) |
| Target Variable | total_booking_value |
| Features | Date components, seasonality, holidays |
| Prediction Horizon | 30, 60, 90 days |
| Refresh Frequency | Weekly |

### Feature Engineering

```python
from pyspark.sql.functions import *

def create_revenue_features(df):
    """Create features for revenue forecasting."""
    return df.select(
        col("check_in_date").alias("ds"),  # Prophet format
        col("total_booking_value").alias("y"),
        # Lag features
        lag("total_booking_value", 7).over(window).alias("revenue_lag_7d"),
        lag("total_booking_value", 30).over(window).alias("revenue_lag_30d"),
        # Rolling averages
        avg("total_booking_value").over(
            Window.orderBy("check_in_date").rowsBetween(-7, -1)
        ).alias("revenue_ma_7d"),
        # Time features
        dayofweek("check_in_date").alias("dow"),
        month("check_in_date").alias("month"),
        quarter("check_in_date").alias("quarter")
    )
```

### Training Pipeline

```python
import mlflow
from prophet import Prophet

def train_revenue_forecaster(spark, catalog, gold_schema):
    """Train revenue forecasting model."""
    
    mlflow.set_experiment("/Wanderbricks/Revenue_Forecaster")
    
    with mlflow.start_run(run_name="revenue_prophet"):
        # Load data
        df = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
        pdf = create_revenue_features(df).toPandas()
        
        # Train Prophet model
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode='multiplicative'
        )
        model.fit(pdf)
        
        # Log model
        mlflow.prophet.log_model(model, "revenue_forecaster")
        
        # Log metrics
        cv_results = cross_validation(model, horizon='30 days')
        mlflow.log_metric("mape", cv_results['mape'].mean())
        mlflow.log_metric("rmse", cv_results['rmse'].mean())
```

### Inference Endpoint

```python
# Model serving endpoint
from mlflow.pyfunc import load_model

def predict_revenue(start_date, end_date):
    """Predict revenue for date range."""
    model = load_model(f"models:/wanderbricks_revenue_forecaster/Production")
    
    future = pd.DataFrame({'ds': pd.date_range(start_date, end_date)})
    forecast = model.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

---

## 💰 Demand Predictor

### Purpose
Predict booking demand by property/destination to optimize inventory and pricing.

### Model Details

| Attribute | Value |
|-----------|-------|
| Algorithm | XGBoost / LightGBM |
| Training Data | fact_booking_daily + dim_property |
| Target Variable | booking_count |
| Features | Property attributes, seasonality, price |
| Prediction Horizon | 7-30 days |

### Feature Set

| Feature Category | Features |
|-----------------|----------|
| Property | property_type, bedrooms, base_price, max_guests |
| Location | destination, country, latitude, longitude |
| Temporal | day_of_week, month, is_holiday, is_weekend |
| Historical | bookings_lag_7d, bookings_lag_30d, bookings_ma_7d |
| Engagement | views_7d, clicks_7d, conversion_rate |

---

## 📊 Conversion Predictor

### Purpose
Predict likelihood of property view converting to booking for marketing optimization.

### Model Details

| Attribute | Value |
|-----------|-------|
| Algorithm | Logistic Regression / XGBoost |
| Training Data | fact_property_engagement + fact_booking_detail |
| Target Variable | is_converted (binary) |
| Features | Property, engagement, user attributes |
| Use Case | Marketing targeting, content optimization |

### Feature Set

| Feature Category | Features |
|-----------------|----------|
| Engagement | view_count, click_count, time_on_page |
| Property | property_type, price, rating, photos_count |
| User | is_repeat, country, device_type |
| Context | day_of_week, time_of_day, referrer |

### Model Output

```python
# Predict conversion probability
{
    "property_id": 12345,
    "user_id": 67890,
    "conversion_probability": 0.23,
    "confidence_interval": [0.18, 0.28],
    "top_factors": [
        {"factor": "low_price", "impact": +0.08},
        {"factor": "high_rating", "impact": +0.05},
        {"factor": "mobile_device", "impact": -0.03}
    ]
}
```

---

## 🏠 Pricing Optimizer

### Purpose
Recommend optimal property prices to maximize revenue and occupancy.

### Model Details

| Attribute | Value |
|-----------|-------|
| Algorithm | Gradient Boosting / Neural Network |
| Training Data | fact_booking_daily + dim_property |
| Target Variable | optimal_price (revenue-maximizing) |
| Features | Property, demand, competition, seasonality |
| Update Frequency | Daily |

### Optimization Logic

```python
def optimize_price(property_id, target_date, demand_forecast):
    """Find revenue-maximizing price."""
    
    # Get property details
    property = get_property(property_id)
    
    # Price elasticity model
    price_range = np.linspace(property.base_price * 0.5, 
                              property.base_price * 2.0, 
                              100)
    
    expected_revenue = []
    for price in price_range:
        # Predict demand at this price
        demand = demand_model.predict(property, price, target_date)
        # Calculate expected revenue
        revenue = price * demand
        expected_revenue.append(revenue)
    
    # Find optimal price
    optimal_idx = np.argmax(expected_revenue)
    optimal_price = price_range[optimal_idx]
    
    return {
        "current_price": property.base_price,
        "recommended_price": optimal_price,
        "expected_demand": demand_model.predict(property, optimal_price, target_date),
        "expected_revenue": expected_revenue[optimal_idx]
    }
```

---

## 🎯 Customer LTV Predictor

### Purpose
Predict customer lifetime value for segmentation and retention targeting.

### Model Details

| Attribute | Value |
|-----------|-------|
| Algorithm | XGBoost / Neural Network |
| Training Data | dim_user + fact_booking_detail |
| Target Variable | 12-month forward revenue |
| Features | Demographics, behavior, transaction history |
| Use Case | Customer segmentation, retention campaigns |

### Feature Set

| Feature Category | Features |
|-----------------|----------|
| Demographics | country, user_type, is_business, tenure_days |
| Transaction | total_bookings, total_spend, avg_booking_value |
| Behavior | booking_frequency, avg_lead_time, cancellation_rate |
| Recency | days_since_last_booking, booking_trend |

### Model Output

```python
{
    "user_id": 12345,
    "predicted_ltv_12m": 2500.00,
    "confidence_interval": [2100.00, 2900.00],
    "ltv_segment": "High Value",
    "churn_risk": "Low",
    "recommended_actions": [
        "Offer loyalty discount",
        "Send personalized recommendations"
    ]
}
```

---

## ML Infrastructure

### MLflow Experiments

| Experiment | Path |
|------------|------|
| Revenue Forecaster | /Wanderbricks/Revenue_Forecaster |
| Demand Predictor | /Wanderbricks/Demand_Predictor |
| Conversion Predictor | /Wanderbricks/Conversion_Predictor |
| Pricing Optimizer | /Wanderbricks/Pricing_Optimizer |
| Customer LTV | /Wanderbricks/Customer_LTV |

### Model Registry

| Model | Stage | Version |
|-------|-------|---------|
| wanderbricks_revenue_forecaster | Production | 1.0 |
| wanderbricks_demand_predictor | Production | 1.0 |
| wanderbricks_conversion_predictor | Staging | 0.9 |
| wanderbricks_pricing_optimizer | Staging | 0.9 |
| wanderbricks_customer_ltv | Staging | 0.9 |

### Model Serving

```yaml
# Serverless model serving endpoint
endpoints:
  - name: wanderbricks-predictions
    served_models:
      - model_name: wanderbricks_revenue_forecaster
        model_version: 1
        workload_size: Small
        scale_to_zero_enabled: true
      - model_name: wanderbricks_demand_predictor
        model_version: 1
        workload_size: Small
```

---

## Feature Store Integration

### Feature Tables

| Feature Table | Entity | Features | Refresh |
|--------------|--------|----------|---------|
| property_features | property_id | 15 | Daily |
| user_features | user_id | 12 | Daily |
| engagement_features | property_id, date | 8 | Hourly |

### Feature Engineering Pipeline

```python
from databricks.feature_engineering import FeatureEngineeringClient

fe = FeatureEngineeringClient()

# Create feature table
fe.create_table(
    name=f"{catalog}.{gold_schema}.property_features",
    primary_keys=["property_id"],
    timestamp_keys=["feature_date"],
    features_df=property_features_df,
    description="Property-level features for ML models"
)
```

---

## Implementation Checklist

### Revenue Forecaster
- [ ] Create training pipeline
- [ ] Engineer features
- [ ] Train and validate model
- [ ] Register in MLflow
- [ ] Create serving endpoint
- [ ] Integrate with dashboards

### Demand Predictor
- [ ] Create training pipeline
- [ ] Engineer features
- [ ] Train and validate model
- [ ] Register in MLflow
- [ ] Create inference job

### Conversion Predictor
- [ ] Create training pipeline
- [ ] Engineer features
- [ ] Train and validate model
- [ ] Register in MLflow
- [ ] Integrate with marketing

### Pricing Optimizer
- [ ] Create optimization logic
- [ ] Train price elasticity model
- [ ] Validate recommendations
- [ ] Create daily batch job
- [ ] Build recommendation API

### Customer LTV Predictor
- [ ] Create training pipeline
- [ ] Engineer features
- [ ] Train and validate model
- [ ] Register in MLflow
- [ ] Integrate with segmentation

---

## Model Performance Targets

| Model | Metric | Target |
|-------|--------|--------|
| Revenue Forecaster | MAPE | <15% |
| Demand Predictor | RMSE | <3 bookings |
| Conversion Predictor | AUC-ROC | >0.75 |
| Pricing Optimizer | Revenue lift | >5% |
| Customer LTV | MAPE | <20% |

---

## References

- [MLflow Documentation](https://docs.databricks.com/mlflow/)
- [Feature Store](https://docs.databricks.com/machine-learning/feature-store/)
- [Model Serving](https://docs.databricks.com/machine-learning/model-serving/)

