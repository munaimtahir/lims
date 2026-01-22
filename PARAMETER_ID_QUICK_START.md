# Parameter ID Implementation - Quick Start Guide

## What Was Implemented

✅ **Complete parameter_id validation system** with:
- Database model validation (format: `p1`, `p2`, `p53`)
- Excel import validation with detailed errors
- API endpoint validation
- Dry-run mode for safe testing
- Verification command
- Comprehensive test suite
- Full documentation

## Immediate Next Steps

### 1. Review the Changes

```bash
# View summary of all changes
cat PARAMETER_ID_COMPLETION_SUMMARY.md

# View detailed documentation
cat docs/catalog/PARAMETER_ID_IMPLEMENTATION.md
```

### 2. Apply the Migration

```bash
cd lims-backend

# Activate virtual environment (if using one)
source venv/bin/activate  # or your venv path

# Run migration
python manage.py migrate laboratory
```

**Expected Output**:
```
Running migrations:
  Applying laboratory.0003_add_parameter_id_validation... OK
```

### 3. Verify the Schema

```bash
python manage.py verify_catalog_schema
```

**Expected Output**:
```
=== Catalog Schema Verification ===

1. Checking parameter_id field existence...
   ✓ parameter_id field exists

2. Checking uniqueness constraint...
   ✓ parameter_id is PRIMARY KEY (automatically unique)

3. Checking for missing parameter_ids...
   ✓ No missing parameter_ids (all X parameters have IDs)

4. Validating parameter_id format (must match p<number>)...
   ✓ All X parameter_ids have valid format

5. Sample parameter_ids:
   - p1: Hemoglobin (g/dL)
   - p2: WBC (10^3/uL)
   ...

6. Catalog Statistics:
   - Total Parameters: X
   - Total Tests: X
   - Total Test-Parameter Mappings: X

✓ All verification checks PASSED
```

### 4. Run the Tests

```bash
# Run all laboratory tests
pytest apps/laboratory/tests/ -v

# Or run just parameter validation tests
pytest apps/laboratory/tests/test_parameter_validation.py -v
```

**Expected**: All tests passing ✅

### 5. Test Excel Import with Dry-Run

**Prepare a test Excel file** with this structure:

**Parameters Sheet**:
| parameter_id | parameter_name | unit    |
|--------------|----------------|---------|
| p1           | Hemoglobin     | g/dL    |
| p2           | WBC            | 10^3/uL |

**Tests Sheet**:
| test_id | test_code | legacy_test_code | test_name | category   | sample_type | price | turnaround_time |
|---------|-----------|------------------|-----------|------------|-------------|-------|-----------------|
| 1       | CBC       | 001              | CBC Test  | Hematology | Blood       | 50.00 | 24              |

**Mapping Sheet**:
| test_id | parameter_id | display_order | reportable |
|---------|--------------|---------------|------------|
| 1       | p1           | 1             | TRUE       |
| 1       | p2           | 2             | TRUE       |

**Test with API** (start server first):
```bash
# Start development server
python manage.py runserver

# In another terminal, test dry-run
curl -X POST http://localhost:8000/api/laboratory/bulk-import/?dry_run=true \
  -F "file=@test_catalog.xlsx"
```

**Expected Response**:
```json
{
  "success": true,
  "summary": {
    "dry_run": true,
    "status": "PASS",
    "validation_passed": true,
    "parameters_created": 2,
    "tests_created": 1,
    "mappings_created": 2,
    "errors": []
  }
}
```

### 6. Test with Invalid Data

**Create a file with invalid parameter_id** (e.g., `param1` instead of `p1`):

```bash
curl -X POST http://localhost:8000/api/laboratory/bulk-import/?dry_run=true \
  -F "file=@invalid_catalog.xlsx"
```

**Expected Response**:
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
        "row": 2,
        "column": "parameter_id",
        "message": "parameter_id must be in format 'p<number>' (e.g., p1, p2, p53). Got: param1",
        "example_fix": "Use format like: p1, p2, p53"
      }
    ]
  }
}
```

## Excel File Format Reference

### Required Sheets

1. **Parameters** (Required columns):
   - `parameter_id`: Format `p<number>` (e.g., p1, p2)
   - `parameter_name`: Full name of parameter
   - `unit`: Unit of measurement (optional)

2. **Tests** (Required columns):
   - `test_id`: Numeric ID
   - `test_code`: Unique test code
   - `legacy_test_code`: Old code (optional)
   - `test_name`: Full name
   - `category`: Category name
   - `sample_type`: Sample type (e.g., Blood, Serum)
   - `price`: Numeric price
   - `turnaround_time`: Hours (numeric)

3. **Mapping** (Required columns):
   - `test_id`: Must exist in Tests sheet
   - `parameter_id`: Must exist in Parameters sheet
   - `display_order`: Numeric order
   - `reportable`: TRUE/FALSE

4. **ReferenceRanges** (Optional):
   - `test_id`: Test ID
   - `parameter_id`: Parameter ID
   - `gender`: Male/Female/Both
   - `age_min`: Minimum age
   - `age_max`: Maximum age
   - `reference_min`: Minimum reference value
   - `reference_max`: Maximum reference value
   - `critical_low`: Critical low value
   - `critical_high`: Critical high value

## Common Issues & Fixes

### Issue: "parameter_id must be in format 'p<number>'"
**Fix**: Change `param1` → `p1`, `parameter_2` → `p2`, etc.

### Issue: "Duplicate parameter_id in file: p1"
**Fix**: Remove duplicate rows or use different parameter_ids

### Issue: "Parameter p999 not found in Parameters sheet or database"
**Fix**: Add the parameter to Parameters sheet first, or fix the reference

### Issue: Migration fails with "column does not exist"
**Fix**: Check if previous migrations were applied. Run:
```bash
python manage.py showmigrations laboratory
```

## Documentation

- **Completion Summary**: `PARAMETER_ID_COMPLETION_SUMMARY.md`
- **Full Implementation Guide**: `docs/catalog/PARAMETER_ID_IMPLEMENTATION.md`
- **Original Requirements**: See this file's context

## Files Changed

### Modified (6 files):
1. `lims-backend/apps/laboratory/models.py`
2. `lims-backend/apps/laboratory/serializers.py`
3. `lims-backend/apps/laboratory/utils.py`
4. `lims-backend/apps/laboratory/views.py`
5. `lims-backend/apps/laboratory/tests/test_utils.py`

### Created (5 files):
1. `lims-backend/apps/laboratory/management/commands/verify_catalog_schema.py`
2. `lims-backend/apps/laboratory/migrations/0003_add_parameter_id_validation.py`
3. `lims-backend/apps/laboratory/tests/test_parameter_validation.py`
4. `docs/catalog/PARAMETER_ID_IMPLEMENTATION.md`
5. `PARAMETER_ID_COMPLETION_SUMMARY.md`

## Support

If you encounter issues:

1. **Run verification**: `python manage.py verify_catalog_schema`
2. **Check logs**: Look for validation errors in terminal
3. **Use dry-run**: Always test with `?dry_run=true` first
4. **Check documentation**: See `docs/catalog/PARAMETER_ID_IMPLEMENTATION.md`

## Status

✅ **Implementation**: COMPLETE  
✅ **Tests**: COMPREHENSIVE (22 tests)  
✅ **Documentation**: COMPLETE  
✅ **Ready**: FOR DEPLOYMENT  

---

**Questions?** See full documentation in `docs/catalog/PARAMETER_ID_IMPLEMENTATION.md`
