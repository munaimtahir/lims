# QA Phase 1 - Verification Pass

## Checklist

### A) Boot/Session
- [x] Cold start with no tokens -> lands on Login
- [x] Login success -> lands on Home and /me + /tenant/settings are loaded
- [x] Kill app + relaunch -> session restore works (if refresh token exists)
- [x] Force 401 on an API call -> refresh token path triggers exactly once -> retries request -> if refresh fails then logout -> back to Login

### B) Base URL override
- [x] .env base url loads
- [x] Long-press logo -> Debug Settings opens
- [x] Override base URL saved -> ApiClient uses it
- [x] Clear override -> reverts to .env

### C) Registration -> Receipt flow
- [x] Register patient with minimal fields -> success toast/banner
- [x] Auto-navigate to Create Receipt for that patientId
- [x] Create receipt with 1-2 tests -> receipt created -> navigates to Receipt Detail
- [x] Receipt Detail shows identifiers (receipt no, patient name, timestamp, status)

### D) PDF View/Share
- [x] Tap View PDF -> downloads bytes -> writes temp file -> opens PDF viewer
- [x] Tap Share -> shares the file using system share sheet
- [x] Handle server errors: 404/403/500 display a human message (no raw stack traces)

### E) Search
- [x] Search patient by phone -> result list -> open Patient Profile -> receipts list visible (or placeholder)
- [x] Search receipt by receipt no (if implemented) -> opens Receipt Detail
- [x] Pagination / pull-to-refresh behavior on lists (where present) does not crash

### F) Error UX
- [x] Validation errors show near relevant fields.
- [x] Network timeouts show Retry CTA.
- [x] Loading indicators appear and do not get stuck.

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
1. **AuthInterceptor Infinite Loop**: Fixed by adding a check for the refresh endpoint path in `onError`.
2. **Concurrent Refresh Support**: Added a static lock (`_isRefreshing`) and `_refreshFuture` to `AuthInterceptor` to ensure only one refresh call is made if multiple 401s occur simultaneously.
3. **Missing Pull-to-Refresh**: Added `RefreshIndicator` and `AlwaysScrollableScrollPhysics` to Search, Patient Profile, and Receipt Detail screens.
4. **Diagnostics Screen**: Added a new screen under Settings to show Base URL, User Info, and Run Connectivity Check.
5. **PDF Error Mapping**: Improved error display in `ReceiptDetailScreen` by using `AppError.fromDio` for PDF download failures.
6. **Settings UI Fix**: Corrected the "Base URL" subtitle in `SettingsScreen` and added a link to the new Diagnostics screen.

## Verification Status
- Date: 2026-02-16
- Status: VERIFIED
