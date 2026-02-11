# PHASE 2A STATUS (Guardrails & State Enforcement)

## Scope Completed
- Added centralized transition services:
  - `lims-backend/apps/orders/services.py` (`transition_visit_state`)
  - `lims-backend/apps/samples/services.py` (`transition_sample_state`, `reject_sample`)
  - `lims-backend/apps/results/services/transitions.py` (`transition_result_state`)
  - `lims-backend/apps/reports/services.py` (`transition_report_state`)
  - `lims-backend/apps/billing/services.py` (`transition_receipt_state`, `admin_override_receipt`)
- Wired transitions into API control points (orders/samples/results/reports/billing).
- Added DB locking + transaction boundaries for critical transitions (`transaction.atomic`, `select_for_update`).
- Enforced terminal/immutable behavior:
  - Order terminal states (`PUBLISHED`, `CANCELLED`) blocked from transition.
  - Sample `RECEIVED` terminal; double `COLLECTED` blocked.
  - Result `FINAL` immutable; `DRAFT -> VERIFIED -> FINAL` enforced.
  - Report `FINAL/AMENDED` immutable + delete blocked.
  - Receipt immutable via blocked update/delete and explicit admin override action.
- API response discipline applied on hardened endpoints:
  - `400` invalid payload
  - `403` permission
  - `409` invalid state
  - payload contains `detail`.

## Validation Evidence
- Targeted hardening tests passed:
  - `DEPLOY_RUNS/PHASE_2_HARDENING/logs/phase2_hardening_pytest.txt`
- Django integrity check passed:
  - `DEPLOY_RUNS/PHASE_2_HARDENING/logs/django_check.txt`

## Notes
- Legacy tests expecting pre-hardening behavior (idempotent collect, non-409 transition errors, older report regeneration semantics) may fail by design after hardening.
