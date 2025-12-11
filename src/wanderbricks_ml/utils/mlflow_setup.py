"""
MLflow Setup Utilities for UC Volume-based Experiment Storage

This module provides functions to create and configure MLflow experiments
with Unity Catalog volume artifact storage for proper governance.

Reference: 
- https://learn.microsoft.com/en-us/azure/databricks/mlflow/experiments
- https://docs.databricks.com/aws/en/mlflow/tracking
"""

import mlflow
from datetime import datetime


def setup_mlflow_experiment(
    spark,
    catalog: str,
    ml_schema: str,
    model_name: str,
    experiment_base_name: str = "/Shared/wanderbricks_ml"
) -> str:
    """
    Set up MLflow experiment with Unity Catalog volume artifact storage.
    
    This ensures:
    1. Experiment is created if it doesn't exist
    2. Artifacts are stored in governed UC volume
    3. Consistent experiment naming across deployments
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name (e.g., 'prashanth_subrahmanyam_catalog')
        ml_schema: ML schema name (e.g., 'dev_prashanth_subrahmanyam_wanderbricks_ml')
        model_name: Name of the model (e.g., 'demand_predictor')
        experiment_base_name: Base path for experiment names
        
    Returns:
        str: Full experiment path that was set
        
    Example:
        experiment_path = setup_mlflow_experiment(
            spark=spark,
            catalog="prashanth_subrahmanyam_catalog",
            ml_schema="dev_prashanth_subrahmanyam_wanderbricks_ml",
            model_name="demand_predictor"
        )
        # Creates experiment: /Shared/wanderbricks_ml/demand_predictor
        # Artifacts stored in: dbfs:/Volumes/{catalog}/{ml_schema}/ml_artifacts/demand_predictor
    """
    print("\n" + "="*80)
    print("Setting up MLflow Experiment with UC Volume Artifact Storage")
    print("="*80)
    
    # 1. Ensure the ML artifacts volume exists
    volume_name = "ml_artifacts"
    volume_path = f"{catalog}.{ml_schema}.{volume_name}"
    artifact_location = f"dbfs:/Volumes/{catalog}/{ml_schema}/{volume_name}/{model_name}"
    
    try:
        spark.sql(f"""
            CREATE VOLUME IF NOT EXISTS {volume_path}
            COMMENT 'Unity Catalog volume for MLflow experiment artifacts - enables governed storage with lineage tracking'
        """)
        print(f"✓ UC Volume ready: {volume_path}")
    except Exception as e:
        print(f"⚠️  Could not create volume (may already exist): {e}")
    
    # 2. Define experiment name
    experiment_name = f"{experiment_base_name}/{model_name}"
    
    # 3. Try to get existing experiment or create new one
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        
        if experiment is None:
            # Create experiment with UC volume artifact location
            experiment_id = mlflow.create_experiment(
                name=experiment_name,
                artifact_location=artifact_location
            )
            print(f"✓ Created new experiment: {experiment_name}")
            print(f"  Artifact location: {artifact_location}")
        else:
            experiment_id = experiment.experiment_id
            print(f"✓ Using existing experiment: {experiment_name}")
            print(f"  Experiment ID: {experiment_id}")
            # Note: Can't change artifact location of existing experiment
        
        # 4. Set the active experiment
        mlflow.set_experiment(experiment_name)
        print(f"✓ Active experiment: {experiment_name}")
        
    except Exception as e:
        print(f"⚠️  Experiment setup warning: {e}")
        print(f"   Falling back to experiment name only")
        try:
            mlflow.set_experiment(experiment_name)
            print(f"✓ Set experiment via fallback: {experiment_name}")
        except Exception as e2:
            print(f"⚠️  Could not set experiment: {e2}")
            experiment_name = None
    
    print("="*80 + "\n")
    return experiment_name


def log_training_dataset(
    spark,
    catalog: str,
    schema: str,
    table_name: str,
    context: str = "training"
) -> bool:
    """
    Log training dataset for MLflow lineage tracking.
    
    Must be called INSIDE an active mlflow.start_run() context.
    
    Args:
        spark: SparkSession
        catalog: Unity Catalog name
        schema: Schema name containing the table
        table_name: Name of the training data table
        context: Dataset context (default: "training")
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        with mlflow.start_run():
            log_training_dataset(spark, catalog, gold_schema, "fact_booking_daily")
            # ... rest of training
    """
    full_table_name = f"{catalog}.{schema}.{table_name}"
    
    try:
        # Load the training data table
        training_df = spark.table(full_table_name)
        
        # Create MLflow dataset object
        dataset = mlflow.data.from_spark(
            df=training_df,
            table_name=full_table_name,
            version="latest"
        )
        
        # Log the dataset - this creates lineage
        mlflow.log_input(dataset, context=context)
        print(f"✓ Logged {context} dataset: {full_table_name}")
        return True
        
    except Exception as e:
        print(f"⚠️  Dataset logging failed for {full_table_name}: {e}")
        return False


def get_run_name(model_name: str, algorithm: str, version: str = "v1") -> str:
    """
    Generate descriptive run name for MLflow tracking.
    
    Format: {model_name}_{algorithm}_{version}_{timestamp}
    
    Example: demand_predictor_xgboost_v2_20250612_103045
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{model_name}_{algorithm}_{version}_{timestamp}"


def get_standard_tags(
    model_name: str,
    domain: str,
    model_type: str,
    algorithm: str,
    use_case: str,
    training_table: str,
    feature_store_enabled: bool = False
) -> dict:
    """
    Get standard MLflow run tags for consistent organization.
    
    Returns:
        dict: Tags dictionary for mlflow.set_tags()
    """
    return {
        "project": "wanderbricks",
        "domain": domain,
        "model_name": model_name,
        "model_type": model_type,
        "algorithm": algorithm,
        "layer": "ml",
        "team": "data_science",
        "use_case": use_case,
        "feature_store_enabled": str(feature_store_enabled).lower(),
        "training_data": training_table
    }

