# Phase 2 State Machines (Authoritative)

Single source of truth for workflow states and who may move them. These
transitions are enforced server-side and mirrored in the UI. All roles refer to
the built-in user roles; any custom role must map to the same permissions.

## Order / Visit (Lab Number = Visit ID)
- **States:** NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED; CANCELLED (terminal)
- **Allowed transitions**
  - NEW → COLLECTED (Phlebotomist, Admin, Manager)
  - COLLECTED → IN_PROCESS (Lab Technician, Admin, Manager)
  - IN_PROCESS → VERIFIED (requires `results.can_verify_results` — Pathologist/Admin/Manager)
  - VERIFIED → PUBLISHED (requires `results.can_verify_results`)
  - NEW/COLLECTED/IN_PROCESS/VERIFIED → CANCELLED (Admin, Manager)
- **Forbidden:** skipping steps (e.g., NEW → VERIFIED), any transition out of PUBLISHED/CANCELLED, editing `lab_number` after creation.

## Sample
- **States:** PENDING → COLLECTED → RECEIVED; POSTPONED; REJECTED (explicit action only)
- **Allowed transitions**
  - PENDING → COLLECTED (Phlebotomist, Admin, Manager)
  - PENDING → POSTPONED (Phlebotomist, Admin, Manager)
  - POSTPONED → COLLECTED (same as above)
  - COLLECTED → RECEIVED (Lab Technician, Admin, Manager)
  - PENDING/COLLECTED → REJECTED (Pathologist/Admin/Manager)
- **Forbidden:** marking COLLECTED twice; edits or deletion once COLLECTED/RECEIVED except privileged override (Admin/Manager only); RECEIVED is terminal.

## Result Entry / Reported Result (per test parameter)
- **States:** DRAFT → VERIFIED → FINAL
- **Allowed transitions**
  - DRAFT → VERIFIED (requires `results.can_verify_results` **and** valid result payload)
  - VERIFIED → FINAL (requires `results.can_verify_results`)
- **Forbidden:** any transition from FINAL; reverting VERIFIED → DRAFT; editing values after VERIFIED/FINAL; verifying with missing/placeholder values.

## Report Artifact (PDF)
- **States:** DRAFT → FINAL; AMENDED (new record linked to prior FINAL); CANCELLED (for drafts only)
- **Allowed transitions**
  - DRAFT → FINAL (requires verifier permission)
  - FINAL → AMENDED (creates a new FINAL report with `amended_from` set)
  - DRAFT → CANCELLED (Admin/Manager)
- **Forbidden:** modifying or regenerating a FINAL report in place; downloading as “final” when status ≠ FINAL/AMENDED; deleting FINAL/AMENDED.

## Receipt / Billing Artifact
- **State:** RECORDED (immutable)
- **Forbidden:** deletion or mutation that desynchronizes payment totals; updates require explicit admin override.

> All state changes must be executed inside DB transactions and return 4xx with
> a clear message when blocked. UI must disable forbidden actions and surface
> the same messages.
