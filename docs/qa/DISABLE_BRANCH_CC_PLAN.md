# Disable Branch / Collection Center / Sample Workflow — Plan & Audit

## Purpose

Multi-branch and collection-center functionality broke core workflows (patient registration, receipt/order creation, result entry, verification, report publish). This document describes how those modules are **disabled** (invisible in UI, 404 in API) while preserving code and migrations, and how the simplified "small lab" workflow is restored.

---

## Step 1 — Inventory & Breakage Map

### Backend — Models

| Location | Model / Change |
|----------|----------------|
| `apps/core/models.py` | `Branch`, `CollectionCenter`, `TenantSettings` (enable_collection_centers, sample_workflow_enabled) |
| `apps/orders/models.py` | `Order`: collection_center, collection_branch, processing_branch, tenant; `Dispatch`, `DispatchItem` |
| `apps/patients/models.py` | `Patient`: registration_center (FK to CollectionCenter) |
| `apps/samples/models.py` | Sample collection/receiving (gated by sample_workflow_enabled) |
| `apps/accounts` | UserBranchMembership (user ↔ branch) |

### Backend — API Endpoints

| Endpoint | Purpose | Gating |
|----------|---------|--------|
| `GET/POST /api/v1/core/branches/`, `.../branches/<id>/` | Branch CRUD | enable_branches → 404 when off |
| `GET/POST /api/v1/core/collection-centers/`, `.../collection-centers/<id>/` | Collection center CRUD | enable_collection_centers → 404 when off |
| `GET/POST /api/v1/orders/dispatches/`, etc. | Dispatch manifest | enable_branches → 404 when off |
| `GET/POST /api/v1/samples/...` | Sample list/collect/receive | enable_sample_workflow (sample_workflow_enabled) → 404 when off |
| `GET/PATCH /api/v1/core/settings/tenant/` | Tenant settings (flags + defaults) | — |
| `GET/PATCH /api/v1/core/settings/features/` | Feature flags only (for UI) | — |

### Backend — Logic That Blocked Core Flows

- **Order create** (`apps/orders/serializers.py`): Required `collection_branch`; when tenant had no branches or user had no branch, raised "No branch assigned. Contact admin."
- **Order.save()** (`apps/orders/models.py`): Defaulted `collection_branch`/`processing_branch` to HQ; order_id used branch-based sequence. When branches disabled, we must allow null branch and use legacy `generate_order_id()`.
- **Results worklist** (`apps/results/views.py`): When sample_workflow_enabled=True, only order items with collected/received samples appeared; when False, paid orders are eligible (already implemented). Branch filtering could hide orders with null branch; authz already allows null.
- **Results _assert_branch_permissions**: Collection-only branch blocks result entry; when branch is null, access is allowed.
- **Patient registration** (`apps/patients/serializers.py`): registration_center optional when enable_collection_centers=False (already implemented).

### Frontend — Routes & UI

| Route / Component | Purpose | Gating |
|-------------------|---------|--------|
| `/dashboard/branches-and-centers` | BranchesAndCentersPage | Hidden when enable_branches=false |
| Sidebar "Branches & Centers" | Nav link | Hidden when enable_branches=false |
| TopHeader branch switcher | Switch current branch | Hidden or single-lab when enable_branches=false |
| `/dashboard/samples`, `/dashboard/collection` | Sample workflow | Already hidden when sample_workflow_enabled=false |
| RegistrationPage | registration_center/branch field | Already hidden when enable_collection_centers=false |
| CreateOrderPage | collection_branch in payload | Omit when enable_branches=false |
| SystemSettingsPage | Branch/CC dropdowns, sample workflow toggle | Show only when flags on (or always for admin, but disable usage when off) |

### Files Touched (Summary)

- **Core**: `models.py` (TenantSettings + enable_branches), `serializers.py`, `views.py`, `urls.py`, `features.py` (new), `services/settings.py`
- **Orders**: `serializers.py`, `models.py`, `views.py` (dispatch gating)
- **Patients**: serializers already handle optional registration_center
- **Results**: worklist and branch check already support null branch
- **Samples**: views return 403 → change to 404 when disabled
- **Frontend**: `App.tsx`, `DashboardLayout.tsx`, `TopHeader.tsx`, `CreateOrderPage.tsx`, `RegistrationPage.tsx`, `api/services.ts`, `types/index.ts`

---

## Feature Flags (Tenant-Scoped)

Stored on **TenantSettings** (OneToOne with Tenant):

| Flag | Default | Effect when False |
|------|---------|-------------------|
| `enable_branches` | False | Branch CRUD and Dispatch APIs return 404; UI hides Branches & Centers; orders/receipts do not require branch. |
| `enable_collection_centers` | False | Collection center CRUD returns 404; registration does not require collection center. |
| `enable_sample_workflow` (backend: `sample_workflow_enabled`) | False | Sample/collection/receive APIs return 404; paid orders go directly to result entry; NEW→IN_PROCESS allowed. |

API for frontend:

