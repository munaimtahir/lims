# LIMS Catalog Importer - Phase B Root Cause Report

**Date:** 2026-02-05  
**Status:** Root cause identified and confirmed

---

## Executive Summary

The catalog import failure ("Tests Created=0") is caused by a **combination of column name mismatches and missing data values** in the source XLSX files. The user's files use a different schema than what the importer expects.

---

## 1. Files Analyzed

| File | Tests | Parameters | Mapping | Result |
|------|-------|------------|---------|--------|
| `LIMS_TestCatalog_IMPORT_READY.xlsx` | 678 rows | 53 rows | 301 rows | ✅ Compatible |
| `source_catalog.xlsx` | 678 rows | 302 rows* | N/A | ❌ Incompatible |
| `LIMS_TestCatalog_MVP_READY_FOR_IMPORT_PHASE_AB_FINALIZED.xlsx` | 678 rows | 302 rows* | N/A | ❌ Incompatible |

*The "Parameters" sheet in these files is actually a Mapping sheet.

---

## 2. Root Cause #1: Column Name Mismatches

### Tests Sheet

| User's File Uses | Importer Expects | Impact |
|-----------------|------------------|--------|
| `tat_hours` | `turnaround_time` | Column not found → value is `None` |
| `sample_volume_ml` | `sample_volume` | Column not found |
| `department` | (not expected) | Ignored |
| `legacy_test_code` at index 1 | at index 2 | Works (header-based, not position-based) |

### ReferenceRanges Sheet

| User's File Uses | Importer Expects | Impact |
|-----------------|------------------|--------|
| `age_min_years` | `age_min` | Column not found |
| `age_max_years` | `age_max` | Column not found |
| `ref_min` | `reference_min` | Column not found |
| `ref_max` | `reference_max` | Column not found |
| `parameter_name` | `parameter_id` | Wrong identifier type |

### Parameters Sheet

| User's File Uses | Importer Expects | Impact |
|-----------------|------------------|--------|
| `field_type` | `data_type` | Column not found |
| `options` | `allowed_values` | Column not found |

---

## 3. Root Cause #2: Missing Data in Columns

Even when columns exist, they may contain no data:

```
source_catalog.xlsx → Tests sheet → tat_hours column:
  Row 2: None
  Row 3: None
  Row 4: None
  ...
  (All 678 rows have None)
```

**Impact:** With `allow_defaults=False` (the API default), missing `turnaround_time` values cause validation errors for **every row**, resulting in `Created=0`.

---

## 4. Root Cause #3: Schema Divergence

The source files have a different sheet structure:

### Expected Structure (what importer supports)
```
Tests         → Test definitions (test_id is PK)
Parameters    → Parameter definitions (parameter_id is PK)  
Mapping       → Links tests to parameters (test_id, parameter_id)
ReferenceRanges → Range values (test_id, parameter_id, gender, age)
```

### Actual Structure (what files have)
```
Tests           → Test definitions (OK)
Parameters      → Actually a MAPPING sheet (contains test_id, test_code, parameter_id)
ParameterMaster → Actual parameter definitions (this sheet is ignored!)
ReferenceRanges → Has parameter_name instead of parameter_id
```

---

## 5. Failure Trace

When importing `source_catalog.xlsx` with `strict=True, allow_defaults=False`:

```
Step 1: Load workbook "source_catalog.xlsx"
Step 2: Check sheet "Tests" exists → YES
Step 3: Read headers: ['test_id', 'legacy_test_code', 'test_code', 'category', 
                        'test_name', 'sample_type', 'sample_volume_ml', 'price', 
                        'tat_hours', 'instructions', 'is_active', 'department']
Step 4: Look for 'turnaround_time' header → NOT FOUND (index = None)
Step 5: For each row:
        - safe_get(row, headers, "turnaround_time") → returns None (column missing)
        - to_int(None) → returns None
        - apply_default("Tests", row_num, "turnaround_time", None, 24)
          → allow_defaults=False, strict=True
          → adds error: "Missing required value (defaults disabled)"
          → returns None
        - tat_val is None → SKIP ROW (continue)
Step 6: After all 678 rows: tests.created = 0
```

---

## 6. Error Message Trace

The reported error "Panels.turnaround_time missing" is caused by:

1. User uploaded a file with a `Panels` sheet
2. The `Panels` sheet uses `tat_hours` instead of `turnaround_time`
3. The importer's error message correctly identifies the **expected** column name (`turnaround_time`)
4. But this is confusing because the user sees `tat_hours` in their file

---

## 7. Why "Decimal not JSON serializable"

In `catalog_io.py`, the `compare_fields()` function and `incoming` dictionary contain `Decimal` objects:

```python
incoming = {
    ...
    "price": price_val,  # This is Decimal("500.00")
    ...
}
```

When the response is serialized:

```python
return Response({
    "summary": summary,  # Contains Decimal objects in diff
    ...
})
```

DRF's default JSON encoder doesn't handle `Decimal`. This causes:
```
TypeError: Object of type Decimal is not JSON serializable
```

---

## 8. Specific Row/Column/Value Failures

### Test Data: Row 2 of source_catalog.xlsx

| Field | Expected Value | Actual Value | Status |
|-------|---------------|--------------|--------|
| `test_id` | 1 | 1 | ✅ OK |
| `test_code` | "ALP" | "ALP" | ✅ OK |
| `test_name` | "ALKALINE PHOSPHATASE" | "ALKALINE PHOSPHATASE" | ✅ OK |
| `category` | "A" | "A" | ✅ OK |
| `sample_type` | "Serum" | "Serum" | ✅ OK |
| `price` | 0 | 0 | ✅ OK |
| `turnaround_time` | 24 | **None** (column `tat_hours` is empty) | ❌ FAIL |

**Result:** Row 2 (and all 678 rows) fail validation.

---

## 9. Confirmation Tests

### Test A: Import "good" file
```bash
# LIMS_TestCatalog_IMPORT_READY.xlsx with correct column names
python manage.py catalog_import_excel --path LIMS_TestCatalog_IMPORT_READY.xlsx --dry-run

# Expected: Tests Created=678, Parameters Created=53, Mappings Created=301
```

### Test B: Import "bad" file
```bash
# source_catalog.xlsx with wrong column names
python manage.py catalog_import_excel --path source_catalog.xlsx --dry-run

# Expected: Tests Created=0, Errors=678 (all rows fail on turnaround_time)
```

---

## 10. Recommended Fixes

### Immediate (Phase C)

1. **Add column aliases** - Map `tat_hours` → `turnaround_time`, `field_type` → `data_type`, etc.
2. **Enable defaults by default** - Change `allow_defaults=True` as the default, or at least for required fields with sensible defaults
3. **Better error messages** - When a column is not found, list the available columns
4. **Fix Decimal serialization** - Convert to string in the response

### Before Import (Validation)

1. **Pre-validate headers** - Before processing rows, check if all required headers exist
2. **Sheet name detection** - Detect `ParameterMaster` and use it instead of `Parameters`
3. **Column mapping UI** - Allow user to map their columns to expected columns

---

## 11. Verification Steps

To confirm the fix works:

1. Add column aliases to `catalog_io.py`
2. Import `source_catalog.xlsx` with aliases enabled
3. Verify: Tests Created > 0
4. Verify: No "Decimal not JSON serializable" errors
5. Verify: Error messages include column context
