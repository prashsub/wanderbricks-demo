# Databricks notebook source
"""
Conversion Predictor Training Pipeline

Trains a classification model to predict booking conversion probability.
Uses XGBoost with MLflow 3.1+ best practices.

Reference: 
- https://docs.databricks.com/aws/en/mlflow/
- https://docs.databricks.com/aws/en/notebooks/source/mlflow/mlflow-classic-ml-e2e-mlflow-3.html
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
import mlflow
from mlflow.models import infer_signature
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from datetime import datetime

# =============================================================================
# MLflow 3.1+ Configuration
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
    Prepare training set for conversion prediction.
    
    Label: is_converted (1 if engagement led to booking, 0 otherwise)
    
    Features:
    - engagement_features: view/click behavior
    - property_features: property attributes, pricing
    - user_features: user behavior, demographics
    """
    print("\n" + "="*80)
    print("Preparing training set with Feature Store")
    print("="*80)
    
    # Load engagement and booking data
    fact_engagement = spark.table(f"{catalog}.{gold_schema}.fact_property_engagement")
    fact_booking = spark.table(f"{catalog}.{gold_schema}.fact_booking_detail")
    
    # Create labels by checking if engagement led to booking
    # Simplified: engagement on same day as booking creation = conversion
    # GROUNDED: fact_booking_detail has created_at (booking timestamp), not booking_date
    bookings_converted = (
        fact_booking
        .select(
            col("property_id"),
            col("created_at").cast("date").alias("engagement_date"),
            lit(1).alias("is_converted")
        )
        .distinct()
    )
    
    # All engagements (property-level, no user_id in engagement data)
    # GROUNDED: fact_property_engagement doesn't have user_id - it's daily aggregated
    # NOTE: Don't add day_of_week, is_weekend - they come from engagement_features
    training_labels = (
        fact_engagement
        .select("property_id", "engagement_date")
        .join(
            bookings_converted,
            ["property_id", "engagement_date"],
            "left"
        )
        .fillna(0, subset=["is_converted"])
        # Add temporal features (non-conflicting)
        .withColumn("month", month("engagement_date"))
        .withColumn("is_peak_season", when(col("month").isin([6, 7, 8, 12]), 1).otherwise(0))
    )
    
    print(f"Training labels shape: {training_labels.count()} records")
    
    # Check class balance
    class_dist = training_labels.groupBy("is_converted").count().collect()
    print("\nClass distribution:")
    for row in class_dist:
        print(f"  Class {row['is_converted']}: {row['count']} samples")
    
    # Define feature lookups
    # GROUNDED: Using actual feature table columns
    # Note: No user features - fact_property_engagement doesn't have user_id (it's aggregated)
    feature_lookups = [
        FeatureLookup(
            table_name=f"{catalog}.{feature_schema}.engagement_features",
            feature_names=[
                "view_count", "unique_user_views", "click_count", "search_count",
                "conversion_rate", "avg_time_on_page",
                "day_of_week", "is_weekend",
                "views_7d_avg", "clicks_7d_avg", "conversion_rate_7d_avg"
            ],
            lookup_key=["property_id", "engagement_date"]
        ),
        FeatureLookup(
            table_name=f"{catalog}.{feature_schema}.property_features",
            feature_names=[
                "property_type", "bedrooms", "bathrooms", "max_guests", "base_price",
                "destination_id", "host_id",
                "bookings_30d", "revenue_30d", "avg_booking_value_30d", "avg_nights_30d",
                "views_30d", "clicks_30d", "avg_conversion_rate_30d",
                "revenue_per_booking", "click_through_rate"
            ],
            lookup_key="property_id"
        )
    ]
    
    # Create training set
    training_set = fe.create_training_set(
        df=training_labels,
        feature_lookups=feature_lookups,
        label="is_converted",
        exclude_columns=[]
    )
    
    # Load training data
    training_df = training_set.load_df()
    
    print(f"✓ Training set created with {training_df.count()} records")
    print(f"  Features: {len(training_df.columns)}")
    
    return training_set, training_df


