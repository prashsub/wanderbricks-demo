# Databricks notebook source
"""
Batch Inference Pipeline for ML Models

Performs batch scoring using registered models with automatic feature lookup.
Supports all Wanderbricks ML models.

Reference: https://learn.microsoft.com/en-us/azure/databricks/machine-learning/feature-store/train-models-with-feature-store#train-models-and-perform-batch-inference-with-feature-tables
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, current_timestamp, current_date, when
from pyspark.sql.window import Window
from databricks.feature_engineering import FeatureEngineeringClient
import mlflow
import pandas as pd
from datetime import datetime, timedelta
import builtins  # For built-in max function


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    model_name = dbutils.widgets.get("model_name")
    input_table = dbutils.widgets.get("input_table")
    output_table = dbutils.widgets.get("output_table")
    model_version = dbutils.widgets.get("model_version")  # "latest" or specific version
    
    # Derive feature_schema from output_table (catalog.schema.table)
    # Default to wanderbricks_ml for backwards compatibility
    try:
        parts = output_table.split(".")
        feature_schema = parts[1] if len(parts) >= 2 else "wanderbricks_ml"
    except:
        feature_schema = "wanderbricks_ml"
    
    print(f"Catalog: {catalog}")
    print(f"Model Name: {model_name}")
    print(f"Feature Schema: {feature_schema}")
    print(f"Input Table: {input_table}")
    print(f"Output Table: {output_table}")
    print(f"Model Version: {model_version}")
    
    return catalog, model_name, input_table, output_table, model_version, feature_schema


def load_model(catalog: str, feature_schema: str, model_name: str, model_version: str):
    """
    Load model from Unity Catalog Model Registry.
    
    Args:
        catalog: UC catalog name
        feature_schema: ML schema name (e.g., wanderbricks_ml)
        model_name: Registered model name
        model_version: Version number, "latest", or alias name
    
    Returns:
        model_uri: URI for loading model
    """
    print("\n" + "="*80)
    print("Loading model")
    print("="*80)
    
    # Construct model URI with 3-level naming
    full_model_name = f"{catalog}.{feature_schema}.{model_name}"
    
    # Get model info using MLflow client
    client = mlflow.tracking.MlflowClient()
    
    if model_version == "latest":
        # For Unity Catalog, search for versions and get the latest by version number
        model_versions = client.search_model_versions(f"name='{full_model_name}'")
        if model_versions:
            # Use builtins.max to avoid conflict with PySpark's max function
            latest_version = builtins.max(model_versions, key=lambda x: int(x.version))
            version_num = latest_version.version
            print(f"Found latest version: {version_num}")
            model_uri = f"models:/{full_model_name}/{version_num}"
        else:
            raise Exception(f"No model versions found for {full_model_name}")
    else:
        # Use specific version number
        model_uri = f"models:/{full_model_name}/{model_version}"
    
    print(f"Full Model Name: {full_model_name}")
    print(f"Model URI: {model_uri}")
    
    return model_uri


def prepare_input_data(spark: SparkSession, input_table: str, model_name: str, catalog: str, feature_schema: str):
    """
    Prepare input data for batch scoring.
    
    Creates keys + temporal columns needed by each model type.
    Feature lookup happens in score_batch.
    """
    print("\n" + "="*80)
    print("Preparing input data for scoring")
    print("="*80)
    
    print(f"Input table: {input_table}")
    
    # Read input table
    input_df = spark.table(input_table)
    
    # Model-specific preparation - create key + temporal columns
    if "demand_predictor" in model_name:
        # Demand predictor needs property_id + temporal columns
        scoring_df = (
            input_df
            .select("property_id", "check_in_date")
            .distinct()
            .withColumn("month", F.month("check_in_date"))
            .withColumn("quarter", F.quarter("check_in_date"))
            .withColumn("is_holiday", F.lit(0))
        )
        
    elif "conversion_predictor" in model_name:
        # Conversion predictor - get property_id from engagement table
        scoring_df = input_df.select("property_id").distinct()
        
    elif "pricing_optimizer" in model_name:
        # Pricing - get property_id from booking table
        scoring_df = input_df.select("property_id").distinct()
        
    elif "customer_ltv" in model_name:
        # LTV - get user_id from booking table
        scoring_df = input_df.select("user_id").distinct()
    else:
        raise ValueError(f"Unknown model type: {model_name}")
    
    record_count = scoring_df.count()
    print(f"Scoring data: {record_count} records")
    print(f"Columns: {scoring_df.columns}")
    
    return scoring_df


def score_batch(
    fe: FeatureEngineeringClient,
    spark: SparkSession,
    model_uri: str,
    scoring_df,
    model_name: str,
    catalog: str,
    feature_schema: str,
    input_table: str
):
    """
    Score batch data using standard MLflow inference.
    
    All models use manual feature lookup and preprocessing to ensure
    consistent schema between training and inference.
    """
    print("\n" + "="*80)
    print("Scoring batch data")
    print("="*80)
    
    record_count = scoring_df.count()
    print(f"Scoring {record_count} records...")
    print(f"Model URI: {model_uri}")
    
    # Join with feature tables based on model type
    if "demand_predictor" in model_name:
        features_df = spark.table(f"{catalog}.{feature_schema}.property_features")
        scoring_df = scoring_df.join(features_df, "property_id", "inner")
    elif "conversion_predictor" in model_name:
        # Conversion model uses both engagement and property features
        engagement_df = spark.table(f"{catalog}.{feature_schema}.engagement_features")
        # Drop columns that would be duplicated after join
        property_df = (
            spark.table(f"{catalog}.{feature_schema}.property_features")
            .drop("feature_date", "feature_timestamp")
        )
        scoring_df = scoring_df.join(engagement_df, "property_id", "inner")
        scoring_df = scoring_df.join(property_df, "property_id", "inner")
    elif "pricing_optimizer" in model_name:
        # Pricing model was trained ONLY with temporal features (month, quarter, is_peak_season)
        # Read booking data to get temporal context
        booking_df = spark.table(input_table)
        scoring_df = (
            booking_df
            .select("property_id", "check_in_date")
            .distinct()
            .withColumn("month", F.month("check_in_date"))
            .withColumn("quarter", F.quarter("check_in_date"))
            .withColumn("is_peak_season", when(F.month("check_in_date").isin([6, 7, 8, 12]), 1).otherwise(0))
            .drop("check_in_date")  # Model doesn't expect this
        )
    elif "customer_ltv" in model_name:
        features_df = spark.table(f"{catalog}.{feature_schema}.user_features")
        scoring_df = scoring_df.join(features_df, "user_id", "inner")
    
    print(f"Joined scoring data: {scoring_df.count()} records")
    
    # Convert to Pandas
    pdf = scoring_df.toPandas()
    
    # Convert ALL boolean columns to float FIRST (before feature selection)
    # This ensures model signature compatibility
    for col_name in pdf.columns:
        if pdf[col_name].dtype == 'bool':
            pdf[col_name] = pdf[col_name].astype(float)
    
    # Get feature columns (exclude keys and timestamps)
    exclude_cols = ['property_id', 'user_id', 'feature_date', 'check_in_date', 'engagement_date']
    feature_cols = [c for c in pdf.columns if c not in exclude_cols]
    
    print(f"Using {len(feature_cols)} features")
    
    # Encode categorical columns (same as training)
    categorical_cols = ['property_type', 'user_type', 'country', 'device_type']
    for col_name in categorical_cols:
        if col_name in pdf.columns and pdf[col_name].dtype == 'object':
            pdf[col_name] = pd.Categorical(pdf[col_name]).codes
    
    # Convert remaining numeric types (handles Decimal, int, object)
    for col_name in feature_cols:
        if col_name in categorical_cols:
            continue  # Already handled
        
        try:
            pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce')
        except (ValueError, TypeError):
            pass  # Keep as-is if conversion fails
    
    # Load model
    model = mlflow.pyfunc.load_model(model_uri)
    
    # Make predictions
    X = pdf[feature_cols].fillna(0)
    pdf['prediction'] = model.predict(X)
    
    # Convert back to Spark
    predictions_df = spark.createDataFrame(pdf)
    
    # Add metadata
    predictions_df = (
        predictions_df
        .withColumn("model_name", lit(model_name))
        .withColumn("model_uri", lit(model_uri))
        .withColumn("scored_at", current_timestamp())
        .withColumn("scoring_date", current_date())
    )
    
    # Rename prediction column based on model type
    if "demand_predictor" in model_name:
        predictions_df = predictions_df.withColumnRenamed("prediction", "predicted_bookings")
        
    elif "conversion_predictor" in model_name:
        # Classification model returns probability
        predictions_df = (
            predictions_df
            .withColumnRenamed("prediction", "conversion_probability")
            .withColumn("predicted_conversion", when(col("conversion_probability") > 0.5, 1).otherwise(0))
        )
        
    elif "pricing_optimizer" in model_name:
        predictions_df = predictions_df.withColumnRenamed("prediction", "recommended_price")
        
    elif "customer_ltv" in model_name:
        predictions_df = (
            predictions_df
            .withColumnRenamed("prediction", "predicted_ltv_12m")
            .withColumn("ltv_segment", 
                       when(col("predicted_ltv_12m") >= 2500, "VIP")
                       .when(col("predicted_ltv_12m") >= 1000, "High")
                       .when(col("predicted_ltv_12m") >= 500, "Medium")
                       .otherwise("Low"))
        )
    
    print(f"✓ Scored {predictions_df.count()} records")
    
    return predictions_df


def save_predictions(predictions_df, output_table: str):
    """
    Save predictions to Delta table.
    
    Uses MERGE to handle incremental updates.
    """
    print("\n" + "="*80)
    print("Saving predictions")
    print("="*80)
    
    print(f"Writing to: {output_table}")
    
    # Write with overwrite mode (or use MERGE for incremental)
    predictions_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .saveAsTable(output_table)
    
    final_count = spark.table(output_table).count()
    
    print(f"✓ Saved {final_count} predictions to {output_table}")
    
    # Show sample predictions
    print("\nSample Predictions:")
    spark.table(output_table).show(10, truncate=False)


def main():
    """Main batch inference pipeline."""
    
    catalog, model_name, input_table, output_table, model_version, feature_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Batch Inference").getOrCreate()
    
    # Initialize Feature Engineering Client for scoring
    fe = FeatureEngineeringClient()
    
    try:
        # Load model from Unity Catalog
        model_uri = load_model(catalog, feature_schema, model_name, model_version)
        
        # Prepare input data
        scoring_df = prepare_input_data(spark, input_table, model_name, catalog, feature_schema)
        
        # Score batch
        predictions_df = score_batch(fe, spark, model_uri, scoring_df, model_name, catalog, feature_schema, input_table)
        
        # Save predictions
        save_predictions(predictions_df, output_table)
        
        print("\n" + "="*80)
        print("✓ Batch inference completed successfully!")
        print("="*80)
        print(f"\nModel: {catalog}.{feature_schema}.{model_name}")
        print(f"Input: {input_table}")
        print(f"Output: {output_table}")
        print(f"Records Scored: {predictions_df.count()}")
        
    except Exception as e:
        print(f"\n❌ Error during batch inference: {str(e)}")
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

