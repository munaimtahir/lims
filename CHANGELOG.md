# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-07

### BREAKING CHANGES - V2 Numbering System (LOCKED)

**⚠️ CRITICAL: Production numbering system is now locked and deterministic.**

#### Added
- **V2 Patient Registration Number (MRN)**: Format `YYMM-CC-SSSS`
  - Monthly reset per collection center
  - Example: `2602-00-0001` (Feb 2026, Center 00, #1)
- **V2 Lab Number (Tube Label)**: Format `MDD-XXX`
  - Daily reset per collection center
  - Example: `B07-001` (Feb 7th, #1)
  - Month codes: A=Jan, B=Feb, ..., L=Dec
- **Collection Centers**: New model for managing registration/collection locations
  - Code `00` = Head Office (default)
  - Codes `01-99` for franchise/satellite centers
- **Atomic Counters**: Concurrency-safe number generation
  - `RegistrationCounter`: Monthly scope per center
  - `LabDailyCounter`: Daily scope per center
  - Row-level locking with `SELECT ... FOR UPDATE`
- **Database Constraints**: Unique constraints on all numbering fields
- **Management Command**: `bootstrap_centers` to initialize collection centers
- **Comprehensive Tests**: Format, reset, concurrency, and validation tests
- **Documentation**: `DOCS/NUMBERING_SYSTEM.md` with complete specification

#### Technical Details
- Numbers are **immutable** after creation (no edits allowed)
- **Concurrency-safe**: No race conditions during simultaneous registrations
- **No legacy "max+1" logic**: Uses dedicated counter tables
- Version constant: `NUMBERING_SYSTEM = "V2_LOCKED_2026_02"`
- Legacy `mrn` and `patient_id` fields maintained for backward compatibility

#### Migration Notes
- New fields added to `Patient`: `registration_number`, `registration_center`, `registration_datetime`
- New fields added to `Order`: `lab_number`, `lab_date`, `daily_serial`, `collection_center`
- Existing records: Legacy fields remain unchanged; new fields nullable for compatibility
- Run `python manage.py bootstrap_centers` after migration

## [1.0.0] - 2024-12-05

### Added
- Complete Django 5 backend with DRF
- React 18 + TypeScript + Vite frontend
- User management with JWT authentication
- Patient management module
- Order management with tests and panels
- Sample collection tracking
- Result entry and verification workflow
- Report generation with PDF support
- Billing and payment processing
- Role-based dashboard with statistics
- Audit trail logging
- Comprehensive test catalog
- Docker and Docker Compose configuration
- CI/CD with GitHub Actions
- Complete API documentation (OpenAPI/Swagger)
- Extensive design documentation

### Fixed
- Backend: Fixed all flake8 linting errors (106 → 0)
- Backend: Generated missing migrations for Report model
- Backend: All 100 tests passing
- Frontend: Fixed ESLint errors (24 → 1 warning)
- Frontend: Fixed TypeScript compilation errors
- Frontend: Build passes successfully

### Technical
- Backend formatted with black for consistency
- Frontend uses proper TypeScript interfaces
- Comprehensive README with setup instructions
- Docker-ready for production deployment
- All core Phase 1 features implemented

### Documentation
- Complete architecture documentation
- API design specification
- Data model documentation
- Workflow documentation
- Deployment guide
- Test catalog expanded

## [0.1.0] - Initial Merge
- Integrated legacy repository as `legacy_lab/` for reference
- Adopted modern architecture as base
- Staged for production-grade implementation
