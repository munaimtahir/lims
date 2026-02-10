## Phase 2A — Guardrails & State Enforcement

Enforced (server-side)
- Orders: immutable `lab_number`; edits blocked after PUBLISHED/CANCELLED; state transitions validated per authoritative model.
- Samples: transition graph enforced; double COLLECTED idempotent; REJECT/POSTPONE limited; deletion blocked after COLLECTED/RECEIVED; RECEIVED terminal.
- Results: DRAFT→VERIFIED→FINAL only; verify/final require value; edits blocked after VERIFIED; FINAL immutable; double verify/final returns 409; select-for-update used for concurrency.
- Reports: download allowed only FINAL/AMENDED; FINAL report file/status immutable; regeneration of FINAL blocked.
- Transactions: critical transitions wrapped in DB transactions.

Deferred / Not in scope
- Receipt override path (admin-only) is not yet implemented beyond existing immutability; pending confirmation of override UX.
- Frontend-only hardening beyond status lock tooltips is minimal by design for Phase 2A.

Tests added
- `apps/results/tests/test_state_guards.py`
- `apps/samples/tests/test_state_guards.py`
