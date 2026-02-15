# Branch / Collection Center Phase-1 — Task Checklist (GitHub-ready)

Use this as a checklist for issues or sprint items. Each task has title, files, and acceptance criteria.

---

## Phase A: Registration + Order creation stable (no internal server errors)

### Task A1: Set patient tenant on create so new patients are visible in list

- **Title:** Set patient tenant on create from request user
- **Files:** `lims-backend/apps/patients/views.py` and/or `lims-backend/apps/patients/serializers.py`
- **Acceptance criteria:**
  - On `POST /api/v1/patients/`, the created patient has `tenant` set to `user_tenant(request.user)`.
  - Newly created patient appears in `GET /api/v1/patients/` for the creating user.
- **Rollback:** Remove tenant assignment in create; ensure no NOT NULL on tenant if reverting.

### Task A2: Accept branch at patient create and map to registration_center (CollectionCenter)

- **Title:** Map branch to registration_center and set tenant on patient create
- **Files:** `lims-backend/apps/patients/serializers.py` (PatientCreateSerializer), optionally `lims-backend/apps/patients/views.py`
- **Acceptance criteria:**
  - API accepts optional `branch` (Branch id) in patient create payload.
  - If `branch` is provided and valid: resolve Branch, get or create CollectionCenter with same `code`, set `registration_center` to that center; set `tenant` from user (or from branch.tenant).
  - If frontend sends `registration_center` with a value that is a Branch id (e.g. no CollectionCenter with that pk), either ignore and use center 00 or map via branch code. Document behavior.
  - No 400/500 when RegistrationPage sends current branch id as registration_center (either as branch or after adding branch field).
- **Rollback:** Remove branch handling; require registration_center to be CollectionCenter id only.

### Task A3: Default order collection_branch from user when not provided

- **Title:** Default order collection_branch from request user's branch
- **Files:** `lims-backend/apps/orders/serializers.py` (OrderSerializer.create)
- **Acceptance criteria:**
  - When `collection_branch` is not in the create payload, set it to the first active branch in the request user's branch_memberships (if any).
  - If user has no branch memberships, keep current model behavior (HQ or null).
  - Branch users creating orders get their branch as collection_branch when UI does not send it.
- **Rollback:** Remove default; rely on Order.save() HQ default only.

### Task A4: Seed: tenant and branch membership for demo users

- **Title:** Assign tenant and HQ branch membership to demo users in seed
- **Files:** `lims-backend/apps/accounts/management/commands/create_demo_users.py`, optionally a combined bootstrap script
- **Acceptance criteria:**
  - After running create_demo_users (and seed_branches for default tenant), each demo user has `tenant` set to default tenant and at least one UserBranchMembership to HQ (code 00).
  - Frontend branch dropdown and currentBranch are populated for these users.
- **Rollback:** Revert create_demo_users to not set tenant/memberships; run seed_branches separately.

---

## Phase B: Collection marking stable

### Task B1: Ensure sample collection sets collected_at_branch from order

- **Title:** Verify sample collected_at_branch is set from order.collection_branch
- **Files:** `lims-backend/apps/samples/models.py` and/or services
- **Acceptance criteria:**
  - When a sample is marked COLLECTED, `collected_at_branch` is set from `order_item.order.collection_branch` if not already set.
  - Branch-scoped sample list shows samples for user's branches.
- **Rollback:** N/A (verification only; logic may already exist in Sample.save).

### Task B2: Collection worklist filtered by user branches

- **Title:** Collection worklist only shows orders/samples for user's branches
- **Files:** `lims-backend/apps/samples/views.py`, `lims-backend/apps/orders/views.py` (worklist if any)
- **Acceptance criteria:**
  - Non-admin users see only samples (and orders) belonging to their allowed branches.
  - filter_queryset_for_branches already applied; confirm and add test.
- **Rollback:** N/A.

---

## Phase C: Dispatch + receiving (minimal or document as Phase-1B)

### Task C1: Document or implement "create dispatch" and "receive dispatch"

- **Title:** Define dispatch manifest and receive workflow for Phase-1
- **Files:** New: `lims-backend/apps/orders` or `core` (Dispatch model/API) or docs only
- **Acceptance criteria:**
  - Either: (1) Add minimal Dispatch model (e.g. branch, list of orders/samples, status) and endpoints to create and “receive” dispatch; main lab receive sets samples to RECEIVED and links received_by; or (2) Document that “receive dispatch” is current “mark samples received” and add SMOKE_TESTS for that flow.
- **Rollback:** If implemented, migration and feature flag or revert migration.

---

## Phase D: UX (keyboard flow, validation messages)

### Task D1: Registration: do not send Branch id as registration_center

- **Title:** Frontend: send branch for patient create instead of registration_center when using branch
- **Files:** `frontend/src/pages/registration/RegistrationPage.tsx`, `frontend/src/types/index.ts`, API contract
- **Acceptance criteria:**
  - Registration form sends `branch` (Branch id) in create payload when user selects a branch; backend maps to registration_center (Task A2). Or backend accepts registration_center only and frontend sends nothing or a valid CollectionCenter id (from new endpoint if needed).
  - No invalid FK from Branch id in registration_center.
