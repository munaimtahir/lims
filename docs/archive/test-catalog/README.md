# Archived Test Catalog Documentation

**Archive Date**: 2026-01-22  
**Reason**: Outdated structure and format

This folder contains historical documentation that is no longer valid for current development.

## ⚠️ Important Notice

**DO NOT USE THESE DOCUMENTS FOR CURRENT DEVELOPMENT**

These files are kept for historical reference only. They document:
- Old catalog structure (before parameter_id implementation)
- Phase 0 diagnosis of issues that have since been fixed
- Outdated Excel import formats

## 📁 Archived Files

### TEST_CATALOG_EXPANDED.md
**Original Purpose**: Comprehensive list of all laboratory tests for Category B lab

**Why Archived**:
- ❌ Uses old structure without `parameter_id` field
- ❌ Parameters defined per-test instead of globally
- ❌ Doesn't follow current Excel import format
- ❌ Missing validation rules

**Replacement**: Use current Excel template from `docs/catalog/templates/`

---

### TEST_CATALOG_GAPS.md
**Original Purpose**: Phase 0 diagnosis of catalog system issues

**Why Archived**:
- ✅ All identified issues have been fixed
- ✅ ReferenceRange system now works correctly
- ✅ Result entry no longer shows blank
- ✅ Expected results service implemented

**Replacement**: System now working as designed

---

## 🔄 Migration Path

If you need to reference information from these documents:

### From TEST_CATALOG_EXPANDED.md

**Old Structure** (archived):
```
Test: CBC
├── Hemoglobin (parameter defined in test)
├── WBC (parameter defined in test)
└── Platelet (parameter defined in test)
```

**New Structure** (current):
```
Parameters Sheet:
| parameter_id | parameter_name | unit  |
|--------------|----------------|-------|
| p1           | Hemoglobin     | g/dL  |
| p2           | WBC            | 10³/µL|
| p3           | Platelet       | 10³/µL|

Tests Sheet:
| test_id | test_code | test_name | ... |
|---------|-----------|-----------|-----|
| 1       | CBC       | Complete Blood Count | ... |

Mapping Sheet:
| test_id | parameter_id | display_order | ... |
|---------|--------------|---------------|-----|
| 1       | p1           | 1             | ... |
| 1       | p2           | 2             | ... |
| 1       | p3           | 3             | ... |
```

**How to Migrate**:
1. Extract all unique parameters from old file
2. Assign sequential parameter_ids (p1, p2, p3, ...)
3. Create Parameters sheet with parameter_id
4. Create Tests sheet with test_id
5. Create Mapping sheet linking tests to parameters
6. Use current import template format

### From TEST_CATALOG_GAPS.md

All issues mentioned in this document have been resolved:

| Old Issue | Status | Solution |
|-----------|--------|----------|
| ReferenceRange not used | ✅ Fixed | Unified range selector implemented |
| Result entry can be blank | ✅ Fixed | Expected results service added |
| Inconsistent range logic | ✅ Fixed | Single source of truth for ranges |

---

## 📚 Current Documentation

**For current, valid documentation, see:**

- **[docs/catalog/README.md](../../catalog/README.md)** - Main catalog documentation
- **[docs/catalog/templates/README.md](../../catalog/templates/README.md)** - Import template guide
- **[docs/catalog/templates/IMPORT_FORMAT_SPEC.md](../../catalog/templates/IMPORT_FORMAT_SPEC.md)** - Excel format spec
- **[docs/catalog/templates/PARAMETER_ID_IMPLEMENTATION.md](../../catalog/templates/PARAMETER_ID_IMPLEMENTATION.md)** - Technical guide

---

## 📅 Timeline

| Date | Event |
|------|-------|
| 2025-12-31 | Initial catalog system implemented |
| 2025-12-31 | TEST_CATALOG_EXPANDED.md created (old structure) |
| 2025-12-31 | TEST_CATALOG_GAPS.md documented issues |
| 2026-01-22 | parameter_id validation implemented |
| 2026-01-22 | All gaps fixed, system working correctly |
| 2026-01-22 | Old docs archived, new templates created |

---

## 🔍 Why Keep These Files?

These files are preserved for:
1. **Historical Reference**: Understanding how the system evolved
2. **Migration Support**: Helping migrate old Excel files to new format
3. **Audit Trail**: Documenting what issues existed and how they were fixed
4. **Learning**: Understanding design decisions and trade-offs

---

## ⚠️ Warning

**Do not copy content from these files into current code or documentation.**

If you need similar information:
1. Check current documentation first
2. Use current Excel template format
3. Follow current validation rules
4. Reference `docs/catalog/templates/` for examples

---

**Questions?**

See current documentation at:
- 📖 **[docs/catalog/templates/README.md](../../catalog/templates/README.md)**
- 🚀 **[docs/catalog/README.md](../../catalog/README.md)**
