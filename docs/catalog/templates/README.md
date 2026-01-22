# LIMS Test Catalog Import Templates

**Current as of**: 2026-01-22  
**Version**: 2.0 (with `parameter_id` validation)

This folder contains the official Excel import templates and documentation for managing the LIMS test catalog.

## 📋 Quick Links

- **[Excel Format Guide](#excel-format-guide)** - Complete specification
- **[Download Template](#download-template)** - Get started quickly
- **[Validation Rules](#validation-rules)** - What's checked during import
- **[Common Errors](#common-errors-and-fixes)** - Troubleshooting guide

---

## Overview

The LIMS system uses **Excel workbooks** to bulk import and update:
- **Tests** (orderable laboratory tests)
- **Parameters** (individual measurements/analytes)
- **Mappings** (which parameters belong to which tests)
- **Reference Ranges** (age/gender-specific normal ranges)

## Download Template

### Via Web UI
1. Navigate to: `Laboratory > Bulk Import`
2. Click **"Download Template"** button
3. Saves as: `LIMS_Import_Template.xlsx`

### Via API
```bash
curl -o template.xlsx \
  http://localhost:8000/api/laboratory/bulk-import/download_template/
```

### Via Management Command
```bash
python manage.py shell
>>> from apps.laboratory.utils import generate_import_template
>>> wb = generate_import_template()
>>> wb.save('template.xlsx')
```

---

## Excel Format Guide

The Excel file **must** contain the following sheets in this structure:

### Required Sheets

1. **[Parameters](#1-parameters-sheet)** - Define all measurable analytes
2. **[Tests](#2-tests-sheet)** - Define orderable tests
3. **[Mapping](#3-mapping-sheet)** - Link parameters to tests
4. **[ReferenceRanges](#4-referencerages-sheet)** - Define normal value ranges (optional)

---

### 1. Parameters Sheet

Defines the global list of all measurable analytes (hemoglobin, glucose, etc.).

**Column Structure:**

| Column | Name | Type | Required | Format | Example |
|--------|------|------|----------|---------|---------|
| A | `parameter_id` | String | **YES** | `p<number>` | `p1`, `p2`, `p53` |
| B | `parameter_name` | String | **YES** | Any text | "Hemoglobin", "WBC" |
| C | `unit` | String | No | Any text | "g/dL", "10³/µL" |

**Validation Rules:**
- ✅ `parameter_id` MUST match format: `p<number>` (lowercase)
- ✅ `parameter_id` MUST be unique within file
- ✅ `parameter_name` cannot be empty
- ✅ Uppercase IDs automatically converted to lowercase (`P1` → `p1`)

**Example:**

```
| parameter_id | parameter_name          | unit    |
|--------------|-------------------------|---------|
| p1           | Hemoglobin              | g/dL    |
| p2           | White Blood Cells       | 10³/µL  |
| p3           | Platelet Count          | 10³/µL  |
| p53          | Fasting Blood Glucose   | mg/dL   |
```

---

### 2. Tests Sheet

Defines orderable tests that can be requested.

**Column Structure:**

| Column | Name | Type | Required | Example |
|--------|------|------|----------|---------|
| A | `test_id` | Integer | **YES** | `1`, `100` |
| B | `test_code` | String | **YES** | "CBC", "FBS" |
| C | `legacy_test_code` | String | No | "OLD-001" |
| D | `test_name` | String | **YES** | "Complete Blood Count" |
| E | `category` | String | **YES** | "Hematology" |
| F | `sample_type` | String | No (default: "Serum") | "EDTA Blood" |
| G | `price` | Decimal | No | `500.00` |
| H | `turnaround_time` | Integer | No (default: 24) | `24` (hours) |

**Validation Rules:**
- ✅ `test_id` must be a unique number
- ✅ `test_code` must be unique
- ✅ `test_name` cannot be empty
- ✅ `category` will be created if it doesn't exist

**Example:**

```
| test_id | test_code | legacy_test_code | test_name               | category   | sample_type | price  | turnaround_time |
|---------|-----------|------------------|------------------------|------------|-------------|--------|-----------------|
| 1       | CBC       | 1001             | Complete Blood Count   | Hematology | EDTA Blood  | 500.00 | 24              |
| 2       | FBS       | 2001             | Fasting Blood Sugar    | Chemistry  | Serum       | 200.00 | 2               |
```

---

### 3. Mapping Sheet

Links parameters to tests (defines which measurements are included in each test).

**Column Structure:**

| Column | Name | Type | Required | Example |
|--------|------|------|----------|---------|
| A | `test_id` | Integer | **YES** | `1` |
| B | `parameter_id` | String | **YES** | `p1` |
| C | `display_order` | Integer | No (default: 0) | `1`, `2`, `3` |
| D | `reportable` | Boolean | No (default: TRUE) | `TRUE`, `FALSE` |

**Validation Rules:**
- ✅ `test_id` must exist in Tests sheet
- ✅ `parameter_id` must exist in Parameters sheet
- ✅ `parameter_id` format validated (`p<number>`)
- ✅ Each test-parameter pair must be unique

**Example:**

```
| test_id | parameter_id | display_order | reportable |
|---------|--------------|---------------|------------|
| 1       | p1           | 1             | TRUE       |
| 1       | p2           | 2             | TRUE       |
| 1       | p3           | 3             | TRUE       |
| 2       | p53          | 1             | TRUE       |
```

---

### 4. ReferenceRanges Sheet

Defines age and gender-specific normal value ranges (optional but recommended).

**Column Structure:**

| Column | Name | Type | Required | Example |
|--------|------|------|----------|---------|
| A | `test_id` | Integer | **YES** | `1` |
| B | `parameter_id` | String | **YES** | `p1` |
| C | `gender` | String | No (default: "Both") | "Male", "Female", "Both" |
| D | `age_min` | Integer | No | `18` |
| E | `age_max` | Integer | No | `65` |
| F | `reference_min` | Decimal | No | `12.0` |
| G | `reference_max` | Decimal | No | `16.0` |
| H | `critical_low` | Decimal | No | `7.0` |
| I | `critical_high` | Decimal | No | `20.0` |

**Validation Rules:**
- ✅ Test-parameter mapping must exist in Mapping sheet
- ✅ `gender` must be: "Male", "Female", or "Both"
- ✅ `age_min` must be less than `age_max` (if both provided)
- ✅ `reference_min` must be less than `reference_max` (if both provided)

**Example:**

```
| test_id | parameter_id | gender | age_min | age_max | reference_min | reference_max | critical_low | critical_high |
|---------|--------------|--------|---------|---------|---------------|---------------|--------------|---------------|
| 1       | p1           | Male   | 18      | 99      | 13.5          | 17.5          | 7.0          | 20.0          |
| 1       | p1           | Female | 18      | 99      | 12.0          | 16.0          | 7.0          | 20.0          |
| 1       | p2           | Both   | 0       | 999     | 4.0           | 11.0          | 1.0          | 30.0          |
```

---

## Validation Rules

### Parameter ID Format

| Example | Valid? | Reason |
|---------|--------|--------|
| `p1` | ✅ | Correct format |
| `p2` | ✅ | Correct format |
| `p53` | ✅ | Correct format |
| `P1` | ✅ | Valid (converted to `p1`) |
| `param1` | ❌ | Wrong prefix (must be 'p') |
| `1` | ❌ | Missing 'p' prefix |
| `p` | ❌ | Missing number |
| `p1x` | ❌ | Letters after number |
| `` | ❌ | Empty string |

### Cross-Reference Validation

The system validates relationships between sheets:

1. **Mapping → Parameters**: All `parameter_id` in Mapping must exist in Parameters sheet
2. **Mapping → Tests**: All `test_id` in Mapping must exist in Tests sheet
3. **ReferenceRanges → Mapping**: All test-parameter combinations must exist in Mapping

---

## Import Workflow

### 1. Dry-Run (Recommended First Step)

Always test your import first without writing to the database:

**Via UI:**
1. Navigate to: `Laboratory > Bulk Import`
2. Upload Excel file
3. Check **"Dry Run"** checkbox
4. Click **"Upload"**
5. Review validation results

**Via API:**
```bash
curl -X POST \
  'http://localhost:8000/api/laboratory/bulk-import/?dry_run=true' \
  -F 'file=@my_catalog.xlsx'
```

**Response (Success):**
```json
{
  "success": true,
  "summary": {
    "dry_run": true,
    "status": "PASS",
    "validation_passed": true,
    "parameters_created": 5,
    "tests_created": 2,
    "mappings_created": 8,
    "ranges_created": 16,
    "errors": []
  }
}
```

**Response (Errors Found):**
```json
{
  "success": false,
  "summary": {
    "dry_run": true,
    "status": "FAIL",
    "validation_passed": false,
    "errors": [
      {
        "sheet": "Parameters",
        "row": 3,
        "column": "parameter_id",
        "message": "parameter_id must be in format 'p<number>' (e.g., p1, p2, p53). Got: param1",
        "example_fix": "Use format like: p1, p2, p53"
      }
    ]
  }
}
```

### 2. Fix Errors

Review error messages and fix issues in Excel file:
- Check **sheet** name
- Navigate to **row** number
- Fix **column** value
- Follow **example_fix** guidance

### 3. Actual Import

Once dry-run passes, perform the actual import:

**Via UI:**
1. Upload Excel file (without "Dry Run" checked)
2. Click **"Upload"**
3. Wait for confirmation

**Via API:**
```bash
curl -X POST \
  http://localhost:8000/api/laboratory/bulk-import/ \
  -F 'file=@my_catalog.xlsx'
```

### 4. Verify

After import, verify the data:

```bash
# Run verification command
python manage.py verify_catalog_schema

# Expected output:
# ✓ All verification checks PASSED
```

---

## Common Errors and Fixes

### Error: "parameter_id must be in format 'p<number>'"

**Cause**: Invalid parameter_id format

**Examples of Invalid IDs:**
- `param1` ❌ (wrong prefix)
- `1` ❌ (missing 'p')
- `p1x` ❌ (letters after number)

**Fix:** Use format `p<number>`:
- `param1` → `p1` ✅
- `1` → `p1` ✅
- `p1x` → `p1` ✅

---

### Error: "Duplicate parameter_id in file: p1"

**Cause**: Same parameter_id appears multiple times in Parameters sheet

**Fix:** Remove duplicate rows or use different parameter_ids

---

### Error: "Parameter p999 not found in Parameters sheet or database"

**Cause**: Mapping sheet references a parameter_id that doesn't exist

**Fix:** Either:
1. Add `p999` to Parameters sheet, OR
2. Change the reference in Mapping sheet to an existing parameter_id

---

### Error: "Test 999 not found in Tests sheet or database"

**Cause**: Mapping or ReferenceRanges sheet references a test_id that doesn't exist

**Fix:** Either:
1. Add test with `test_id=999` to Tests sheet, OR
2. Change the reference to an existing test_id

---

### Error: "Mapping for Test 1 and Parameter p1 not found"

**Cause**: ReferenceRanges sheet references a test-parameter combination that doesn't exist in Mapping

**Fix:** Add the test-parameter mapping to Mapping sheet first

---

## Update vs. Create Behavior

### Parameters
- **If `parameter_id` exists**: Updates the existing parameter (name, unit)
- **If `parameter_id` is new**: Creates new parameter

### Tests
- **If `test_id` exists**: Updates the existing test
- **If `test_id` is new**: Creates new test

### Mappings
- **If test-parameter pair exists**: No change
- **If test-parameter pair is new**: Creates new mapping

### Reference Ranges
- **Always updates or creates**: Based on test_id, parameter_id, gender, age_min, age_max

---

## Best Practices

### 1. Start Small
- Import a few tests first
- Validate they appear correctly
- Then import full catalog

### 2. Use Dry-Run
- Always test with `?dry_run=true` first
- Fix all errors before actual import
- Prevents database pollution

### 3. Consistent Naming
- Use clear parameter names: "Hemoglobin" not "HGB"
- Use standard units: "g/dL" not "gm/dl"
- Use consistent test codes: "CBC" not "cbc"

### 4. Sequential IDs
- Use sequential parameter_ids: p1, p2, p3, ...
- Use sequential test_ids: 1, 2, 3, ...
- Makes tracking and debugging easier

### 5. Version Control
- Keep Excel templates in version control
- Document changes in commit messages
- Tag stable versions

### 6. Backup Before Import
- Export existing data before major updates
- Keep backups of working Excel files
- Test imports on staging first

---

## Advanced Features

### Upsert Behavior

The import uses "upsert" logic:
- **Existing records**: Updated with new data
- **New records**: Created
- **Missing from Excel**: Not deleted (preserved)

### Case Normalization

All `parameter_id` values are automatically normalized to lowercase:
- `P1` → `p1`
- `P53` → `p53`
- `p100` → `p100`

### Partial Imports

You can import only specific sheets:
- **Parameters only**: Just populate Parameters sheet
- **Tests only**: Just populate Tests sheet
- **Mixed**: Any combination of sheets

---

## Verification Tools

### 1. Schema Verification

```bash
python manage.py verify_catalog_schema
```

Checks:
- ✅ parameter_id field exists
- ✅ Uniqueness constraint in place
- ✅ No missing parameter_ids
- ✅ All parameter_ids match format
- ✅ Shows sample data
- ✅ Displays statistics

### 2. API Verification

```bash
# List all parameters
curl http://localhost:8000/api/laboratory/parameters/

# Get specific parameter
curl http://localhost:8000/api/laboratory/parameters/p1/

# List all tests
curl http://localhost:8000/api/laboratory/tests/
```

### 3. Database Queries

```python
from apps.laboratory.models import Parameter, Test, TestParameter

# Count parameters
Parameter.objects.count()

# List all parameter_ids
list(Parameter.objects.values_list('parameter_id', flat=True))

# Check for invalid formats
for p in Parameter.objects.all():
    if not p.parameter_id.startswith('p') or not p.parameter_id[1:].isdigit():
        print(f"Invalid: {p.parameter_id}")
```

---

## Migration from Old Format

If you have Excel files from before 2026-01-22:

### Old Format (OUTDATED):
```
Parameters Sheet:
| TestCode | Name       | Unit  |
|----------|------------|-------|
| CBC      | Hemoglobin | g/dL  |
```

### New Format (CURRENT):
```
Parameters Sheet:
| parameter_id | parameter_name | unit  |
|--------------|----------------|-------|
| p1           | Hemoglobin     | g/dL  |

Tests Sheet:
| test_id | test_code | ... |
|---------|-----------|-----|
| 1       | CBC       | ... |

Mapping Sheet:
| test_id | parameter_id | ... |
|---------|--------------|-----|
| 1       | p1           | ... |
```

**Migration Steps:**
1. Extract all unique parameters from old file
2. Assign parameter_ids (p1, p2, p3, ...)
3. Create new Parameters sheet with parameter_id
4. Create new Tests sheet with test_id
5. Create new Mapping sheet linking tests to parameters
6. Test with dry-run
7. Import

---

## Related Documentation

- **[PARAMETER_ID_IMPLEMENTATION.md](../PARAMETER_ID_IMPLEMENTATION.md)** - Full technical implementation
- **[EXPECTED_RESULTS.md](../EXPECTED_RESULTS.md)** - How results are generated
- **[REFERENCE_RANGES.md](../REFERENCE_RANGES.md)** - How ranges are selected

---

## Support

### Get Help

1. **Check Error Message**: Most errors include fix suggestions
2. **Review This Guide**: Search for error message
3. **Use Dry-Run**: Validate before importing
4. **Run Verification**: `python manage.py verify_catalog_schema`

### Report Issues

If you find bugs or have suggestions:
1. Check existing issues in repository
2. Provide sample Excel file (anonymized)
3. Include error messages
4. Describe expected vs actual behavior

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-01-22 | Added parameter_id validation, dry-run mode, comprehensive error messages |
| 1.0 | 2025-12-31 | Initial Excel import format |

---

**Last Updated**: 2026-01-22  
**Maintained By**: LIMS Development Team
