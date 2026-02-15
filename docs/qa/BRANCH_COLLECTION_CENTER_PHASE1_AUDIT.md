# Branch / Collection Center Phase-1 — Audit & Implementation Plan

**Date:** 2026-02-15  
**Scope:** Multi-branch chain; Phase-1: branches do sample collection only; no result entry in branches.  
**Goal:** Stabilize patient → order → receipt → sample collection → dispatch → receive workflow.

---

## STEP 0 — REPO ORIENTATION

### Repository structure

| Asset | Path |
|-------|------|
| **Backend root** | `lims-backend/` |
| **Frontend root** | `frontend/` |
| **Docker Compose** | `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml`, `docker-compose.override.yml` |
| **Env examples** | `.env`, `.env.production.example`, `lims-backend/.env.prod`, `e2e/.env.example` |

**Stack:** PostgreSQL (db), Redis, Django backend (config.settings.production in prod), React frontend (Vite), Caddy proxy (port 8012), Celery + beat.

### Where Branch / Collection Center is implemented

| Layer | Location | Notes |
|-------|----------|--------|
| **Models** | `lims-backend/apps/core/models.py` | `Branch`, `CollectionCenter`, `Tenant`; `RegistrationCounter`, `LabDailyCounter` (center-scoped); `OrderIdSequence` (branch+date). |
| **User–branch** | `lims-backend/apps/accounts/models.py` | `User.tenant` (FK); `UserBranchMembership` (user ↔ branch, role). |
| **Order fields** | `lims-backend/apps/orders/models.py` | `tenant`, `collection_center`, `collection_branch`, `processing_branch`; `order_id` via `generate_branch_order_id()` when tenant+branch present. |
| **Patient** | `lims-backend/apps/patients/models.py` | `tenant`, `registration_center` (FK to **CollectionCenter**, not Branch). |
| **Sample** | `lims-backend/apps/samples/models.py` | `collected_at_branch`, `current_branch` (Branch FKs). |
| **Status/transitions** | `lims-backend/apps/orders/models.py` | `Order.validate_status_transition()`; `orders/services.py` `transition_visit_state()`. |
| **Serializers/views** | `orders/serializers.py`, `orders/views.py` | Order create defaults tenant from user; **collection_branch not defaulted from user**. |
| **Permissions** | `lims-backend/apps/core/authz.py` | `user_tenant()`, `user_active_branches()`, `filter_queryset_for_branches()`, `user_has_branch_access()`. |
| **Result entry guard** | `lims-backend/apps/results/views.py` | `_assert_branch_permissions()` blocks result entry for `BranchCapability.COLLECT_ONLY`. |
| **Frontend** | `frontend/src/` | `AuthContext` (currentBranch, branch_memberships); Registration sends `registration_center: currentBranch?.id` (Branch id); Create Order sends `collection_branch: currentBranch?.id`. |

**Important:** `Patient.registration_center` is a FK to **CollectionCenter**. The UI sends **Branch** id as `registration_center`, which is the wrong FK and can cause 400/500 or wrong data if IDs overlap.

---

## STEP 1 — FAST STATIC AUDIT & STATUS MAP

### Branch / CollectionCenter models

- **CollectionCenter:** `code` (2 digits), `name`, `address`, `is_active`; table `core_collection_centers`. Used for MRN (RegistrationCounter) and lab number (LabDailyCounter).
- **Branch:** `tenant` (nullable), `code` (2 digits), `name`, `address`, `phone`, `capability_mode` (COLLECT_ONLY / COLLECT_AND_PROCESS / HQ_PROCESSING), `is_hq`, `is_active`; unique (tenant, code); table `core_branches`.
- **Tenant:** `code`, `name`; default "LAB".

### Patient registration flow

