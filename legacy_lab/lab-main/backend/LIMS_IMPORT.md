# LIMS Master Data Import Guide

This guide explains how to import and update the Laboratory Information Management System (LIMS) master data from the Excel file.

## Overview

The LIMS system maintains master data for:
- **Parameters** (Analytes/Test Components) - 1161 parameters
- **Tests** (Individual tests and panels) - 987 tests
- **Test-Parameter Relationships** (Which parameters belong to which tests) - 337 mappings
- **Reference Ranges** (Normal and critical ranges by age, sex, etc.) - 1161 ranges
- **Parameter Quick Texts** (Templates for common comments)

All this master data is maintained in a single Excel file located at:
```
backend/seed_data/AlShifa_LIMS_Master.xlsx
```

## Excel File Structure

The Excel file contains 5 sheets:

1. **Tests** - All available tests (both single tests and panels)
2. **Parameters** - All test parameters/analytes
3. **Test_Parameters** - Relationships between tests and their parameters
4. **Reference_Ranges** - Normal and critical ranges for each parameter
5. **Parameter_Quick_Text** - Quick text templates for common findings

## How to Import Data

### Option 1: Test Import (Dry Run) - Recommended First

To test the import without making any changes to the database:

```bash
docker compose exec backend python manage.py import_lims_master --dry-run
```

This will:
- Read and parse the Excel file
- Validate all data
- Show you what would be imported
- **NOT save anything** to the database

### Option 2: Perform Actual Import

Once you're satisfied with the dry-run results, perform the real import:

```bash
docker compose exec backend python manage.py import_lims_master
```

This will:
- Read the Excel file
- Import/update all master data
- Save changes to the database
- Show a summary of what was imported

### Option 3: Import from a Different File

If you have a different Excel file, specify it with the `--file` option:

```bash
docker compose exec backend python manage.py import_lims_master --file /path/to/your/file.xlsx
```

## Import Behavior

The import command is **idempotent**, which means:
- You can run it multiple times safely
- Existing records are **updated** (not duplicated)
- New records are **created**
- Records are matched by their **code** fields (Test_Code, Parameter_Code)

### What Gets Updated

When you re-run the import:
- If a test/parameter with the same code exists, it will be **updated** with new values
- If a test/parameter doesn't exist, it will be **created**
- Old records are **not deleted** automatically

### Import Order

The command imports data in the correct order to respect database relationships:
1. Parameters first
2. Tests second
3. Reference Ranges third
4. Quick Texts fourth
5. Test-Parameter relationships last

## Expected Output

When the import completes successfully, you'll see a summary like:

```
================================================================================
IMPORT SUMMARY:
  Parameters:       1161 created, 0 updated
  Tests:            987 created, 0 updated
  Reference Ranges: 1161 created, 0 updated
  Quick Texts:      0 created, 0 updated
  Test Parameters:  337 created, 0 updated
================================================================================

Import completed successfully!
```

## Updating Master Data

To update the master data:

1. Edit the Excel file at `backend/seed_data/AlShifa_LIMS_Master.xlsx`
2. Run the import command:
   ```bash
   docker compose exec backend python manage.py import_lims_master
   ```
3. The system will update existing records and create new ones

## Troubleshooting

### File Not Found Error

If you get a "file not found" error:
- Make sure you're running the command from the project root
- Check that the Excel file exists at `backend/seed_data/AlShifa_LIMS_Master.xlsx`
- Try specifying the full path with `--file`

### Import Fails

If the import fails:
- Run with `--dry-run` first to see what the issue is
- Check that the Excel file follows the expected format
- Ensure all required columns are present
- The transaction will automatically roll back on error (no partial imports)

### Missing Tests or Parameters

If you see warnings about missing tests or parameters:
- This means Test_Parameters or Reference_Ranges reference codes that don't exist
- Check the Excel file for typos in the codes
- Make sure the referenced tests/parameters are present in their respective sheets

## Data Verification

After import, you can verify the data in the Django admin interface or by querying the database:

```bash
docker compose exec backend python manage.py shell
```

Then in the Python shell:
```python
from catalog.models import Parameter, Test, TestParameter, ReferenceRange

# Count records
print(f"Parameters: {Parameter.objects.count()}")
print(f"Tests: {Test.objects.count()}")
print(f"Test-Parameter mappings: {TestParameter.objects.count()}")
print(f"Reference Ranges: {ReferenceRange.objects.count()}")

# Check a specific panel
test = Test.objects.get(code="LIPID_PROFILE")
print(f"{test.name}: {test.test_parameters.count()} parameters")
```

## Technical Notes

- The command uses **pandas** and **openpyxl** to read Excel files
- All imports are wrapped in a database transaction
- If any error occurs, the entire import is rolled back (all-or-nothing)
- The command handles missing values (NaN) gracefully
- Boolean fields accept "Yes"/"No", "True"/"False", or "1"/"0"

## Support

If you encounter issues:
1. Run with `--dry-run` to diagnose
2. Check the Excel file format matches the expected structure
3. Verify all codes are unique and match between sheets
4. Review the import summary for any warnings or errors
