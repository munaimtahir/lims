# 📚 Test Catalog Documentation - Quick Reference

**Last Updated**: 2026-01-22

## 🎯 Where to Find What You Need

### 🚀 I Want to Import Laboratory Tests

**Go Here**: [`docs/catalog/templates/README.md`](docs/catalog/templates/README.md)

This comprehensive guide covers everything:
- ✅ How to download the Excel template
- ✅ Excel file format specification
- ✅ Validation rules and requirements
- ✅ Step-by-step import workflow
- ✅ Common errors and how to fix them
- ✅ API reference and examples

**Quick Actions**:
```bash
# Download template
curl -o template.xlsx \
  http://localhost:8000/api/laboratory/bulk-import/download_template/

# Test import (dry-run)
curl -X POST 'http://localhost:8000/api/laboratory/bulk-import/?dry_run=true' \
  -F 'file=@my_catalog.xlsx'

# Actual import
curl -X POST http://localhost:8000/api/laboratory/bulk-import/ \
  -F 'file=@my_catalog.xlsx'

# Verify
python manage.py verify_catalog_schema
```

---

### 🔧 I'm a Developer Working on the Catalog System

**Go Here**: [`docs/catalog/README.md`](docs/catalog/README.md)

Developer documentation hub with:
- ✅ System architecture overview
- ✅ API endpoints reference
- ✅ Common development tasks
- ✅ Testing guide
- ✅ Troubleshooting tips

**Technical Details**: [`docs/catalog/templates/PARAMETER_ID_IMPLEMENTATION.md`](docs/catalog/templates/PARAMETER_ID_IMPLEMENTATION.md)

---

### ⚡ I Need Quick Commands (Cheat Sheet)

**Go Here**: [`docs/catalog/templates/PARAMETER_ID_QUICK_START.md`](docs/catalog/templates/PARAMETER_ID_QUICK_START.md)

Quick reference with:
- ✅ Common commands
- ✅ Excel format examples
- ✅ Verification steps
- ✅ Migration guide

---

### 📖 I Need Detailed Excel Format Specification

**Go Here**: [`docs/catalog/templates/IMPORT_FORMAT_SPEC.md`](docs/catalog/templates/IMPORT_FORMAT_SPEC.md)

Detailed specification of Excel format (4 sheets):
- ✅ Parameters sheet structure
- ✅ Tests sheet structure
- ✅ Mapping sheet structure
- ✅ ReferenceRanges sheet structure

---

### 🔍 I Want to Understand How the System Works

**Core Documentation**:

| Topic | Document | Description |
|-------|----------|-------------|
| **Catalog Overview** | [`docs/catalog/README.md`](docs/catalog/README.md) | Main hub for all catalog docs |
| **Import Templates** | [`docs/catalog/templates/README.md`](docs/catalog/templates/README.md) | Complete import guide |
| **Results System** | [`docs/catalog/EXPECTED_RESULTS.md`](docs/catalog/EXPECTED_RESULTS.md) | How test results are generated |
| **Reference Ranges** | [`docs/catalog/REFERENCE_RANGES.md`](docs/catalog/REFERENCE_RANGES.md) | How ranges are selected and displayed |

---

## 📁 Documentation Structure

```
docs/
└── catalog/                                    ← MAIN CATALOG FOLDER
    ├── README.md                               ← Documentation hub (START HERE for devs)
    │
    ├── templates/                              ← IMPORT TEMPLATES & GUIDES
    │   ├── README.md                           ← Comprehensive import guide (START HERE for imports)
    │   ├── IMPORT_FORMAT_SPEC.md              ← Detailed Excel format specification
    │   ├── PARAMETER_ID_IMPLEMENTATION.md     ← Technical implementation details
    │   ├── PARAMETER_ID_COMPLETION_SUMMARY.md ← Implementation summary
    │   └── PARAMETER_ID_QUICK_START.md        ← Quick reference guide
    │
    ├── EXPECTED_RESULTS.md                     ← How results work
    └── REFERENCE_RANGES.md                     ← How ranges work

archive/
└── test-catalog/                               ← ARCHIVED (OUTDATED)
    ├── README.md                               ← Why these are archived
    ├── TEST_CATALOG_EXPANDED.md               ← Old format (archived)
    └── TEST_CATALOG_GAPS.md                   ← Old issues (archived)
```

---

## 🎓 Learning Paths

### Path 1: Lab Administrator (Non-Technical)

1. Read [`docs/catalog/templates/README.md`](docs/catalog/templates/README.md) sections:
   - Overview
   - Excel Format Guide
   - Import Workflow
   - Common Errors

2. Download template:
   - Via UI: Laboratory > Bulk Import > Download Template
   - Or via API (see quick commands above)

