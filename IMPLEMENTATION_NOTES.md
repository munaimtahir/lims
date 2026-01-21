# LIMS UI + Workflow Upgrade - Implementation Notes

## Overview
Complete implementation of branding system and streamlined Registration→Order fast flow.

## Backend Changes

### 1. Database Changes
- **File**: `lims-backend/apps/core/models.py`
  - Added `lab_display_name` field to `SystemSettings` model
- **Migration**: `lims-backend/apps/core/migrations/0004_add_lab_display_name.py`
  - Run migration: `python3 manage.py migrate core`

### 2. API Endpoints Added

#### Patient Lookup
- **Endpoint**: `GET /api/patients/lookup/?mobile={phone}`
- **Purpose**: Fast patient search by mobile number for registration
- **Returns**: List of matching patients with summary info
- **File**: `lims-backend/apps/patients/views.py`

#### Test Search
- **Endpoint**: `GET /api/laboratory/tests/search/?q={query}&limit={limit}`
- **Purpose**: Fast test search by name or code for order entry
- **Returns**: List of matching tests with essential info
- **File**: `lims-backend/apps/laboratory/views.py`

### 3. Existing Endpoints Utilized
- Branding settings: `GET/PUT/PATCH /api/core/settings/`
- Order creation already supports all payment fields (discount_percent, paid_amount, due_amount)

## Frontend Changes

### 1. Branding System

#### New Components
- **BrandingContext** (`frontend/src/contexts/BrandingContext.tsx`)
  - Provides branding settings across the app
  - Fetches lab_display_name and lab_logo

#### Updated Components
- **DashboardLayout** (`frontend/src/components/dashboard/DashboardLayout.tsx`)
  - Header now shows logo + lab display name
  - Clickable brand block navigates to home
  - Keyboard accessible

- **LoginPage** (`frontend/src/pages/auth/LoginPage.tsx`)
  - Shows same branding (logo + name)
  - Clean centered layout

- **SystemSettingsPage** (`frontend/src/pages/settings/SystemSettingsPage.tsx`)
  - New "UI Update" tab
  - Upload/remove lab logo (PNG, JPG, JPEG, WEBP up to 5MB)
  - Edit lab display name
  - Live preview of branding

### 2. Registration & Order Flow

#### New Registration Page (`frontend/src/pages/registration/RegistrationPage.tsx`)
Features:
- **Mobile-first workflow**: Mobile number field auto-focused on load
- **Type-ahead patient lookup**: 
  - Debounced search (300ms) as user types
  - Shows patient suggestions with name, age, gender, last visit
  - Arrow keys to navigate, Enter to select, Escape to close
  - Auto-populates form when patient selected
- **Patient form**: Full name, age, gender, address, father/husband name
- **Seamless transition**: After saving patient, order form auto-opens with test search focused

#### Order Form Features
- **Test search**:
  - Type-ahead search (200ms debounce)
  - Search by test name or code
  - Arrow keys + Enter to add tests
  - Focus stays in search after adding
- **Added tests list**:
  - Shows test code, name, price
  - Remove button for each test
- **Payment section**:
  - Total amount (auto-calculated)
  - Discount % and Discount Amount (linked fields)
  - Paid Amount (auto-fills to net payable)
  - Due Amount (auto-calculated, highlighted if > 0)
  - Referred By field

#### Routing
- Added route: `/dashboard/registration`
- Added to sidebar for Admin and Receptionist roles

### 3. TypeScript Types Updated
- **File**: `frontend/src/types/index.ts`
  - Added `PatientLookupResult` interface
  - Added `TestSearchResult` interface
  - Updated `SystemSettings` with `lab_display_name`
  - Updated `Order` with payment fields
  - Updated `OrderCreateRequest` with payment fields

### 4. API Services Updated
- **File**: `frontend/src/api/services.ts`
  - Added `patientApi.lookup(mobile)`
  - Added `laboratoryApi.searchTests(query, limit)`

## Media/Logo Configuration

### Django Settings
Current setup in `lims-backend/config/settings/`:
- `MEDIA_URL` and `MEDIA_ROOT` should be configured
- Media files served via Django in development
- In production with Caddy:
  - Static files served from `/static/`
  - Media files served from `/media/`