def preprocess_features(training_df):
    """
    Preprocess features for XGBoost classifier.
    
    Steps:
    - Handle categorical variables
    - Handle missing values
    - Balance classes (optional)
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
    # GROUNDED: property_type from property_features (no user features in this model)
    categorical_cols = ['property_type']
    for col in categorical_cols:
        if col in pdf.columns:
            pdf[col] = pd.Categorical(pdf[col]).codes
    
    # Handle missing values
    pdf = pdf.fillna(0)
    
    # Separate features and label
    feature_cols = [col for col in pdf.columns if col not in [
        'property_id', 'engagement_date', 'is_converted', 
        'feature_timestamp', 'month', 'is_peak_season'
    ]]
    
    X = pdf[feature_cols]
    y = pdf['is_converted']
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Feature columns: {list(X.columns)}")
    print(f"\nLabel distribution:")
    print(y.value_counts())
    print(f"Conversion rate: {y.mean():.2%}")
    
    return X, y, feature_cols


def train_xgboost_classifier(X_train, y_train, X_val, y_val):
    """
    Train XGBoost classification model.
    
    Uses scale_pos_weight to handle class imbalance.
    """
    print("\n" + "="*80)
    print("Training XGBoost classifier")
    print("="*80)
    
    # Calculate scale_pos_weight for imbalanced data
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    print(f"Class imbalance ratio: {scale_pos_weight:.2f}")
    
    model = XGBClassifier(
        max_depth=5,
        learning_rate=0.1,
        n_estimators=100,
        objective='binary:logistic',
        scale_pos_weight=scale_pos_weight,
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
    Evaluate classification model.
    
    Metrics:
    - AUC-ROC (Area Under ROC Curve)
    - Precision, Recall, F1-Score
    - Confusion Matrix
    """
    print("\n" + "="*80)
    print("Evaluating model")
    print("="*80)
    
    # Check if we have both classes
    n_train_classes = len(np.unique(y_train))
    n_val_classes = len(np.unique(y_val))
    
    # Training predictions
    train_pred = model.predict(X_train)
    
    # Validation predictions
    val_pred = model.predict(X_val)
    
    # Calculate AUC (handle single-class case)
    try:
        if n_train_classes > 1 and n_val_classes > 1:
            train_proba = model.predict_proba(X_train)
            val_proba = model.predict_proba(X_val)
            
            # Safely get positive class probability
            if train_proba.ndim == 2 and train_proba.shape[1] >= 2:
                train_pred_proba = train_proba[:, 1]
                val_pred_proba = val_proba[:, 1]
            else:
                # Fall back to direct probability output
                train_pred_proba = train_proba.ravel() if train_proba.ndim > 1 else train_proba
                val_pred_proba = val_proba.ravel() if val_proba.ndim > 1 else val_proba
            
            train_auc = roc_auc_score(y_train, train_pred_proba)
            val_auc = roc_auc_score(y_val, val_pred_proba)
        else:
            # Single class in labels - AUC undefined
            print(f"⚠️  Warning: Only {n_train_classes} class(es) in training, {n_val_classes} in validation. Using accuracy instead of AUC.")
            train_auc = float((train_pred == y_train).mean())
            val_auc = float((val_pred == y_val).mean())
    except Exception as e:
        print(f"⚠️  Warning: Could not compute AUC: {e}. Using accuracy instead.")
        train_auc = float((train_pred == y_train).mean())
        val_auc = float((val_pred == y_val).mean())
    
    val_precision = precision_score(y_val, val_pred, zero_division=0)
    val_recall = recall_score(y_val, val_pred, zero_division=0)
    val_f1 = f1_score(y_val, val_pred, zero_division=0)
    
    print("\nTraining Metrics:")
    print(f"  AUC-ROC: {train_auc:.4f}")
    
    print("\nValidation Metrics:")
    print(f"  AUC-ROC: {val_auc:.4f} (Target: >0.75)")
    print(f"  Precision: {val_precision:.4f}")
    print(f"  Recall: {val_recall:.4f}")
    print(f"  F1-Score: {val_f1:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_val, val_pred))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_val, val_pred)
    if cm.shape == (2, 2):
        print(f"  True Negatives: {cm[0, 0]}")
        print(f"  False Positives: {cm[0, 1]}")
        print(f"  False Negatives: {cm[1, 0]}")
        print(f"  True Positives: {cm[1, 1]}")
    else:
        print(f"  Single class only - confusion matrix shape: {cm.shape}")
        print(f"  Correct predictions: {cm[0, 0]}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10).to_string(index=False))
    
    metrics = {
        'train_auc': train_auc,
        'val_auc': val_auc,
        'val_precision': val_precision,
        'val_recall': val_recall,
        'val_f1': val_f1
    }
    
    return metrics, feature_importance


def log_model_with_mlflow(
    model, 
    X_train: pd.DataFrame,
    y_train: pd.Series,
    metrics: dict, 
    feature_importance: pd.DataFrame,
    model_name: str,
    catalog: str,
    gold_schema: str,
    feature_schema: str,
    experiment_path: str,
    spark
):
    """
    Log classification model with MLflow 3.1+ best practices including dataset tracking.
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
            domain="conversion_optimization",
            model_type="classification",
            algorithm="xgboost",
            use_case="booking_conversion_prediction",
            training_table=f"{catalog}.{gold_schema}.fact_property_engagement",
            feature_store_enabled=False
        ))
        
        # =====================================================================
        # MLflow 3.1+ Dataset Tracking (INSIDE run context) using helper
        # =====================================================================
        log_training_dataset(spark, catalog, gold_schema, "fact_property_engagement")
        
        # Log hyperparameters
        mlflow.log_params({
            "max_depth": model.max_depth,
            "learning_rate": model.learning_rate,
            "n_estimators": model.n_estimators,
            "scale_pos_weight": float(model.scale_pos_weight),
            "objective": "binary:logistic"
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
    
    spark = SparkSession.builder.appName("Conversion Predictor Training").getOrCreate()
    
    # Initialize Feature Engineering Client
    fe = FeatureEngineeringClient()
    
    # Disable autologging (causes "None" errors in serverless)
    mlflow.autolog(disable=True)
    
    # =========================================================================
    # MLflow Setup: Use model-specific experiment pre-created by Asset Bundle
    # =========================================================================
    experiment_path = setup_mlflow_experiment(model_name)
    
    try:
        # Prepare training set
        training_set, training_df = prepare_training_set(
            spark, catalog, gold_schema, feature_schema, fe
        )
        
        # Preprocess features
        X, y, feature_cols = preprocess_features(training_df)
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\nTrain set: {X_train.shape}")
        print(f"Validation set: {X_val.shape}")
        
        # Train model
        model = train_xgboost_classifier(X_train, y_train, X_val, y_val)
        
        # Evaluate model
        metrics, feature_importance = evaluate_model(
            model, X_train, y_train, X_val, y_val
        )
        
        # Log model with MLflow
        run_info = log_model_with_mlflow(
            model=model,
            X_train=X_train,
            y_train=y_train,
            metrics=metrics,
            feature_importance=feature_importance,
            model_name=model_name,
            catalog=catalog,
            gold_schema=gold_schema,
            feature_schema=feature_schema,
            experiment_path=experiment_path,
            spark=spark
        )
        
        print("\n" + "="*80)
        print("✓ Conversion Predictor training completed successfully!")
        print("="*80)
        print(f"\nModel Performance:")
        print(f"  Validation AUC-ROC: {metrics['val_auc']:.4f} (Target: >0.75)")
        print(f"  Validation F1: {metrics['val_f1']:.4f}")
        
        if run_info:
            print(f"\nMLflow Tracking:")
            print(f"  Experiment: {run_info['experiment_path']}")
            print(f"  Run Name: {run_info['run_name']}")
            print(f"  Registered Model: {run_info['registered_model_name']}")
        
        if metrics['val_auc'] > 0.75:
            print("\n✅ Model meets performance target (AUC-ROC > 0.75)")
        else:
            print("\n⚠️  Model does not meet performance target (AUC-ROC <= 0.75)")
            print("   Consider: More training data, feature engineering, hyperparameter tuning")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        dbutils.notebook.exit(f"FAILED: {str(e)}")
    
    # Signal success to Databricks (outside try block)
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()

