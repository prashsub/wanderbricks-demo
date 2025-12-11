# Databricks notebook source

"""
Wanderbricks Gold Layer - Metric Views Creation

Creates Metric Views from YAML configuration for Genie AI and AI/BI dashboards.

Critical: Uses 'WITH METRICS LANGUAGE YAML' syntax (not TBLPROPERTIES).

Usage:
  databricks bundle run metric_views_job -t dev
"""

import yaml
from pathlib import Path
from pyspark.sql import SparkSession


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, gold_schema


def find_yaml_base():
    """
    Find the base directory containing metric_views YAML files.
    
    Handles both local execution and Databricks workspace paths.
    """
    # Try common paths
    possible_paths = [
        "/Workspace/files/wanderbricks_gold/semantic/metric_views",
        "/Workspace/Shared/wanderbricks_gold/semantic/metric_views",
        "metric_views",
        "../metric_views",
        "./semantic/metric_views",
        "../semantic/metric_views",
    ]
    
    for path_str in possible_paths:
        path = Path(path_str)
        if path.exists() and path.is_dir():
            print(f"Found metric views directory: {path}")
            return path
    
    # If not found, raise error
    raise FileNotFoundError(
        "Could not find metric_views directory. Searched paths:\n" +
        "\n".join(f"  - {p}" for p in possible_paths)
    )


def load_metric_views_yaml(catalog: str, schema: str):
    """
    Load all metric views from YAML files with parameter substitution.
    
    Replaces ${catalog} and ${gold_schema} placeholders with actual values.
    Returns list of tuples: (view_name, metric_view_dict).
    """
    yaml_dir = find_yaml_base()
    yaml_files = list(yaml_dir.glob("*.yaml"))
    
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files found in {yaml_dir}")
    
    print(f"\nFound {len(yaml_files)} metric view YAML file(s):")
    for f in yaml_files:
        print(f"  - {f.name}")
    
    all_metric_views = []
    
    for yaml_file in yaml_files:
        # Extract view name from filename (remove .yaml extension)
        view_name = yaml_file.stem
        
        with open(yaml_file, "r") as f:
            yaml_content = f.read()
        
        # Substitute parameters
        yaml_content = yaml_content.replace("${catalog}", catalog)
        yaml_content = yaml_content.replace("${gold_schema}", schema)
        
        # Parse YAML (returns dictionary for each metric view)
        metric_view = yaml.safe_load(yaml_content)
        
        # Each YAML file contains one metric view as a dictionary
        if isinstance(metric_view, dict):
            all_metric_views.append((view_name, metric_view))
        elif isinstance(metric_view, list):
            # Fallback if someone makes it a list again
            for mv in metric_view:
                all_metric_views.append((view_name, mv))
        else:
            print(f"  ⚠️  Warning: {yaml_file.name} has unexpected format: {type(metric_view)}")
    
    return all_metric_views