- **Rollback:** Revert to sending registration_center only; ensure backend accepts and maps (A2).

### Task D2: Order create: always send collection_branch when user has branch

- **Title:** Frontend: send currentBranch.id as collection_branch when creating order
- **Files:** `frontend/src/pages/orders/CreateOrderPage.tsx`, `frontend/src/pages/patients/PatientsPage.tsx` (create order modal)
- **Acceptance criteria:**
  - When user has currentBranch, order create payload includes collection_branch: currentBranch.id.
  - Backend still defaults from user when not sent (Task A3).
- **Rollback:** Rely on backend default only.

---

## Tests and smoke

### Task T1: API smoke test for branch flow

- **Title:** Add smoke test: patient create → order create (branch) → mark collected
- **Files:** `scripts/smoke_flow_branch.sh` or `lims-backend/apps/core/tests/test_smoke_branch_flow.py`
- **Acceptance criteria:**
  - Script or pytest: login as branch user (or receptionist with branch), create patient, create order, mark sample collected; assert order has collection_branch and patient has tenant.
- **Rollback:** Remove test file.

### Task T2: Test patient create sets tenant

- **Title:** Unit test: patient create sets tenant from request user
- **Files:** `lims-backend/apps/patients/tests/test_patients.py` or test_serializers
- **Acceptance criteria:**
  - Create patient via API with authenticated user; assert patient.tenant == user_tenant(user).
- **Rollback:** Remove or adjust test.

### Task T3: Test order create defaults collection_branch from user

- **Title:** Unit test: order create defaults collection_branch from user branch membership
- **Files:** `lims-backend/apps/orders/tests/test_orders.py` or test_serializers
- **Acceptance criteria:**
  - Create order without collection_branch; user has one branch membership; assert order.collection_branch == user's branch.
- **Rollback:** Remove or adjust test.
- **Status:** Covered in `core/tests/test_smoke_branch_flow.py`.

---

## Phase-1 Optional Module (Completed)

### Task F1: TenantSettings and feature flag — DONE

- **Title:** Add TenantSettings (enable_collection_centers, default_branch, default_collection_center)
- **Files:** `lims-backend/apps/core/models.py`, `core/services/settings.py`, `core/views.py`, `core/urls.py`, `core/migrations/0008_add_tenant_settings.py`
- **Acceptance criteria:** GET/PATCH `/api/v1/core/settings/tenant/`; fresh DB has enable_collection_centers=False; default_branch seeded by create_demo_users.

### Task F2: Patient create gated by tenant settings — DONE

- **Title:** Patient create: when centers OFF ignore invalid registration_center; when ON require center or default, accept branch id
- **Files:** `lims-backend/apps/patients/serializers.py`
- **Acceptance criteria:** Centers OFF: no required center; invalid/Branch id in registration_center ignored. Centers ON: require center or default; accept branch or registration_center (CC pk or Branch pk bridge).

### Task F3: Order create default_branch fallback and 400 — DONE

- **Title:** Order create: default collection_branch from user, then tenant default_branch; 400 if none
- **Files:** `lims-backend/apps/orders/serializers.py`
- **Acceptance criteria:** collection_branch defaulted; friendly 400 "No branch assigned. Contact admin." when no user branch and no tenant default_branch.

### Task F4: UI registration respects tenant settings — DONE

- **Title:** Frontend: fetch tenant settings; when OFF hide CC, do not send registration_center/branch; when ON send branch
- **Files:** `frontend/src/api/services.ts`, `frontend/src/pages/registration/RegistrationPage.tsx`, `frontend/src/types/index.ts`
- **Acceptance criteria:** GET `core/settings/tenant/` on load; centers OFF: no CC UI, payload without center/branch; centers ON: branch dropdown, send branch.

### Task F5: Data migration backfill tenant — DONE

- **Title:** Backfill Patient and Order tenant where NULL
- **Files:** `lims-backend/apps/core/migrations/0009_backfill_tenant_on_patient_order.py`
- **Acceptance criteria:** No patients/orders remain with tenant=NULL after migration.

### Task F6: Dispatch model and API (Phase-1B) — DONE

- **Title:** Dispatch + DispatchItem; POST create, send, receive
- **Files:** `lims-backend/apps/orders/models.py`, `orders/views.py`, `orders/serializers.py`, `orders/urls.py`, `orders/migrations/0009_dispatch_dispatchitem.py`
- **Acceptance criteria:** Create dispatch from collected orders; send (IN_TRANSIT); receive (samples RECEIVED, dispatch RECEIVED). Branch/receive permissions enforced.

### Task F7: Smoke tests OFF/ON and dispatch — DONE

- **Title:** Pytest and smoke script: centers OFF/ON cases, dispatch flow
- **Files:** `lims-backend/apps/core/tests/test_smoke_branch_flow.py`, `scripts/smoke_flow_branch.sh`, `docs/qa/SMOKE_TESTS.md`
- **Acceptance criteria:** test_patient_create_ignores_invalid_center_when_flag_off; test_patient_create_requires_center_when_flag_on_no_default; test_dispatch_flow_minimal; script shows tenant settings.
