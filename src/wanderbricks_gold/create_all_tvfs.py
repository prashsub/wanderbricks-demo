# Databricks notebook source
"""
Wanderbricks Gold Layer - Create All Table-Valued Functions

This script creates all 26 TVFs across 5 domains by reading and executing
the SQL files from the tvfs/ directory.

Created: December 2025
"""

from pyspark.sql import SparkSession
import os


def get_parameters():
    """Get job parameters from dbutils widgets."""
    catalog = dbutils.widgets.get("catalog")
    gold_schema = dbutils.widgets.get("gold_schema")
    
    print(f"Catalog: {catalog}")
    print(f"Gold Schema: {gold_schema}")
    
    return catalog, gold_schema


def get_tvf_sql_files():
    """Return list of TVF SQL files in order."""
    return [
        "revenue_tvfs.sql",
        "engagement_tvfs.sql",
        "property_tvfs.sql",
        "host_tvfs.sql",
        "customer_tvfs.sql"
    ]


def read_sql_file(filepath):
    """Read SQL file content."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {str(e)}")
        raise


def execute_tvf_domain(spark, sql_content, domain_name, catalog, gold_schema):
    """Execute TVFs for a single domain."""
    print(f"\n{'=' * 80}")
    print(f"Creating {domain_name} TVFs...")
    print(f"{'=' * 80}")
    
    # Replace placeholders
    sql_content = sql_content.replace("${catalog}", catalog)
    sql_content = sql_content.replace("${gold_schema}", gold_schema)
    
    # Split by CREATE OR REPLACE FUNCTION statements
    # Each function is a separate statement
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        # Skip USE CATALOG and USE SCHEMA statements (we'll set context once)
        if line.strip().startswith('USE CATALOG') or line.strip().startswith('USE SCHEMA'):
            continue
        
        # Check if this is start of new function
        if line.strip().startswith('CREATE OR REPLACE FUNCTION'):
            if current_statement:
                statements.append('\n'.join(current_statement))
                current_statement = []
        
        current_statement.append(line)
    
    # Add final statement
    if current_statement:
        statements.append('\n'.join(current_statement))
    
    # Execute each function
    function_count = 0
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt or stmt.startswith('--'):
            continue
        
        try:
            spark.sql(stmt)
            # Extract function name for logging
            if 'CREATE OR REPLACE FUNCTION' in stmt:
                func_name = stmt.split('FUNCTION')[1].split('(')[0].strip()
                print(f"  ✓ Created {func_name}")
                function_count += 1
        except Exception as e:
            print(f"  ✗ Error executing statement: {str(e)}")
            print(f"Statement:\n{stmt[:200]}...")
            raise
    
    print(f"\n✓ Created {function_count} functions in {domain_name} domain")
    return function_count


def main():
    """Main entry point."""
    catalog, gold_schema = get_parameters()
    
    spark = SparkSession.builder.appName("Create TVFs").getOrCreate()
    
    try:
        # Set context
        print(f"\n{'=' * 80}")
        print("Wanderbricks TVF Creation")
        print(f"Catalog: {catalog}")
        print(f"Schema: {gold_schema}")
        print(f"{'=' * 80}")
        
        spark.sql(f"USE CATALOG {catalog}")
        spark.sql(f"USE SCHEMA {gold_schema}")
        
        # Verify context
        result = spark.sql("SELECT current_catalog(), current_schema()").collect()[0]
        print(f"\nActive context: {result[0]}.{result[1]}")
        
        # Get base path for SQL files
        # In Databricks, files are synced to /Workspace/.../
        # Use dbutils to get the notebook path
        notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        
        # Notebook path looks like: /Users/email/.bundle/wanderbricks/dev/files/src/wanderbricks_gold/create_all_tvfs
        # We need to construct: /Workspace/Users/email/.bundle/wanderbricks/dev/files/src/wanderbricks_gold/tvfs
        script_dir = os.path.dirname(notebook_path)
        
        # Add /Workspace prefix if not already present
        if not script_dir.startswith('/Workspace'):
            script_dir = '/Workspace' + script_dir
        
        tvfs_dir = os.path.join(script_dir, "tvfs")
        
        print(f"\nNotebook path: {notebook_path}")
        print(f"Script directory: {script_dir}")
        print(f"TVF SQL directory: {tvfs_dir}")
        
        # Domain mapping
        domains = {
            "revenue_tvfs.sql": "Revenue (6 functions)",
            "engagement_tvfs.sql": "Engagement (5 functions)",
            "property_tvfs.sql": "Property (5 functions)",
            "host_tvfs.sql": "Host (5 functions)",
            "customer_tvfs.sql": "Customer (5 functions)"
        }
        
        total_functions = 0
        
        # Execute each domain's TVFs
        for sql_file in get_tvf_sql_files():
            filepath = os.path.join(tvfs_dir, sql_file)
            domain_name = domains.get(sql_file, sql_file)
            
            print(f"\nReading {filepath}...")
            sql_content = read_sql_file(filepath)
            
            function_count = execute_tvf_domain(
                spark, 
                sql_content, 
                domain_name, 
                catalog, 
                gold_schema
            )
            total_functions += function_count
        
        # Verify TVF creation
        print(f"\n{'=' * 80}")
        print("Verification")
        print(f"{'=' * 80}")
        
        tvf_count = spark.sql(f"""
            SELECT COUNT(*) as count
            FROM {catalog}.information_schema.routines
            WHERE routine_schema = '{gold_schema}'
              AND routine_type = 'FUNCTION'
              AND routine_name LIKE 'get_%'
        """).collect()[0]['count']
        
        print(f"\nTotal TVFs in {catalog}.{gold_schema}: {tvf_count}")
        
        # List all TVFs
        print("\nTVF List:")
        tvfs = spark.sql(f"""
            SELECT routine_name
            FROM {catalog}.information_schema.routines
            WHERE routine_schema = '{gold_schema}'
              AND routine_type = 'FUNCTION'
              AND routine_name LIKE 'get_%'
            ORDER BY routine_name
        """).collect()
        
        for row in tvfs:
            print(f"  - {row['routine_name']}")
        
        print(f"\n{'=' * 80}")
        print("Summary")
        print(f"{'=' * 80}")
        print(f"  Revenue:    6 TVFs ✓")
        print(f"  Engagement: 5 TVFs ✓")
        print(f"  Property:   5 TVFs ✓")
        print(f"  Host:       5 TVFs ✓")
        print(f"  Customer:   5 TVFs ✓")
        print(f"  ─────────────────────")
        print(f"  Total:     {tvf_count} TVFs ✓")
        print(f"\n✅ All Wanderbricks TVFs created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating TVFs: {str(e)}")
        raise
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

