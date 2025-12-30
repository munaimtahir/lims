# LIMS Frontend Architecture Guide

## 1. Folder Structure

src/
├── pages/             # Page-level components
├── components/        # Shared UI components
├── modules/           # Feature domains (patients, results, etc.)
├── services/          # API clients
├── types/             # TS interfaces
├── hooks/             # Custom hooks
├── layouts/           # Shells and wrappers
└── utils/             # Helpers

## 2. Architectural Rules
- Each module lives in its own folder
- API functions per module (patients.ts, results.ts)
- React Query for all data fetching
- One global auth context
- ProtectedRoute guard for role-based access

## 3. Workflow Mapping
- Reception → Patient Registration
- Phlebotomy → Sample Collection
- Technologist → Result Entry
- Pathologist → Verification + Printing
- Admin → Settings + CSV Imports + Analytics

## 4. Communication Flow
UI → Module → Service(API) → Backend → React Query Cache → UI

## 5. Testing Strategy
- Unit tests for form components
- Integration tests for workflows
- E2E tests for patient→result→report cycle