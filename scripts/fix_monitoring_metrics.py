#!/usr/bin/env python3
"""
Fix Databricks SDK metric definitions in monitoring scripts.
Converts dict format to SDK class format.
"""

import re
import sys

def convert_metric_dict_to_sdk(content: str) -> str:
    """Convert metric dict definitions to SDK MonitorMetric class."""
    
    # Pattern to match a metric dict
    metric_pattern = r'{[\s\S]*?"type":\s*"(AGGREGATE|DERIVED|DRIFT)"[\s\S]*?}'
    
    def replace_metric(match):
        metric_text = match.group(0)
        
        # Extract type
        type_match = re.search(r'"type":\s*"(AGGREGATE|DERIVED|DRIFT)"', metric_text)
        if not type_match:
            return metric_text
        metric_type = type_match.group(1)
        
        # Map to SDK type
        sdk_type = f"MonitorMetricType.CUSTOM_METRIC_TYPE_{metric_type}"
        
        # Replace "type": "X" with type=MonitorMetricType.CUSTOM_METRIC_TYPE_X
        result = re.sub(
            r'"type":\s*"(AGGREGATE|DERIVED|DRIFT)"',
            lambda m: f'type=MonitorMetricType.CUSTOM_METRIC_TYPE_{m.group(1)}',
            metric_text
        )
        
        # Replace other fields: "field": value → field=value
        result = re.sub(r'"(\w+)":\s*', r'\1=', result)
        
        # Wrap in MonitorMetric()
        result = f"MonitorMetric(\n            {result.strip()[1:-1]}\n        )"
        
        return result
    
    # Replace all metrics
    result = re.sub(metric_pattern, replace_metric, content)
    
    return result

def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_monitoring_metrics.py <file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    converted = convert_metric_dict_to_sdk(content)
    
    with open(filepath, 'w') as f:
        f.write(converted)
    
    print(f"✓ Converted metrics in {filepath}")

if __name__ == "__main__":
    main()

