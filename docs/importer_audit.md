# LIMS Catalog Importer - Phase A Audit Report

**Date:** 2026-02-05  
**Author:** Antigravity (Automated Audit)

---

## 1. Import Engine Code Paths

### 1.1 Core Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Main Import Logic | `lims-backend/apps/laboratory/catalog_io.py` | Core import/export functions |
| API Endpoint | `lims-backend/apps/laboratory/views.py::BulkImportViewSet` | REST API for uploads |
| CLI Command | `lims-backend/apps/laboratory/management/commands/catalog_import_excel.py` | Management command |
| Template Generator | `lims-backend/apps/laboratory/utils.py::generate_import_template` | Downloads blank template |

### 1.2 Parsing Library

- **openpyxl** - Used for reading/writing `.xlsx` files
- Direct cell iteration via `sheet.iter_rows(min_row=2, values_only=True)`
- Header normalization via `normalize_header()` function

---

## 2. Sheet Name Mapping

The importer uses **exact sheet name matching** (case-sensitive):

```python
SHEET_ORDER = ["Tests", "Parameters", "Mapping", "Panels", "PanelTests", "ReferenceRanges"]
```

| Expected Sheet | Status | Notes |
|---------------|--------|-------|
| `Tests` | Required | Core test definitions |
| `Parameters` | Required | Global parameter definitions |
| `Mapping` | Required | Links tests to parameters |
| `Panels` | Optional | Test panel definitions |
| `PanelTests` | Optional | Links panels to tests |
| `ReferenceRanges` | Optional | Age/gender-specific ranges |

**Behavior with unexpected sheets:**
- Extra sheets (e.g., `INSTRUCTIONS`, `README`, `FREEZE_META`) are **silently ignored**
- Sheet name matching is case-sensitive (`tests` ≠ `Tests`)

---

## 3. Required Columns Per Sheet

### Tests Sheet

| Column | Type | Required | Default (if `allow_defaults=True`) |
|--------|------|----------|-------------------------------------|
| `test_id` | Integer | **Yes** (PK) | - |
| `test_code` | String | **Yes** | - |
| `test_name` | String | **Yes** | - |
| `category` | String | **Yes** | - |
| `sample_type` | String | No | `"Serum"` |
| `sample_volume` | String | No | `None` |
| `price` | Decimal | No | `0` |
| `turnaround_time` | Integer | No | `24` |
| `loinc_code` | String | No | `None` |
| `instructions` | String | No | `None` |
| `is_active` | Boolean | No | `True` |
| `legacy_test_code` | String | No | `None` |

### Parameters Sheet

| Column | Type | Required | Default |
|--------|------|----------|---------|
| `parameter_id` | String | **Yes** (PK) | - |
| `parameter_name` | String | **Yes** | - |
| `unit` | String | No | `None` |
| `data_type` | String | No | `"Numeric"` |
| `editor_type` | String | No | `"Plain"` |
| `decimal_places` | Integer | No | `2` |
| `allowed_values` | String | No | `""` |
| `flag_direction` | String | No | `"Both"` |
| `has_quick_text` | Boolean | No | `False` |
| `active` | Boolean | No | `True` |

### Mapping Sheet

| Column | Type | Required | Default |
|--------|------|----------|---------|
| `test_id` | Integer | **Yes** (FK) | - |
| `parameter_id` | String | **Yes** (FK) | - |
| `display_order` | Integer | No | `0` |
| `reportable` | Boolean | No | `True` |

### Panels Sheet

| Column | Type | Required | Default |
|--------|------|----------|---------|
| `panel_code` | String | **Yes** (PK) | - |
| `panel_name` | String | **Yes** | - |
| `category` | String | **Yes** | - |
| `sample_type` | String | No | `"Serum"` |
| `sample_volume` | String | No | `None` |
| `price` | Decimal | No | `0` |
| `turnaround_time` | Integer | No | `24` |
| `description` | String | No | `None` |
| `is_active` | Boolean | No | `True` |

### PanelTests Sheet

| Column | Type | Required |
|--------|------|----------|
| `panel_code` | String | **Yes** (FK) |
| `test_id` | Integer | **Yes** (FK) |

### ReferenceRanges Sheet

| Column | Type | Required | Default |
|--------|------|----------|---------|
| `test_id` | Integer | **Yes** (FK) | - |
| `parameter_id` | String | **Yes** (FK) | - |
| `gender` | String | No | `"Both"` |
| `age_min` | Integer | No | `None` |
| `age_max` | Integer | No | `None` |
| `reference_min` | Decimal | No | `None` |
| `reference_max` | Decimal | No | `None` |
| `critical_low` | Decimal | No | `None` |
| `critical_high` | Decimal | No | `None` |
| `is_active` | Boolean | No | `True` |
| `version` | Integer | No | `1` |
| `notes` | String | No | `None` |

---

## 4. Header Normalization Rules

The `normalize_header()` function applies these transformations:

```python
def normalize_header(value):
    return str(value).strip().lower().replace(" ", "_").replace("(", "").replace(")", "")
```

| Original Header | Normalized |
|----------------|------------|
| `Test ID` | `test_id` |
| `Turnaround Time (hours)` | `turnaround_time_hours` ⚠️ |
| `TAT_Hours` | `tat_hours` ⚠️ |
| `sample_volume_ml` | `sample_volume_ml` ⚠️ |
| `age_min_years` | `age_min_years` ⚠️ |

