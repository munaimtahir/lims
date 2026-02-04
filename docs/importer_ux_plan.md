# LIMS Catalog Importer - Phase D UX Improvement Plan

**Date:** 2026-02-05  
**Status:** Recommendation for implementation

---

## Executive Summary

After auditing the import engine and fixing the core parsing issues (Phase C), this document outlines the recommended UX improvements to make the catalog import process more user-friendly and reliable.

---

## Chosen Approach: Option 1 - Enhanced Single XLSX Upload

### Why This Approach?

| Criterion | Option 1: Enhanced Single Upload | Option 2: Sheet-wise Upload |
|-----------|----------------------------------|----------------------------|
| User Friction | Low - one upload action | High - 6 separate uploads |
| Error Recovery | Fix all, retry once | Fix one, upload, repeat |
| Consistency | All-or-nothing transaction | Partial state possible |
| Implementation | Moderate changes | Significant changes |
| Backward Compatible | ✅ Yes | ⚠️ New workflow |

**Recommendation:** Option 1 is lower risk and provides better UX without fragmenting the workflow.

---

## User Workflow (After Improvements)

### Step 1: Upload File

User uploads their XLSX file. The system immediately validates:

```
┌──────────────────────────────────────────────────────────────┐
│  📁 Upload Catalog File                                       │
│  ────────────────────────────────────────────────────────────│
│                                                              │
│  [Drop file here or click to browse]                         │
│                                                              │
│  Supported format: .xlsx with sheets:                        │
│  Tests, Parameters, Mapping, ReferenceRanges, Panels*        │
│                                                              │
│  * Panels and PanelTests are optional                        │
│                                                              │
│  [Download Template]                                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 2: Validation Preview

System runs dry-run validation and shows per-sheet results:

```
┌──────────────────────────────────────────────────────────────┐
│  📊 Validation Results                                        │
│  ────────────────────────────────────────────────────────────│
│                                                              │
│  Sheet          Status      Create  Update  Unchanged        │
│  ─────────────────────────────────────────────────────────   │
│  ✅ Tests        Valid       678     0       0               │
│  ✅ Parameters   Valid        53     0       0               │
│  ✅ Mapping      Valid       301     0       0               │
│  ⚠️ ReferenceRanges Warnings  0     0       0  (empty sheet)│
│  ➖ Panels       Not Found   -       -       -               │
│  ➖ PanelTests   Not Found   -       -       -               │
│                                                              │
│  [Expand to see warnings]                                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Warnings (2)                                           │  │
│  │ • ReferenceRanges: Sheet is empty (no data rows)      │  │
│  │ • Tests: Unrecognized column 'department' (ignored)   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│           [Cancel]         [Import 1,032 records]            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 3: Error Details (if validation fails)

If there are errors, show expandable per-sheet error table:

```
┌──────────────────────────────────────────────────────────────┐
│  ❌ Validation Failed                                         │
│  ────────────────────────────────────────────────────────────│
│                                                              │
│  Sheet          Status      Errors                           │
│  ─────────────────────────────────────────────────────────   │
│  ❌ Tests        Errors      678                             │
│  ✅ Parameters   Valid       0                               │
│  ⏸️ Mapping      Blocked     -  (depends on Tests)          │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│  ▼ Tests Errors (showing 10 of 678)                          │
│  ─────────────────────────────────────────────────────────   │
│  Row   Column           Issue                                │
│  2     turnaround_time  Missing required value               │
│  3     turnaround_time  Missing required value               │
│  4     turnaround_time  Missing required value               │
│  ...                                                         │
│                                                              │
│  [Download Error Report (CSV)]                               │
│                                                              │
│  ─────────────────────────────────────────────────────────   │
│  💡 Tip: Your file uses 'tat_hours' which is empty.          │
│     Fill in the turnaround_time column and re-upload.        │
│  ─────────────────────────────────────────────────────────   │
│                                                              │
│           [Cancel]         [Import Anyway (not recommended)] │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Step 4: Import Confirmation

After successful import:

```
┌──────────────────────────────────────────────────────────────┐
│  ✅ Import Successful                                         │
│  ────────────────────────────────────────────────────────────│
│                                                              │
│  Summary:                                                    │
│  • 678 tests created                                         │
│  • 53 parameters created                                     │
│  • 301 mappings created                                      │
│  • 0 reference ranges created                                │
│                                                              │
│  Import Job ID: #1234                                        │
│                                                              │
│           [View Catalog]         [Import Another]            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Backend Changes Required

### 1. New Query Parameter: `validation_only`

```python
# In BulkImportViewSet.create()
validation_only = parse_bool(request.query_params.get("validation_only"), False)

if validation_only:
    # Run dry-run and return structured validation results
    # Do NOT create CatalogImportJob record
    return Response({
        "validation": True,
        "sheets": {
            "Tests": {"status": "valid", "counts": {...}, "errors": []},
            "Parameters": {"status": "valid", "counts": {...}, "errors": []},
            ...
        },
        "summary": {...},
    })
```

### 2. Per-Sheet Error Grouping

