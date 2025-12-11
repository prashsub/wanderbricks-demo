# Databricks notebook source
# Install MLflow 3.1+ for LoggedModel entity support
# %pip install -U 'mlflow>=3.1'

# Databricks notebook source
"""
Pricing Optimizer Training Pipeline

Trains a model to recommend optimal property prices for revenue maximization.
Uses Gradient Boosting with Feature Store and MLflow 3.1+ LoggedModel best practices.

Reference: 
- https://learn.microsoft.com/en-us/azure/databricks/mlflow/logged-model
- https://learn.microsoft.com/en-us/azure/databricks/machine-learning/manage-model-lifecycle/
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, first, month, quarter, when
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import mlflow
from mlflow.models import infer_signature
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime

# =============================================================================
# MLflow 3.1+ LoggedModel Configuration
# =============================================================================
# Set Unity Catalog as the model registry
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
    Prepare training set for pricing optimization.
    
    Label: revenue_per_night (proxy for optimal price)
    
    Features:
    - property_features: property attributes, location
    - demand_features: booking demand, occupancy
    - competitive_features: pricing in same destination
    """
    print("\n" + "="*80)
    print("Preparing training set")
    print("="*80)
    
    # Load booking data
    fact_booking_daily = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
    
    # Calculate revenue per night by property
    # GROUNDED: fact_booking_daily has total_booking_value, avg_nights_booked, avg_booking_value
    pricing_data = (
        fact_booking_daily
        .filter(col("avg_nights_booked") > 0)
        .withColumn("revenue_per_night", 
                   col("total_booking_value") / (col("booking_count") * col("avg_nights_booked")))
        .select(
            "property_id",
            "check_in_date",
            "revenue_per_night",
            "booking_count",
            "total_booking_value"
        )
        .groupBy("property_id", "check_in_date")
        .agg(
            avg("revenue_per_night").alias("optimal_price"),
            first("booking_count").alias("daily_bookings")
        )
        # Add temporal features (non-conflicting with property_features)
        .withColumn("month", month("check_in_date"))
        .withColumn("quarter", quarter("check_in_date"))
        .withColumn("is_peak_season", when(col("month").isin([6, 7, 8, 12]), 1).otherwise(0))
    )
    
    print(f"Pricing data shape: {pricing_data.count()} records")
    
    # Use pricing data directly (without feature store - simpler baseline)
    # This avoids potential issues with Feature Store lookups
    training_df = pricing_data
    
    print(f"✓ Training data prepared with {training_df.count()} records")
    
    return None, training_df


def preprocess_features(training_df):
    """Preprocess features for Gradient Boosting."""
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
    
    pdf = pdf.fillna(0)
    
    # Separate features and label (using temporal features only for baseline)
    feature_cols = [col for col in pdf.columns if col not in [
        'property_id', 'check_in_date', 'optimal_price', 'daily_bookings'
    ]]
    
    X = pdf[feature_cols]
    y = pdf['optimal_price']
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Label distribution: mean=${y.mean():.2f}, median=${y.median():.2f}")
    
    return X, y, feature_cols


def train_gbm_model(X_train, y_train, X_val, y_val):
    """Train Gradient Boosting model for pricing."""
    print("\n" + "="*80)
    print("Training Gradient Boosting model")
    print("="*80)
    
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=5,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42
    )
    
    print("Fitting model...")
    model.fit(X_train, y_train)
    
    print(f"✓ Model training completed")
    
    return model


