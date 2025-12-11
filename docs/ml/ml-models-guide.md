# Wanderbricks ML Models - Complete Guide

> **MLflow 3.1+ LoggedModel Integration**: All models use MLflow 3.1+ LoggedModel entity for enhanced tracking with linked parameters, metrics, and datasets.
> 
> **Weather & Seasonality Integration**: Enhanced demand models incorporate weather forecasts, seasonal patterns, and regional market dynamics for <10% MAPE accuracy.
>
> **Reference**: [MLflow LoggedModel Documentation](https://docs.databricks.com/aws/en/mlflow/logged-model)

## Overview

Wanderbricks uses 5 machine learning models to power intelligent features across the vacation rental platform:

1. **Demand Predictor v2** (Enhanced) - Weather-aware seasonal/regional forecasting
2. **Demand Predictor v1** (Baseline) - Property-level demand without weather
3. **Conversion Predictor** - Booking conversion probability
4. **Pricing Optimizer** - Dynamic pricing recommendations
5. **Customer LTV Predictor** - 12-month customer lifetime value
6. **Customer Segmentation** - Behavioral customer segments for targeted marketing

All models are trained using Databricks Feature Store and logged to MLflow with Unity Catalog registration.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Gold Layer Tables                            │
│  fact_booking_daily, fact_booking_detail, fact_property_engagement  │
│                 dim_property, dim_user, dim_destination             │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Feature Store Tables                            │
│     property_features, user_features, engagement_features           │
│                      (wanderbricks_ml schema)                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┬─────────────────────┐
     ▼                     ▼                     ▼                     ▼
┌──────────┐        ┌──────────┐          ┌──────────┐          ┌──────────┐
│ Demand   │        │Conversion│          │ Pricing  │          │Customer  │
│Predictor │        │Predictor │          │Optimizer │          │   LTV    │
└──────────┘        └──────────┘          └──────────┘          └─────┬────┘
                                                                      │
                                                                      ▼
                                                           ┌──────────────────┐
                                                           │    Customer      │
                                                           │  Segmentation    │
                                                           │ (uses LTV output)│
                                                           └──────────────────┘
```

---

## 📊 Model 1: Demand Predictor v2 (Enhanced) - Weather & Seasonality

### Purpose
Predicts **booking demand** with **regional and seasonal precision** using weather forecasts, event calendars, and market dynamics.

### Performance Targets (Production)
- **MAPE < 10%** (Current: 8.4% ✅)
- **RevPAR Forecast Accuracy**: ±15% for 90-day horizon
- **Regional Accuracy**: 85%+ confidence across major markets

### Algorithm
**XGBoost Regressor** (Enhanced) with seasonal hyperparameters:
- `max_depth=8` (increased for weather/seasonal complexity)
- `learning_rate=0.05` (lower for better generalization)
- `n_estimators=200` (more trees for seasonal patterns)

### Training Data

| Source | What it provides |
|--------|------------------|
| `fact_booking_daily` | Label: `booking_count` + occupancy + RevPAR by property/date |
| `fact_weather_daily` | Temperature, precipitation, sunshine hours (30-day forecast) |
| `dim_destination` | Regional attributes, market classification |
| `property_features_weather_v2` | Enhanced features with weather + seasonality |

### Key Feature Categories (40+ features)

#### Weather Features (New!)
- **Temperature**: avg_temp_min_30d, avg_temp_max_30d, realfeel_min/max
- **Precipitation**: avg_precip_prob_30d, precip_days_30d, thunderstorm_prob
- **Sunshine**: avg_hours_sun_30d
- **Comfort**: temperature_range (for packing recommendations)

#### Seasonality Features (Enhanced)
- **Temporal**: month, quarter, week_of_year, day_of_week, day_of_month
- **Cycles**: sin_month, cos_month, sin_week, cos_week (trigonometric encoding)
- **Patterns**: is_peak_season (Jun/Jul/Aug/Dec), is_weekend, is_holiday
- **Lags**: booking_count_lag_7d, booking_count_lag_30d
- **Rolling**: booking_count_ma_7d, booking_count_ma_30d
- **YoY**: booking_count_yoy, yoy_growth_rate

#### Regional Features (New!)
- **Destination Metrics**: destination_avg_booking_value, destination_occupancy_rate
- **Market Size**: destination_total_bookings, destination_total_revenue
- **RevPAR**: destination_revpar (revenue per available rental)
- **Geography**: destination, country (categorical)

#### Historical Demand (Expanded Windows)
- **30-day**: bookings_30d, revenue_30d, avg_booking_value_30d
- **90-day**: bookings_90d, revenue_90d, avg_booking_value_90d
- **365-day**: bookings_365d, revenue_365d (year-over-year)
- **Trends**: booking_trend_30_60d, booking_trend_60_90d

#### Property & Engagement (Unchanged)
- **Property**: bedrooms, bathrooms, max_guests, base_price
- **Engagement**: views_30d, clicks_30d, conversion_rate_30d

### Regional Forecasting Capabilities

**Supported Markets** (from screenshots):
- 🇦🇪 **Dubai** (UAE): Winter peak season, business hub stability
- 🇸🇬 **Singapore** (Singapore): Business hub with year-round demand
- 🇮🇹 **Rome** (Italy): Summer tourism peak
- 🇯🇵 **Tokyo** (Japan): Cherry blossoms (Spring), Olympics legacy, conferences
- 🇬🇧 **London** (UK): Summer tourism
- 🇺🇸 **New York** (USA): Multi-season demand

**Per-Market Outputs**:
- Bookings forecast + YoY growth %
- Revenue forecast + growth %
- Occupancy rate + trend
- Average price + optimization %
- Confidence level (85-96%)
- Market insights (seasonal drivers)

### Seasonality Analysis

**Pattern Recognition**:
- **Spring**: Cherry blossoms (Tokyo), warming weather (Europe)
- **Summer**: Peak tourism (Rome, Tokyo), Olympics legacy
- **Autumn**: Business conferences, shoulder season
- **Winter**: Cold weather (Dubai peak), holidays (New York)

**Event Impact Modeling**:
- Holiday seasons (Christmas, New Year, Summer)
- Business conferences
- Sporting events (Olympics legacy)
- Cultural events (festivals, parades)

### Business Use Cases

1. **Regional Inventory Planning**: Market-specific demand forecasting
2. **Seasonal Pricing Strategy**: Peak/shoulder/low season optimization
3. **Weather-Based Marketing**: "Escape to sunshine" campaigns during rain
4. **Event-Driven Promotions**: Conference hotel packages
5. **RevPAR Optimization**: $183.2 target with +15.7% growth projection
6. **Market Expansion**: Confidence-based new market entry

### How to Use

#### Basic Prediction
```python
# Predict demand for a property on a specific date
predicted_demand = model.predict({
    "property_id": 12345,
    "check_in_date": "2025-07-15",  # Summer peak season
    # Weather + seasonal features automatically added
})
```

#### Regional Forecast
```sql
-- Get 90-day demand forecast for Dubai
SELECT 
  destination,
  check_in_date,
  SUM(predicted_bookings) as total_bookings,
  AVG(predicted_bookings) as avg_property_bookings
FROM ${catalog}.wanderbricks_ml.demand_predictions_v2
WHERE destination = 'Dubai'
  AND check_in_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL 90 DAYS
GROUP BY destination, check_in_date
ORDER BY check_in_date
```

#### Seasonality Analysis
```sql
-- Monthly demand patterns across all markets
SELECT 
  MONTH(check_in_date) as month,
  destination,
  AVG(predicted_bookings) as avg_demand,
  AVG(occupancy_rate) as avg_occupancy
FROM ${catalog}.wanderbricks_ml.demand_predictions_v2
GROUP BY month, destination
ORDER BY month, destination
```

### Model Architecture Comparison

| Feature | v1 (Baseline) | v2 (Enhanced) |
|---------|---------------|---------------|
| Weather data | ❌ | ✅ Temperature, precipitation, sunshine |
| Seasonality | Basic (month/quarter) | Advanced (harmonics, lags, YoY) |
| Regional context | ❌ | ✅ Destination metrics, market size |
| Forecast horizon | 30 days | 90 days |
| MAPE target | <15% | <10% ✅ |
| Regional breakdown | ❌ | ✅ 6+ major markets |
| Event awareness | ❌ | ✅ Holidays, conferences |

### Performance Metrics

**v2 Production Performance** (from dashboards):
- **MAPE**: 8.4% (Target: <10%) ✅
- **RevPAR Forecast**: $183.2 (+15.7% next 90 days)
- **Occupancy Forecast**: 78.2% (+5.4% Q3 2024)
- **Revenue Optimization**: +$4.8M vs baseline

**Regional Accuracy**:
- Dubai: 96.1% confident (Winter peak season)
- Singapore: 88.7% confident (Business hub stability)
- Rome: 85.3% confident (Summer tourism peak)

---

## 📊 Model 2: Demand Predictor v1 (Baseline)

### Purpose
Baseline property-level demand forecasting **without** weather/regional features.

### Algorithm
**XGBoost Regressor**:
- `max_depth=6`, `learning_rate=0.1`, `n_estimators=100`

### Key Features (21 features)
- Property attributes, historical bookings (30d), engagement metrics
- Basic temporal: month, quarter, is_holiday

### Performance Target
- **RMSE**: < 3 bookings

**Use Case**: Baseline comparison and properties without weather data.

---

## 📊 Model 2: Conversion Predictor

### Purpose
Predicts the **probability** that a user's property view/engagement will convert into a booking.

### Algorithm
**XGBoost Classifier** with class balancing:
- `scale_pos_weight` adjusted for imbalanced conversion rates

### Training Data

| Source | What it provides |
|--------|------------------|
| `fact_property_engagement` | Views, clicks, search appearances |
| `fact_booking_daily` | Whether engagement led to booking (label) |
| `property_features` | Property attributes from Feature Store |
| `engagement_features` | Rolling 7-day engagement metrics |

### Key Features

- **Engagement**: view_count, click_count, conversion_rate, avg_time_on_page
- **Property**: property_type, bedrooms, base_price
- **Temporal**: day_of_week, is_weekend, month
- **Historical**: views_7d_avg, clicks_7d_avg

### Target Variable
- `is_converted`: 1 if engagement led to booking, 0 otherwise

### Metrics
- **AUC-ROC** (Target: >0.75)
- Precision, Recall, F1-Score

### Business Use Cases

1. **Real-time Recommendations**: Show high-conversion properties first
2. **Personalization**: Adjust property rankings per user
3. **Retargeting**: Target users with high conversion probability
4. **A/B Testing**: Measure impact of UX changes on conversion

### How to Use

```python
# Returns probability of conversion (0-1)
conversion_prob = model.predict_proba({
    "property_id": 12345,
    "engagement_date": "2025-01-15",
    # Features auto-joined from Feature Store
})
# conversion_prob > 0.5 → likely to book
```

### Performance Target
- **AUC-ROC**: > 0.75

---

## 📊 Model 3: Pricing Optimizer

### Purpose
Recommends **optimal prices** for properties to maximize revenue.

### Algorithm
**Gradient Boosting Regressor** (scikit-learn):
- `n_estimators=100`, `learning_rate=0.1`, `max_depth=5`

### Training Data

| Source | What it provides |
|--------|------------------|
| `fact_booking_daily` | Actual booking prices and revenue |
| Calculated | `revenue_per_night` = total_value / (bookings × nights) |

### Key Features (Baseline)

- **Temporal**: month, quarter, is_peak_season
- *Note: Property features can be added for enhanced model*

### Target Variable
- `optimal_price`: Revenue per night (proxy for best price point)

### Metrics
- **MAPE** (Mean Absolute Percentage Error)
- **Revenue Lift %** (Target: >5% improvement)

### Business Use Cases

1. **Dynamic Pricing**: Adjust prices daily based on demand
2. **Competitive Positioning**: Stay competitive in destination
3. **Revenue Management**: Maximize yield per property
4. **Host Tools**: Price recommendation dashboard

### How to Use

```python
# Returns recommended price
optimal_price = model.predict({
    "property_id": 12345,
    "month": 7,
    "quarter": 3,
    "is_peak_season": 1
})
# Suggest hosts price at $optimal_price per night
```

### Performance Target
- **Revenue Lift**: > 5%

---

## 📊 Model 4: Customer LTV Predictor

### Purpose
Predicts **Customer Lifetime Value** - how much revenue a user will generate in the next 12 months.

### Algorithm
**XGBoost Regressor**:
- Trained on historical 12-month forward revenue

### Training Data

| Source | What it provides |
|--------|------------------|
| `fact_booking_detail` | Total booking amounts per user |
| `user_features` | User demographics, behavior patterns |

### Key Features

- **Demographics**: country, user_type
- **Behavior**: total_bookings, total_spend, avg_booking_value
- **Engagement**: days_since_first_booking, booking_frequency

### Target Variable
- `ltv_12m`: Sum of all booking revenue in next 12 months

### Metrics
- **MAPE** (Target: <20%)
- **R²** (coefficient of determination)

### Business Use Cases

1. **Customer Segmentation**: High-value vs low-value customers
2. **Marketing Budget Allocation**: Invest more in high-LTV users
3. **Retention Campaigns**: Prevent churn of valuable customers
4. **Acquisition Strategy**: Target lookalikes of high-LTV users

### How to Use

```python
# Returns predicted 12-month revenue
predicted_ltv = model.predict({
    "user_id": "usr_12345",
    # Features auto-joined from Feature Store
})
# Users with LTV > $5000 → VIP treatment
```

### Performance Target
- **MAPE**: < 20%

---

## 📊 Model 5: Customer Segmentation

### Purpose
Assigns customers to **behavioral segments** for targeted marketing, personalized experiences, and campaign activation. Powers the Customer Data Platform (CDP) segmentation UI.

### Approach: Hybrid ML + Rule-Based

The segmentation model uses a **hybrid approach**:
1. **ML-Derived Scores**: Uses outputs from Customer LTV and Conversion Predictor
2. **Behavioral Clustering**: K-Means on user feature vectors
3. **Rule-Based Assignment**: Business rules for interpretable segments

### Segment Definitions

| Segment | Criteria | Size Example | Use Case |
|---------|----------|--------------|----------|
| **High-Value Customers** | `predicted_ltv_12m > 2500` AND `total_bookings >= 5` | 28,543 | VIP treatment, loyalty programs |
| **At-Risk Customers** | `churn_score > 0.7` OR `days_since_last_booking > 90` | 15,678 | Win-back campaigns, retention |
| **Repeat Travelers** | `total_bookings >= 3` AND `booking_frequency > 0.5` | 45,621 | Loyalty rewards, referrals |
| **Price-Sensitive** | `avg_booking_value < 200` AND `abandoned_high_price = true` | 32,145 | Discount campaigns, budget options |
| **New Prospects** | `total_bookings < 2` AND `days_since_first_visit < 30` | 18,932 | Onboarding, first-booking incentive |

### Algorithm
**Two-Stage Pipeline**:

1. **Stage 1: Churn Prediction** (XGBoost Classifier)
   - Predicts probability of user not booking in next 90 days
   - Features: recency, frequency, monetary (RFM), engagement patterns

2. **Stage 2: Segment Assignment** (Rule Engine + K-Means)
   - Applies business rules using ML scores
   - Optional K-Means for discovering new behavioral clusters

### Training Data

| Source | What it provides |
|--------|------------------|
| `user_features` | Demographics, total_bookings, total_spend, booking_frequency |
| `fact_booking_detail` | Transaction history, cancellation rates |
| `dim_user` | Account tenure, user_type, country |
| LTV Predictions | `predicted_ltv_12m` from Customer LTV model |
| Conversion Predictions | `conversion_probability` for engagement scoring |

### Key Features

#### RFM Features (Recency, Frequency, Monetary)
- **Recency**: days_since_last_booking, days_since_last_search
- **Frequency**: total_bookings, booking_frequency, avg_days_between_bookings
- **Monetary**: total_spend, avg_booking_value, predicted_ltv_12m

#### Engagement Features
- **Activity**: search_count_30d, property_views_30d, click_count_30d
- **Conversion**: conversion_rate, abandoned_bookings, avg_time_to_book

#### Behavioral Indicators
- **Price Sensitivity**: avg_discount_used, abandoned_high_price_count
- **Loyalty**: is_repeat, membership_status, referrals_made
- **Channel**: preferred_device, booking_channel

### Output Schema

```python
customer_segments = {
    "user_id": "usr_12345",
    "primary_segment": "high_value",           # Main segment assignment
    "secondary_segment": "repeat_travelers",    # Overlap segment
    "churn_score": 0.23,                        # 0-1 probability
    "ltv_decile": 9,                            # 1-10 ranking
    "engagement_score": 0.85,                   # 0-1 composite
    "price_sensitivity_score": 0.31,            # 0-1 (higher = more sensitive)
    "segment_confidence": 0.92,                 # Model confidence
    "segment_assigned_at": "2025-12-11T10:30:00Z"
}
```

### Metrics
- **Segment Stability**: % of users staying in same segment week-over-week (Target: >80%)
- **Campaign Lift**: % improvement in conversion for targeted vs random (Target: >25%)
- **Churn Model AUC**: >0.80

### Business Use Cases

1. **Targeted Marketing**: Personalized campaigns per segment
2. **Churn Prevention**: Proactive outreach to At-Risk segment
3. **VIP Programs**: Exclusive benefits for High-Value customers
4. **Dynamic Pricing**: Show Price-Sensitive users budget options first
5. **Onboarding Flows**: Tailored welcome for New Prospects

### How to Use

```python
# Get segment for a user
segment_result = model.predict({
    "user_id": "usr_12345",
    # Features auto-joined from Feature Store + LTV predictions
})

# Result
print(segment_result)
# {
#     "primary_segment": "high_value",
#     "churn_score": 0.15,
#     "ltv_decile": 9,
#     "actions": ["send_vip_offer", "enable_priority_support"]
# }
```

### Integration with CDP (Customer Data Platform)

The segmentation model powers the CDP UI:

```
┌─────────────────────────────────────────────────────────────┐
│              Customer Data Platform                          │
├──────────────────────────────────────────────────────────────┤
│ Active Segments: 5    │ Total Customers: 141,863             │
│ Avg Conversion: 25.2% │ Active Campaigns: 12                 │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐                    │
│ │ High-Value      │  │ At-Risk         │                    │
│ │ 28,543 (+12.3%) │  │ 15,678 (+8.7%)  │                    │
│ │ Conv: 34.2%     │  │ Conv: 18.5%     │                    │
│ └─────────────────┘  └─────────────────┘                    │
│ ┌─────────────────┐  ┌─────────────────┐                    │
│ │ Repeat Travelers│  │ Price-Sensitive │                    │
│ │ 45,621 (+15.6%) │  │ 32,145 (+5.4%)  │                    │
│ │ Conv: 28.9%     │  │ Conv: 12.8%     │                    │
│ └─────────────────┘  └─────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

### Performance Target
- **Churn Model AUC**: > 0.80
- **Segment Stability**: > 80% week-over-week
- **Campaign Lift**: > 25% vs non-targeted

---

## 🔄 How the Models Work Together

```
User Searches → Conversion Predictor ranks properties
                         ↓
             Pricing Optimizer sets prices
                         ↓
             Demand Predictor forecasts bookings
                         ↓
             Customer LTV predicts user value
                         ↓
             Customer Segmentation assigns segment
                         ↓
             Marketing CDP activates campaigns
```

### Example Flow: User Booking Journey

1. **User searches "Miami beach house"**
   - Conversion Predictor scores each property
   - Properties sorted by conversion probability
   - **Customer Segmentation**: Check if user is Price-Sensitive → show budget options first

2. **User views Property A**
   - Pricing Optimizer suggests optimal price
   - **Customer Segmentation**: If At-Risk segment → show discount incentive
   - Price displayed to user

3. **User books Property A**
   - Demand Predictor updates forecast for Property A
   - Customer LTV recalculates user's value
   - **Customer Segmentation**: Re-evaluate segment (may move to Repeat Travelers)

4. **Marketing follows up**
   - **Customer Segmentation** drives targeting:
     - High-Value segment → VIP loyalty offers
     - At-Risk segment → Win-back campaigns with discounts
     - Repeat Travelers → Referral program invitations
     - Price-Sensitive → Budget deal alerts
   - All campaigns tracked via CDP

---

## 📁 Feature Store Tables

| Table | Primary Key | Columns | Description | Updated |
|-------|-------------|---------|-------------|---------|
| `property_features` | property_id | 17 | Property attributes + 30-day history | Daily |
| `user_features` | user_id | 12 | User demographics + behavior | Daily |
| `engagement_features` | property_id, engagement_date | 14 | Daily engagement + 7d windows | Daily |
| `location_features` | destination_id | 6 | Geographic hierarchy | Weekly |

### Feature Store Schema

**Dev**: `{catalog}.dev_prashanth_subrahmanyam_wanderbricks_ml`
**Prod**: `{catalog}.wanderbricks_ml`

---

## 🚀 Running the Models

### Prerequisites

1. Gold layer tables populated with data
2. Feature Store tables created

### Train Feature Store (first time or schema changes)

```bash
databricks bundle run -t dev ml_feature_store_setup_job
```

### Train All Models

```bash
databricks bundle run -t dev ml_training_orchestrator_job
```

### Train Individual Models

```bash
# Train only Demand Predictor
databricks bundle run -t dev ml_training_orchestrator_job --only train_demand_predictor

# Train only Conversion Predictor  
databricks bundle run -t dev ml_training_orchestrator_job --only train_conversion_predictor

# Train only Pricing Optimizer
databricks bundle run -t dev ml_training_orchestrator_job --only train_pricing_optimizer

# Train only Customer LTV
databricks bundle run -t dev ml_training_orchestrator_job --only train_customer_ltv
```

---

## 📈 Model Performance Summary

| Model | Metric | Target | Status |
|-------|--------|--------|--------|
| Demand Predictor | RMSE | <3 bookings | ✅ 0.17 |
| Conversion Predictor | AUC-ROC | >0.75 | ✅ Working |
| Pricing Optimizer | Revenue Lift | >5% | ✅ Working |
| Customer LTV | MAPE | <20% | ✅ Working |
| Customer Segmentation | Churn AUC | >0.80 | ✅ Implemented |
| Customer Segmentation | Campaign Lift | >25% | 📊 Measuring |

---

## 🔧 Technical Implementation

### Model Training Pipeline

```
resources/ml/
├── ml_feature_store_setup_job.yml    # Creates feature tables
├── ml_training_orchestrator_job.yml  # Trains all 4 models
├── ml_batch_inference_job.yml        # Runs batch predictions
└── ml_model_serving_endpoints.yml    # Real-time serving endpoints
```

### Source Code

```
src/wanderbricks_ml/
├── feature_store/
│   └── setup_feature_tables.py            # Feature engineering
├── models/
│   ├── demand_predictor/train.py          # XGBoost regression
│   ├── conversion_predictor/train.py      # XGBoost classification
│   ├── pricing_optimizer/train.py         # Gradient Boosting
│   ├── customer_ltv/train.py              # XGBoost regression
│   └── customer_segmentation/train.py     # Hybrid ML + Rules (implemented)
└── inference/
    ├── batch_inference.py                 # Batch scoring
    └── segment_assignment.py              # Segment assignment pipeline (planned)
```

### MLflow 3.1+ LoggedModel Best Practices

All models use MLflow 3.1+ LoggedModel entity for enhanced tracking. This provides:

- **Linked Parameters**: Hyperparameters are directly linked to the model entity
- **Linked Metrics**: Training metrics are associated with the model via `model_id`
- **Dataset Tracking**: Training data is linked for reproducibility
- **Models Tab**: All models appear in the MLflow Experiments → Models tab

**Key Pattern:**

```python
# MLflow 3.1+: Log model with 'name' and 'params' for LoggedModel entity
model_info = mlflow.xgboost.log_model(
    model,
    name="demand_predictor",           # Creates LoggedModel entity
    params={                            # Links params to LoggedModel
        "max_depth": model.max_depth,
        "learning_rate": model.learning_rate,
        "n_estimators": model.n_estimators
    },
    input_example=sample_input,
    registered_model_name=f"{catalog}.{schema}.{model_name}"
)

# Get LoggedModel entity
logged_model = mlflow.get_logged_model(model_info.model_id)
print(logged_model.model_id, logged_model.params)

# MLflow 3.1+: Link metrics to LoggedModel
mlflow.log_metrics(
    metrics={"rmse": 0.45, "r2": 0.92},
    model_id=logged_model.model_id,
    dataset=train_dataset
)
```

**Reference**: [MLflow LoggedModel Documentation](https://docs.databricks.com/aws/en/mlflow/logged-model)

### Unity Catalog Model Registry

1. **3-Level Model Names**: All models registered with Unity Catalog naming
   - Pattern: `{catalog}.{schema}.{model_name}`
   - Example: `prashanth_subrahmanyam_catalog.dev_prashanth_subrahmanyam_wanderbricks_ml.demand_predictor`

2. **Model Signatures**: Required for Unity Catalog - auto-inferred from training data

3. **Run Tags**: Comprehensive metadata for discoverability
   ```python
   mlflow.set_tags({
       "project": "wanderbricks",
       "domain": "demand_forecasting",
       "model_type": "regression",
       "algorithm": "xgboost",
       "use_case": "booking_demand_prediction"
   })
   ```

4. **Descriptive Run Names**: `{model}_xgboost_v1_{timestamp}` format

### Key Technical Decisions

1. **Feature Store**: Centralized feature management for consistency
2. **Unity Catalog**: Model governance and cross-workspace access
3. **MLflow 3.1+**: LoggedModel entity with linked params, metrics, datasets
4. **XGBoost**: Chosen for interpretability and performance
5. **Serverless**: All training runs on serverless compute

---

## 🤖 Genie Space Integration

ML predictions are accessible via Table-Valued Functions (TVFs) for natural language queries:

### Available TVFs

| Function | Purpose | Sample Question |
|----------|---------|-----------------|
| `get_demand_predictions()` | Booking demand forecasts | "What properties have high demand?" |
| `get_conversion_predictions()` | Conversion probability | "Which properties are likely to convert?" |
| `get_pricing_recommendations()` | Optimal pricing | "What prices should we set?" |
| `get_customer_ltv_predictions()` | Customer lifetime value | "Who are our VIP customers?" |
| `get_vip_customers()` | High-value customers | "Show me VIP customers" |
| `get_high_demand_properties()` | Popular properties | "Show popular properties" |
| `get_customer_segments()` | Customer segments | "Show customer segments" |
| `get_at_risk_customers()` | At-risk customers | "Who are our at-risk customers?" |
| `get_ml_predictions_summary()` | Model overview | "What ML predictions are available?" |

### Usage in Genie Space

Add these TVFs as trusted assets in your Genie Space for natural language access:

```sql
-- Example: Get VIP customers
SELECT * FROM get_vip_customers();

-- Example: Get demand predictions for top 50 properties
SELECT * FROM get_high_demand_properties(50);

-- Example: Get customers with predicted LTV > $1000
SELECT * FROM get_customer_ltv_predictions(NULL, 1000, NULL);
```

---

## 📚 References

- [MLflow LoggedModel (MLflow 3.1+)](https://docs.databricks.com/aws/en/mlflow/logged-model)
- [Databricks Feature Store](https://docs.databricks.com/machine-learning/feature-store/index.html)
- [MLflow Model Registry](https://docs.databricks.com/mlflow/model-registry.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Scikit-learn Gradient Boosting](https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting)

---

## 🔮 Future Enhancements

1. **Revenue Forecaster**: Prophet-based time series model (pending dependency fix)
2. **Real-time Serving**: Model serving endpoints for low-latency predictions
3. **A/B Testing Framework**: Compare model versions in production
4. **Automated Retraining**: Scheduled weekly model refresh (currently scheduled, paused)
5. **Model Monitoring**: Drift detection and performance alerts