- **GET /api/v1/core/settings/features/**  
  Returns `{ enable_branches, enable_collection_centers, enable_sample_workflow }` (read-only for current tenant).
- **PATCH /api/v1/core/settings/features/**  
  Admin only; updates the three flags (and underlying TenantSettings).

Existing **GET/PATCH /api/v1/core/settings/tenant/** continues to expose full tenant settings including these flags and default_branch / default_collection_center.

---

## What Was Changed (Implementation Summary)

1. **TenantSettings**: Added `enable_branches` (default False). `sample_workflow_enabled` default remains True in DB for backward compatibility; new installs or docs recommend setting to False for "small lab".
2. **core/features.py**: `is_enabled(request, flag_name)`, `FeatureDisabled` (→ 404), `FeatureFlagPermission`, `@requires_feature(flag)`.
3. **API gating**: BranchViewSet, CollectionCenterViewSet, DispatchViewSet (and dispatch-related actions) check feature flags; when disabled, raise 404. Sample endpoints already gated; switched to 404 and aligned with `enable_sample_workflow` naming in docs.
4. **Order create/save**: When `enable_branches` is False, serializer does not require or set collection_branch/processing_branch (stays null). Order.save() does not default branches when tenant has enable_branches=False; uses `generate_order_id()` when no branch.
5. **Frontend**: Feature flags loaded from tenant settings (or dedicated features endpoint). Hide "Branches & Centers" nav and route when enable_branches=false; hide or simplify branch switcher; Create Order does not send collection_branch when enable_branches=false.
6. **Registration → Create Order**: Already navigates to `/dashboard/orders/create?patient_id=...` on success; no change needed except ensuring order create works without branch.

---

## What Is Hidden When Disabled

- **UI**: Sidebar "Branches & Centers", route `/dashboard/branches-and-centers`, branch switcher (or single "Lab" when branches off). Samples/Collection menus when sample workflow off (already implemented).
- **API**: All branch and collection-center list/detail/create/update/delete return 404. Dispatch list/create/update/delete return 404. Sample endpoints return 404 when sample workflow off.

---

## Fallbacks for Core Workflow (Flags Off)

- **Patient registration**: Tenant set from user; MRN/registration number generated (tenant-wide or center-based as per existing logic); registration_center optional (null when enable_collection_centers=false).
- **Order/Receipt creation**: No collection_branch/processing_branch required; order_id from legacy ORD-YYYYMMDD-NNNN; lab_number still generated via default collection_center "00" in Order.save() for legacy compatibility.
- **Result entry**: Worklist shows paid orders (and items without results or with DRAFT); no dependency on sample status when sample_workflow_enabled=false; null branch allowed in filter and permission.
- **Verification / Publish**: No change; state flow NEW → IN_PROCESS → VERIFIED → PUBLISHED; when sample workflow off, NEW → IN_PROCESS is allowed.

---

## Re-enabling Later (What to Revisit)

1. **Data**: Ensure at least one Branch (e.g. code "00") and optionally CollectionCenter exist per tenant before turning enable_branches or enable_collection_centers on.
2. **Orders**: Existing orders with null collection_branch/processing_branch may need a backfill to default_branch or HQ when re-enabling branches.
3. **State machine**: When re-enabling sample workflow, consider whether existing IN_PROCESS orders without samples should be treated as "received" or require a one-time receive step.
4. **UI**: Re-show Branches & Centers nav, branch switcher, and collection center field in registration; re-enable collection_branch in Create Order.

---

## SMOKE CHECK

### Prerequisites

- Backend running (e.g. `docker compose up` or `python manage.py runserver`).
- Frontend running (e.g. `npm run dev`).
- Valid JWT for an admin user (tenant with enable_branches=false, enable_collection_centers=false, sample_workflow_enabled=false).

### 1. Docker (if used)

```bash
cd /path/to/lims
docker compose up -d
# Wait for DB and app to be ready
```

### 2. Backend — curl (replace TOKEN and base URL)

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your_jwt>"

# Features (should show flags; default off)
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/core/settings/features/"

# Branches disabled → 404
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/core/branches/"
# Expect: 404

# Collection centers disabled → 404
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/core/collection-centers/"
# Expect: 404

# Dispatches disabled (when branches off) → 404
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/orders/dispatches/"
# Expect: 404

# Samples disabled → 404
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/samples/"
# Expect: 404

# Patient create (no registration_center) → 201
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"full_name":"Smoke Patient","phone":"0300-1234567","gender":"Male"}' \
  "$BASE/patients/" -o /dev/null -w "%{http_code}"
# Expect: 201

# Order create (no collection_branch) — use patient_id from above
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"patient":<PATIENT_ID>,"test_ids":[],"panel_ids":[]}' \
  "$BASE/orders/" -o /dev/null -w "%{http_code}"
# Expect: 201

# Results worklist → 200
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/results/worklist/"
# Expect: 200

# Verification (e.g. list or action) → 200
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/results/"
# Expect: 200

# Report PDF (replace ORDER_ID) → 200 + bytes
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE/reports/<ORDER_ID>/pdf/"
# Expect: 200
```

### 3. UI Flow (Minimal)

1. Log in as receptionist or admin.
2. **Registration**: Open Registration, fill required fields (e.g. name, phone, gender), submit. Expect success and **redirect to Create Order** with patient pre-selected.
3. **Create Order**: Add tests/panels, save. Expect order created without selecting branch/collection center.
4. **Pay** (if needed): Open order, add payment so order is paid.
5. **Result entry**: Open Worklist / Result Entry, select order item, enter result, save.
6. **Verification**: Open Verification, verify the result.
7. **Report**: Open Reports or order detail, trigger Print/PDF. Expect PDF or download.

### 4. Visibility Checks

- Sidebar must **not** show "Branches & Centers" when enable_branches is false.
- Visiting `/dashboard/branches-and-centers` directly should either redirect or show "not available" when flags off (or 404 from API if page calls branches API).
- Branch switcher in header should be hidden or show single lab when enable_branches is false.

---

*End of plan.*