### Caddy Configuration
Ensure your Caddyfile has media file routing:
```
handle /media/* {
    root * /path/to/lims-backend
    file_server
}
```

## Files Changed

### Backend
1. `lims-backend/apps/core/models.py` - Added lab_display_name field
2. `lims-backend/apps/core/serializers.py` - Added lab_display_name to serializer
3. `lims-backend/apps/core/migrations/0004_add_lab_display_name.py` - New migration
4. `lims-backend/apps/patients/views.py` - Added lookup endpoint
5. `lims-backend/apps/laboratory/views.py` - Added search endpoint

### Frontend
1. `frontend/src/App.tsx` - Added BrandingProvider, Registration route
2. `frontend/src/types/index.ts` - Added new types
3. `frontend/src/api/services.ts` - Added new API calls
4. `frontend/src/contexts/BrandingContext.tsx` - New branding context
5. `frontend/src/components/dashboard/DashboardLayout.tsx` - Updated header
6. `frontend/src/components/dashboard/DashboardLayout.module.css` - Added logo styles
7. `frontend/src/pages/auth/LoginPage.tsx` - Added branding
8. `frontend/src/pages/auth/LoginPage.module.css` - Added logo styles
9. `frontend/src/pages/settings/SystemSettingsPage.tsx` - Added UI Update tab
10. `frontend/src/pages/settings/SystemSettingsPage.module.css` - Added new styles
11. `frontend/src/pages/registration/RegistrationPage.tsx` - New registration page
12. `frontend/src/pages/registration/RegistrationPage.module.css` - New styles
13. `frontend/src/pages/registration/index.ts` - New export

## Deployment Steps

1. **Backend**:
   ```bash
   cd lims-backend
   python3 manage.py migrate core
   python3 manage.py collectstatic --noinput
   # Restart backend service
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install  # If any new dependencies
   npm run build
   # Deploy built files
   ```

3. **Verify media serving**:
   - Upload a logo via Settings → UI Update
   - Check that it appears in header and login page
   - Verify URL resolves correctly (should be `/media/settings/logos/...`)

## Testing Checklist

### Branding
- [ ] Logo upload works (Settings → UI Update)
- [ ] Logo appears in dashboard header
- [ ] Logo appears on login page
- [ ] Lab display name updates in header
- [ ] Lab display name updates on login page
- [ ] Brand block in header navigates to home
- [ ] Brand block is keyboard accessible (Tab + Enter)

### Registration Flow
- [ ] Registration page loads with mobile field focused
- [ ] Typing mobile number shows patient suggestions
- [ ] Arrow keys navigate suggestions
- [ ] Enter selects patient and populates form
- [ ] New patient can be created
- [ ] Existing patient can be updated
- [ ] After saving patient, order form opens
- [ ] Test search field is auto-focused

### Order Flow
- [ ] Test search shows suggestions
- [ ] Arrow keys + Enter add tests
- [ ] Tests appear in added list with correct prices
- [ ] Remove button works
- [ ] Total amount calculates correctly
- [ ] Discount % and amount are linked
- [ ] Changing % updates amount
- [ ] Changing amount updates %
- [ ] Paid amount auto-fills to net payable
- [ ] Due amount calculates correctly
- [ ] Order creation succeeds
- [ ] Form resets after order creation

### Permissions
- [ ] Registration appears in Admin sidebar
- [ ] Registration appears in Receptionist sidebar
- [ ] Settings → UI Update accessible to Admin
- [ ] Settings → UI Update accessible to Manager

## Notes

- All calculations are client-side for instant feedback
- Discount cannot exceed total amount (clamped to 0)
- Due amount cannot be negative (clamped to 0)
- Mobile lookup triggers after 3+ characters (300ms debounce)
- Test search triggers after 2+ characters (200ms debounce)
- Logo file size limited to 5MB
- Accepted logo formats: PNG, JPG, JPEG, WEBP

## Known Limitations

1. Panel search not yet implemented (only tests) - can be added later
2. No barcode scanner integration - manual entry only
3. No receipt preview before saving - direct save to DB
4. Patient history not shown during lookup - only basic info

## Future Enhancements

1. Add panel search support
2. Add barcode scanner for test entry
3. Add order preview before submission
4. Show patient test history during lookup
5. Add payment method selection (cash/card/etc)
6. Add print receipt functionality
