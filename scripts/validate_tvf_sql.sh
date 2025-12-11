#!/bin/bash
# Validate TVF SQL for common errors BEFORE deployment
# Usage: ./scripts/validate_tvf_sql.sh
# Exit code: 0 = all checks pass, 1 = errors found

set -e

echo "🔍 Validating TVF SQL..."
echo "========================================"

cd "$(dirname "$0")/.." || exit 1
TVF_DIR="src/wanderbricks_gold/tvfs"

if [ ! -d "$TVF_DIR" ]; then
  echo "❌ ERROR: TVF directory not found: $TVF_DIR"
  exit 1
fi

ERRORS=0

# Check 1: Deprecated column names - dd.city
echo ""
echo "1️⃣  Checking for deprecated column name: dd.city..."
if grep -n "dd\.city" "$TVF_DIR"/*.sql 2>/dev/null; then
  echo "   ❌ ERROR: Found references to dd.city (should be dd.destination)"
  echo "   Fix: Replace dd.city with dd.destination"
  ERRORS=$((ERRORS + 1))
else
  echo "   ✅ No dd.city references found"
fi

# Check 2: Deprecated column names - dd.state (not state_or_province)
echo ""
echo "2️⃣  Checking for deprecated column name: dd.state..."
if grep -n "dd\.state[^_]" "$TVF_DIR"/*.sql 2>/dev/null | grep -v "state_or_province"; then
  echo "   ❌ ERROR: Found references to dd.state (should be dd.state_or_province)"
  echo "   Fix: Replace dd.state with dd.state_or_province"
  ERRORS=$((ERRORS + 1))
else
  echo "   ✅ No dd.state references found"
fi

# Check 3: Standalone 'city' in RETURNS clauses
echo ""
echo "3️⃣  Checking for 'city' in RETURNS TABLE clauses..."
if grep -E "^\s+city\s+STRING" "$TVF_DIR"/*.sql 2>/dev/null; then
  echo "   ❌ ERROR: Found 'city' in RETURNS clause (should be 'destination')"
  echo "   Fix: Replace 'city STRING' with 'destination STRING' in RETURNS TABLE"
  ERRORS=$((ERRORS + 1))
else
  echo "   ✅ No standalone 'city' in RETURNS clauses"
fi

# Check 4: Standalone 'state' in RETURNS clauses (not state_or_province)
echo ""
echo "4️⃣  Checking for 'state' in RETURNS TABLE clauses..."
if grep -E "^\s+state\s+STRING" "$TVF_DIR"/*.sql 2>/dev/null | grep -v "state_or_province"; then
  echo "   ❌ ERROR: Found 'state' in RETURNS clause (should be 'state_or_province')"
  echo "   Fix: Replace 'state STRING' with 'state_or_province STRING' in RETURNS TABLE"
  ERRORS=$((ERRORS + 1))
else
  echo "   ✅ No standalone 'state' in RETURNS clauses"
fi

# Check 5: Missing SCD Type 2 filters (is_current = true)
echo ""
echo "5️⃣  Checking for missing is_current filters on SCD Type 2 joins..."
# List of SCD Type 2 dimensions (from YAML: scd_type: 2)
SCD2_DIMS=("dim_property" "dim_host" "dim_user")

for dim in "${SCD2_DIMS[@]}"; do
  # Find all JOIN statements for this dimension
  if grep -n "JOIN.*$dim" "$TVF_DIR"/*.sql 2>/dev/null | grep -v "is_current = true"; then
    echo "   ⚠️  WARNING: Found JOIN to $dim without is_current filter"
    echo "   Recommendation: Add 'AND {alias}.is_current = true' to SCD Type 2 dimension joins"
    # Not counted as error, just warning
  fi
done
echo "   ℹ️  Manual review recommended for SCD Type 2 filters"

# Check 6: Ambiguous table aliases (duplicate alias names)
echo ""
echo "6️⃣  Checking for duplicate table aliases..."
for file in "$TVF_DIR"/*.sql; do
  # Extract all table aliases from FROM and JOIN clauses
  # Pattern: FROM table_name alias OR JOIN table_name alias
  aliases=$(grep -oE "(FROM|JOIN)\s+[a-z_]+\s+[a-z]+" "$file" 2>/dev/null | awk '{print $3}' | sort)
  
  # Find duplicates
  duplicates=$(echo "$aliases" | uniq -d)
  
  if [ -n "$duplicates" ]; then
    echo "   ❌ ERROR in $(basename "$file"): Duplicate table aliases found: $duplicates"
    echo "   Fix: Use unique aliases for each table (e.g., fbd1, fbd2 instead of fbd, fbd)"
    ERRORS=$((ERRORS + 1))
  fi
done
echo "   ✅ No duplicate table aliases found"

# Check 7: Using function_name instead of routine_name in information_schema queries
echo ""
echo "7️⃣  Checking for incorrect information_schema column names..."
if grep -n "function_name" "$TVF_DIR"/../*.py 2>/dev/null | grep "information_schema.routines"; then
  echo "   ❌ ERROR: Found 'function_name' in information_schema.routines query"
  echo "   Fix: Replace 'function_name' with 'routine_name'"
  ERRORS=$((ERRORS + 1))
else
  echo "   ✅ Correct column names for information_schema"
fi

# Summary
echo ""
echo "========================================"
if [ $ERRORS -eq 0 ]; then
  echo "✅ All validation checks passed!"
  echo ""
  echo "Ready to deploy:"
  echo "  databricks bundle deploy -t dev"
  echo "  databricks bundle run gold_setup_job -t dev"
  exit 0
else
  echo "❌ Found $ERRORS error(s)"
  echo ""
  echo "Please fix the errors above before deploying."
  echo ""
  echo "Quick fixes:"
  echo "  cd $TVF_DIR"
  echo "  sed -i '' 's/dd\.city/dd.destination/g' *.sql"
  echo "  sed -i '' 's/dd\.state/dd.state_or_province/g' *.sql"
  echo ""
  echo "Then re-run this script: ./scripts/validate_tvf_sql.sh"
  exit 1
fi

