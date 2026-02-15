# Branch / Collection Center Phase-1 — Smoke Test Plan

## Objective

Automated smoke tests verify end-to-end:

1. Create patient (tenant + optional branch/center set)
2. Create order with branch context
3. Print receipt (or generate receipt payload)
4. Mark sample collected
5. (Optional) Create dispatch; receive dispatch at main lab

Current codebase has no Dispatch model; “receive” is implemented as marking samples RECEIVED. Smoke tests use **API only** (Django APIClient or pytest + requests).

---

## Scope

- **Mandatory:** API smoke (patient → order → payment → sample collected).
- **Branch-specific:** Login as user with branch; create patient and order; assert order has `collection_branch` and patient has `tenant`; assert result entry forbidden for COLLECT_ONLY branch.
- **Optional:** Playwright UI smoke (same flow in browser).

---

## Environment

- Base URL: `http://127.0.0.1:8012` (or `BASE_URL` env).
- API prefix: `/api/v1`.
- Requires: backend + DB + migrations applied; demo users (and optionally `seed_branches` + tenant/branch on users) for branch flow.

---

## Existing asset

- **Script:** `scripts/smoke_flow.sh` — curl-based: login (receptionist) → create patient → get tests → create order → payment → mark sample collected → result entry → verify → report/receipt download.
- **Gap:** Does not set or assert branch; does not test branch user or “no result entry at branch”.

---

## Smoke test design

### 1. API smoke (pytest + Django APIClient) — recommended

- **Location:** e.g. `lims-backend/apps/core/tests/test_smoke_branch_flow.py` or `lims-backend/tests/test_smoke_branch_api.py`.
- **Steps:**
  1. Ensure tenant and HQ branch exist (fixture or migration).
  2. Create or use user with tenant and one branch membership.
  3. POST login (JWT or session as needed).
  4. POST create patient (minimal payload); assert 201; assert `tenant` in response or fetch and assert.
  5. GET tests; pick one test id.
  6. POST create order (patient, test_ids, optional collection_branch); assert 201; assert `collection_branch` present when user has branch.
  7. POST payment for order; assert 201.
  8. GET samples for order; PATCH one sample to COLLECTED with barcode; assert 200.
  9. (Optional) For COLLECT_ONLY branch user: POST result entry; assert 400 with “collection-only” or equivalent.
- **Run:** `pytest lims-backend/apps/core/tests/test_smoke_branch_flow.py -v`

### 2. API smoke (curl script)

- **Location:** `scripts/smoke_flow_branch.sh`.
- **Steps:** Same as above using curl; parse JSON for ids and tokens; exit 1 on any failure.
- **Run:** `./scripts/smoke_flow_branch.sh` (or `BASE_URL=http://... ./scripts/smoke_flow_branch.sh`).

### 3. Receipt / print

- **Option A:** GET receipt URL (e.g. `payments/{id}/receipt/`) and assert 200 and non-zero body.
- **Option B:** Call internal “generate receipt payload” endpoint if exists; assert 200.

### 4. Dispatch receive (when implemented)

- When Dispatch exists: POST create dispatch (branch, order ids); POST receive dispatch (main lab user); assert samples RECEIVED and dispatch status updated.
- Until then: smoke “receive” = PATCH sample to RECEIVED (as in existing flow).

---

## Minimal test code (pytest + APIClient)

See `lims-backend/apps/core/tests/test_smoke_branch_flow.py` (created below). It uses Django test client and JWT/session as configured in the project.

---

## Acceptance criteria for “smoke passing”

- Patient create returns 201 and patient has tenant.
- Order create returns 201 and order has collection_branch when user has branch.
- Sample can be marked COLLECTED; receipt can be retrieved (200).
- For COLLECT_ONLY branch user, result entry returns 403/400 with clear message.

---

## Mandatory cases (Phase-1 optional module)

### 1) Collection centers OFF

- Create patient **without** `registration_center` → 201 OK.
- Create patient with **invalid** `registration_center` (e.g. Branch id) → value ignored → 201 OK.
- Create order **without** `collection_branch` → defaults from user or tenant default_branch → 201 OK.

### 2) Collection centers ON

- With **default center** set: create patient without providing center → 201 OK (default applied).
- **Without** default center: create patient without center → 400 with friendly "Please select a collection center."

### 3) Dispatch (Phase-1B)

- Create dispatch from collected order(s) → 201.
- POST `dispatches/{id}/send/` → 200 (IN_TRANSIT).
- POST `dispatches/{id}/receive/` (main lab) → 200; samples RECEIVED, dispatch RECEIVED.
