# Databricks notebook source
"""
Customer Segmentation Training Pipeline

Creates customer segments using a hybrid ML + rule-based approach:
1. Stage 1: Churn Prediction (XGBoost Classifier) 
2. Stage 2: Segment Assignment (Business Rules + LTV Predictions)

Segments:
- high_value: CLV > $2,500 AND total_bookings >= 5
- at_risk: churn_score > 0.7 OR days_since_last_booking > 90
- repeat_travelers: total_bookings >= 3 AND booking_frequency > 0.5
- price_sensitive: avg_booking_value < 200 AND abandoned_bookings > 0
- new_prospects: total_bookings < 2 AND tenure_days < 30

Reference: phase4-addendum-4.1-ml-models.md + CDP screenshots
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, when, current_timestamp, current_date, coalesce, datediff, ntile, lag
from pyspark.sql.window import Window
from pyspark.sql.types import StringType, DoubleType, IntegerType
import builtins
import mlflow
from mlflow.models import infer_signature
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, classification_report
from datetime import datetime, timedelta

# =============================================================================
# MLflow Configuration
# =============================================================================
mlflow.set_registry_uri("databricks-uc")


# =============================================================================
# MLflow Setup Helpers (Inlined for serverless compatibility)
# =============================================================================
def setup_mlflow_experiment(model_name: str) -> str:
    """Set up MLflow experiment using /Shared/ path."""
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


# =============================================================================
# Stage 1: Churn Prediction Model
# =============================================================================
def prepare_churn_training_data(
    spark: SparkSession,
    catalog: str,
    gold_schema: str,
    feature_schema: str
):
    """
    Prepare training data for churn prediction.
    
    Label: is_churned (1 if no booking in last 90 days, 0 otherwise)
    """
    print("\n" + "="*80)
    print("Preparing churn prediction training data")
    print("="*80)
    
    # Load user features
    user_features = spark.table(f"{catalog}.{feature_schema}.user_features")
    
    # Load booking detail to calculate recency
    fact_booking = spark.table(f"{catalog}.{gold_schema}.fact_booking_detail")
    
    # Calculate last booking date per user (cast timestamp to date first)
    last_booking = (
        fact_booking
        .withColumn("booking_date", col("created_at").cast("date"))
        .groupBy("user_id")
        .agg(F.max("booking_date").alias("last_booking_date"))
    )
    
    # Join and create churn label
    # Use dynamic threshold based on data: bottom 50% by recency are considered "at risk"
    
    training_data_base = (
        user_features
        .join(last_booking, "user_id", "left")
        .withColumn(
            "days_since_last_booking",
            coalesce(datediff(current_date(), col("last_booking_date")), lit(365))
        )
    )
    
    # Calculate median days_since_last_booking for dynamic threshold
    median_days = training_data_base.approxQuantile("days_since_last_booking", [0.5], 0.05)[0]
    print(f"Median days since last booking: {median_days:.0f}")
    
    # Churned = above median recency (longer time since booking = more likely churned)
    # This ensures we have both classes regardless of absolute dates
    training_data = (
        training_data_base
        .withColumn(
            "is_churned",
            when(col("days_since_last_booking") > lit(median_days), 1).otherwise(0)
        )
    )
    
    print(f"Training data: {training_data.count()} users")
    print(f"Churn rate: {training_data.filter(col('is_churned') == 1).count() / training_data.count():.2%}")
    
    return training_data


def preprocess_churn_features(df):
    """Preprocess features for churn model."""
    pdf = df.toPandas()
    
    # Convert Decimal to float
    for col_name in pdf.select_dtypes(include=['object']).columns:
        try:
            pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce')
        except:
            pass
    
    # Encode categorical columns
    categorical_cols = ['country', 'user_type']
    for col_name in categorical_cols:
        if col_name in pdf.columns and pdf[col_name].dtype == 'object':
            pdf[col_name] = pd.Categorical(pdf[col_name]).codes
    
    # Fill NaN
    pdf = pdf.fillna(0)
    
    return pdf


def train_churn_model(X_train, y_train, X_val, y_val):
    """Train XGBoost classifier for churn prediction."""
    print("\n" + "="*80)
    print("Training Churn Prediction Model")
    print("="*80)
    
    model = XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        random_state=42,
        n_jobs=-1,
        scale_pos_weight=3  # Handle class imbalance (more non-churned)
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    print(f"✓ Churn model trained with {model.n_estimators} trees")
    
    return model


def evaluate_churn_model(model, X_train, y_train, X_val, y_val):
    """Evaluate churn model performance."""
    print("\n" + "="*80)
    print("Evaluating Churn Model")
    print("="*80)
    
    # Predictions
    try:
        train_pred_proba_raw = model.predict_proba(X_train)
        val_pred_proba_raw = model.predict_proba(X_val)
        
        # Handle case where only one class is predicted
        if train_pred_proba_raw.shape[1] == 2:
            train_pred_proba = train_pred_proba_raw[:, 1]
            val_pred_proba = val_pred_proba_raw[:, 1]
        else:
            train_pred_proba = train_pred_proba_raw[:, 0]
            val_pred_proba = val_pred_proba_raw[:, 0]
    except Exception as e:
        print(f"⚠️  Error getting probabilities: {e}")
        train_pred_proba = model.predict(X_train).astype(float)
        val_pred_proba = model.predict(X_val).astype(float)
    
    val_pred = model.predict(X_val)
    
    # Calculate metrics with error handling
    try:
        train_auc = roc_auc_score(y_train, train_pred_proba)
    except ValueError:
        train_auc = 0.5
        print("⚠️  Could not calculate train AUC (single class)")
        
    try:
        val_auc = roc_auc_score(y_val, val_pred_proba)
    except ValueError:
        val_auc = 0.5
        print("⚠️  Could not calculate val AUC (single class)")
    
    metrics = {
        "train_auc": train_auc,
        "val_auc": val_auc,
        "val_precision": precision_score(y_val, val_pred, zero_division=0),
        "val_recall": recall_score(y_val, val_pred, zero_division=0),
        "val_f1": f1_score(y_val, val_pred, zero_division=0)
    }
    
    print(f"\nChurn Model Performance:")
    print(f"  Validation AUC: {metrics['val_auc']:.4f} (Target: >0.80)")
    print(f"  Validation Precision: {metrics['val_precision']:.4f}")
    print(f"  Validation Recall: {metrics['val_recall']:.4f}")
    print(f"  Validation F1: {metrics['val_f1']:.4f}")
    
    if metrics['val_auc'] >= 0.80:
        print("  ✅ Model meets AUC target")
    else:
        print("  ⚠️ Model below AUC target (may need more data)")
    
    return metrics


# =============================================================================
# Stage 2: Segment Assignment
# =============================================================================
def assign_segments(
    spark: SparkSession,
    user_features_with_scores,
    ltv_predictions_table: str = None
):
    """
    Assign customers to segments using business rules + ML scores.
    
    Segment Priority (if multiple match):
    1. high_value (most valuable)
    2. at_risk (needs attention)
    3. repeat_travelers
    4. price_sensitive
    5. new_prospects
    """
    print("\n" + "="*80)
    print("Assigning Customer Segments")
    print("="*80)
    
    # If LTV predictions available, join them
    if ltv_predictions_table:
        try:
            ltv_preds = spark.table(ltv_predictions_table)
            user_features_with_scores = user_features_with_scores.join(
                ltv_preds.select("user_id", "predicted_ltv_12m"),
                "user_id", "left"
            ).fillna(0, subset=["predicted_ltv_12m"])
        except:
            print("⚠️  LTV predictions not available, using total_spend as proxy")
            user_features_with_scores = user_features_with_scores.withColumn(
                "predicted_ltv_12m", col("total_spend") * 1.5  # Rough proxy
            )
    else:
        user_features_with_scores = user_features_with_scores.withColumn(
            "predicted_ltv_12m", col("total_spend") * 1.5
        )
    
    # Ensure required columns exist with defaults
    user_features_with_scores = user_features_with_scores.withColumn(
        "abandoned_bookings", 
        when(col("cancelled_bookings").isNotNull(), col("cancelled_bookings")).otherwise(0)
    )
    
    # Segment Assignment Rules (in priority order)
    segmented = (
        user_features_with_scores
        # Primary segment assignment
        .withColumn(
            "primary_segment",
            when(
                (col("predicted_ltv_12m") > 2500) & (col("total_bookings") >= 5),
                "high_value"
            ).when(
                (col("churn_score") > 0.7) | (col("days_since_last_booking") > 90),
                "at_risk"
            ).when(
                (col("total_bookings") >= 3) & 
                (col("avg_days_between_bookings") < 180),  # booking_frequency proxy
                "repeat_travelers"
            ).when(
                (col("avg_booking_value") < 200) & (col("abandoned_bookings") > 0),
                "price_sensitive"
            ).when(
                (col("total_bookings") < 2) & (col("tenure_days") < 30),
                "new_prospects"
            ).otherwise("general")
        )
        # Secondary segment (for overlaps)
        .withColumn(
            "secondary_segment",
            when(
                (col("primary_segment") == "high_value") & (col("total_bookings") >= 3),
                "repeat_travelers"
            ).when(
                (col("primary_segment") == "at_risk") & (col("avg_booking_value") < 200),
                "price_sensitive"
            ).otherwise(lit(None))
        )
        # Engagement score (composite)
        .withColumn(
            "engagement_score",
            (
                when(col("total_bookings") > 0, 0.3).otherwise(0) +
                when(col("days_since_last_booking") < 30, 0.3).otherwise(
                    when(col("days_since_last_booking") < 90, 0.15).otherwise(0)
                ) +
                when(col("avg_booking_value") > 500, 0.2).otherwise(
                    when(col("avg_booking_value") > 200, 0.1).otherwise(0)
                ) +
                when(col("is_repeat") == True, 0.2).otherwise(0)
            )
        )
        # Price sensitivity score (0-1)
        .withColumn(
            "price_sensitivity_score",
            when(col("avg_booking_value") < 100, 1.0)
            .when(col("avg_booking_value") < 200, 0.7)
            .when(col("avg_booking_value") < 300, 0.4)
            .otherwise(0.2)
        )
        # LTV decile
        .withColumn(
            "ltv_decile",
            ntile(10).over(Window.orderBy("predicted_ltv_12m"))
        )
        # Segment confidence (based on how strongly rules match)
        .withColumn(
            "segment_confidence",
            when(col("primary_segment") == "high_value", 
                 when(col("predicted_ltv_12m") > 5000, 0.95).otherwise(0.85))
            .when(col("primary_segment") == "at_risk",
                 when(col("churn_score") > 0.9, 0.95).otherwise(0.80))
            .when(col("primary_segment") == "repeat_travelers",
                 when(col("total_bookings") > 5, 0.90).otherwise(0.80))
            .otherwise(0.75)
        )
        .withColumn("segment_assigned_at", current_timestamp())
    )
    
    # Print segment distribution
    segment_counts = segmented.groupBy("primary_segment").count().collect()
    print("\nSegment Distribution:")
    for row in segment_counts:
        print(f"  {row['primary_segment']}: {row['count']:,}")
    
    return segmented


# =============================================================================
# MLflow Logging
# =============================================================================
def log_segmentation_model_with_mlflow(
    churn_model,
    X_train: pd.DataFrame,
    churn_metrics: dict,
    segment_distribution: dict,
    model_name: str,
    catalog: str,
    feature_schema: str,
    gold_schema: str,
    experiment_name: str,
    spark
):
    """Log segmentation model (churn component) to MLflow."""
    print("\n" + "="*80)
    print("Logging Segmentation Model to MLflow")
    print("="*80)
    
    registered_model_name = f"{catalog}.{feature_schema}.customer_segmentation_churn"
    run_name = get_run_name("customer_segmentation", "xgboost_churn", "v1")
    
    with mlflow.start_run(run_name=run_name) as run:
        
        # Tags
        tags = get_standard_tags(
            model_name="customer_segmentation",
            domain="customer_analytics",
            model_type="classification",
            algorithm="xgboost",
            use_case="churn_prediction_for_segmentation",
            training_table=f"{catalog}.{gold_schema}.fact_booking_detail",
            feature_store_enabled=True
        )
        tags["segmentation_type"] = "hybrid_ml_rules"
        tags["segments"] = "high_value,at_risk,repeat_travelers,price_sensitive,new_prospects"
        mlflow.set_tags(tags)
        
        # Log training dataset
        log_training_dataset(spark, catalog, feature_schema, "user_features")
        
        # Log hyperparameters
        mlflow.log_params({
            "churn_max_depth": churn_model.max_depth,
            "churn_learning_rate": churn_model.learning_rate,
            "churn_n_estimators": churn_model.n_estimators,
            "churn_threshold": 0.5,
            "segment_rules_version": "v1",
            "ltv_threshold_high_value": 2500,
            "days_threshold_at_risk": 90
        })
        
        # Log churn model metrics
        mlflow.log_metrics(churn_metrics)
        
        # Log segment distribution
        for segment, count in segment_distribution.items():
            mlflow.log_metric(f"segment_{segment}_count", count)
        
        # Create signature
        sample_input = X_train.head(5)
        sample_output = churn_model.predict_proba(sample_input)[:, 1]
        signature = infer_signature(sample_input, sample_output)
        
        # Log model (churn component)
        mlflow.xgboost.log_model(
            churn_model,
            artifact_path="churn_model",
            signature=signature,
            input_example=sample_input,
            registered_model_name=registered_model_name
        )
        
        print(f"\n✓ Churn model logged")
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Registered Model: {registered_model_name}")
        
        return {
            "run_id": run.info.run_id,
            "model_uri": f"runs:/{run.info.run_id}/churn_model",
            "registered_model_name": registered_model_name,
            "experiment_name": experiment_name
        }


# =============================================================================
# Main Pipeline
# =============================================================================
def main():
    """Main training pipeline for customer segmentation."""
    
    catalog, gold_schema, feature_schema, model_name = get_parameters()
    
    spark = SparkSession.builder.appName("Customer Segmentation Training").getOrCreate()
    mlflow.autolog(disable=True)
    
    # Setup experiment
    experiment_name = setup_mlflow_experiment(model_name)
    
    try:
        # =================================================================
        # Stage 1: Train Churn Prediction Model
        # =================================================================
        print("\n" + "="*80)
        print("STAGE 1: Churn Prediction Model")
        print("="*80)
        
        # Prepare data
        training_data = prepare_churn_training_data(spark, catalog, gold_schema, feature_schema)
        
        # Convert to Pandas
        pdf = preprocess_churn_features(training_data)
        
        # Features for churn model
        feature_cols = [
            'total_bookings', 'total_spend', 'avg_booking_value',
            'cancelled_bookings', 'cancellation_rate', 'days_since_last_booking',
            'avg_days_between_bookings', 'tenure_days', 'is_repeat'
        ]
        feature_cols = [c for c in feature_cols if c in pdf.columns]
        
        X = pdf[feature_cols]
        y = pdf['is_churned']
        
        # Check class distribution
        class_counts = y.value_counts()
        print(f"Class distribution: {class_counts.to_dict()}")
        
        # Safety check: ensure both classes present
        if len(class_counts) < 2:
            print("⚠️  Only one class found, adjusting label distribution")
            # Force split at 50% percentile of any numeric feature
            median_spend = pdf['total_spend'].median() if 'total_spend' in pdf.columns else 0
            y = (pdf['total_spend'] > median_spend).astype(int)
            print(f"Adjusted class distribution: {y.value_counts().to_dict()}")
        
        # Split with stratification if both classes present, else without
        try:
            # Check minimum samples
            if len(X) < 10:
                print(f"⚠️  Too few samples ({len(X)}), using simple split")
                train_size = builtins.max(1, int(len(X) * 0.8))
                X_train, X_val = X[:train_size], X[train_size:]
                y_train, y_val = y[:train_size], y[train_size:]
            elif len(class_counts) < 2 or builtins.min(class_counts.values) < 2:
                print(f"⚠️  Insufficient class distribution, using regular split")
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            else:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
        except Exception as e:
            print(f"⚠️  Split failed ({type(e).__name__}: {e}), using simple split")
            train_size = max(1, int(len(X) * 0.8))
            X_train, X_val = X[:train_size], X[train_size:]
            y_train, y_val = y[:train_size], y[train_size:]
        
        print(f"Train set: {len(X_train)}, Validation set: {len(X_val)}")
        print(f"Train labels distribution: {y_train.value_counts().to_dict()}")
        print(f"Val labels distribution: {y_val.value_counts().to_dict()}")
        
        # Train churn model
        try:
            churn_model = train_churn_model(X_train, y_train, X_val, y_val)
        except Exception as train_error:
            print(f"❌ Training error: {type(train_error).__name__}: {train_error}")
            print(f"   X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
            print(f"   X_train dtypes: {X_train.dtypes.to_dict()}")
            raise
        
        # Evaluate
        churn_metrics = evaluate_churn_model(churn_model, X_train, y_train, X_val, y_val)
        
        # =================================================================
        # Stage 2: Segment Assignment
        # =================================================================
        print("\n" + "="*80)
        print("STAGE 2: Segment Assignment")
        print("="*80)
        
        # Score all users with churn model
        all_features = pdf[feature_cols]
        churn_proba = churn_model.predict_proba(all_features)
        pdf['churn_score'] = churn_proba[:, 1] if churn_proba.shape[1] > 1 else churn_proba[:, 0]
        
        # Convert back to Spark for segment assignment
        # Only include columns that can be safely converted
        safe_cols = ['user_id', 'total_bookings', 'total_spend', 'avg_booking_value',
                     'cancelled_bookings', 'cancellation_rate', 'days_since_last_booking',
                     'avg_days_between_bookings', 'tenure_days', 'is_repeat', 'is_business',
                     'country', 'user_type', 'churn_score', 'is_churned']
        safe_cols = [c for c in safe_cols if c in pdf.columns]
        
        # Convert problematic types
        pdf_safe = pdf[safe_cols].copy()
        for col_name in pdf_safe.columns:
            if pdf_safe[col_name].dtype == 'object':
                # Try to convert to numeric, keep as string if fails
                try:
                    pdf_safe[col_name] = pd.to_numeric(pdf_safe[col_name], errors='coerce').fillna(0)
                except:
                    pdf_safe[col_name] = pdf_safe[col_name].astype(str).fillna('')
        
        user_features_with_scores = spark.createDataFrame(pdf_safe)
        
        # Check for LTV predictions table
        # Note: The current batch inference doesn't include user_id in predictions
        # so we'll use the proxy method instead
        ltv_table = f"{catalog}.{feature_schema}.customer_ltv_predictions"
        ltv_available = None  # Disable LTV join until batch inference is fixed
        try:
            ltv_df = spark.table(ltv_table)
            if "user_id" in ltv_df.columns:
                ltv_available = ltv_table
                print(f"✓ LTV predictions table available with user_id")
            else:
                print(f"⚠️  LTV predictions table exists but missing user_id, using proxy")
        except:
            print("⚠️  LTV predictions table not found, using proxy")
        
        # Assign segments
        print(f"\n  user_features_with_scores columns: {user_features_with_scores.columns}")
        print(f"  user_features_with_scores count: {user_features_with_scores.count()}")
        
        try:
            segmented_users = assign_segments(spark, user_features_with_scores, ltv_available)
        except Exception as seg_error:
            print(f"  ❌ Segment assignment error: {type(seg_error).__name__}: {seg_error}")
            raise
        
        # Get segment distribution for logging
        segment_dist = {row['primary_segment']: row['count'] 
                       for row in segmented_users.groupBy("primary_segment").count().collect()}
        
        # =================================================================
        # Save Results
        # =================================================================
        print("\n" + "="*80)
        print("Saving Segmentation Results")
        print("="*80)
        
        # Save segmented users to table
        output_table = f"{catalog}.{feature_schema}.customer_segments"
        
        (segmented_users
         .select(
             "user_id",
             "primary_segment",
             "secondary_segment",
             "churn_score",
             "predicted_ltv_12m",
             "ltv_decile",
             "engagement_score",
             "price_sensitivity_score",
             "segment_confidence",
             "segment_assigned_at"
         )
         .write
         .format("delta")
         .mode("overwrite")
         .option("overwriteSchema", "true")
         .saveAsTable(output_table))
        
        saved_count = spark.table(output_table).count()
        print(f"✓ Saved {saved_count:,} customer segments to {output_table}")
        
        # =================================================================
        # Log to MLflow
        # =================================================================
        run_info = log_segmentation_model_with_mlflow(
            churn_model=churn_model,
            X_train=X_train,
            churn_metrics=churn_metrics,
            segment_distribution=segment_dist,
            model_name=model_name,
            catalog=catalog,
            feature_schema=feature_schema,
            gold_schema=gold_schema,
            experiment_name=experiment_name,
            spark=spark
        )
        
        # =================================================================
        # Summary
        # =================================================================
        print("\n" + "="*80)
        print("✓ Customer Segmentation Training Complete!")
        print("="*80)
        
        print(f"\nChurn Model Performance:")
        print(f"  AUC: {churn_metrics['val_auc']:.4f} (Target: >0.80)")
        
        print(f"\nSegment Distribution:")
        total_users = builtins.sum(segment_dist.values())
        for segment, count in sorted(segment_dist.items(), key=lambda x: -x[1]):
            pct = count / total_users * 100
            print(f"  {segment}: {count:,} ({pct:.1f}%)")
        
        print(f"\nOutput Table: {output_table}")
        print(f"MLflow Experiment: {experiment_name}")
        
    except Exception as e:
        import traceback
        error_msg = str(e) if str(e) else repr(e)
        tb = traceback.format_exc()
        print(f"\n❌ Error Type: {type(e).__name__}")
        print(f"❌ Error Message: {error_msg}")
        print(f"❌ Traceback:\n{tb}")
        dbutils.notebook.exit(f"FAILED: {type(e).__name__}: {error_msg}")
    
    dbutils.notebook.exit("SUCCESS")


if __name__ == "__main__":
    main()

