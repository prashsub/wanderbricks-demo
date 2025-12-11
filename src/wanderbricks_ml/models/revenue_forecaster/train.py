# Databricks notebook source
"""
Revenue Forecaster Training Pipeline

Trains a time series model to forecast revenue for the next 30/60/90 days.
Uses Prophet and MLflow 3.0 best practices.

Reference: https://learn.microsoft.com/en-us/azure/databricks/mlflow/mlflow-3-install
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import mlflow
from mlflow.models import infer_signature
import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    model_name = dbutils.widgets.get("model_name")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    print(f"Model Name: {model_name}")
    
    return catalog, gold_schema, model_name


def prepare_training_data(spark: SparkSession, catalog: str, gold_schema: str) -> pd.DataFrame:
    """
    Prepare training data for Prophet model.
    
    Prophet requires:
    - ds: date column
    - y: target variable
    """
    print("\n" + "="*80)
    print("Preparing training data")
    print("="*80)
    
    # Load daily booking data
    fact_booking_daily = spark.table(f"{catalog}.{gold_schema}.fact_booking_daily")
    
    # Aggregate to daily revenue
    daily_revenue = (
        fact_booking_daily
        .groupBy("check_in_date")
        .agg(
            sum("total_booking_value").alias("revenue"),
            count("*").alias("booking_count")
        )
        .orderBy("check_in_date")
    )
    
    # Convert to Pandas DataFrame
    pdf = daily_revenue.toPandas()
    pdf.columns = ['ds', 'y', 'booking_count']
    
    # Remove future dates
    pdf = pdf[pdf['ds'] <= datetime.now().date()]
    
    print(f"Training data shape: {pdf.shape}")
    print(f"Date range: {pdf['ds'].min()} to {pdf['ds'].max()}")
    print(f"Total revenue: ${pdf['y'].sum():,.2f}")
    
    return pdf


def create_features(pdf: pd.DataFrame) -> pd.DataFrame:
    """
    Create additional features for the model.
    
    Features:
    - Lag features (7, 30 days)
    - Rolling averages (7, 30 days)
    - Day of week, month, quarter
    """
    print("\nCreating features...")
    
    pdf = pdf.sort_values('ds').copy()
    
    # Lag features
    pdf['revenue_lag_7d'] = pdf['y'].shift(7)
    pdf['revenue_lag_30d'] = pdf['y'].shift(30)
    
    # Rolling averages
    pdf['revenue_ma_7d'] = pdf['y'].rolling(window=7, min_periods=1).mean()
    pdf['revenue_ma_30d'] = pdf['y'].rolling(window=30, min_periods=1).mean()
    
    # Time features
    pdf['day_of_week'] = pd.to_datetime(pdf['ds']).dt.dayofweek
    pdf['month'] = pd.to_datetime(pdf['ds']).dt.month
    pdf['quarter'] = pd.to_datetime(pdf['ds']).dt.quarter
    pdf['is_weekend'] = pdf['day_of_week'].isin([5, 6]).astype(int)
    
    # Fill NAs from lag/rolling features
    pdf = pdf.fillna(method='bfill').fillna(0)
    
    print(f"Features created: {list(pdf.columns)}")
    
    return pdf


def train_prophet_model(train_df: pd.DataFrame) -> Prophet:
    """
    Train Prophet model for revenue forecasting.
    
    Prophet configuration:
    - Yearly seasonality: True
    - Weekly seasonality: True
    - Daily seasonality: False
    - Seasonality mode: multiplicative
    """
    print("\n" + "="*80)
    print("Training Prophet model")
    print("="*80)
    
    # Initialize Prophet
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0
    )
    
    # Add custom regressors
    model.add_regressor('booking_count')
    model.add_regressor('day_of_week')
    model.add_regressor('is_weekend')
    
    # Fit model
    print("Fitting model...")
    model.fit(train_df[['ds', 'y', 'booking_count', 'day_of_week', 'is_weekend']])
    
    print("✓ Model training completed")
    
    return model


def evaluate_model(model: Prophet, train_df: pd.DataFrame) -> dict:
    """
    Evaluate model using cross-validation.
    
    Returns:
    - MAPE (Mean Absolute Percentage Error)
    - RMSE (Root Mean Squared Error)
    - MAE (Mean Absolute Error)
    """
    print("\n" + "="*80)
    print("Evaluating model")
    print("="*80)
    
    print("Running cross-validation (this may take a few minutes)...")
    
    # Cross-validation
    cv_results = cross_validation(
        model,
        initial='365 days',
        period='30 days',
        horizon='30 days',
        parallel="processes"
    )
    
    # Calculate metrics
    metrics = performance_metrics(cv_results)
    
    # Average metrics
    avg_metrics = {
        'mape': metrics['mape'].mean(),
        'rmse': metrics['rmse'].mean(),
        'mae': metrics['mae'].mean(),
        'coverage': metrics['coverage'].mean()
    }
    
    print("\nCross-Validation Metrics:")
    print(f"  MAPE: {avg_metrics['mape']:.4f}")
    print(f"  RMSE: ${avg_metrics['rmse']:,.2f}")
    print(f"  MAE: ${avg_metrics['mae']:,.2f}")
    print(f"  Coverage: {avg_metrics['coverage']:.4f}")
    
    return avg_metrics


def generate_forecast(model: Prophet, periods: int = 90) -> pd.DataFrame:
    """
    Generate forecast for next N periods.
    
    Args:
        model: Trained Prophet model
        periods: Number of days to forecast (default: 90)
    
    Returns:
        DataFrame with forecast (ds, yhat, yhat_lower, yhat_upper)
    """
    print(f"\nGenerating {periods}-day forecast...")
    
    # Create future dataframe
    future = model.make_future_dataframe(periods=periods)
    
    # Add regressors (use historical averages)
    future['booking_count'] = model.history['booking_count'].mean()
    future['day_of_week'] = pd.to_datetime(future['ds']).dt.dayofweek
    future['is_weekend'] = future['day_of_week'].isin([5, 6]).astype(int)
    
    # Generate forecast
    forecast = model.predict(future)
    
    # Filter to future dates only
    forecast = forecast[forecast['ds'] > model.history['ds'].max()]
    
    print(f"Forecast generated for {len(forecast)} days")
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]


def log_model_with_mlflow(
    model: Prophet,
    train_df: pd.DataFrame,
    metrics: dict,
    model_name: str,
    catalog: str
):
    """
    Log model with MLflow 3.0 best practices.
    
    Logs:
    - Model artifacts
    - Parameters
    - Metrics
    - Training data
    - Model signature
    """
    print("\n" + "="*80)
    print("Logging model to MLflow")
    print("="*80)
    
    # Set experiment
    experiment_name = f"/Users/{spark.sql('SELECT current_user()').collect()[0][0]}/wanderbricks_ml/revenue_forecaster"
    mlflow.set_experiment(experiment_name)
    
    # Start MLflow run
    with mlflow.start_run(run_name=f"revenue_prophet_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
        
        # Log parameters
        mlflow.log_params({
            "model_type": "Prophet",
            "yearly_seasonality": True,
            "weekly_seasonality": True,
            "daily_seasonality": False,
            "seasonality_mode": "multiplicative",
            "changepoint_prior_scale": 0.05,
            "training_samples": len(train_df),
            "date_range_start": str(train_df['ds'].min()),
            "date_range_end": str(train_df['ds'].max())
        })
        
        # Log metrics
        mlflow.log_metrics({
            "mape": metrics['mape'],
            "rmse": metrics['rmse'],
            "mae": metrics['mae'],
            "coverage": metrics['coverage']
        })
        
        # Log training data
        train_dataset = mlflow.data.from_pandas(
            train_df,
            source=f"{catalog}.wanderbricks_gold.fact_booking_daily",
            name="training_data"
        )
        mlflow.log_input(train_dataset, context="training")
        
        # Infer signature
        sample_input = train_df[['ds', 'booking_count', 'day_of_week', 'is_weekend']].head(5)
        sample_forecast = model.predict(sample_input)
        signature = infer_signature(
            sample_input,
            sample_forecast[['yhat', 'yhat_lower', 'yhat_upper']]
        )
        
        # Log model using Prophet flavor
        model_info = mlflow.prophet.log_model(
            pr_model=model,
            artifact_path="model",
            signature=signature,
            input_example=sample_input,
            registered_model_name=f"{catalog}.wanderbricks_ml.{model_name}"
        )
        
        print(f"\n✓ Model logged to MLflow")
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Model URI: {model_info.model_uri}")
        print(f"  Registered Model: {catalog}.wanderbricks_ml.{model_name}")
        
        return model_info


def main():
    """Main training pipeline."""
    
    catalog, gold_schema, model_name = get_parameters()
    
    spark = SparkSession.builder.appName("Revenue Forecaster Training").getOrCreate()
    
    # Enable MLflow autologging (additional logging beyond manual)
    mlflow.autolog(exclusive=False)
    
    try:
        # Prepare training data
        train_df = prepare_training_data(spark, catalog, gold_schema)
        
        # Create features
        train_df = create_features(train_df)
        
        # Train model
        model = train_prophet_model(train_df)
        
        # Evaluate model
        metrics = evaluate_model(model, train_df)
        
        # Generate sample forecast
        forecast = generate_forecast(model, periods=90)
        print("\nSample Forecast (next 7 days):")
        print(forecast.head(7).to_string(index=False))
        
        # Log model to MLflow
        model_info = log_model_with_mlflow(
            model=model,
            train_df=train_df,
            metrics=metrics,
            model_name=model_name,
            catalog=catalog
        )
        
        print("\n" + "="*80)
        print("✓ Revenue Forecaster training completed successfully!")
        print("="*80)
        print(f"\nModel Performance:")
        print(f"  MAPE: {metrics['mape']:.2%} (Target: <15%)")
        print(f"  RMSE: ${metrics['rmse']:,.2f}")
        print(f"  MAE: ${metrics['mae']:,.2f}")
        
        if metrics['mape'] < 0.15:
            print("\n✅ Model meets performance target (MAPE < 15%)")
        else:
            print("\n⚠️  Model does not meet performance target (MAPE >= 15%)")
            print("   Consider: More training data, feature engineering, hyperparameter tuning")
        
    except Exception as e:
        print(f"\n❌ Error during training: {str(e)}")
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

