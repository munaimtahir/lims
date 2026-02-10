Endpoint → Rule Enforcement

- `POST /api/v1/results/{id}/verify/`
  - Requires `results.can_verify_results` (403 otherwise)
  - DRAFT → VERIFIED only; 409 if already VERIFIED/FINAL; 400 if value missing
  - Atomic; select-for-update prevents double-verify

- `POST /api/v1/results/{id}/finalize/`
  - Requires `results.can_verify_results` (403)
  - VERIFIED → FINAL only; 409 if already FINAL; 400 if value missing
  - Atomic; select-for-update

- `POST /api/v1/results/bulk_entry/`
  - Edits allowed only while DRAFT; errors returned per row
  - Uses transactions; rejects edits of VERIFIED/FINAL (400)

- `POST /api/v1/results/bulk-verify/`
  - Permission enforced (403)
  - Skips already VERIFIED/FINAL with 400 + detail; requires value

- `POST /api/v1/results/bulk-finalize/`
  - Permission enforced (403)
  - Requires VERIFIED and value; 400 with detail when invalid

- `PATCH /api/v1/samples/{id}/`
  - Enforces PENDING/POSTPONED → COLLECTED → RECEIVED; other transitions 400
  - Collected/received edits guarded; received terminal
  - Idempotent double COLLECTED returns 200 unchanged

- `DELETE /api/v1/samples/{id}/`
  - 400 if status COLLECTED/RECEIVED

- `POST /api/v1/reports/generate/`
  - Blocks regeneration overwrite of FINAL (409); uses FINAL-only download gate

- `GET /api/v1/reports/{id}/download/`
  - 403 unless status FINAL/AMENDED; 404 if file missing

- `PATCH /api/v1/orders/orders/{id}/`
  - Model-level guard: lab_number immutable; PUBLISHED/CANCELLED mutations raise ValidationError (surfaced as 400/409 via DRF)
  - Status transitions validated (no skipping; no exit from terminal)
