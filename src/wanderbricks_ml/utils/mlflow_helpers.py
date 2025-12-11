"""
MLflow Helper Functions for Wanderbricks ML Models

Provides consistent experiment setup, dataset tracking, and model logging
across all ML models to ensure MLflow 3.1+ best practices.
"""

import mlflow
from datetime import datetime


def setup_mlflow_experiment(model_name: str, model_description: str = ""):
    """
    Set up MLflow experiment with descriptive name (not "train").
    
    Args:
        model_name: Model name (e.g., "demand_predictor", "conversion_predictor")
        model_description: Optional description for new experiments
    
    Returns:
        experiment_path: Full experiment path
    """
    # Use descriptive experiment names
    experiment_path = f"/Workspace/Users/prashanth.subrahmanyam@databricks.com/wanderbricks_ml/{model_name}"
    
    try:
        experiment = mlflow.get_experiment_by_name(experiment_path)
        if experiment is None:
            mlflow.create_experiment(
                experiment_path,
                tags={"model": model_name, "project": "wanderbricks"}
            )
            print(f"✓ Created new experiment: {experiment_path}")
        mlflow.set_experiment(experiment_path)
        print(f"Experiment: {experiment_path}")
    except Exception as e:
        print(f"Warning: Could not set experiment: {e}")
        experiment_path = "default"
    
    return experiment_path


def log_training_dataset(spark_df, catalog: str, schema: str, table_name: str, target_column: str):
    """
    Log training dataset for MLflow 3.1+ dataset tracking.
    
    Args:
        spark_df: Spark DataFrame used for training
        catalog: Unity Catalog name
        schema: Schema name
        table_name: Source table name
        target_column: Target/label column name
    """
    try:
        dataset = mlflow.data.from_spark(
            df=spark_df,
            table_name=f"{catalog}.{schema}.{table_name}",
            version="latest",
            targets=target_column
        )
        mlflow.log_input(dataset, context="training")
        print(f"✓ Logged training dataset: {catalog}.{schema}.{table_name}")
    except Exception as e:
        print(f"⚠️  Could not log dataset: {e}")


def create_run_name(model_name: str, algorithm: str) -> str:
    """
    Create descriptive run name with timestamp.
    
    Args:
        model_name: Model name (e.g., "demand_predictor")
        algorithm: Algorithm used (e.g., "xgboost", "prophet")
    
    Returns:
        run_name: Descriptive run name
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_{timestamp}"


def get_registered_model_name(catalog: str, schema: str, model_name: str) -> str:
    """
    Get 3-level Unity Catalog model name.
    
    Args:
        catalog: Catalog name
        schema: Schema name (usually ml_schema)
        model_name: Base model name
    
    Returns:
        registered_model_name: Full UC model name
    """
    return f"{catalog}.{schema}.{model_name}"


def log_standard_tags(
    model_name: str,
    algorithm: str,
    model_type: str,
    domain: str,
    use_case: str,
    catalog: str,
    schema: str,
    source_table: str,
    **extra_tags
):
    """
    Log standard tags for consistency across all models.
    
    Args:
        model_name: Model name
        algorithm: Algorithm (xgboost, prophet, etc.)
        model_type: regression, classification, forecasting
        domain: Business domain
        use_case: Specific use case description
        catalog: Catalog name
        schema: Schema name
        source_table: Source data table
        **extra_tags: Additional model-specific tags
    """
    tags = {
        "project": "wanderbricks",
        "model_name": model_name,
        "algorithm": algorithm,
        "model_type": model_type,
        "domain": domain,
        "layer": "ml",
        "use_case": use_case,
        "training_data": f"{catalog}.{schema}.{source_table}",
        **extra_tags
    }
    mlflow.set_tags(tags)