**⚠️ Known Mismatches:** The normalization does NOT handle unit suffixes like `_hours`, `_ml`, `_years`. Files with these suffixes will **fail silently**.

---

## 5. Value Parsing & Type Conversion

### Numeric Conversion

```python
def to_int(value):
    if value is None or str(value).strip() == "":
        return None
    # Converts to int; invalid values return None
```

```python
def to_decimal(value):
    if value is None or str(value).strip() == "":
        return None
    # Converts to Decimal; invalid values return None
```

### Boolean Conversion

```python
def to_bool(value, default=None):
    # Accepts: True/False (bool), "true"/"false", "1"/"0", "yes"/"no", "y"/"n"
    # Empty strings return the default
```

### Empty/NA Value Handling

| Input | Behavior |
|-------|----------|
| `None` | Treated as missing |
| `""` (empty string) | Treated as missing |
| `"NA"`, `"N/A"`, `"-"` | **NOT treated specially** - passes through as literal string ⚠️ |
| `"NULL"`, `"null"` | **NOT treated specially** - passes through as literal string ⚠️ |

**⚠️ Bug:** If a cell contains "NA" or "N/A", the importer may try to use it as a literal value (e.g., converting "NA" to integer will fail silently and return `None`).

---

## 6. Import Transaction Logic

### Execution Mode

```python
if dry_run:
    transaction_context = DummyContext()  # No-op context, no DB writes
else:
    transaction_context = transaction.atomic()  # All-or-nothing
```

### Import Order

The importer processes sheets in this **fixed order**:

1. **Tests** - Must succeed first (provides test_id references)
2. **Parameters** - Must succeed (provides parameter_id references)
3. **Panels** - Depends on categories
4. **Mapping** - Depends on Tests and Parameters
5. **PanelTests** - Depends on Panels and Tests
6. **ReferenceRanges** - Depends on Mapping (needs test_id + parameter_id combo)

### Error Handling

- **Individual row errors** are collected but **do not stop processing**
- **All errors** are accumulated and returned at the end
- If `strict=True`, missing required values are **errors**
- If `strict=False`, missing required values are **warnings**
- If `allow_defaults=False`, missing optional values with defined defaults are **errors**

---

## 7. Error Reporting

### Error Structure

```python
{
    "sheet": "Tests",        # Sheet name
    "row": 5,                # 1-indexed row number (2 = first data row)
    "field": "turnaround_time",
    "message": "Missing required value (defaults disabled)"
}
```

### Where Errors Appear

1. **API Response:** `summary.errors[]` array
2. **CLI Output:** Printed to stdout
3. **CatalogImportJob Model:** Stored in `errors_json` field
4. **Server Logs:** Not currently logged to files

---

## 8. Known Issues Found

### Issue 1: Column Name Mismatches

Files like `source_catalog.xlsx` use non-standard column names:

| File Uses | Importer Expects |
|-----------|------------------|
| `tat_hours` | `turnaround_time` |
| `sample_volume_ml` | `sample_volume` |
| `age_min_years` | `age_min` |
| `age_max_years` | `age_max` |
| `ref_min` / `ref_max` | `reference_min` / `reference_max` |
| `parameter_name` (in ReferenceRanges) | `parameter_id` |

**Impact:** All columns with wrong names are treated as missing, leading to validation errors or silent null values.

### Issue 2: Schema Divergence Between Files

- `source_catalog.xlsx` has a `Parameters` sheet that is actually a **Mapping sheet** (contains `test_id`)
- It has a separate `ParameterMaster` sheet with the actual parameter definitions
- The importer looks for `Parameters` but gets mapping data instead

### Issue 3: ReferenceRanges Linking by Name

Some files use `parameter_name` instead of `parameter_id` for ReferenceRanges linking. The importer strictly requires `parameter_id`.

### Issue 4: Defaults Disabled Behavior

When `allow_defaults=False` (the API default), any missing optional field with a defined default becomes an **error**, not a warning. This is overly strict.

### Issue 5: Decimal Serialization

The response includes `Decimal` objects. When serialized to JSON, this may cause:
```
TypeError: Object of type Decimal is not JSON serializable
```

This occurs in:
- `compare_fields()` return values in the diff
- `incoming` dictionary values for price fields

---

## 9. Files Analyzed

| File | Sheet Structure | Compatible |
|------|-----------------|------------|
| `LIMS_TestCatalog_IMPORT_READY.xlsx` | Tests, Parameters, Mapping, ReferenceRanges | ✅ Yes |
| `source_catalog.xlsx` | Tests, Parameters*, ParameterMaster, ReferenceRanges | ❌ No (wrong schema) |
| `LIMS_TestCatalog_MVP_READY_FOR_IMPORT_PHASE_AB_FINALIZED.xlsx` | Same as above | ❌ No (wrong schema) |

*Parameters sheet in these files is actually a Mapping sheet

---

## 10. Recommendations

### Immediate Fixes

1. **Add column alias support** - Map common variations to expected names
2. **Handle "NA" values** - Treat common null representations as None
3. **Fix Decimal serialization** - Convert to string before JSON response
4. **Improve error messages** - Include actual column names found vs expected

### Short-term Improvements

1. Add a "validation-only" mode that scans all sheets first
2. Return per-sheet validation results before any import
3. Add column header validation with clear error on unknown columns
4. Support both `parameter_id` and `parameter_name` for lookups

### Long-term

1. Consider supporting multiple input file formats with adapters
2. Add import preview showing what will be created/updated
3. Implement undo/rollback for committed imports
