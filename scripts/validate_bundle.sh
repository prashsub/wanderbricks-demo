#!/bin/bash
# Pre-Deployment Validation Script for Wanderbricks Asset Bundle
# Catches common errors before deployment

set -e  # Exit on error

echo "🔍 Wanderbricks Asset Bundle - Pre-Deployment Validation"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track errors
ERRORS=0
WARNINGS=0

# 1. Check for duplicate YAML files
echo "1. Checking for duplicate resource files..."
duplicates=$(find resources -name "*.yml" | awk -F/ '{print $NF}' | sort | uniq -d)
if [ -n "$duplicates" ]; then
    echo -e "${RED}❌ ERROR: Duplicate resource files found:${NC}"
    echo "$duplicates"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ No duplicate files${NC}"
fi

# 2. Check databricks.yml exists
echo ""
echo "2. Checking databricks.yml exists..."
if [ ! -f "databricks.yml" ]; then
    echo -e "${RED}❌ ERROR: databricks.yml not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ databricks.yml found${NC}"
fi

# 3. Check for notebook header in dq_rules_loader.py
echo ""
echo "3. Checking dq_rules_loader.py (must be pure Python)..."
if [ -f "src/wanderbricks_silver/dq_rules_loader.py" ]; then
    if head -1 "src/wanderbricks_silver/dq_rules_loader.py" | grep -q "# Databricks notebook source"; then
        echo -e "${RED}❌ ERROR: dq_rules_loader.py has notebook header (must be removed)${NC}"
        echo "   Fix: Remove '# Databricks notebook source' from first line"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅ dq_rules_loader.py is pure Python${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  WARNING: dq_rules_loader.py not found${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 4. Check for CLI-style parameters in notebook_task
echo ""
echo "4. Checking for CLI-style parameters..."
if grep -r 'parameters:' resources/ 2>/dev/null | grep -E '"\-\-' > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Found CLI-style parameters (should be base_parameters)${NC}"
    grep -rn 'parameters:' resources/ | grep -E '"\-\-'
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ No CLI-style parameters found${NC}"
fi

# 5. Check for missing var. prefix
echo ""
echo "5. Checking variable references..."
if grep -r '\${catalog}' resources/ 2>/dev/null > /dev/null 2>&1; then
    echo -e "${RED}❌ ERROR: Found \${catalog} without var. prefix${NC}"
    grep -rn '\${catalog}' resources/
    echo "   Fix: Use \${var.catalog} instead"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ Variable references correct${NC}"
fi

# 6. Check that all notebook paths exist
echo ""
echo "6. Checking notebook paths..."
MISSING_NOTEBOOKS=0
while IFS= read -r line; do
    if [[ $line =~ notebook_path:\ *(.+\.py) ]]; then
        path="${BASH_REMATCH[1]}"
        # Remove leading ../
        path="${path#../../}"
        if [ ! -f "$path" ]; then
            echo -e "${RED}❌ ERROR: Notebook not found: $path${NC}"
            MISSING_NOTEBOOKS=$((MISSING_NOTEBOOKS + 1))
        fi
    fi
done < <(find resources -name "*.yml" -exec cat {} \;)

if [ $MISSING_NOTEBOOKS -eq 0 ]; then
    echo -e "${GREEN}✅ All notebook paths exist${NC}"
else
    ERRORS=$((ERRORS + 1))
fi

# 7. Validate YAML syntax with Databricks CLI
echo ""
echo "7. Validating bundle syntax..."
if command -v databricks &> /dev/null; then
    if databricks bundle validate 2>&1 | grep -q "validation passed"; then
        echo -e "${GREEN}✅ Bundle validation passed${NC}"
    else
        echo -e "${RED}❌ ERROR: Bundle validation failed${NC}"
        databricks bundle validate
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  WARNING: Databricks CLI not found, skipping validation${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 8. Check for required directories
echo ""
echo "8. Checking directory structure..."
REQUIRED_DIRS=(
    "src/wanderbricks_silver"
    "resources"
    "resources/silver"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ ERROR: Directory not found: $dir${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All required directories exist${NC}"
fi

# Summary
echo ""
echo "========================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All pre-deployment checks passed!${NC}"
    echo ""
    echo "Ready to deploy with:"
    echo "  databricks bundle deploy -t dev"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  ${WARNINGS} warning(s) found (deployment OK)${NC}"
    echo ""
    echo "You can proceed with:"
    echo "  databricks bundle deploy -t dev"
    exit 0
else
    echo -e "${RED}❌ ${ERRORS} error(s) and ${WARNINGS} warning(s) found${NC}"
    echo ""
    echo "Please fix errors before deploying."
    exit 1
fi

