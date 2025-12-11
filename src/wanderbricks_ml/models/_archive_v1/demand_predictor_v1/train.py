# Databricks notebook source
# Install MLflow 3.1+ for LoggedModel entity support
# %pip install -U 'mlflow>=3.1'

# Databricks notebook source
"""
Demand Predictor Training Pipeline

Trains an XGBoost model to predict booking demand by property/destination.
Uses Feature Store and MLflow 3.1+ LoggedModel best practices with Unity Catalog.

Reference: 
- https://learn.microsoft.com/en-us/azure/databricks/mlflow/logged-model
- https://learn.microsoft.com/en-us/azure/databricks/machine-learning/manage-model-lifecycle/
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import mlflow
from mlflow.models import infer_signature
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta

# =============================================================================
# MLflow 3.1+ LoggedModel Configuration
# =============================================================================
# Set Unity Catalog as the model registry
mlflow.set_registry_uri("databricks-uc")


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    feature_schema = dbutils.widgets.get("feature_schema")
    model_name = dbutils.widgets.get("model_name")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Feature Schema: {feature_schema}")
    print(f"Model Name: {model_name}")
    
    return catalog, gold_schema, feature_schema, model_name


def prepare_training_set(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    fe: FeatureEngineeringClient
):
    """
    Prepare training set using Feature Store.
    
    Features from Feature Store:
    - property_features: property attributes, historical bookings
    - engagement_features: view/click metrics
    
    Label: booking_count (from fact_booking_daily)
    """
    print("\n" + "="*80)
    print("Preparing training set with Feature Store")
    print("="*80)
    
    # Load label data (booking demand)
    fact_booking_daily = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
    
    # Use daily aggregated data directly
    # GROUNDED: fact_booking_daily already has booking_count, total_booking_value, avg_nights_booked
    # NOTE: Don't add day_of_week, is_weekend here - they come from engagement_features to avoid conflicts
    training_labels = (
        fact_booking_daily
        .select(
            "property_id",
            "check_in_date",
            "booking_count",
            "total_booking_value",
            "avg_nights_booked"
        )
        .withColumn("month", month("check_in_date"))
        .withColumn("quarter", quarter("check_in_date"))
        .withColumn("is_holiday", lit(0))  # Simplified - could add holiday calendar
    )
    
    print(f"Training labels shape: {training_labels.count()} records")
    
    # Define feature lookups from Feature Store
    # GROUNDED: Using actual feature table columns
    # NOTE: Only using property_features - engagement features require engagement_date which we don't have
    feature_lookups = [
        FeatureLookup(
            table_name=f"{catalog}.{feature_schema}.property_features",
            feature_names=[
                "property_type", "bedrooms", "bathrooms", "max_guests", "base_price",
                "destination_id", "host_id", "property_latitude", "property_longitude",
                "bookings_30d", "revenue_30d", "avg_booking_value_30d", "avg_nights_30d",
                "views_30d", "clicks_30d", "avg_conversion_rate_30d",
                "revenue_per_booking", "click_through_rate"
            ],
            lookup_key="property_id"
        )
    ]
    
    # Create training set with automatic feature joins
    training_set = fe.create_training_set(
        df=training_labels,
        feature_lookups=feature_lookups,
        label="booking_count",
        exclude_columns=["total_booking_value", "avg_nights_booked"]
    )
    
    # Load training data
    training_df = training_set.load_df()
    
    print(f"✓ Training set created with {training_df.count()} records")
    print(f"  Features: {len(training_df.columns)}")
    
    return training_set, training_df


def preprocess_features(training_df):
    """
    Preprocess features for XGBoost.
    
    Steps:
    - Convert categorical features to numeric
    - Handle missing values
    - Create feature matrix
    """
    print("\n" + "="*80)
    print("Preprocessing features")
    print("="*80)
    
    # Convert to Pandas
    pdf = training_df.toPandas()
    
    print(f"Raw data shape: {pdf.shape}")
    
    # Convert Decimal columns to float (Spark DECIMAL -> Python decimal.Decimal)
    for col in pdf.select_dtypes(include=['object']).columns:
        try:
            pdf[col] = pd.to_numeric(pdf[col], errors='coerce')
        except (ValueError, TypeError):
            pass  # Keep as-is if not numeric
    
    # Encode categorical features
    # GROUNDED: property_type from property_features (destination_id is numeric FK)
    categorical_cols = ['property_type']
    for col in categorical_cols:
        if col in pdf.columns:
            pdf[col] = pd.Categorical(pdf[col]).codes
    
    # Handle missing values
    pdf = pdf.fillna(0)
    
    # Separate features and label
    feature_cols = [col for col in pdf.columns if col not in [
        'property_id', 'check_in_date', 'booking_count',
        'feature_timestamp', 'engagement_date'
    ]]
    
    X = pdf[feature_cols]
    y = pdf['booking_count']
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Feature columns: {list(X.columns)}")
    print(f"Label distribution:")
    print(y.describe())
    
    return X, y, feature_cols


def train_xgboost_model(X_train, y_train, X_val, y_val):
    """
    Train XGBoost regression model.
    
    Hyperparameters optimized for demand prediction:
    - max_depth: 6 (moderate complexity)
    - learning_rate: 0.1
    - n_estimators: 100
    - objective: reg:squarederror
    """
    print("\n" + "="*80)
    print("Training XGBoost model")
    print("="*80)
    
    model = XGBRegressor(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        objective='reg:squarederror',
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    print("Fitting model...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10,
        verbose=False
    )
    
    print(f"✓ Model training completed")
    print(f"  Best iteration: {model.best_iteration}")
    
    return model


def evaluate_model(model, X_train, y_train, X_val, y_val):
    """
    Evaluate model performance.
    
    Metrics:
    - RMSE (Root Mean Squared Error)
    - MAE (Mean Absolute Error)
    - R² Score
    - Cross-validation score
    """
    print("\n" + "="*80)
    print("Evaluating model")
    print("="*80)
    
    # Training predictions
    train_pred = model.predict(X_train)
    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    train_mae = mean_absolute_error(y_train, train_pred)
    train_r2 = r2_score(y_train, train_pred)
    
    # Validation predictions
    val_pred = model.predict(X_val)
    val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    val_mae = mean_absolute_error(y_val, val_pred)
    val_r2 = r2_score(y_val, val_pred)
    
    print("\nTraining Metrics:")
    print(f"  RMSE: {train_rmse:.4f}")
    print(f"  MAE: {train_mae:.4f}")
    print(f"  R²: {train_r2:.4f}")
    
    print("\nValidation Metrics:")
    print(f"  RMSE: {val_rmse:.4f} (Target: <3 bookings)")
    print(f"  MAE: {val_mae:.4f}")
    print(f"  R²: {val_r2:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))
    
    metrics = {
        'train_rmse': train_rmse,
        'train_mae': train_mae,
        'train_r2': train_r2,
        'val_rmse': val_rmse,
        'val_mae': val_mae,
        'val_r2': val_r2
    }
    
    return metrics, feature_importance


def log_model_with_mlflow(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    feature_cols: list,
    metrics: dict,
    feature_importance: pd.DataFrame,
    model_name: str,
    catalog: str,
    feature_schema: str
):
    """
    Log model with standard MLflow.
    
    Using standard MLflow logging ensures signature matches actual training features.
    """
    print("\n" + "="*80)
    print("Logging model with MLflow")
    print("="*80)
    
    # Set experiment with descriptive path
    try:
        experiment_path = f"/Workspace/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/{model_name}"
        experiment = mlflow.get_experiment_by_name(experiment_path)
        if experiment is None:
            mlflow.create_experiment(experiment_path)
        mlflow.set_experiment(experiment_path)
        print(f"Experiment: {experiment_path}")
    except Exception as e:
        print(f"Warning: Could not create experiment {experiment_path}: {e}")
        print("Using default notebook experiment")
        experiment_path = "default"
    
    # 3-level model name for Unity Catalog
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    print(f"Registered Model Name: {registered_model_name}")
    
    # Descriptive run name
    run_name = f"demand_predictor_xgboost_v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        
        # Set run tags for organization and discoverability
        mlflow.set_tags({
            "project": "wanderbricks",
            "domain": "demand_forecasting",
            "model_type": "regression",
            "algorithm": "xgboost",
            "layer": "ml",
            "team": "data_science",
            "use_case": "booking_demand_prediction"
        })
        
        # Log hyperparameters
        mlflow.log_params({
            "max_depth": model.max_depth,
            "learning_rate": model.learning_rate,
            "n_estimators": model.n_estimators,
            "subsample": model.subsample,
            "colsample_bytree": model.colsample_bytree,
            "num_features": len(feature_cols),
            "objective": "reg:squarederror"
        })
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Log feature importance as artifact
        feature_importance_path = "feature_importance.csv"
        feature_importance.to_csv(feature_importance_path, index=False)
        mlflow.log_artifact(feature_importance_path)
        
        # Create signature from actual training data
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # Log model with standard MLflow
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            signature=signature,
            input_example=sample_input,
            registered_model_name=registered_model_name
        )
        
        run_id = run.info.run_id
        model_uri = f"runs:/{run_id}/model"
        
        print(f"\n✓ Model logged with MLflow")
        print(f"  Run ID: {run_id}")
        print(f"  Run Name: {run_name}")
        print(f"  Model URI: {model_uri}")
        print(f"  Registered Model: {registered_model_name}")
        print(f"  Experiment: {experiment_path}")
        
        return {
            "run_id": run_id,
            "run_name": run_name,
            "model_uri": model_uri,
            "registered_model_name": registered_model_name,
            "experiment_path": experiment_path
        }


def main():
    """Main training pipeline."""
    
    catalog, gold_schema, feature_schema, model_name = get_parameters()
    
    spark = SparkSession.builder.appName("Demand Predictor Training").getOrCreate()
    
    # Initialize Feature Engineering Client
    fe = FeatureEngineeringClient()
    
    # Disable autologging (causes "None" errors in serverless)
    mlflow.autolog(disable=True)
    
    try:
        # Prepare training set with Feature Store
        training_set, training_df = prepare_training_set(
            spark, catalog, gold_schema, feature_schema, fe
        )
        
        # Preprocess features
        X, y, feature_cols = preprocess_features(training_df)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"\nTrain set: {X_train.shape}")
        print(f"Validation set: {X_val.shape}")
        
        # Train model
        model = train_xgboost_model(X_train, y_train, X_val, y_val)
        
        # Evaluate model
        metrics, feature_importance = evaluate_model(
            model, X_train, y_train, X_val, y_val
        )
        
        # Log model with MLflow
        run_info = log_model_with_mlflow(
            model=model,
            X_train=X_train,
            y_train=y_train,
            feature_cols=feature_cols,
            metrics=metrics,
            feature_importance=feature_importance,
            model_name=model_name,
            catalog=catalog,
            feature_schema=feature_schema
        )
        
        print("\n" + "="*80)
        print("✓ Demand Predictor training completed successfully!")
        print("="*80)
        print(f"\nModel Performance:")
        print(f"  Validation RMSE: {metrics['val_rmse']:.4f} (Target: <3)")
        print(f"  Validation R²: {metrics['val_r2']:.4f}")
        
        if run_info:
            print(f"\nMLflow Tracking:")
            print(f"  Experiment: {run_info['experiment_path']}")
            print(f"  Run Name: {run_info['run_name']}")
            print(f"  Registered Model: {run_info['registered_model_name']}")
        
        if metrics['val_rmse'] < 3.0:
            print("\n✅ Model meets performance target (RMSE < 3)")
        else:
            print("\n⚠️  Model does not meet performance target (RMSE >= 3)")
            print("   Consider: More training data, feature engineering, hyperparameter tuning")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        dbutils.notebook.exit(f"FAILED: {str(e)}")
    
    # Signal success to Databricks (outside try block)
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()

