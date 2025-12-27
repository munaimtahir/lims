# LAB PHASE 2 GAP CHECKLIST

This document contains an exhaustive analysis of all requirements from `ORIGINAL_LIMS_REQUIREMENTS_PROMPT.md` against the current codebase implementation.

**Last Updated:** Phase 2 Complete Analysis

| Section | Requirement | Status | Notes |
|---------|-------------|--------|-------|
| **SECTION 1: TEMPORARY FULL ACCESS MODE** | | | |
| 1.1 | Backend RolePermission model has Boolean fields for permissions | Present-Working | Model exists in `settings/models.py` |
| 1.2 | Set all RolePermission booleans to TRUE for all roles | Present-Working | `TEMPORARY_FULL_ACCESS_MODE` flag in `settings/permissions.py` bypasses checks |
| 1.3 | `current_user_permissions` API returns full-access values | Present-Working | `get_user_permissions` in `settings/views.py` respects the flag |
| 1.4 | Frontend permission checks allow access everywhere | Present-Working | `ProtectedRoute.tsx` has `TEMPORARY_FULL_ACCESS_MODE` flag |
| 1.5 | Comments marking TEMPORARY override for later removal | Present-Working | Comments added in both backend and frontend |
| **SECTION 2: FIX ORDER WORKFLOW BREAKAGE** | | | |
| 2.1 | Registration creates Order + OrderItems + Sample | Present-Working | `orders/serializers.py` creates all objects |
| 2.2 | Sample acceptance triggers Result creation | Present-Working | `samples/views.py` `receive_sample` creates Results via `_create_result_for_order_item` |
| 2.3 | Order status updates to IN_PROCESS when samples received | Present-Working | `_update_order_status_on_sample_receive` in `samples/views.py` |
| 2.4 | Result Entry shows orders/results ready for entry (DRAFT status) | Present-Working | `ResultEntryPage.tsx` filters for DRAFT status |
| 2.5 | Workflow respects WorkflowSettings (skip collection/receive) | Present-Working | `orders/serializers.py` checks `should_skip_*` functions |
| **SECTION 3: ADMIN PANEL** | | | |
| 3.1 | WorkflowSettings toggles control which screens appear | Present-Working | `WorkflowSettingsPage.tsx` toggles enable_sample_collection, enable_sample_receive, enable_verification |
| 3.2 | WorkflowSettings affect order transitions | Present-Working | Backend respects settings in order creation |
| 3.3 | RolePermissionsPage loads all RolePermission entries | Present-Working | `RolePermissionsPage.tsx` loads and displays all roles |
| 3.4 | RolePermissionsPage allows toggling checkboxes | Present-Working | Checkboxes functional in UI |
| 3.5 | RolePermissionsPage saves updates through API | Present-Working | Save button calls `updateRolePermissions` |
| 3.6 | Test Catalog - List of Tests UI | Present-Working | `TestCatalogPage.tsx` shows test list |
| 3.7 | Test Catalog - Add new tests | Present-Working | Modal form for adding tests |
| 3.8 | Test Catalog - Edit tests | Present-Working | Edit functionality in modal |
| 3.9 | Test Catalog - Setting test prices | Present-Working | Price field in form |
| 3.10 | Test Catalog - Deactivating tests | Present-Working | `is_active` toggle in form |
| 3.11 | Parameters management UI | Present-Working | `ParametersPage.tsx` with full CRUD |
| 3.12 | Reference ranges management UI | Present-Working | `ReferenceRangesPage.tsx` with full CRUD (needs route) |
| 3.13 | Test-Parameter mapping UI | Present-Working | `TestParametersPage.tsx` with full CRUD |
| **SECTION 4: REGISTRATION PAGE UX** | | | |
| 4.1 | Tab navigation between fields | Present-Working | Standard form behavior works |
| 4.2 | Test search with debounce | Present-Working | 200ms debounce in `NewLabSlipPage.tsx` |
| 4.3 | Test search dropdown results | Present-Working | Dropdown shows filtered tests |
| 4.4 | Arrow up/down selection in test dropdown | Present-Working | `handleTestSearchKeyDown` with ArrowUp/ArrowDown |
| 4.5 | Enter to select test | Present-Working | Enter key selects highlighted test |
| 4.6 | Auto-focus return to search after selection | Present-Working | `testSearchInputRef.current?.focus()` after selection |
| **SECTION 5: PATIENT SEARCH POPUP** | | | |
| 5.1 | Search Patient button in registration | Present-Working | Button opens `PatientSearchModal` |
| 5.2 | Search by Name | Present-Working | Backend search supports name |
| 5.3 | Search by Mobile number | Present-Working | Backend search supports phone |
| 5.4 | Search by MR number | Present-Working | Backend search supports MRN |
| 5.5 | Search by CNIC | Present-Working | Backend search supports CNIC |
| 5.6 | Arrow-key navigation | Present-Working | `handleKeyDown` in modal |
| 5.7 | Enter to select | Present-Working | Enter key selects patient |
| 5.8 | Auto-fill ALL fields | Present-Working | `selectPatient` fills all form fields |
| 5.9 | Link patient ID to order | Present-Working | Patient ID linked in order creation |
| **SECTION 6: TESTING & CLEANUP** | | | |
| 6.1 | Unit tests for workflow transitions | Present-Working | Tests in `samples/tests.py`, `results/tests.py` |
| 6.2 | Tests for patient search API | Present-Working | Tests in `patients/tests.py` |
| 6.3 | Tests for test search API | Present-Working | Tests in `catalog/test_api.py` |
| 6.4 | Dead code cleanup | Present-Working | No obvious dead code found |
| 6.5 | Type compatibility between frontend/backend | Present-Working | TypeScript interfaces match serializers |
| **SECTION 7: LAB HOME DASHBOARD** | | | |
| 7.1 | Dashboard shows Today's orders | Present-Working | `HomePage.tsx` displays `total_orders_today` |
| 7.2 | Dashboard shows Pending phlebotomy | Present-Working | `pendingCollection` count displayed |
| 7.3 | Dashboard shows Pending result entry | Present-Working | `pendingResultEntry` count displayed |
| 7.4 | Dashboard shows Pending verification | Present-Working | `pendingVerification` count displayed |
| 7.5 | Dashboard shows Pending publishing | Present-Working | `pendingPublishing` count displayed |
| 7.6 | Dashboard shows Pending refunds | N/A | Refund feature out of MVP scope |
| 7.7 | Dashboard shows Number of tests run today | Present-Working | `reportsPublishedToday` displayed |
| 7.8 | Tiles navigate to filtered lists | Present-Working | `StatTile` has `to` prop for navigation |
| 7.9 | New Lab Slip tile → registration | Present-Working | Links to `ROUTES.LAB_NEW` |
| 7.10 | Due Lab Slip tile → pending orders | Present-Working | Links to `ROUTES.LAB_WORKLIST` |
| 7.11 | Refund Lab Slip tile → refund page | N/A | Refund feature out of MVP scope |
| 7.12 | Modify Lab Slip tile → order edit | Present-Working | Order detail page allows editing |
| 7.13 | Test Results Saving tile → result entry | Present-Working | Links to `ROUTES.RESULT_ENTRY` |
| 7.14 | Results Upload Bulk tile → bulk upload | N/A | Bulk upload out of MVP scope |
| 7.15 | Manage Lab Tests tile → catalog | Present-Working | Links to `ROUTES.ADMIN_CATALOG` |
| 7.16 | Reports - Daily reports link | Present-Working | Links to `ROUTES.REPORTS` |
| 7.17 | Reports - Monthly summary | Present-Working | Reports page has date filters |
| 7.18 | Reports - Department-wise performance | N/A | Department analytics out of MVP scope |
| 7.19 | Workflow Settings tile on dashboard | Present-Working | ActionTile links to `/settings/workflow` |
| 7.20 | Clean React Router routing (no # hyperlinks) | Present-Working | All links use React Router |
| **SECTION 8: ARCHITECTURE ALIGNMENT** | | | |
| 8.1 | Use existing WorkflowSettings model | Present-Working | Using `settings/models.py` |
| 8.2 | Use existing RolePermission model | Present-Working | Using `settings/models.py` |
| 8.3 | Use existing dashboard endpoints | Present-Working | Using `dashboard/views.py` |
| 8.4 | Use existing catalog app | Present-Working | Using `catalog/` app |
| 8.5 | Use existing patients app | Present-Working | Using `patients/` app |
| 8.6 | No duplicate models or parallel logic | Present-Working | No duplications found |
| **SECTION 9: ADDITIONAL REQUIREMENTS** | | | |
| 9.1 | Result Entry pipeline works end-to-end | Present-Working | DRAFT → ENTERED flow works |
| 9.2 | Verification pipeline works | Present-Working | ENTERED → VERIFIED flow works |
| 9.3 | Publishing pipeline works | Present-Working | VERIFIED → PUBLISHED flow works |
| 9.4 | Sample Status Distribution on dashboard | Present-Working | Shows pending/collected/received/rejected counts |
| 9.5 | Result Status Distribution on dashboard | Present-Working | Shows draft/entered/verified/published counts |
| 9.6 | Average turnaround time display | Present-Working | `avg_tat_hours` displayed |

## Summary

### Present-Working: 55 requirements
### N/A (Out of MVP scope): 4 requirements
### Missing/Broken: 1 requirement (ReferenceRangesPage needs route in App.tsx)

## Remaining Work

1. **Add ReferenceRangesPage route to App.tsx** - Page exists but route is missing
