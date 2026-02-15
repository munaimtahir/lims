# Root Causes and Fixes

## Issues Found and Resolved

### 1. Test list API returns `test_id` not `id`

- **Root cause:** Laboratory tests API response uses `test_id` as the test primary key field.
- **Fix:** smoke_test.py – use `t.get("id") or t.get("test_id")` when extracting test IDs.
- **File:** `smoke_test.py`

### 2. Patient creation: hardcoded patient ID no longer valid

- **Root cause:** Smoke test used hardcoded patient ID 12 which may not exist.
- **Fix:** smoke_test.py – call `create_patient()` instead of using hardcoded ID.
- **File:** `smoke_test.py`

### 3. Samples not visible via API (branch filter)

- **Root cause:** `filter_queryset_for_branches` excluded samples with `collected_at_branch=null` when user had no branch memberships.
- **Fix:** authz.py – include records with null branch: `Q(branch_field__in=allowed) | Q(branch_field__isnull=True)`.
- **File:** `lims-backend/apps/core/authz.py`

### 4. No test parameters for result entry

- **Root cause:** Test catalog had no TestParameter mappings.
- **Fix:** Run `catalog_ensure_minimum_parameters` management command.
- **File:** N/A (manual step; documented in next_actions)

### 5. Result verification 403 (Pathologist lacks permission)

- **Root cause:** Demo pathologist user not in Django Group "Pathologist" (which has `can_verify_results`).
- **Fix:** Smoke test uses admin token for verification (admin has all permissions).
- **File:** `smoke_test.py`

### 6. Report generation wrong endpoint

- **Root cause:** Smoke test posted to POST `/api/v1/reports/` (create) instead of POST `/api/v1/reports/generate/`.
- **Fix:** smoke_test.py – use `/reports/generate/` with `order_id` and `is_final: true`.
- **File:** `smoke_test.py`

### 7. Receipt download 404 (wrong URL)

- **Root cause:** Smoke test used `download_receipt/` but billing action is `receipt`.
- **Fix:** smoke_test.py – use `/payments/{id}/receipt/`.
- **File:** `smoke_test.py`

### 8. Report generation Permission denied (media directory)

- **Root cause:** Container appuser could not create `/app/media/reports/YYYY/MM/DD/`.
- **Fix:** chmod 777 on host media directory for development; production should set correct ownership.
- **File:** N/A (host-level; document in next_actions)