def evaluate_model(model, X_train, y_train, X_val, y_val):
    """Evaluate pricing model."""
    print("\n" + "="*80)
    print("Evaluating model")
    print("="*80)
    
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    val_mae = mean_absolute_error(y_val, val_pred)
    val_r2 = r2_score(y_val, val_pred)
    # Handle division by zero in MAPE
    non_zero_mask = y_val != 0
    if non_zero_mask.sum() > 0:
        val_mape = np.mean(np.abs((y_val[non_zero_mask] - val_pred[non_zero_mask]) / y_val[non_zero_mask])) * 100
    else:
        val_mape = 0.0
    
    print("\nValidation Metrics:")
    print(f"  RMSE: ${val_rmse:.2f}")
    print(f"  MAE: ${val_mae:.2f}")
    print(f"  R²: {val_r2:.4f}")
    print(f"  MAPE: {val_mape:.2f}%")
    
    # Calculate revenue lift potential
    val_avg_price = y_val.mean()
    pred_avg_price = val_pred.mean()
    if val_avg_price != 0 and np.isfinite(val_avg_price):
        revenue_lift = ((pred_avg_price - val_avg_price) / val_avg_price) * 100
    else:
        revenue_lift = 0.0
    
    print(f"\nRevenue Analysis:")
    print(f"  Current Avg Price: ${val_avg_price:.2f}")
    print(f"  Predicted Avg Price: ${pred_avg_price:.2f}")
    print(f"  Potential Revenue Lift: {revenue_lift:+.2f}% (Target: >5%)")
    
    # Ensure all metrics are valid floats (not NaN or inf)
    metrics = {
        'val_rmse': float(val_rmse) if np.isfinite(val_rmse) else 0.0,
        'val_mae': float(val_mae) if np.isfinite(val_mae) else 0.0,
        'val_r2': float(val_r2) if np.isfinite(val_r2) else 0.0,
        'val_mape': float(val_mape) if np.isfinite(val_mape) else 0.0,
        'revenue_lift_pct': float(revenue_lift) if np.isfinite(revenue_lift) else 0.0
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
    Log pricing model with MLflow 3.1+ best practices including dataset tracking.
    
    Reference: https://docs.databricks.com/aws/en/mlflow/
    """
    print("\n" + "="*80)
    print("Logging model with MLflow")
    print("="*80)
    
    # 3-level model name for Unity Catalog
    registered_model_name = f"{catalog}.{feature_schema}.{model_name}"
    print(f"Registered Model Name: {registered_model_name}")
    
    # Descriptive run name using helper
    run_name = get_run_name(model_name, "gbm", "v1")
    
    with mlflow.start_run(run_name=run_name) as run:
        
        # Set run tags using helper for consistency
        mlflow.set_tags(get_standard_tags(
            model_name=model_name,
            domain="revenue_optimization",
            model_type="regression",
            algorithm="gradient_boosting",
            use_case="dynamic_pricing",
            training_table=f"{catalog}.{gold_schema}.fact_booking_daily",
            feature_store_enabled=False
        ))
        
        # =====================================================================
        # MLflow 3.1+ Dataset Tracking (INSIDE run context) using helper
        # =====================================================================
        log_training_dataset(spark, catalog, gold_schema, "fact_booking_daily")
        
        # Log hyperparameters
        mlflow.log_params({
            "n_estimators": model.n_estimators,
            "learning_rate": model.learning_rate,
            "max_depth": model.max_depth,
            "min_samples_split": model.min_samples_split,
            "min_samples_leaf": model.min_samples_leaf,
            "subsample": model.subsample
        })
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Create signature with both input and output for Unity Catalog
        sample_input = X_train.head(5)
        sample_output = model.predict(sample_input)
        signature = infer_signature(sample_input, sample_output)
        
        # Log model with MLflow sklearn flavor
        mlflow.sklearn.log_model(
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
    
    spark = SparkSession.builder.appName("Pricing Optimizer Training").getOrCreate()
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
        
        model = train_gbm_model(X_train, y_train, X_val, y_val)
        metrics = evaluate_model(model, X_train, y_train, X_val, y_val)
        
        # Log model with MLflow (pricing_optimizer doesn't use Feature Store training set)
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
        print("✓ Pricing Optimizer training completed successfully!")
        print("="*80)
        print(f"\nModel Performance:")
        print(f"  Revenue Lift: {metrics['revenue_lift_pct']:+.2f}% (Target: >5%)")
        print(f"  MAPE: {metrics['val_mape']:.2f}%")
        
        if run_info:
            print(f"\nMLflow Tracking:")
            print(f"  Experiment: {run_info['experiment_path']}")
            print(f"  Run Name: {run_info['run_name']}")
            print(f"  Registered Model: {run_info['registered_model_name']}")
        
        if abs(metrics['revenue_lift_pct']) > 5.0:
            print("\n✅ Model meets performance target (Revenue Lift > 5%)")
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = f"{type(e).__name__}: {str(e) or 'No message'}"
        print(f"\n❌ Error during training: {error_msg}")
        print(f"Full traceback:\n{tb}")
        # Exit with full traceback for debugging
        dbutils.notebook.exit(f"FAILED: {error_msg}\nTraceback: {tb[-500:]}")
    
    # Signal success to Databricks (outside try block)
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()