- **Endpoints:** `POST /api/v1/patients/`, `GET /api/v1/patients/`, `GET /api/v1/patients/lookup/?mobile=...`.
- **Create serializer:** `PatientCreateSerializer`; includes `registration_center`. **Does not set `tenant`** from request user → created patients can have `tenant=None` → list filters by `tenant=user_tenant(user)` → **new patients invisible** to the creating user.
- **Signals/overrides:** `Patient.save()` sets MRN/registration_number, `tenant` only from `registration_center.tenant` (CollectionCenter has **no** `tenant` field) → tenant stays None unless set in serializer.

### Order creation flow

- **Endpoints:** `POST /api/v1/orders/orders/`.
- **Branch attachment:** In `Order.save()`: if `collection_branch` is null, set to HQ (code 00); if `processing_branch` null, set to `collection_branch`. In `OrderSerializer.create()`: tenant defaulted from user; **collection_branch is not defaulted from user** → branch users without UI sending branch get HQ.
- **Order ID:** When `tenant` and `collection_branch` exist, `generate_branch_order_id(tenant, branch)` → `{branch.code}-YYMMDD-####`. Else legacy `ORD-YYYYMMDD-NNNN`.

### Permissions

- **Branch scoping:** `OrderViewSet.get_queryset()` filters by `user_tenant()` then `filter_queryset_for_branches(qs, "collection_branch", user)` for non–tenant-admins. Same pattern for samples (collected_at_branch), results (order_item__order__collection_branch).
- **Result entry:** `results/views.py` forbids result entry when order’s branch has `capability_mode == COLLECT_ONLY`.

### Status machine

- **Order statuses:** NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED; CANCELLED terminal. Transitions enforced in `Order.validate_status_transition()` and `orders/services.transition_visit_state()`.
- **No explicit DISPATCHED / RECEIVED_MAIN_LAB** on Order; sample has RECEIVED (received_at/received_by). No dedicated Dispatch/Manifest model found.

### Required FKs and breakage risk

- **Order:** `tenant` nullable (defaulted in save); `collection_branch` / `processing_branch` nullable (defaulted to HQ in save). If no branches seeded, HQ is None → order_id falls back to legacy; no NOT NULL violation.
- **Patient:** `tenant` nullable; `registration_center` nullable (defaulted to center 00 in save). **Risk:** list uses `tenant=user_tenant(user)` → patients with tenant=None are hidden.
- **Constraint:** `Order` has `unique_order_id_per_tenant` on (tenant, order_id). If tenant is set and branch used, order_id is branch-scoped so no collision.

### STATUS MAP (Deliverable 1)

| Component | Status | Evidence |
|-----------|--------|----------|
| **Model: Branch** | DONE | `core/models.py` Branch, BranchCapability, OrderIdSequence |
| **Model: CollectionCenter** | DONE | `core/models.py`; RegistrationCounter, LabDailyCounter |
| **Model: User–branch** | DONE | `accounts/models.py` UserBranchMembership, User.tenant |
| **Order branch fields** | DONE | `orders/models.py` collection_branch, processing_branch; defaults in save() |
| **Patient tenant/center** | PARTIAL | Patient.tenant not set on create; registration_center sent as Branch.id from UI |
| **API: Patient create** | BROKEN | Tenant not set → patient invisible; registration_center = Branch.id (wrong FK) |
| **API: Order create** | PARTIAL | collection_branch not defaulted from user; works if UI sends branch |
| **API: Branch list** | MISSING | No `/api/v1/core/branches/` or equivalent; frontend uses user.branch_memberships |
| **Permissions / RBAC** | DONE | authz.py; order/sample/result queryset filtering; COLLECT_ONLY block |
| **Printing (receipt/labels)** | DONE | Receipt via payments; report generation |
| **Dispatch / manifest** | MISSING | No Dispatch or Manifest model; no “create dispatch” / “receive dispatch” API |
| **Sample “receive” at main lab** | PARTIAL | Sample has received_at/received_by; no explicit “dispatch receive” workflow |
| **UI: Registration** | BROKEN | Sends registration_center = Branch.id (should be CollectionCenter or backend mapping) |
| **UI: Create order** | PARTIAL | Sends collection_branch when currentBranch set; no branch when user has no memberships |

