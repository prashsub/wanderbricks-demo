# Databricks notebook source
# Install MLflow 3.1+ for LoggedModel entity support
# %pip install -U 'mlflow>=3.1'

# Databricks notebook source
"""
Customer LTV Predictor Training Pipeline

Trains a model to predict customer lifetime value (12-month forward revenue).
Uses XGBoost with Feature Store and MLflow 3.1+ LoggedModel best practices.

Reference: https://docs.databricks.com/aws/en/mlflow/logged-model
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import mlflow
from mlflow.models import infer_signature
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta

# =============================================================================
# MLflow 3.1+ LoggedModel Configuration
# =============================================================================
mlflow.set_registry_uri("databricks-uc")


# =============================================================================
# MLflow Setup Helpers (Inlined for serverless compatibility)
# =============================================================================
def setup_mlflow_experiment(model_name: str) -> str:
    """Set up MLflow experiment - uses experiment pre-created by Asset Bundle."""
    print("\n" + "="*80)
    print(f"Setting up MLflow Experiment: {model_name}")
    print("="*80)
    
    experiment_name = f"/Shared/wanderbricks_ml_{model_name}"
    
    try:
        experiment = mlflow.set_experiment(experiment_name)
        print(f"✓ Experiment set: {experiment_name}")
        print(f"  Experiment ID: {experiment.experiment_id}")
        return experiment_name
    except Exception as e:
        print(f"❌ Experiment setup failed: {e}")
        return None


def log_training_dataset(spark, catalog: str, schema: str, table_name: str) -> bool:
    """Log training dataset for MLflow lineage. Must be inside mlflow.start_run()."""
    full_table_name = f"{catalog}.{schema}.{table_name}"
    try:
        print(f"  Logging dataset: {full_table_name}")
        training_df = spark.table(full_table_name)
        dataset = mlflow.data.from_spark(df=training_df, table_name=full_table_name, version="latest")
        mlflow.log_input(dataset, context="training")
        print(f"✓ Dataset logged: {full_table_name}")
        return True
    except Exception as e:
        print(f"⚠️  Dataset logging: {e}")
        return False


def get_run_name(model_name: str, algorithm: str, version: str = "v1") -> str:
    """Generate descriptive run name."""
    return f"{model_name}_{algorithm}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_standard_tags(model_name: str, domain: str, model_type: str, algorithm: str,
                      use_case: str, training_table: str, feature_store_enabled: bool = False) -> dict:
    """Get standard MLflow run tags."""
    return {
        "project": "wanderbricks", "domain": domain, "model_name": model_name,
        "model_type": model_type, "algorithm": algorithm, "layer": "ml",
        "team": "data_science", "use_case": use_case,
        "feature_store_enabled": str(feature_store_enabled).lower(),
        "training_data": training_table
    }


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
    Prepare training set for LTV prediction.
    
    Label: 12-month forward revenue per customer
    """
    print("\n" + "="*80)
    print("Preparing training set")
    print("="*80)
    
    fact_booking = spark.table(f"{catalog}.{gold_schema}.fact_booking_detail")
    
    # Calculate 12-month forward revenue
    # Use cutoff date 12 months ago to have complete forward-looking data
    # GROUNDED: fact_booking_detail has created_at (timestamp), total_amount (revenue)
    cutoff_date = (datetime.now() - timedelta(days=365)).date()
    
    # Revenue in 12 months after cutoff
    future_revenue = (
        fact_booking
        .filter(col("created_at").cast("date") > lit(cutoff_date))
        .groupBy("user_id")
        .agg(sum("total_amount").alias("ltv_12m"))
    )
    
    # Users at cutoff date
    training_labels = (
        fact_booking
        .filter(col("created_at").cast("date") <= lit(cutoff_date))
        .select("user_id")
        .distinct()
        .join(future_revenue, "user_id", "left")
        .fillna(0, subset=["ltv_12m"])
    )
    
    print(f"Training labels: {training_labels.count()} users")
    
    # Define feature lookups
    # GROUNDED: Using actual feature table columns
    feature_lookups = [
        FeatureLookup(
            table_name=f"{catalog}.{feature_schema}.user_features",
            feature_names=[
                "country", "user_type", "is_business",
                "total_bookings", "total_spend", "avg_booking_value",
                "cancelled_bookings", "cancellation_rate",
                "days_since_last_booking", "avg_days_between_bookings",
                "tenure_days", "is_repeat"
            ],
            lookup_key="user_id"
        )
    ]
    
    training_set = fe.create_training_set(
        df=training_labels,
        feature_lookups=feature_lookups,
        label="ltv_12m"
    )
    
    training_df = training_set.load_df()
    
    print(f"✓ Training set created with {training_df.count()} records")
    
    return training_set, training_df


def preprocess_features(training_df):
    """Preprocess features for XGBoost."""
    print("\n" + "="*80)
    print("Preprocessing features")
    print("="*80)
    
    pdf = training_df.toPandas()
    
    # Convert Decimal columns to float (Spark DECIMAL -> Python decimal.Decimal)
    for col in pdf.select_dtypes(include=['object']).columns:
        try:
            pdf[col] = pdf[col].astype(float)
        except (ValueError, TypeError):
            pass  # Keep as-is if not numeric
    
    # Encode categorical
    categorical_cols = ['country', 'user_type']
    for col in categorical_cols:
        if col in pdf.columns:
            pdf[col] = pd.Categorical(pdf[col]).codes
    
    pdf = pdf.fillna(0)
    
    feature_cols = [col for col in pdf.columns if col not in [
        'user_id', 'ltv_12m', 'feature_timestamp', 'account_created_date',
        'last_booking_timestamp'
    ]]
    
    X = pdf[feature_cols]
    y = pdf['ltv_12m']
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Label distribution: mean=${y.mean():.2f}, median=${y.median():.2f}")
    
    return X, y, feature_cols


