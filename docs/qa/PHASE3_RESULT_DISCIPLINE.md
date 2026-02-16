# Phase 3: Result Entry Discipline & Predictability

## 1. Overview
Implemented robust result entry rules to support optional parameters, formulas, and default values. Enforced NULL storage for empty results to allow accurate report generation.

## 2. Key Changes

### Data Model (TestParameter)
- Added `is_required_for_verification` (default=True): Blocks verification if NULL.
- Added `is_printable` (default=True): Omits row from report if False.
- Added `default_value`: Automatically applied to NULL results on GET/POST ensure.
- Added `value_source` (MANUAL, FORMULA, INSTRUMENT).
- Added `formula_expression`: Supports math like `{WBC} * 0.1`.
- Added `allow_manual_override`: Manual input takes precedence over formula.

### Result Management
- `TestResult.result_value` is now nullable.
- Empty user input is stored as `NULL` (no more `*` placeholders).
- Missing result rows are automatically created via `ensure_order_item_results`.

### Formulas (Server-side)
- Safe math evaluation for `FORMULA` parameters.
- Recomputed on every SAVE of manual parameters.
- Supports placeholders using parameter `short_name` or `parameter_id`.

### Worklist & Verification
- Worklist includes items with:
    - Missing required parameters (even if status is ENTERED).
    - Draft results.
- Verification blocks if any parameter with `is_required_for_verification=True` is NULL.
- Optional parameters (Required=False) do NOT block verification if left blank.

### Report Printing
- Rows with `result_value IS NULL` are omitted.
- Rows with `is_printable=False` are omitted.

## 3. Implementation Checklist
- [x] Backend: Model migrations for `TestParameter` and `TestResult`.
- [x] Backend: `ensure_order_item_results` service with default value logic.
- [x] Backend: Safe formula evaluation service.
- [x] Backend: Updated `TestResultSerializer` for requirements validation.
- [x] Backend: Updated `worklist` query for visibility.
- [x] Backend: Updated `report_pdf` data preparation (filter NULL/non-printable).
- [x] Frontend: Simplified 4-column result entry table.
- [x] Frontend: Required parameter indicators (*).
- [x] Frontend: Keyboard navigation (Enter next, Ctrl+S save).
- [x] Frontend: Handling NULL instead of `*`.

## 4. Testing Guide
1. Create a test with 1 required and 1 optional parameter.
2. Open Result Entry: verify default value (if set) is applied.
3. Save empty: verify `result_value` in DB is NULL.
4. Try to Verify: should block if required parameter is NULL.
5. Fill required, leave optional blank: should allow verification.
6. Print Report: verify optional blank parameter is OMITTED from PDF.
7. Test Formula: set a parameter as `{P1} + 1`. Enter value for P1 and save. Verify formula computes.
