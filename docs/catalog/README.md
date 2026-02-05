# LIMS Test Catalog Documentation

**Last Updated**: 2026-01-22

This folder contains all documentation related to the LIMS test catalog system, including how to import tests, manage parameters, and configure reference ranges.

## 📁 Folder Structure

```
docs/catalog/
├── README.md                      ← You are here
├── templates/                     ← Excel import templates & guides
│   ├── README.md                  ← Main template guide (START HERE)
│   ├── IMPORT_FORMAT_SPEC.md     ← Detailed Excel format specification
│   ├── PARAMETER_ID_IMPLEMENTATION.md  ← Technical implementation guide
│   ├── PARAMETER_ID_COMPLETION_SUMMARY.md  ← Implementation summary
│   └── PARAMETER_ID_QUICK_START.md  ← Quick start guide
├── EXPECTED_RESULTS.md            ← How test results are generated
└── REFERENCE_RANGES.md            ← How reference ranges work
```

## 🚀 Quick Start

### For Lab Administrators

**Goal**: Import laboratory tests into the system

1. **Download Template**:
   ```bash
   # Via UI: Laboratory > Bulk Import > Download Template
   # Or via API:
   curl -o template.xlsx \
     http://localhost:8000/api/laboratory/bulk-import/download_template/
   ```

2. **Read the Guide**:
   - Open `templates/README.md` for complete instructions
   - See example data in downloaded template

3. **Fill in Your Data**:
   - Parameters: Define all analytes (hemoglobin, glucose, etc.)
   - Tests: Define orderable tests (CBC, LFT, etc.)
   - Mapping: Link parameters to tests
   - Reference Ranges: Define normal value ranges

4. **Import**:
   - Test with dry-run first: `?dry_run=true`
   - Fix any errors
   - Perform actual import

**See**: `templates/README.md` for detailed step-by-step guide

### For Developers

**Goal**: Understand the catalog system implementation

1. **Read Implementation Guide**:
   - `templates/PARAMETER_ID_IMPLEMENTATION.md` - Full technical details
   - `templates/PARAMETER_ID_QUICK_START.md` - Quick reference

2. **Understand Core Concepts**:
   - **Parameters**: Global analytes with unique `parameter_id` (e.g., `p1`, `p2`)
   - **Tests**: Orderable tests that contain multiple parameters
   - **Mappings**: Test-Parameter relationships
   - **Reference Ranges**: Age/gender-specific normal ranges

3. **Key Files**:
   ```
   lims-backend/apps/laboratory/
   ├── models.py           ← Parameter, Test, TestParameter, ReferenceRange
   ├── utils.py            ← import_tests_from_excel(), generate_import_template()
   ├── views.py            ← BulkImportViewSet with dry-run support
   ├── serializers.py      ← Validation logic
   └── management/commands/
       └── verify_catalog_schema.py  ← Verification tool
   ```

## 📚 Documentation Index

### Import & Templates

| Document | Purpose | Audience |
|----------|---------|----------|
| **[templates/README.md](templates/README.md)** | **Main import guide** | Lab admins, developers |
| [templates/IMPORT_FORMAT_SPEC.md](templates/IMPORT_FORMAT_SPEC.md) | Detailed Excel format | Lab admins |
| [templates/PARAMETER_ID_IMPLEMENTATION.md](templates/PARAMETER_ID_IMPLEMENTATION.md) | Technical implementation | Developers |
| [templates/PARAMETER_ID_QUICK_START.md](templates/PARAMETER_ID_QUICK_START.md) | Quick reference | Developers |
| [templates/PARAMETER_ID_COMPLETION_SUMMARY.md](templates/PARAMETER_ID_COMPLETION_SUMMARY.md) | Implementation summary | Project managers |

### System Behavior

| Document | Purpose | Audience |
|----------|---------|----------|
| [EXPECTED_RESULTS.md](EXPECTED_RESULTS.md) | How results are generated | Developers |
| [REFERENCE_RANGES.md](REFERENCE_RANGES.md) | How ranges are selected | Developers |

## 🔑 Key Concepts

### Parameter ID

Every parameter has a unique identifier in format `p<number>`:
- ✅ Valid: `p1`, `p2`, `p53`, `p100`
- ❌ Invalid: `param1`, `1`, `P1x`

**Why?**
- Consistent identification across imports
- Easy to reference in mappings
- Prevents naming conflicts

### Test Structure

A test is composed of multiple parameters:

```
Test: CBC (Complete Blood Count)
├── p1: Hemoglobin
├── p2: White Blood Cells
├── p3: Red Blood Cells
├── p4: Platelet Count
└── p5: Hematocrit
```

### Reference Ranges

Ranges can be age/gender-specific:

```
Hemoglobin (p1):
├── Male, 18-99 years:   13.5-17.5 g/dL
├── Female, 18-99 years: 12.0-16.0 g/dL
└── Both, 0-17 years:    11.0-16.0 g/dL
```

## 🛠️ Common Tasks

### Import New Tests

```bash
# 1. Download template
curl -o template.xlsx http://localhost:8000/api/laboratory/bulk-import/download_template/

# 2. Fill in data using Excel

# 3. Test with dry-run
curl -X POST 'http://localhost:8000/api/laboratory/bulk-import/?dry_run=true' \
  -F 'file=@my_catalog.xlsx'

# 4. If validation passes, do actual import
curl -X POST http://localhost:8000/api/laboratory/bulk-import/ \
  -F 'file=@my_catalog.xlsx'

# 5. Verify
python manage.py verify_catalog_schema
```