def train_xgboost_model(X_train, y_train, X_val, y_val):
    """Train XGBoost for LTV prediction."""
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
    
    return model


def evaluate_model(model, X_train, y_train, X_val, y_val):
    """Evaluate LTV model."""
    print("\n" + "="*80)
    print("Evaluating model")
    print("="*80)
    
    val_pred = model.predict(X_val)
    
    val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    val_mae = mean_absolute_error(y_val, val_pred)
    val_r2 = r2_score(y_val, val_pred)
    val_mape = np.mean(np.abs((y_val - val_pred) / (y_val + 1))) * 100  # +1 to avoid division by zero
    
    print("\nValidation Metrics:")
    print(f"  RMSE: ${val_rmse:.2f}")
    print(f"  MAE: ${val_mae:.2f}")
    print(f"  R²: {val_r2:.4f}")
    print(f"  MAPE: {val_mape:.2f}% (Target: <20%)")
    
    # Segment performance
    ltv_segments = pd.DataFrame({
        'actual': y_val,
        'predicted': val_pred
    })
    ltv_segments['segment'] = pd.cut(
        ltv_segments['actual'], 
        bins=[0, 500, 1000, 2500, np.inf],
        labels=['Low', 'Medium', 'High', 'VIP']
    )
    
    print("\nPerformance by LTV Segment:")
    for segment in ['Low', 'Medium', 'High', 'VIP']:
        seg_data = ltv_segments[ltv_segments['segment'] == segment]
        if len(seg_data) > 0:
            seg_mae = mean_absolute_error(seg_data['actual'], seg_data['predicted'])
            print(f"  {segment}: MAE=${seg_mae:.2f}, Count={len(seg_data)}")
    
    metrics = {
        'val_rmse': val_rmse,
        'val_mae': val_mae,
        'val_r2': val_r2,
        'val_mape': val_mape
    }
    
    return metrics


def log_model_with_mlflow(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    metrics: dict,
    model_name: str,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    experiment_path: str,
    spark
):
    """
    Log LTV model with MLflow 3.1+ best practices including dataset tracking.
    
    Reference: https://docs.databricks.com/aws/en/mlflow/
    """
    print("\n" + "="*80)
    print("Logging model with MLflow")
    print("="*80)
    
    # 3-level model name for Unity Catalog
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    print(f"Registered Model Name: {registered_model_name}")
    
    # Descriptive run name using helper
    run_name = get_run_name(model_name, "xgboost", "v1")
    
    with mlflow.start_run(run_name=run_name) as run:
        
        # Set run tags using helper for consistency
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="customer_analytics",
            model_type="regression",
            algorithm="xgboost",
            use_case="customer_lifetime_value_prediction",
            training_table=f"{catalog}.{gold_schema}.dim_user",
            feature_store_enabled=False
        ))
        
        # =====================================================================
        # MLflow 3.1+ Dataset Tracking (INSIDE run context) using helper
        # =====================================================================
        log_training_dataset(spark, catalog, gold_schema, "dim_user")
        
        # Log hyperparameters
        mlflow.log_params({
            "max_depth": model.max_depth,
            "learning_rate": model.learning_rate,
            "n_estimators": model.n_estimators,
            "subsample": model.subsample,
            "colsample_bytree": model.colsample_bytree,
            "objective": "reg:squarederror"
        })
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Create signature with both input and output for Unity Catalog
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # Log model with standard MLflow xgboost flavor
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
    
    spark = SparkSession.builder.appName("Customer LTV Training").getOrCreate()
    fe = FeatureEngineeringClient()
    mlflow.autolog(disable=True)
    
    # =========================================================================
    # MLflow Setup: Use model-specific experiment pre-created by Asset Bundle
    # =========================================================================
    experiment_path = setup_mlflow_experiment(model_name)
    
    try:
        training_set, training_df = prepare_training_set(
            spark, catalog, gold_schema, feature_schema, fe
        )
        
        X, y, feature_cols = preprocess_features(training_df)
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = train_xgboost_model(X_train, y_train, X_val, y_val)
        metrics = evaluate_model(model, X_train, y_train, X_val, y_val)
        
        # Log model with MLflow
        run_info = log_model_with_mlflow(
            model=model,
            X_train=X_train,
            y_train=y_train,
            metrics=metrics,
            model_name=model_name,
            catalog=catalog,
            gold_schema=gold_schema,
            feature_schema=feature_schema,
            experiment_path=experiment_path,
            spark=spark
        )
        
        print("\n" + "="*80)
        print("✓ Customer LTV Predictor training completed successfully!")
        print("="*80)
        print(f"\nModel Performance:")
        print(f"  MAPE: {metrics['val_mape']:.2f}% (Target: <20%)")
        print(f"  R²: {metrics['val_r2']:.4f}")
        
        if run_info:
            print(f"\nMLflow Tracking:")
            print(f"  Experiment: {run_info['experiment_path']}")
            print(f"  Run Name: {run_info['run_name']}")
            print(f"  Registered Model: {run_info['registered_model_name']}")
        
        if metrics['val_mape'] < 20.0:
            print("\n✅ Model meets performance target (MAPE < 20%)")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        dbutils.notebook.exit(f"FAILED: {str(e)}")
    
    # Signal success to Databricks (outside try block)
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()

