# Wanderbricks ML Documentation

## Overview

This folder contains documentation for the Wanderbricks ML platform, which provides intelligent features powered by machine learning models.

---

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [ml-models-guide.md](ml-models-guide.md) | **Complete guide** to all ML models, features, and usage |
| [../ML_DEPLOYMENT_STATUS.md](../ML_DEPLOYMENT_STATUS.md) | Current deployment status and commands |

---

## 🎯 Quick Start

### 1. Deploy ML Infrastructure

```bash
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle deploy -t dev
```

### 2. Setup Feature Store

```bash
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run -t dev ml_feature_store_setup_job
```

### 3. Train All Models

```bash
DATABRICKS_CONFIG_PROFILE=wanderbricks databricks bundle run -t dev ml_training_orchestrator_job
```

---

## 📊 Model Summary

| Model | Purpose | Algorithm | Status |
|-------|---------|-----------|--------|
| **Demand Predictor** | Forecast booking demand per property | XGBoost Regressor | ✅ Training |
| **Conversion Predictor** | Predict booking conversion probability | XGBoost Classifier | ✅ Training |
| **Pricing Optimizer** | Recommend optimal property prices | Gradient Boosting | ✅ Training |
| **Customer LTV** | Predict 12-month customer lifetime value | XGBoost Regressor | ✅ Training |
| **Revenue Forecaster** | Time series revenue forecasting | Prophet | ⚠️ Pending |

---

## 🏗️ Architecture

```
Gold Layer Tables
       │
       ▼
Feature Store Tables
       │
       ├── Demand Predictor
       ├── Conversion Predictor
       ├── Pricing Optimizer
       └── Customer LTV
```

---

## 📁 Source Code

```
src/wanderbricks_ml/
├── feature_store/
│   └── setup_feature_tables.py
├── models/
│   ├── demand_predictor/train.py
│   ├── conversion_predictor/train.py
│   ├── pricing_optimizer/train.py
│   ├── customer_ltv/train.py
│   └── revenue_forecaster/train.py
└── README.md
```

---

## 🔗 Related Resources

- **Plan:** [phase4-addendum-4.1-ml-models.md](../../plans/phase4-addendum-4.1-ml-models.md)
- **Asset Bundles:** [resources/ml/](../../resources/ml/)
- **Feature Store:** [src/wanderbricks_ml/feature_store/](../../src/wanderbricks_ml/feature_store/)

