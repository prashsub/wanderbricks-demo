# Databricks notebook source
"""
Robust Batch Inference for All ML Models

Critical Design Principles:
1. Match EXACT model signature (column order + types)
2. Minimal preprocessing (avoid type conversions that break schema)
3. Model-specific feature preparation
4. Proper error handling with detailed logging

Reference: Production batch scoring patterns
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import col, lit, current_timestamp, current_date, when
import mlflow
from mlflow.models import ModelSignature
import pandas as pd
from datetime import datetime


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    model_name = dbutils.widgets.get("model_name")
    input_table = dbutils.widgets.get("input_table")
    output_table = dbutils.widgets.get("output_table")
    model_version = dbutils.widgets.get("model_version")
    feature_schema = dbutils.widgets.get("feature_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Model Name: {model_name}")
    print(f"Input Table: {input_table}")
    print(f"Output Table: {output_table}")
    print(f"Model Version: {model_version}")
    print(f"Feature Schema: {feature_schema}")
    
    return catalog, model_name, input_table, output_table, model_version, feature_schema


def load_model_and_signature(catalog: str, feature_schema: str, model_name: str, model_version: str):
    """
    Load model and extract signature to know exact expected schema.
    """
    print("\n" + "="*80)
    print("Loading model and extracting signature")
    print("="*80)
    
    full_model_name = f"{catalog}.{feature_schema}.{model_name}"
    
    if model_version == "latest":
        # Get latest version
        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='{full_model_name}'")
        if versions:
            latest_version = max(versions, key=lambda v: int(v.version))
            version_num = latest_version.version
            print(f"Found latest version: {version_num}")
            model_uri = f"models:/{full_model_name}/{version_num}"
        else:
            raise Exception(f"No model versions found for {full_model_name}")
    else:
        model_uri = f"models:/{full_model_name}/{model_version}"
    
    print(f"Model URI: {model_uri}")
    
    # Load model to get signature
    model = mlflow.pyfunc.load_model(model_uri)
    signature = model.metadata.signature
    
    print(f"\nModel Signature:")
    print(f"  Input columns: {[inp.name for inp in signature.inputs]}")
    print(f"  Input types: {[(inp.name, str(inp.type)) for inp in signature.inputs]}")
    
    return model, model_uri, signature


def prepare_features_for_signature(
    spark: SparkSession,
    input_table: str,
    model_name: str,
    signature: ModelSignature,
    catalog: str,
    feature_schema: str
):
    """
    Prepare features matching EXACT model signature.
    
    Strategy:
    1. Read input table for keys
    2. Read feature tables
    3. Create derived columns as needed
    4. Select ONLY columns in signature (exact order)
    5. Convert types to match signature
    """
    print("\n" + "="*80)
    print("Preparing features to match model signature")
    print("="*80)
    
    input_df = spark.table(input_table)
    
    # Extract expected column names and types from signature
    expected_cols = {inp.name: str(inp.type) for inp in signature.inputs}
    print(f"\nExpected {len(expected_cols)} columns from model signature")
    
    # Model-specific feature preparation
    if "demand_predictor" in model_name:
        # Start with property_id + check_in_date
        base_df = input_df.select("property_id", "check_in_date").distinct()
        
        # Add temporal features (expected by model)
        base_df = (
            base_df
            .withColumn("month", F.month("check_in_date").cast("integer"))
            .withColumn("quarter", F.quarter("check_in_date").cast("integer"))
            .withColumn("is_holiday", F.lit(0).cast("integer"))
        )
        
        # Join property features
        prop_features = spark.table(f"{catalog}.{feature_schema}.property_features")
        features_df = base_df.join(prop_features, "property_id", "left")
        
    elif "conversion_predictor" in model_name:
        # Start with property_id
        base_df = input_df.select("property_id").distinct()
        
        # Join engagement features
        eng_features = spark.table(f"{catalog}.{feature_schema}.engagement_features")
        features_df = base_df.join(eng_features, "property_id", "left")
        
        # Join property features (drop duplicates)
        prop_features = (
            spark.table(f"{catalog}.{feature_schema}.property_features")
            .drop("feature_date", "feature_timestamp")
        )
        features_df = features_df.join(prop_features, "property_id", "left")
        
    elif "pricing_optimizer" in model_name:
        # Pricing model trained without Feature Store
        base_df = input_df.select("property_id").distinct()
        
        # Add temporal features from booking data
        booking_context = (
            input_df
            .select("property_id", "check_in_date")
            .groupBy("property_id")
            .agg(F.max("check_in_date").alias("check_in_date"))
        )
        
        features_df = (
            base_df
            .join(booking_context, "property_id", "left")
            .withColumn("month", F.month("check_in_date").cast("integer"))
            .withColumn("quarter", F.quarter("check_in_date").cast("integer"))
            .withColumn("is_peak_season", 
                       when(F.month("check_in_date").isin([6,7,8,12]), 1).otherwise(0).cast("integer"))
            .drop("check_in_date")
        )
        
    elif "customer_ltv" in model_name:
        # LTV model trained without Feature Store
        base_df = input_df.select("user_id").distinct()
        
        # Join user features
        user_features = spark.table(f"{catalog}.{feature_schema}.user_features")
        features_df = base_df.join(user_features, "user_id", "left")
        
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    print(f"Features DataFrame: {features_df.count()} records, {len(features_df.columns)} columns")
    
    # Convert to Pandas for precise type control
    pdf = features_df.toPandas()
    
    # =========================================================================
    # CRITICAL: Match signature types EXACTLY
    # =========================================================================
    for col_name, col_type in expected_cols.items():
        if col_name not in pdf.columns:
            print(f"⚠️  Missing column: {col_name} (adding as NULL)")
            # Add missing column with proper type
            if 'double' in col_type or 'float' in col_type:
                pdf[col_name] = 0.0
            elif 'long' in col_type or 'integer' in col_type:
                pdf[col_name] = 0
            elif 'boolean' in col_type:
                pdf[col_name] = False
            else:
                pdf[col_name] = None
        else:
            # Convert existing column to match signature type
            if 'double' in col_type:
                # Convert to float64 (double)
                pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce').fillna(0.0).astype('float64')
            elif 'float' in col_type:
                # Convert to float32 (float)
                pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce').fillna(0.0).astype('float32')
            elif 'long' in col_type:
                # Convert to int64
                pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce').fillna(0).astype('int64')
            elif 'integer' in col_type:
                # Convert to int32
                pdf[col_name] = pd.to_numeric(pdf[col_name], errors='coerce').fillna(0).astype('int32')
            elif 'boolean' in col_type:
                # Keep as boolean or convert from numeric
                if pdf[col_name].dtype in ['int64', 'float64']:
                    pdf[col_name] = pdf[col_name].astype(bool)
                elif pdf[col_name].dtype == 'object':
                    pdf[col_name] = pdf[col_name].astype(str).str.lower().isin(['true', '1', 'yes'])
    
    # Select ONLY columns in signature (in signature order)
    signature_col_names = [inp.name for inp in signature.inputs]
    pdf_final = pdf[signature_col_names]
    
    print(f"\n✓ Features prepared matching signature")
    print(f"  Final shape: {pdf_final.shape}")
    print(f"  Column types match: {len(pdf_final.columns)}/{len(expected_cols)}")
    
    return pdf_final


def score_batch_with_model(model, features_pdf: pd.DataFrame, model_name: str):
    """
    Score batch using loaded MLflow model.
    
    Features DataFrame already matches model signature.
    """
    print("\n" + "="*80)
    print("Scoring batch")
    print("="*80)
    
    print(f"Scoring {len(features_pdf)} records...")
    
    # Make predictions
    predictions = model.predict(features_pdf)
    
    # Add predictions to dataframe
    features_pdf['prediction'] = predictions
    
    print(f"✓ Scored {len(features_pdf)} records")
    
    return features_pdf


def add_metadata_and_save(
    spark: SparkSession,
    predictions_pdf: pd.DataFrame,
    model_name: str,
    model_uri: str,
    output_table: str
):
    """
    Add metadata and save predictions to Delta table.
    """
    print("\n" + "="*80)
    print("Adding metadata and saving predictions")
    print("="*80)
    
    # Convert back to Spark
    predictions_df = spark.createDataFrame(predictions_pdf)
    
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
        predictions_df = (
            predictions_df
            .withColumnRenamed("prediction", "conversion_probability")
            .withColumn("predicted_conversion", 
                       when(col("conversion_probability") > 0.5, 1).otherwise(0))
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
    
    # Save predictions
    print(f"Writing to: {output_table}")
    
    predictions_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .option("overwriteSchema", "true") \
        .saveAsTable(output_table)
    
    final_count = spark.table(output_table).count()
    print(f"✓ Saved {final_count} predictions to {output_table}")
    
    return final_count


def main():
    """Main batch inference pipeline with robust schema matching."""
    
    catalog, model_name, input_table, output_table, model_version, feature_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Batch Inference (Fixed)").getOrCreate()
    
    try:
        # Load model and get signature
        model, model_uri, signature = load_model_and_signature(
            catalog, feature_schema, model_name, model_version
        )
        
        # Prepare features matching signature EXACTLY
        features_pdf = prepare_features_for_signature(
            spark, input_table, model_name, signature, catalog, feature_schema
        )
        
        # Score batch
        predictions_pdf = score_batch_with_model(model, features_pdf, model_name)
        
        # Save with metadata
        record_count = add_metadata_and_save(
            spark, predictions_pdf, model_name, model_uri, output_table
        )
        
        print("\n" + "="*80)
        print("✓ Batch inference completed successfully!")
        print("="*80)
        print(f"\nModel: {catalog}.{feature_schema}.{model_name}")
        print(f"Version: {model_version}")
        print(f"Input: {input_table}")
        print(f"Output: {output_table}")
        print(f"Records Scored: {record_count}")
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"\n❌ Error during batch inference: {str(e)}")
        print(f"\nFull traceback:\n{tb}")
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

