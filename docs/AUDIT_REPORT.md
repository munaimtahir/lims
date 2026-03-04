u# Audit Report & Implementation Plan

**Date:** 2026-02-19
**Author:** Senior Platform Engineer

## Findings

### 1. Workflow State Consistency
- **Current State:**
  - `Order`, `OrderItem`, `TestResult`, and `Sample` each have their own status fields.
  - Transitions are partially enforced in `models.save()` methods (e.g., `Order.validate_status_transition`), but there is no central orchestration.
  - Risk of "split brain": Order says `VERIFIED` but Items are `NEW`.
- **Fix Plan:**
  - Introduce `OrderWorkflowService` as the **Single Source of Truth** for status mutations.
  - Status changes will ripple down (Order -> Items) or bubble up (Items -> Order) deterministically.
  - `Order.status` will be the primary driver.

### 2. Cross-Patient & Scoping Leakage
- **Current State:**
  - Frontend queries often fetch lists without strict order/patient scoping in all views.
  - `Sample` and `Verification` queues run the risk of showing mixed items if not strictly filtered by `order_id`.
- **Fix Plan:**
  - Enforce **Order-Centric** views.
  - Verification Queue will return a list of *Orders*, not loose *Results*.
  - Detail views will strictly require `order_id` in the URL/Query.
  - Test suite will explicitely check for cross-order leakage.

### 3. Deployment Ambiguity
- **Current State:**
  - `docker-compose.yml` mounts `./lims-backend/media` to `/app/media`.
  - Deployment uses a `Dockerfile` that installs to system Python, but a local `.venv` exists.
  - Permission errors reported for report generation (likely UID mismatch on host mounted volumes).
- **Fix Plan:**
  - **Single Canonical Deployment:** Docker-only. No local `venv` usage for production.
  - **Reports:** Move report output to a dedicate `reports/` directory with explicit permissions (volume mount).
  - Add version/commit hash stamp to ensure client/server alignment.

### 4. Codebase & Structure
- **Backend:** Django 4.x/5.x (Python 3.12). Structure is standard but `apps/orders/models.py` has too much business logic in `save()`.
- **Frontend:** React/Vite. Uses `axios` for API.
- **Legacy:** "V2 Lab Numbering" logic exists in `Order.save()`.

## Phase 1: Workflow State Machine (Backend)

### Goal
Enforce ONE GLOBAL STATUS.

### Implementation Steps
1.  **Define Status Hierarchy:**
    - `DRAFT`: Order created, tests added.
    - `RECEIVED`: Samples collected/received.
    - `PROCESSING`: Results being entered.
    - `VERIFIED`: All required results verified.
    - `PUBLISHED`: Report generated/sent.
2.  **Create `OrderWorkflowService`:**
    - Methods: `receive_sample()`, `enter_result()`, `verify_order()`, `publish_order()`.
    - These methods update `Order.status` and related `OrderItem`/`Sample` statuses atomically.
    - **No direct status manipulation allowed in Views.**
3.  **Refactor Models:**
    - Remove logic from `Order.save()` that mutates logic based on status changes (move to Service).
    - Keep `validate_status_transition` as a safety net.

## Phase 2: Order-Centric Queues (API + Frontend)

### Goal
Eliminate "loose items" in queues.

### Implementation Steps
1.  **Backend:**
    - `GET /api/workflow/verification_queue/`: Returns `List[OrderSummary]`.
    - `GET /api/workflow/orders/{id}/verification/`: Returns full verification context for ONE order.
2.  **Frontend:**
    - Rewrite `VerificationQueuePage.tsx` to display Order Cards.
    - Clicking an Order opens `VerificationDetail` (modal or page) scoped to that Order.

## Phase 3: Reports & Permissions

### Goal
Fix `permission denied`.

### Implementation Steps
1.  **Volume:** Create `docker_reports_data` volume or host mount to `/var/lib/lims/reports`.
2.  **Config:** Set `REPORT_OUTPUT_DIR` env var.
3.  **Permissions:** Ensure `chown 1000:1000` on the target directory.

## Phase 4: Deployment Decontamination

### Goal
One way to run.

### Implementation Steps
1.  **Dockerfile:** Ensure clean build.
2.  **Compose:** Use `docker-compose.prod.yml` exclusively for prod.
3.  **Cleanup:** Remove ambiguous scripts.

## Phase 5: Verification

1.  **Smoke Script:** `scripts/smoke_workflow.sh`
2.  **End-to-End Test:** Full patient -> order -> report cycle.
