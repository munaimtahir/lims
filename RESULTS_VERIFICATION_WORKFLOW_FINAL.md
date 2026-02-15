# Results Verification Workflow - Final Documentation

## 1. Statuses and Lifecycle

### Test Result Statuses
- **DRAFT**: Initial creation. Optional fields may be missing.
- **ENTERED**: Tech has entered data. All required fields must be present (or ABSENT confirmed).
- **VERIFIED**: Pathologist has approved the result. Locked for editing.
- **FINAL**: Report generated/finalized. Archival state.
- **REJECTED**: (Internal) Not typically persisted as a status, but used as a transition to return to ENTERED with reason.

### Order / Order Item Statuses
Derived automatically from Test Result statuses:
- **NEW**: Order created, no samples collected.
- **COLLECTED**: Samples collected.
- **IN_PROCESS**: At least one result is DRAFT or ENTERED, or mixed statuses.
- **VERIFIED**: All results in the order/item are VERIFIED (or FINAL).
- **PUBLISHED**: Final report generated.

## 2. Transition Rules

### Verification Rules
- **Required Parameters**: A result marked `is_required=True` (TestParameter) MUST have a value to be Verified.
- **Optional Parameters**: Can be empty/null without blocking verification.
- **ABSENT Logic**: If a result is truly absent (e.g. quantity not sufficient), it should be marked explicitly (e.g. "ABSENT") or handled via specific flag if implemented. Currently, empty optional strings allow verification.

### Order Status Derivation
- When a Test Result status changes:
  1. **OrderItem Status**:
     - Becomes **VERIFIED** if *all* its results are VERIFIED/FINAL.
     - Becomes **IN_PROCESS** if *any* result exists but not all are verified.
  2. **Order Status**:
     - Becomes **VERIFIED** if *all* items are VERIFIED/PUBLISHED.
     - Becomes **IN_PROCESS** if *any* item is IN_PROCESS or VERIFIED (but not all).
- **Reversion**: Un-verifying a result triggers OrderItem and Order to revert from VERIFIED to IN_PROCESS.

## 3. API Endpoints

### Verification Queue
- `GET /api/v1/results/verification_queue/`: Returns grouped orders with pending results.
  - Structure: `{ "queue": [ { "order_id": ..., "items": [...] }, ... ] }`

### Actions
- `POST /api/v1/results/{id}/verify/`: Verify single result.
- `POST /api/v1/results/{id}/reject/`: Unverify/Return result. Requires `reason`.
- `POST /api/v1/results/bulk-verify/`: Verify multiple results.
- `POST /api/v1/results/bulk-reject/`: Unverify multiple results. Requires `reason`.
- `POST /api/v1/results/bulk_entry/`: Enter multiple results (Technician).

### Reports
- `POST /api/v1/reports/generate/`: Generate report. Use `is_final=false` for Draft/Preview.

## 4. Manual Testing Checklist

| &nbsp; | Scenario | Expected Outcome |
| :--- | :--- | :--- |
| [ ] | **Tech Entry** | Enter results for Order X. Ensure Order status -> `IN_PROCESS`. |
| [ ] | **Queue Visibility** | Log in as Pathologist. Check Verification Queue. Order X should appear. |
| [ ] | **Detail View** | Click Order X. Verify patient info and test list are correct. |
| [ ] | **Single Label** | Verify tests with "Result" parameter show nicely (e.g. "Typhoid -> Positive"). |
| [ ] | **Verify Required** | Enter value for required param. Click Verify. Status -> VERIFIED. |
| [ ] | **Verify Missing** | Clear value for required param. Click Verify. Should Error ("Required"). |
| [ ] | **Verify Optional** | Leave optional param empty. Click Verify. Should Success. |
| [ ] | **Order Completion** | Verify ALL results for Order X. Order status -> `VERIFIED`. Disappears from Queue. |
| [ ] | **Unverify Flow** | Go to Patient History / Search Order X. Click Unverify/Reject on a result. Order status -> `IN_PROCESS`. |
| [ ] | **Preview Report** | Click "Preview Report" in queue. Should open DRAFT PDF in new tab. |
| [ ] | **Final Report** | Verify all results. Check if Final Report is generated (or generate manually via Reports). |