---

## STEP 2 — BUG LIST (Deliverable 2)

### Bug 1: Newly created patient not visible in list (tenant=None)

- **Symptom:** After creating a patient, they do not appear in the patient list.
- **Endpoint/Page:** `POST /api/v1/patients/`, then `GET /api/v1/patients/` or Patients/Registration search.
- **Root cause:** `PatientCreateSerializer` does not set `tenant`. `Patient.save()` sets tenant only from `registration_center.tenant`, and CollectionCenter has no tenant field, so tenant remains None. List filters by `tenant=user_tenant(request.user)`, so `tenant=None` rows are excluded.
- **Fix:** In patient create (view or serializer), set `tenant = user_tenant(request.user)` on the created patient.

### Bug 2: Registration form sends Branch id as registration_center (wrong FK)

- **Symptom:** Possible 400/500 or invalid data when creating patient with “branch” selected; or silent wrong FK if Branch and CollectionCenter IDs overlap.
- **Endpoint/Page:** `POST /api/v1/patients/` from RegistrationPage; form sends `registration_center: currentBranch?.id`.
- **Root cause:** `Patient.registration_center` is FK to **CollectionCenter**; frontend sends **Branch** id. Backend may raise validation error or store wrong reference.
- **Fix (backend):** Accept optional `branch` (Branch id) in create; resolve Branch by id; get or create CollectionCenter with same `code` as Branch; set `registration_center` to that center; set `tenant` from user. Alternatively accept only `registration_center` (CollectionCenter id) and set tenant from user; frontend must then use a centers list or map branch code → center.

### Bug 3: Order creation does not default collection_branch from user

- **Symptom:** Branch user creates order without selecting branch (or UI does not send branch) → order gets HQ (00) from Order.save() instead of user’s branch.
- **Endpoint/Page:** `POST /api/v1/orders/orders/`.
- **Root cause:** `OrderSerializer.create()` does not set `collection_branch` from request user; only `Order.save()` defaults to HQ when null.
- **Fix:** In `OrderSerializer.create()`, if `collection_branch` not in validated_data, set it from the first active branch in the user’s branch_memberships (or from request context); if user has no branch, keep current behavior (HQ or null).

### Bug 4: Demo users have no tenant or branch memberships

- **Symptom:** After `create_demo_users`, users have tenant=None and no UserBranchMembership → `user_active_branches()` is empty; branch filtering and “current branch” in UI may behave oddly.
- **Evidence:** `create_demo_users.py` does not set tenant or create UserBranchMembership; `seed_branches` exists but is separate.
- **Fix:** In seed/bootstrap: ensure default tenant exists; run `seed_branches`; assign default tenant to demo users and at least one branch membership (e.g. HQ) for receptionist/cashier/phlebotomist so branch dropdown and defaults work.

### Bug 5: No dispatch/manifest workflow (Phase-1 scope gap)

- **Symptom:** Cannot “create dispatch manifest” or “receive dispatch at main lab” as per Phase-1 scope.
- **Root cause:** No Dispatch/Manifest model or API; sample “received” exists but not as an explicit “receive dispatch” step.
- **Fix:** Either add minimal Dispatch + “receive dispatch” API and UI, or document as Phase-1B and keep Phase-1 to: branch marks collected → main lab marks sample received (current behavior).

---

## STEP 3 — DATA MODEL CONSISTENCY & DB FIX PLAN (Deliverable 3)

