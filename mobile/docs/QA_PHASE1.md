# QA Phase 1 - Verification Pass

## Checklist

### A) Boot/Session
- [ ] Cold start with no tokens -> lands on Login
- [ ] Login success -> lands on Home and /me + /tenant/settings are loaded
- [ ] Kill app + relaunch -> session restore works (if refresh token exists)
- [ ] Force 401 on an API call -> refresh token path triggers exactly once -> retries request -> if refresh fails then logout -> back to Login

### B) Base URL override
- [ ] .env base url loads
- [ ] Long-press logo -> Debug Settings opens
- [ ] Override base URL saved -> ApiClient uses it
- [ ] Clear override -> reverts to .env

### C) Registration -> Receipt flow
- [ ] Register patient with minimal fields -> success toast/banner
- [ ] Auto-navigate to Create Receipt for that patientId
- [ ] Create receipt with 1-2 tests -> receipt created -> navigates to Receipt Detail
- [ ] Receipt Detail shows identifiers (receipt no, patient name, timestamp, status)

### D) PDF View/Share
- [ ] Tap View PDF -> downloads bytes -> writes temp file -> opens PDF viewer
- [ ] Tap Share -> shares the file using system share sheet
- [ ] Handle server errors: 404/403/500 display a human message (no raw stack traces)

### E) Search
- [ ] Search patient by phone -> result list -> open Patient Profile -> receipts list visible (or placeholder)
- [ ] Search receipt by receipt no (if implemented) -> opens Receipt Detail
- [ ] Pagination / pull-to-refresh behavior on lists (where present) does not crash

### F) Error UX
- [ ] Validation errors show near relevant fields.
- [ ] Network timeouts show Retry CTA.
- [ ] Loading indicators appear and do not get stuck.

## How to run locally
1. Ensure Flutter is installed.
2. Clone repository.
3. Run `flutter pub get`.
4. Copy `.env.example` to `.env` and set `API_BASE_URL`.
5. Run `flutter run`.

## Known Backend Dependencies
- `/api/v1/auth/login/`
- `/api/v1/auth/refresh/`
- `/api/v1/me/`
- `/api/v1/tenant/settings/`
- `/api/v1/patients/`
- `/api/v1/patients/search/`
- `/api/v1/orders/`
- `/api/v1/receipts/`
- `/api/v1/receipts/{id}/pdf/`

## Issues Found + Fixes Applied
(To be populated)

## Verification Status
- Date: 2026-02-16
- Status: In Progress