def create_metric_view(spark: SparkSession, catalog: str, schema: str, view_name: str, metric_view: dict):
    """
    Create a single metric view using WITH METRICS LANGUAGE YAML syntax.
    
    Critical: Must use 'WITH METRICS' and 'AS $$...$$' syntax, NOT TBLPROPERTIES.
    The view name is specified in CREATE VIEW statement, NOT in YAML.
    
    Args:
        view_name: Name of the metric view (from filename)
        metric_view: Metric view YAML definition (without 'name' field)
    
    Returns:
        True if successful, False if error occurred
    """
    fully_qualified_name = f"{catalog}.{schema}.{view_name}"
    
    print(f"\n{'='*80}")
    print(f"Creating metric view: {view_name}")
    print(f"Fully qualified name: {fully_qualified_name}")
    print(f"{'='*80}")
    
    # Drop existing table/view (might conflict with metric view)
    try:
        print(f"Dropping existing view/table if exists...")
        spark.sql(f"DROP VIEW IF EXISTS {fully_qualified_name}")
        spark.sql(f"DROP TABLE IF EXISTS {fully_qualified_name}")
        print(f"  ✓ Cleanup complete")
    except Exception as e:
        print(f"  ⚠️  Cleanup warning: {e}")
    
    # Convert metric view dict back to YAML string
    # Must preserve structure exactly as it appears in YAML
    # DO NOT wrap in list - Databricks expects just the dictionary
    yaml_str = yaml.dump(metric_view, default_flow_style=False, sort_keys=False)
    
    # Escape single quotes in comment for SQL
    view_comment = metric_view.get('comment', 'Metric view for Genie AI')
    view_comment_escaped = view_comment.replace("'", "''")
    
    # ✅ CORRECT: WITH METRICS LANGUAGE YAML syntax
    create_sql = f"""
CREATE VIEW {fully_qualified_name}
WITH METRICS
LANGUAGE YAML
COMMENT '{view_comment_escaped}'
AS $$
{yaml_str}
$$
"""
    
    try:
        print(f"Executing CREATE VIEW statement...")
        
        # Print first 200 chars of YAML for debugging
        print(f"  YAML content (first 200 chars): {yaml_str[:200]}...")
        
        spark.sql(create_sql)
        print(f"  ✓ CREATE VIEW succeeded")
        
        # Verify it's a METRIC_VIEW (not just VIEW)
        print(f"Verifying metric view type...")
        result = spark.sql(f"DESCRIBE EXTENDED {fully_qualified_name}").collect()
        view_type = next((row.data_type for row in result if row.col_name == "Type"), "UNKNOWN")
        
        if view_type == "METRIC_VIEW":
            print(f"  ✓ Verified as METRIC_VIEW")
        else:
            print(f"  ⚠️  Warning: Type is {view_type}, expected METRIC_VIEW")
            print(f"     This may indicate the view was created as a regular VIEW instead of METRIC_VIEW")
        
        print(f"\n✅ Successfully created: {view_name}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating {view_name}:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        
        # Print full error details
        import traceback
        print(f"\n  Full error traceback:")
        traceback.print_exc()
        
        # Print first 1000 chars of SQL for debugging
        print(f"\n  SQL statement (first 1000 chars):")
        print(create_sql[:1000])
        print("...")
        
        # Print first 500 chars of YAML
        print(f"\n  YAML content (first 500 chars):")
        print(yaml_str[:500])
        print("...")
        
        return False


def main():
    """
    Main entry point for metric views creation.
    
    Reads metric view YAML files and creates all metric views.
    Raises RuntimeError if any metric view fails (job should fail, not succeed silently).
    """
    print("\n" + "="*80)
    print("WANDERBRICKS METRIC VIEWS CREATION")
    print("="*80)
    
    # Get parameters from widgets
    catalog, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Create Metric Views").getOrCreate()
    
    try:
        # Load metric views from YAML files
        print("\n" + "="*80)
        print("LOADING YAML CONFIGURATIONS")
        print("="*80)
        
        metric_views = load_metric_views_yaml(catalog, gold_schema)
        
        print(f"\n✓ Loaded {len(metric_views)} metric view(s)")
        print("\nMetric views to create:")
        for i, (name, view) in enumerate(metric_views, 1):
            print(f"  {i}. {name}")
        
        # Create each metric view
        print("\n" + "="*80)
        print("CREATING METRIC VIEWS")
        print("="*80)
        
        success_count = 0
        failed_views = []
        
        for view_name, metric_view in metric_views:
            if create_metric_view(spark, catalog, gold_schema, view_name, metric_view):
                success_count += 1
            else:
                failed_views.append(view_name)
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Created: {success_count} of {len(metric_views)} metric views")
        
        if failed_views:
            print(f"\n❌ Failed to create: {', '.join(failed_views)}")
            print("\n" + "="*80)
            print("DEPLOYMENT FAILED")
            print("="*80)
            
            # ✅ Raise exception to fail the job
            raise RuntimeError(
                f"Failed to create {len(failed_views)} metric view(s): "
                f"{', '.join(failed_views)}"
            )
        
        print(f"\n✅ All metric views deployed successfully!")
        print("\nNext steps:")
        print("  1. Verify metric views in Databricks SQL Editor")
        print("  2. Test queries with MEASURE() function")
        print("  3. Configure Genie Space with these metric views")
        print("  4. Create AI/BI dashboards using metric views")
        
        print("\n" + "="*80)
        print("DEPLOYMENT COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("\n" + "="*80)
        print("DEPLOYMENT FAILED")
        print("="*80)
        raise
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