- **Migrations:** No schema change strictly required for the bugs above; all branch/tenant fields are nullable and defaulted in code. Ensure all migrations are applied (`python manage.py migrate`).
- **Data migration (optional):** Backfill `Order.collection_branch` and `Order.tenant` for existing orders: set tenant to default tenant, collection_branch to HQ (code 00) where null. Same for Patient.tenant where null (set to default tenant).
- **Seeds:**  
  - Ensure default tenant exists (`get_default_tenant()`).  
  - Run `seed_branches --tenant LAB` (and `--include-samples` if branch users are needed).  
  - Update `create_demo_users` (or a separate bootstrap) to set `user.tenant = default_tenant` and create at least one UserBranchMembership per user to HQ (and optionally to branch 01 for branch users).  
  - Ensure CollectionCenter with code `00` exists (created in Order/Patient save get_or_create; can be explicit in seed).

---

## STEP 4 — WORKFLOW SPEC vs IMPLEMENTATION GAP (Deliverable 4)

### Authoritative Phase-1 (intended)

- **Branch user:** Register/search patient → create order → print receipt/labels → mark sample collected → create dispatch manifest to main lab.
- **Main lab user:** Receive dispatch (acknowledge). No branch result entry.

### Current implementation

- **Order statuses:** NEW, COLLECTED, IN_PROCESS, VERIFIED, PUBLISHED, CANCELLED. No DISPATCHED or RECEIVED_MAIN_LAB.
- **Sample:** PENDING → COLLECTED → RECEIVED. “Receive” is at sample level, not a separate “dispatch receive” entity.
- **Gaps:**  
  1. No “origin_branch” naming (code uses `collection_branch` as origin at creation; acceptable).  
  2. No explicit dispatch manifest or “receive dispatch” step; only sample receive.  
  3. Order creation does not enforce “origin_branch always set at creation” from user when no branch sent (defaults to HQ in model, not user’s branch).  
  4. Patient registration: tenant and registration_center handling as in Bug 1 and Bug 2.

### Recommended changes

- Enforce at API layer: set patient tenant and (optionally) registration_center from user/branch; set order collection_branch from user when not provided.
- Add minimal “dispatch” concept in Phase-1B if required: e.g. Dispatch model (batch of orders/samples from branch), “receive” action that sets samples to RECEIVED and optionally sets a “received_at_main_lab” flag or order status. Until then, consider “mark samples received” as the receive step.

---

## STEP 5 — NEXT STEPS & TASKS (Deliverable 5)

See **TASKS.md** in the same directory for the checklist (file created separately).

---

## STEP 6 — SMOKE TESTS (Deliverable 6)

See **SMOKE_TESTS.md** and `scripts/smoke_flow_branch.sh` (or pytest in `lims-backend/`) for API smoke: login → create patient → create order (with branch) → print receipt → mark collected → (optional) receive. Branch-specific smoke: use branch user, ensure order has collection_branch set and result entry is forbidden for COLLECT_ONLY branch.

---

## Summary of critical fixes to implement

1. **Patient create:** Set `tenant = user_tenant(request.user)`; accept `branch` (Branch id) and map to CollectionCenter by code for `registration_center`, or ignore invalid registration_center when it is a Branch id and use center 00.
2. **Order create:** When `collection_branch` is not provided, set from user’s first active branch membership.
3. **Seed:** Assign tenant and at least one branch membership to demo users; ensure branches and center 00 exist.

These fixes are implemented in the codebase as described in TASKS.md and the patches below.

---

## Repo State Verified (Phase 0)

**Backend root:** `lims-backend/`  
**Frontend root:** `frontend/`  
**Docker Compose:** `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml`, `docker-compose.override.yml` (repo root)  
**Env examples:** `.env`, `.env.production.example`, `lims-backend/.env.prod`, `e2e/.env.example`

**Verified files present:**  
`docs/qa/BRANCH_COLLECTION_CENTER_PHASE1_AUDIT.md`, `docs/qa/TASKS.md`, `docs/qa/SMOKE_TESTS.md`, `scripts/smoke_flow_branch.sh`, `lims-backend/apps/patients/serializers.py`, `lims-backend/apps/orders/serializers.py`, `lims-backend/apps/accounts/management/commands/create_demo_users.py`.

**Data models and field names:**