3. Fill in your data following examples

4. Use dry-run to validate

5. Import when validation passes

**Time Required**: 30-60 minutes

---

### Path 2: Developer (Technical)

1. Read [`docs/catalog/README.md`](docs/catalog/README.md) for overview

2. Read [`docs/catalog/templates/PARAMETER_ID_IMPLEMENTATION.md`](docs/catalog/templates/PARAMETER_ID_IMPLEMENTATION.md) for details

3. Review code:
   ```
   lims-backend/apps/laboratory/
   ├── models.py           ← Data models
   ├── utils.py            ← Import logic
   ├── views.py            ← API endpoints
   ├── serializers.py      ← Validation
   └── management/commands/
       └── verify_catalog_schema.py
   ```

4. Run tests:
   ```bash
   pytest apps/laboratory/tests/test_parameter_validation.py -v
   pytest apps/laboratory/tests/test_utils.py -v
   ```

5. Make changes and test locally

**Time Required**: 2-4 hours

---

### Path 3: Quick Task (I just need to do one thing)

1. Check [`docs/catalog/templates/PARAMETER_ID_QUICK_START.md`](docs/catalog/templates/PARAMETER_ID_QUICK_START.md)

2. Find the command you need

3. Run it

**Time Required**: 5 minutes

---

## 🔑 Key Concepts

### Parameter ID
- Format: `p<number>` (e.g., `p1`, `p2`, `p53`)
- Always lowercase
- Unique identifier for each analyte
- Used across all mappings

### Excel Structure
- **4 Sheets**: Parameters, Tests, Mapping, ReferenceRanges
- **Sequential Processing**: Parameters → Tests → Mapping → Ranges
- **Validation**: Comprehensive checks at each step

### Import Modes
- **Dry-Run**: Validate without writing (`?dry_run=true`)
- **Actual Import**: Write to database
- **Upsert Logic**: Update existing, create new

---

## ⚠️ Important Notes

### ✅ CURRENT Documentation (USE THESE)
- Everything in `docs/catalog/`
- Everything in `docs/catalog/templates/`
- All files dated 2026-01-22 or later

### ❌ ARCHIVED Documentation (DON'T USE)
- Everything in `docs/archive/test-catalog/`
- Old parameter structure
- Outdated formats
- Kept for historical reference only

**Rule**: If you find documentation that doesn't mention `parameter_id`, it's outdated!

---

## 🆘 Need Help?

### Common Issues

| Problem | Solution |
|---------|----------|
| "parameter_id format error" | Use `p1`, `p2`, `p53` format |
| "duplicate parameter_id" | Remove duplicates in Excel |
| "parameter not found" | Add to Parameters sheet first |
| "test not found" | Add to Tests sheet first |
| Import fails | Use dry-run to see errors |

### Getting Support

1. **Check Documentation**: Start with [`docs/catalog/templates/README.md`](docs/catalog/templates/README.md)
2. **Review Error Message**: Includes fix suggestions
3. **Use Dry-Run**: Test before importing
4. **Run Verification**: `python manage.py verify_catalog_schema`
5. **Check Tests**: `pytest apps/laboratory/tests/ -v`

---

## 📊 Quick Stats

- **Total Documentation**: 8 files, ~250 pages
- **Main Guide**: 100+ pages
- **Code Coverage**: 22 comprehensive tests
- **Validation Points**: 15+ different checks
- **Error Messages**: Structured with fixes
- **API Endpoints**: 2 (import + download template)

---

## 🔗 Quick Links

| Link | Purpose |
|------|---------|
| **[Main Import Guide](docs/catalog/templates/README.md)** | Complete guide for importing |
| **[Developer Hub](docs/catalog/README.md)** | Developer documentation |
| **[Excel Format Spec](docs/catalog/templates/IMPORT_FORMAT_SPEC.md)** | Detailed Excel format |
| **[Technical Implementation](docs/catalog/templates/PARAMETER_ID_IMPLEMENTATION.md)** | How it works |
| **[Quick Start](docs/catalog/templates/PARAMETER_ID_QUICK_START.md)** | Cheat sheet |

---

## 📅 Version Information

| Version | Date | Status |
|---------|------|--------|
| **2.0** | **2026-01-22** | **CURRENT** ← Use this |
| 1.0 | 2025-12-31 | Archived |

**What Changed in 2.0**:
- ✅ Added parameter_id validation
- ✅ Added dry-run mode
- ✅ Added structured error messages
- ✅ Added verification command
- ✅ Reorganized documentation
- ✅ Created comprehensive guides

---

**Remember**: Always use the documentation in `docs/catalog/` - it's current, comprehensive, and tested!
