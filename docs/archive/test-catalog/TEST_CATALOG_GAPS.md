# Test Catalog Gaps (Phase 0 Diagnosis)

## Why ReferenceRange isn’t used today
- `TestResult.validate_result()` reads `TestParameter.reference_min_*` / `reference_max_*` only and never consults `ReferenceRange`, so flags are based on the older per-parameter min/max fields.  
- `generate_pdf_report()` also formats ranges from `TestParameter` gender-specific min/max values, ignoring `ReferenceRange`.  

## Why result entry can be blank
- The result entry UI renders inputs only from existing `TestResult` rows (`/api/v1/results/?order_item=...`).  
- If an `OrderItem` has no `TestResult` rows yet (common for panels or newly ordered tests), the page has nothing to render and shows the “No parameters found” message.  
- There is no backend endpoint to “ensure” rows exist for each expected parameter, nor a shared service to list expected parameters for tests/panels.

## Minimal fixes
- Add a shared reference range selector (age + gender aware) that prefers `ReferenceRange` and falls back to `TestParameter` values.  
- Use that selector for both flag validation and PDF reporting so the range logic is consistent.  
- Add an expected-results service + endpoints to list expected parameter rows and to create missing `TestResult` rows so the UI never renders blank.
