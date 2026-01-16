# Core LIMS Scope Documentation

**Date:** 2026-01-17  
**Purpose:** Define the core scope of the LIMS system after cleanup of out-of-scope modules

---

## Core Modules (KEPT)

### Backend Django Apps

1. **apps.accounts** - Authentication & Authorization + RBAC
   - User management
   - JWT authentication
   - Role-based access control

2. **apps.patients** - Patient Management
   - Patient registration with MRN generation
   - Patient demographics and history
   - Search and filtering

3. **apps.laboratory** - Test Catalog
   - Test categories
   - Individual tests
   - Test panels
   - Test parameters
   - Reference ranges

4. **apps.orders** - Order Management / Worklist
   - Order creation and management
   - Order status workflow
   - Order items and pricing

5. **apps.samples** - Sample Collection & Lifecycle
   - Sample collection tracking
   - Sample status management
   - Barcode tracking

6. **apps.results** - Result Entry
   - Test result entry
   - Abnormal/critical flagging
   - Result validation

7. **apps.reports** - Report Generation
   - PDF report generation
   - Report templates
   - Report verification

8. **apps.billing** - Billing & Payments
   - Payment processing
   - Receipt generation (PDF)
   - Payment methods

9. **apps.audit** - Audit Logs
   - Activity logging
   - Audit trail

10. **apps.dashboard** - Minimal Dashboards
    - Role-based statistics
    - Basic metrics

11. **apps.core** - Core Utilities
    - System settings
    - Health check endpoint
    - Core utilities

---

## Removed Modules

### Backend Django Apps (DELETED)

1. **apps.notifications** - Email/SMS/WhatsApp Notifications
   - Removed completely (app directory deleted)
   - Notification sending utilities removed
   - References removed from orders, results, reports, billing models

2. **apps.integrations** - Analyzer Integrations / HL7 Devices
   - Removed completely (app directory deleted)
   - HL7 parser removed
   - Analyzer models removed

### Terminal/Kiosk/Offline Functionality (REMOVED)

1. **LabTerminal Model** - Removed from apps.core.models
   - Terminal management removed
   - Offline MRN range allocation removed

2. **Patient Offline Fields** - Removed from apps.patients.models
   - `origin_terminal` field removed
   - `is_offline_entry` field removed
   - `synced_at` field removed
   - Offline MRN generation logic simplified

### Frontend Pages/Components (DELETED)

1. **pages/notifications** - Notifications page and components
2. **pages/terminals** - Lab terminals page and components

### Frontend Routes (REMOVED)

- `/dashboard/notifications` route removed
- `/dashboard/terminals` route removed

### Frontend API Services (REMOVED)

- `notificationApi` service removed
- `labTerminalApi` service removed

### Frontend Types (REMOVED)

- `LabTerminal` interface removed
- `LabTerminalCreateRequest` interface removed
- `Notification` interface removed
- `NotificationType` type removed
- `NotificationStatus` type removed

---

## Core Workflow Chain (9 Steps)

1. **Patient Registration** - Create patient record with MRN
2. **Order Creation** - Create order with tests/panels
3. **Sample Collection** - Track sample collection with barcode
4. **Result Entry** - Enter test results with auto-flagging
5. **Verification** - Pathologist verifies and approves results
6. **Report Generation** - Generate PDF report
7. **Payment Processing** - Process payment and generate receipt
8. **Audit Logging** - All activities logged
9. **Dashboard Viewing** - Role-based dashboards for oversight

---

## API Endpoints (Core Only)

### Authentication
- `/api/v1/auth/` - Authentication endpoints

### Patients
- `/api/v1/patients/` - Patient CRUD operations

### Laboratory
- `/api/v1/laboratory/` - Test catalog, categories, panels, parameters, reference ranges

### Orders
- `/api/v1/orders/` - Order management

### Samples
- `/api/v1/samples/` - Sample collection tracking

### Results
- `/api/v1/results/` - Result entry and verification

### Reports
- `/api/v1/reports/` - Report generation

### Billing
- `/api/v1/payments/` - Payment processing

### Audit
- `/api/v1/audit/` - Audit log viewing

### Dashboard
- `/api/v1/dashboard/` - Dashboard statistics

### Core
- `/api/v1/core/settings/` - System settings (singleton)
- `/api/v1/core/health/` - Health check endpoint

---

## Removed Endpoints

- `/api/v1/notifications/` - Removed
- `/api/v1/integrations/` - Removed
- `/api/v1/core/terminals/` - Removed

---

## Frontend Routes (Core Only)

### Public Routes
- `/login` - Login page

### Protected Routes (Dashboard Layout)
- `/dashboard` - Dashboard home
- `/dashboard/patients` - Patient management
- `/dashboard/orders` - Order management
- `/dashboard/tests` - Test catalog
- `/dashboard/samples` - Sample management
- `/dashboard/collection` - Collection worklist
- `/dashboard/results` - Results management
- `/dashboard/worklist` - Result entry worklist
- `/dashboard/review` - Verification queue
- `/dashboard/reports` - Report viewing
- `/dashboard/payments` - Payment management
- `/dashboard/audit` - Audit logs
- `/dashboard/reference-ranges` - Reference range management
- `/dashboard/settings` - System settings

### Removed Routes
- `/dashboard/notifications` - Removed
- `/dashboard/terminals` - Removed

---

## Migration Notes

### Removed Apps
- `apps.notifications` - All migrations remain in git history but app removed
- `apps.integrations` - All migrations remain in git history but app removed

### Model Changes
- `apps.core.models.LabTerminal` - Model removed (table may exist in DB)
- `apps.patients.models.Patient` - Offline fields removed:
  - `origin_terminal` ForeignKey removed
  - `is_offline_entry` BooleanField removed
  - `synced_at` DateTimeField removed

### Migration Strategy
- No destructive migration rewrites performed
- Removed fields will remain in database schema until manual migration
- Removed app tables will remain until manually dropped
- Code no longer references removed models/fields

---

## Build Status

After cleanup:
- ✅ Backend imports: All references to removed apps cleaned
- ✅ Frontend build: Routes and components for removed modules deleted
- ✅ Docker Compose: Configuration unchanged (still functional)

---

## Next Steps

1. Run `python manage.py makemigrations` to create migration for removed Patient fields (if needed)
2. Manually drop removed app tables from database if desired:
   - `notifications` table
   - `analyzers` table
   - `analyzer_result_imports` table
   - `lab_terminals` table
3. Verify all core functionality works end-to-end
4. Update production deployment if needed

---

**Note:** This document reflects the cleaned "Core LIMS" scope. All out-of-scope modules have been removed from the codebase but may still exist in the database schema.