### Update Existing Tests

- Same process as import
- System automatically updates if `test_id` or `parameter_id` exists
- Never deletes data

### Verify Catalog Integrity

```bash
python manage.py verify_catalog_schema
```

Checks:
- ✅ Schema is correct
- ✅ All parameter_ids are valid format
- ✅ No missing data
- ✅ Statistics

### Generate Import Template

```bash
# Via management command
python manage.py shell
>>> from apps.laboratory.utils import generate_import_template
>>> wb = generate_import_template()
>>> wb.save('template.xlsx')

# Via API endpoint
curl -o template.xlsx \
  http://localhost:8000/api/laboratory/bulk-import/download_template/
```

## 🔍 Validation

### What Gets Validated

During import, the system checks:

1. **Format**:
   - ✅ parameter_id matches `p<number>` pattern
   - ✅ test_id is numeric
   - ✅ Required fields not empty

2. **Uniqueness**:
   - ✅ No duplicate parameter_ids within file
   - ✅ No duplicate test_ids within file

3. **Cross-References**:
   - ✅ Mapping references existing parameters
   - ✅ Mapping references existing tests
   - ✅ ReferenceRanges references existing mappings

4. **Data Integrity**:
   - ✅ age_min < age_max
   - ✅ reference_min < reference_max
   - ✅ Valid gender values

### Error Messages

All errors include:
- **Sheet name**: Where the error occurred
- **Row number**: Exact row with issue
- **Column name**: Which field is problematic
- **Error message**: What's wrong
- **Example fix**: How to fix it

Example:
```json
{
  "sheet": "Parameters",
  "row": 5,
  "column": "parameter_id",
  "message": "parameter_id must be in format 'p<number>'",
  "example_fix": "Use format like: p1, p2, p53"
}
```

## 🧪 Testing

### Dry-Run Mode

Always use dry-run first:

```bash
curl -X POST \
  'http://localhost:8000/api/laboratory/bulk-import/?dry_run=true' \
  -F 'file=@catalog.xlsx'
```

Benefits:
- ✅ Validates entire file
- ✅ No database changes
- ✅ Shows what would happen
- ✅ Fast feedback

### Verification Command

After import, verify:

```bash
python manage.py verify_catalog_schema
```

### Test Suite

Run automated tests:

```bash
# All parameter validation tests
pytest apps/laboratory/tests/test_parameter_validation.py -v

# All import tests
pytest apps/laboratory/tests/test_utils.py -v

# All laboratory tests
pytest apps/laboratory/tests/ -v
```

## 📖 API Endpoints

### Import

```bash
# Import with validation
POST /api/laboratory/bulk-import/
Content-Type: multipart/form-data
Body: file=@catalog.xlsx

# Dry-run import
POST /api/laboratory/bulk-import/?dry_run=true
Content-Type: multipart/form-data
Body: file=@catalog.xlsx

# Download template
GET /api/laboratory/bulk-import/download_template/
```

### View Data

```bash
# List parameters
GET /api/laboratory/parameters/

# Get specific parameter
GET /api/laboratory/parameters/{parameter_id}/

# List tests
GET /api/laboratory/tests/

# Get specific test
GET /api/laboratory/tests/{test_id}/

# List test parameters (mappings)
GET /api/laboratory/test-parameters/

# List reference ranges
GET /api/laboratory/reference-ranges/
```

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "parameter_id must be in format 'p<number>'" | Change to p1, p2, p53 format |
| "Duplicate parameter_id in file" | Remove duplicate rows |
| "Parameter p999 not found" | Add parameter to Parameters sheet first |
| "Test 999 not found" | Add test to Tests sheet first |
| "Mapping not found" | Add test-parameter mapping to Mapping sheet |

### Get Help

1. Check error message (includes fix suggestion)
2. Read `templates/README.md` (comprehensive guide)
3. Use dry-run to test
4. Run verification command
5. Check test suite

## 📝 Version History

| Version | Date | Major Changes |
|---------|------|---------------|
| 2.0 | 2026-01-22 | Added parameter_id validation, dry-run mode, comprehensive error messages |
| 1.0 | 2025-12-31 | Initial catalog system with Excel import |

## 🗃️ Historical Notes

Historical phase catalog reports were removed during repository cleanup to avoid stale guidance. Use the documents in this folder as the current source of truth.

## 🔗 Related Documentation

- **[API Design](../api/API_DESIGN.md)** - Overall API structure
- **[Data Model](../DATA_MODEL.md)** - Database schema
- **[Architecture](../architecture/ARCHITECTURE.md)** - System architecture

## 👥 Maintainers

This documentation is maintained by the LIMS development team.

For questions or issues:
1. Check this documentation first
2. Review error messages
3. Use dry-run mode
4. Create an issue if needed

---

**Quick Links:**
- 🚀 **[Start Here: Import Template Guide](templates/README.md)**
- 📋 **[Excel Format Specification](templates/IMPORT_FORMAT_SPEC.md)**
- 🔧 **[Technical Implementation](templates/PARAMETER_ID_IMPLEMENTATION.md)**
- ⚡ **[Quick Start for Developers](templates/PARAMETER_ID_QUICK_START.md)**