```python
# Group errors by sheet for easier UI display
errors_by_sheet = {}
for error in errors:
    sheet = error["sheet"]
    if sheet not in errors_by_sheet:
        errors_by_sheet[sheet] = []
    errors_by_sheet[sheet].append(error)

return {
    "errors": errors,
    "errors_by_sheet": errors_by_sheet,
    ...
}
```

### 3. Sheet Detection in Response

```python
# Add sheet detection information
sheets_found = set(workbook.sheetnames)
sheets_expected = set(SHEET_ORDER)

return {
    "sheets_found": list(sheets_found),
    "sheets_missing": list(sheets_expected - sheets_found),
    "sheets_extra": list(sheets_found - sheets_expected),
    ...
}
```

### 4. Smart Error Messages

When a column is missing but an alias exists:

```python
if field not in headers:
    # Check if there's an alias that exists
    for alias, canonical in COLUMN_ALIASES.items():
        if canonical == field and alias in headers:
            # Found alias but value is empty
            message = f"Column '{alias}' found but value is empty"
            break
    else:
        # Check what columns we do have
        message = f"Column '{field}' not found. Available: {', '.join(headers.keys())}"
```

---

## Frontend Changes Required

### 1. New `CatalogUploadWizard` Component

```typescript
// frontend/src/components/catalog/CatalogUploadWizard.tsx

interface UploadStep {
  file: File | null;
  validationResult: ValidationResult | null;
  importResult: ImportResult | null;
}

const CatalogUploadWizard: React.FC = () => {
  const [step, setStep] = useState<'upload' | 'validate' | 'confirm' | 'done'>('upload');
  const [data, setData] = useState<UploadStep>({...});
  
  // Step 1: File upload
  // Step 2: Validation (dry-run) with progress
  // Step 3: Confirmation dialog
  // Step 4: Success/Error display
};
```

### 2. Error Table Component

```typescript
// frontend/src/components/catalog/ImportErrorTable.tsx

interface ImportError {
  sheet: string;
  row: number;
  field: string;
  message: string;
}

const ImportErrorTable: React.FC<{ errors: ImportError[] }> = ({ errors }) => {
  // Paginated, sortable, filterable error table
  // Download as CSV button
};
```

### 3. Sheet Status Cards

```typescript
// frontend/src/components/catalog/SheetStatusCard.tsx

interface SheetStatus {
  name: string;
  status: 'valid' | 'warnings' | 'errors' | 'missing' | 'blocked';
  counts: { created: number; updated: number; unchanged: number };
  errors: ImportError[];
}

const SheetStatusCard: React.FC<{ sheet: SheetStatus }> = ({ sheet }) => {
  // Collapsible card showing sheet status and errors
};
```

---

## Implementation Phases

### Phase 1: Backend Enhancements (1-2 days)

- [x] Add column aliases (DONE in Phase C)
- [x] Add null value handling (DONE in Phase C)
- [x] Fix Decimal serialization (DONE in Phase C)
- [ ] Add `validation_only` mode
- [ ] Add `errors_by_sheet` grouping
- [ ] Add sheet detection info
- [ ] Add smart error messages

### Phase 2: API Contract Update (0.5 days)

- [ ] Update API documentation
- [ ] Add OpenAPI/Swagger annotations
- [ ] Update TypeScript types in frontend

### Phase 3: Frontend UI (2-3 days)

- [ ] Create `CatalogUploadWizard` component
- [ ] Create `SheetStatusCard` component
- [ ] Create `ImportErrorTable` component
- [ ] Add CSV error export functionality
- [ ] Add progress indicators
- [ ] Integrate with existing TestCatalogPage

### Phase 4: Testing & Polish (1 day)

- [ ] End-to-end tests for upload workflow
- [ ] Error state testing
- [ ] Mobile responsiveness
- [ ] Accessibility audit

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `catalog_io.py` | Modified | Add validation_only mode, error grouping |
| `views.py` | Modified | Handle new query params |
| `TestCatalogPage.tsx` | Modified | Replace simple upload with wizard |
| `CatalogUploadWizard.tsx` | New | Multi-step upload component |
| `SheetStatusCard.tsx` | New | Per-sheet validation display |
| `ImportErrorTable.tsx` | New | Error list with export |
| `catalog.types.ts` | New/Modified | TypeScript types for API |

---

## Success Criteria

1. **No silent failures** - Every rejected row has sheet+row+field+message
2. **Clear validation** - User sees validation results before committing
3. **Actionable errors** - Error messages tell user how to fix the issue
4. **Backward compatible** - Existing API contract still works
5. **Fast feedback** - Validation runs in <5 seconds for typical files

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| New UI breaks existing workflow | Low | Medium | Keep old upload as fallback |
| Performance issues with large files | Medium | Low | Stream validation, paginate errors |
| Browser memory issues | Low | Low | Use server-side validation only |

---

## Appendix: Alternative Considered - Sheet-wise Upload

This approach was considered but **not recommended** because:

1. **User friction** - Requires 6 separate upload actions
2. **Partial state** - Database can be left in inconsistent state
3. **Order confusion** - Users must upload sheets in correct order
4. **More API calls** - Higher server load
5. **Complex rollback** - If later sheets fail, earlier ones already committed

If this approach is preferred in the future, it can be implemented as a separate "advanced mode" behind a feature flag.
