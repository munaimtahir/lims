# LIMS Catalog Import Engine Fix - Summary Report

**Date:** 2026-02-05  
**Status:** ✅ Phase A-C Complete, Phase D Planned

---

## Overview

This document summarizes the catalog import engine audit and fixes completed to address the user's issues with XLSX imports failing ("Tests Created=0" and "Panels.turnaround_time missing").

---

## Problem Statement

Users experienced the following issues when importing catalog data from XLSX files:

1. **"Tests Created=0"** - No tests were imported even from valid files
2. **"Panels.turnaround_time missing"** - Validation errors that seemed incorrect
3. **"Decimal not JSON serializable"** - Occasional server errors
4. **Silent failures** - Rows rejected without clear error messages

---

## Root Cause Analysis

### Finding #1: Column Name Mismatches

The user's source files (`source_catalog.xlsx`, `LIMS_TestCatalog_MVP_READY_FOR_IMPORT_PHASE_AB_FINALIZED.xlsx`) use different column names than what the importer expected:

| User's File | Expected | Impact |
|------------|----------|--------|
| `tat_hours` | `turnaround_time` | Column not found |
| `sample_volume_ml` | `sample_volume` | Column not found |
| `field_type` | `data_type` | Column not found |
| `age_min_years` | `age_min` | Column not found |
| `ref_min`/`ref_max` | `reference_min`/`reference_max` | Column not found |

### Finding #2: Empty Data Values

Even after fixing column names, the `tat_hours` column in `source_catalog.xlsx` contains **empty cells** for all 678 rows. This is a **data quality issue**, not a code issue.

### Finding #3: Schema Divergence

The source files have a different sheet structure:
- `Parameters` sheet actually contains **mapping data** (has `test_id` column)
- `ParameterMaster` sheet has actual parameter definitions (but importer ignores it)

---

## Fixes Implemented (Phase C)

### 1. Column Alias Support

Added `COLUMN_ALIASES` dictionary that maps common column name variations to the expected names:

```python
COLUMN_ALIASES = {
    "tat_hours": "turnaround_time",
    "sample_volume_ml": "sample_volume",
    "field_type": "data_type",
    "age_min_years": "age_min",
    "ref_min": "reference_min",
    # ... and more
}
```

### 2. Null Value Handling

Added `is_null_value()` function that treats common null representations as `None`:

```python
NULL_VALUES = frozenset([
    "na", "n/a", "null", "none", "-", "--", ".", "",
    "#n/a", "#null", "#na", "nil", "undefined",
])
```

### 3. Decimal JSON Serialization

Added `_serialize_for_json()` function to convert `Decimal` objects to strings before returning API responses, preventing `TypeError: Object of type Decimal is not JSON serializable`.

### 4. Improved Integer Parsing

Enhanced `to_int()` to handle float-like strings (`"24.0"` → `24`).

### 5. Helper Functions

Added `apply_column_aliases()` and `_validate_sheet_headers()` for better header management.

---

## Files Modified

| File | Changes |
|------|---------|
| `lims-backend/apps/laboratory/catalog_io.py` | Added aliases, null handling, JSON serialization |
| `docs/importer_audit.md` | Phase A audit documentation |
| `docs/importer_root_cause.md` | Phase B root cause analysis |
| `docs/importer_ux_plan.md` | Phase D UX improvement plan |
| `lims-backend/apps/laboratory/tests/test_import_fixes.py` | New test cases |

---

## Verification

### Test 1: Column Aliases Work

```
Headers (with aliases applied): 
  ['test_id', 'legacy_test_code', 'test_code', 'category', 'test_name', 
   'sample_type', 'sample_volume_ml', 'price', 'tat_hours', 'instructions', 
   'is_active', 'department', 'turnaround_time', 'sample_volume']
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                               (aliases added automatically)
```

### Test 2: Good File Still Works

```
LIMS_TestCatalog_IMPORT_READY.xlsx:
  RESULT: 678 valid tests, 0 errors ✅
```

### Test 3: Null Values Handled

```python
is_null_value("NA") = True
is_null_value("N/A") = True
is_null_value("-") = True
is_null_value("null") = True
is_null_value("Hello") = False
is_null_value(123) = False
```

---

## What's NOT Fixed (Data Issues)

The `source_catalog.xlsx` file still won't import all tests because:

1. **Empty `tat_hours` column** - All 678 rows have `None` for turnaround time
2. **Missing `Mapping` sheet** - The `Parameters` sheet is misnamed
3. **Empty `ReferenceRanges` sheet** - No reference range data

These are **data quality issues** that must be fixed in the source file, not the importer.

---

## Recommended Next Steps

### Immediate

1. ✅ Deploy the Phase C fixes
2. ⏳ User should use `LIMS_TestCatalog_IMPORT_READY.xlsx` (the compatible file)
3. ⏳ If `source_catalog.xlsx` is needed, populate the `tat_hours` column

### Short-term

1. Implement `validation_only` API mode
2. Add per-sheet error grouping in response
3. Create new frontend upload wizard

### Long-term

1. Add import preview showing what will be created/updated
2. Support importing from `ParameterMaster` sheet (as an alternative to `Parameters`)
3. Add import history with rollback capability

---

## API Usage Examples

### Current Behavior (After Fixes)

```bash
# Dry-run import with defaults enabled
curl -X POST 'http://localhost/api/laboratory/imports/?dry_run=true&allow_defaults=true' \
  -F 'file=@catalog.xlsx'

# Response includes:
{
  "dry_run": true,
  "counts": {
    "tests": {"created": 678, "updated": 0, "unchanged": 0},
    ...
  },
  "errors": [],
  "warnings": [
    {"sheet": "Tests", "row": 1, "field": "headers", 
     "message": "Unrecognized columns (ignored): department"}
  ]
}
```

### With `allow_defaults=false` (Strict Mode)

```bash
curl -X POST 'http://localhost/api/laboratory/imports/?dry_run=true&strict=true&allow_defaults=false' \
  -F 'file=@source_catalog.xlsx'

# Response includes errors for missing turnaround_time:
{
  "errors": [
    {"sheet": "Tests", "row": 2, "field": "turnaround_time", 
     "message": "Missing required value (defaults disabled)"},
    ...
  ]
}
```

---

## Conclusion

The catalog importer has been enhanced with:
- ✅ Column alias support for common naming variations
- ✅ Robust null value handling
- ✅ JSON-safe response serialization
- ✅ Improved integer parsing

The `LIMS_TestCatalog_IMPORT_READY.xlsx` file now imports successfully. For `source_catalog.xlsx`, the user needs to populate the empty `tat_hours` column with actual values, as this is a data completeness issue rather than a code issue.
