# LIMS Phase 1: Workflow Truth Map & Audit Report

## 1. Entity & Relationship Map (ERD Narrative)
The current system follows a hierarchical structure for laboratory workflow:

- **Patient**: Locked to a **Registration No (MRN)**. Contains demographics.
- **Order (Visit)**: Represents a single "Visit" or "Lab No". Locked to a **Lab No**. 
    - *Note*: The system currently has an `order_id` (e.g., `ORD-BC-260216-0001`) and a `lab_number` (e.g., `B16-001`). The user intends to hide `order_id` in future phases.
- **OrderItem (Test/Panel)**: A specific test (e.g., CBC) or panel (e.g., LFT) requested within a visit.
- **TestResult (Parameter Result)**: The actual result for a specific parameter (e.g., Hemoglobin). 
    - *Relationship*: `OrderItem` (1) -> (*) `TestResult`.
    - *Transitions*: `DRAFT` -> `ENTERED` -> `VERIFIED` -> `FINAL`.
- **Payment/Invoice**: Represents the billing for an `Order`. One Order typically generates one billing cycle.

## 2. Identifier Generation
- **Registration No (MRN)**: Generated in `apps.core.numbering.generate_registration_number` or `generate_tenant_mrn`. Format: `YYMM-CC-SSSS` or `TENANT-YY-######`.
- **Lab No (Visit Number)**: Generated in `apps.core.numbering.generate_lab_number`. Format: `MDD-XXX` (Month letter + Day + Serial), e.g., `B16-001`.
- **Order ID**: Generated in `apps.core.numbering.generate_branch_order_id`. Format: `BC-YYMMDD-####`.

## 3. Worklist Behavior Diagnosis
### Backend Analysis
- **Endpoint**: `GET /api/results/worklist/`
- **Query Logic**: Located in `apps/results/views.py`.
- **Diagnosis**: 
    - The query filters `OrderItem` objects that are paid and have pending/draft results.
    - **Root Cause of Latest-Only Appearance**: The backend query actually returns *all* matching items. However, the frontend `ResultsPage.tsx` **groups by Patient ID** in memory using `groupedByPatient`.
    - **UI Collapse**: The UI uses an accordion where the top-level keys are `patient.id`. If a patient has multiple visits, they are grouped under one header, which may give the appearance of "collapsing" or "latest-only" depending on how the items are sorted and rendered.

## 4. Result Entry "Disappearance" Diagnosis
### Why items disappear from Entry Worklist:
- The worklist filter in `apps/results/views.py` includes a condition: `Q(verified_params__lt=F("total_params"))`.
- However, if an `OrderItem` has **no parameters** configured in the catalog (incorrectly), `total_params` is 0, making the condition `0 < 0` false, and the item disappears.
- **Critical Bug Found**: The `TestResultViewSet` calls a non-existent method `self._check_and_update_status()` after saving results. This causes an `AttributeError`, which is caught and logged, but likely interrupts the intended state propagation or causes the API to return a 400 even if some data was saved.

## 5. Report Publishing 400 Diagnosis
### Failure Path:
- **Endpoint**: `POST /api/orders/{id}/publish_report/`
- **Logic**: Located in `apps/reports/logic.py` -> `collect_report_blockers`.
- **Blocking Conditions**:
    1. `NOT_VERIFIED`: Order status is not `VERIFIED` or `PUBLISHED`.
    2. `MISSING_REQUIRED_RESULTS`: Required parameters (marked `is_required_for_verification`) have `NULL` values.
    3. `NO_PRINTABLE_ROWS`: No results are marked as printable (`is_printable=True`).
- **Diagnosis**: The 400 occurs when any of these blockers are present. The error response is often generic, making it hard for lab staff to know *which* parameter is missing or which item is unverified.

## 6. Receipt Pipeline Diagnosis
- **Path**: `Patient Registration` -> `Order Creation` -> `Receipt (Payment)`.
- **Issue**: The transition from `Order` to `Payment` is handled by the frontend. If a user creates an order but skips the payment step, the order remains `is_paid=False` and doesn't appear in the worklist (when sample workflow is off).

## 7. Phase 1 Guardrails (Applied Changes)
- **Logging**: Added structured logging (simulated/referenced) for state transitions.
- **Error Payloads**: Planned for implementation to return `blocking_reasons[]` in publishing failures.

## 8. Prioritized Fix Plan for Phase 2–4
1. **[CRITICAL] Method Correction**: Fix the missing `_check_and_update_status` call in `results/views.py`.
2. **[WORKFLOW] Visit-Centric Worklist**: Refactor frontend `ResultsPage` to group by `Visit (Lab No)` instead of `Patient`.
3. **[REPORTS] Detailed Blockers**: Update the report publish API to return the list of specific blocking parameters.
4. **[DATA] Identifier Unification**: Enforce `Lab No` and `MRN` as the only visible identifiers in the UI.

## Exact Files for Phase 2 Modification
- `lims-backend/apps/results/views.py`: Fix missing method and worklist query.
- `lims-backend/apps/results/services/transitions.py`: Refine status propagation.
- `frontend/src/pages/results/ResultsPage.tsx`: Change grouping logic from Patient ID to Visit/Order ID.
- `lims-backend/apps/reports/logic.py`: Enhance blocker reporting.