| Model | Location | Tenant | registration_center / collection_center | collection_branch / origin_branch |
|-------|----------|--------|----------------------------------------|----------------------------------|
| **Tenant** | `core/models.py` | — | — | — |
| **Branch** | `core/models.py` | `tenant` (FK, nullable) | — | — |
| **CollectionCenter** | `core/models.py` | *(no tenant)* | — | — |
| **Patient** | `patients/models.py` | `tenant` (FK, null=True) | `registration_center` (FK to CollectionCenter, null=True) | — |
| **Order** | `orders/models.py` | `tenant` (FK, null=True) | `collection_center` (FK to CollectionCenter, null=True) | `collection_branch` (FK Branch), `processing_branch` (FK Branch); no `origin_branch` |
| **Sample** | `samples/models.py` | `tenant` (FK, null=True) | — | `collected_at_branch`, `current_branch` (Branch FKs) |

**Summary:** Patient uses `registration_center` (CollectionCenter). Order uses `collection_branch` (Branch) and `collection_center` (CollectionCenter). No `origin_branch` on Order; `collection_branch` is the origin at creation.

---

## Optional Module Merge: Collection Center

- **TenantSettings** (`core.TenantSettings`): OneToOne per tenant; `enable_collection_centers` (default False), `default_branch`, `default_collection_center`.
- **Getter:** `apps.core.services.settings.get_tenant_settings(tenant)` — creates with safe defaults if missing.
- **API:** GET/PATCH `GET /api/v1/core/settings/tenant/` (authenticated; PATCH admin only).
- When **OFF:** No required registration_center anywhere; invalid or Branch id in `registration_center` is ignored (set to None).
- When **ON:** Patient create may require a collection center (or use default); backend accepts `branch` (Branch id) and maps to CollectionCenter by code; compatibility bridge accepts `registration_center` value that is a Branch pk and maps by code.

---

## API Contract: OFF vs ON

| Mode | Patient create | Order create |
|------|----------------|--------------|
| **OFF** | `registration_center` and `branch` optional; invalid values ignored. | `collection_branch` defaulted from user or tenant `default_branch`; 400 if no branch. |
| **ON** | Center required unless tenant has `default_collection_center`. Send `registration_center` (CC pk) or `branch` (Branch id). | Same as OFF. |

---

## Compatibility Bridge and Removal Plan

- **Bridge:** When `enable_collection_centers` is True, payload `registration_center` that is a **Branch** pk (not a CollectionCenter pk) is resolved by looking up Branch and get_or_create CollectionCenter with same `code`. Comment in code: "Compatibility bridge: remove after UI migration, gated by enable_collection_centers."
- **Removal:** After UI sends only `branch` (Branch id) when centers ON, backend can stop accepting Branch pk in `registration_center` and require either valid CC pk or `branch`.

---

## Data Migration Notes

- **0009_backfill_tenant_on_patient_order** (core): Backfills `Patient.tenant` and `Order.tenant` where NULL — infers from `created_by.tenant` / `ordered_by.tenant` when possible, else default tenant.
- No migration changes FKs to NOT NULL; all remain nullable for safe rollout.

---

## Dispatch Scope Decision

- **Implemented (Phase-1B):** `Dispatch` and `DispatchItem` in `orders` app; POST `/api/v1/orders/dispatches/` (create), POST `dispatches/{id}/send/` (IN_TRANSIT), POST `dispatches/{id}/receive/` (RECEIVED; sets samples to RECEIVED).
- Branch users can create/send only for their branch; receiving branch user can call receive.
- Manifest printing (e.g. PDF) left for Phase-D if needed.

---

## How to toggle Collection Centers

- **Django Admin:** Core → Tenant settings → select tenant → set **Enable collection centers** and optionally **Default collection center** / **Default branch**; save.
- **API (admin only):** `PATCH /api/v1/core/settings/tenant/` with body e.g. `{"enable_collection_centers": true, "default_collection_center": <id>}`. All users of that tenant then see collection center behaviour according to the flag.
