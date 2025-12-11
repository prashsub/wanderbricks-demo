#!/usr/bin/env python3
"""
Generate Column-Level Lineage Documentation from YAML Schema Files

This script reads all Gold layer YAML schema files and generates a comprehensive
lineage document showing Bronze → Silver → Gold mapping for every column.

Usage:
    python scripts/generate_lineage_doc.py
    
Output:
    gold_layer_design/COLUMN_LINEAGE.md
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def load_yaml_file(yaml_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def get_transformation_type_emoji(trans_type: str) -> str:
    """Get emoji for transformation type."""
    emoji_map = {
        'DIRECT_COPY': '📋',
        'RENAME': '✏️',
        'CAST': '🔄',
        'AGGREGATE_SUM': '➕',
        'AGGREGATE_SUM_CONDITIONAL': '➕❓',
        'AGGREGATE_COUNT': '🔢',
        'AGGREGATE_COUNT_CONDITIONAL': '🔢❓',
        'AGGREGATE_AVG': '📊',
        'DERIVED_CALCULATION': '🧮',
        'DERIVED_CONDITIONAL': '🔀',
        'HASH_MD5': '🔐',
        'HASH_SHA256': '🔒',
        'COALESCE': '🛡️',
        'DATE_TRUNC': '📅',
        'GENERATED': '⚙️',
        'LOOKUP': '🔍'
    }
    return emoji_map.get(trans_type, '❓')


def generate_table_lineage(config: Dict[str, Any]) -> List[str]:
    """Generate lineage markdown for a single table."""
    lines = []
    
    table_name = config.get('table_name', 'Unknown')
    grain = config.get('grain', 'Not specified')
    domain = config.get('domain', 'N/A')
    
    lines.append(f"## Table: `{table_name}`\n")
    lines.append(f"**Grain:** {grain}  \n")
    lines.append(f"**Domain:** {domain}  \n")
    lines.append(f"**Bronze Source:** {config.get('bronze_source', 'N/A')}  \n")
    lines.append("\n")
    
    # Create column lineage table
    lines.append("| Gold Column | Type | Bronze Source | Silver Source | Transform | Logic | Notes |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    
    for col in config.get('columns', []):
        name = col['name']
        dtype = col['type']
        lineage = col.get('lineage', {})
        
        if not lineage:
            # No lineage documented
            lines.append(f"| `{name}` | {dtype} | ❌ Missing | ❌ Missing | ❌ Missing | ❌ Missing | ⚠️ No lineage documented |\n")
            continue
        
        bronze_table = lineage.get('bronze_table', 'N/A')
        bronze_column = lineage.get('bronze_column', 'N/A')
        silver_table = lineage.get('silver_table', 'N/A')
        silver_column = lineage.get('silver_column', 'N/A')
        trans_type = lineage.get('transformation', 'UNKNOWN')
        trans_logic = lineage.get('transformation_logic', 'Not documented')
        notes = lineage.get('notes', '')
        
        bronze_src = f"{bronze_table}.{bronze_column}" if bronze_table != 'N/A' else 'N/A'
        silver_src = f"{silver_table}.{silver_column}" if silver_table != 'N/A' else 'N/A'
        
        emoji = get_transformation_type_emoji(trans_type)
        
        lines.append(
            f"| `{name}` | {dtype} | {bronze_src} | {silver_src} | "
            f"{emoji} {trans_type} | `{trans_logic}` | {notes} |\n"
        )
    
    lines.append("\n")
    
    # Add aggregation summary if applicable
    has_aggregation = any(
        col.get('lineage', {}).get('groupby_columns')
        for col in config.get('columns', [])
    )
    
    if has_aggregation:
        lines.append("### Aggregation Details\n\n")
        
        # Find groupby columns
        groupby_cols = None
        for col in config.get('columns', []):
            gb = col.get('lineage', {}).get('groupby_columns')
            if gb:
                groupby_cols = gb
                break
        
        if groupby_cols:
            lines.append(f"**Grain:** `GROUP BY ({', '.join(groupby_cols)})`\n\n")
        
        # List aggregated measures
        agg_measures = [
            col['name']
            for col in config.get('columns', [])
            if col.get('lineage', {}).get('transformation', '').startswith('AGGREGATE_')
        ]
        
        if agg_measures:
            lines.append("**Aggregated Measures:** " + ", ".join(f"`{m}`" for m in agg_measures) + "\n\n")
    
    lines.append("---\n\n")
    
    return lines


def generate_lineage_document(yaml_dir: Path, output_path: Path):
    """Generate complete lineage documentation."""
    print(f"🔍 Scanning YAML files in: {yaml_dir}")
    
    yaml_files = sorted(yaml_dir.rglob("*.yaml"))
    
    if not yaml_files:
        print("❌ No YAML files found!")
        return
    
    print(f"📄 Found {len(yaml_files)} YAML files")
    
    lines = []
    
    # Header
    lines.append("# Column-Level Lineage: Bronze → Silver → Gold\n\n")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
    lines.append(f"**Project:** Wanderbricks  \n")
    lines.append(f"**Total Tables:** {len(yaml_files)}  \n\n")
    
    lines.append("## Purpose\n\n")
    lines.append(
        "This document provides complete column-level data lineage from Bronze through Gold layer, "
        "including transformation logic for every column. Use this as reference when implementing "
        "Gold merge scripts to prevent schema mismatches.\n\n"
    )
    
    lines.append("## Legend\n\n")
    lines.append("| Emoji | Transformation Type |\n")
    lines.append("|---|---|\n")
    lines.append("| 📋 | Direct Copy (no transformation) |\n")
    lines.append("| ✏️ | Rename (column name changed) |\n")
    lines.append("| 🔄 | Cast (data type conversion) |\n")
    lines.append("| ➕ | Aggregate SUM |\n")
    lines.append("| ➕❓ | Aggregate SUM (conditional) |\n")
    lines.append("| 🔢 | Aggregate COUNT |\n")
    lines.append("| 🔢❓ | Aggregate COUNT (conditional) |\n")
    lines.append("| 📊 | Aggregate AVG |\n")
    lines.append("| 🧮 | Derived Calculation |\n")
    lines.append("| 🔀 | Derived Conditional (CASE/WHEN) |\n")
    lines.append("| 🔐 | MD5 Hash |\n")
    lines.append("| 🔒 | SHA256 Hash |\n")
    lines.append("| 🛡️ | Coalesce (null handling) |\n")
    lines.append("| 📅 | Date Truncation |\n")
    lines.append("| ⚙️ | Generated (not from source) |\n")
    lines.append("| 🔍 | Lookup (from dimension join) |\n\n")
    
    lines.append("---\n\n")
    
    # Process each YAML file
    tables_with_missing_lineage = []
    
    for yaml_file in yaml_files:
        print(f"  Processing: {yaml_file.name}")
        
        try:
            config = load_yaml_file(yaml_file)
            table_lines = generate_table_lineage(config)
            lines.extend(table_lines)
            
            # Check for missing lineage
            missing_count = sum(
                1 for col in config.get('columns', [])
                if not col.get('lineage')
            )
            
            if missing_count > 0:
                tables_with_missing_lineage.append((config.get('table_name', 'Unknown'), missing_count))
        
        except Exception as e:
            print(f"  ⚠️  Error processing {yaml_file.name}: {str(e)}")
    
    # Add summary if there are missing lineages
    if tables_with_missing_lineage:
        lines.append("## ⚠️ Missing Lineage Documentation\n\n")
        lines.append("The following tables have columns without lineage documentation:\n\n")
        lines.append("| Table | Missing Columns |\n")
        lines.append("|---|---|\n")
        for table, count in tables_with_missing_lineage:
            lines.append(f"| `{table}` | {count} |\n")
        lines.append("\n**Action Required:** Add `lineage` section to these columns in YAML files.\n\n")
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ Generated lineage document: {output_path}")
    print(f"📊 Total tables: {len(yaml_files)}")
    
    if tables_with_missing_lineage:
        print(f"⚠️  Tables with missing lineage: {len(tables_with_missing_lineage)}")


def main():
    """Main entry point."""
    # Project paths
    project_root = Path(__file__).parent.parent
    yaml_dir = project_root / "gold_layer_design" / "yaml"
    output_path = project_root / "gold_layer_design" / "COLUMN_LINEAGE.md"
    
    print("=" * 80)
    print("GOLD LAYER COLUMN LINEAGE GENERATOR")
    print("=" * 80)
    print()
    
    if not yaml_dir.exists():
        print(f"❌ YAML directory not found: {yaml_dir}")
        return 1
    
    generate_lineage_document(yaml_dir, output_path)
    
    print()
    print("=" * 80)
    print("✅ Lineage generation complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review COLUMN_LINEAGE.md for completeness")
    print("  2. Add missing lineage documentation to YAML files")
    print("  3. Use lineage document when implementing Gold merge scripts")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())

