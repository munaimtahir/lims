# E2E Smoke Test Status Matrix

**Date:** 2026-02-15  
**Run ID:** 20260215_182915  
**Environment:** Docker Compose (http://127.0.0.1:8012)

## Steps 1–8: PASS/FAIL

| Step | Description | Status | Reason |
|------|-------------|--------|--------|
| 1 | Register patient | PASS | Patient created via POST /api/v1/patients/ |
| 2 | Create order | PASS | Order created, samples auto-created |
| 3 | Generate receipt/payment | PASS | Payment recorded, receipt downloaded |
| 4 | Collect sample | PASS | Sample marked COLLECTED |
| 5 | Enter results | PASS | Result entered via bulk_entry |
| 6 | Verify results | PASS | Result verified |
| 7 | Generate and download report PDF | PASS | Report generated, PDF downloaded |
| 8 | Patient search, report accessible | PASS | Verified |

## Evidence

- smoke_run.log – Commands and outputs
- api_smoke_flow.md – Curl flow
- scripts/smoke_flow.sh – Script

**26/26 tests passed (100%)**
