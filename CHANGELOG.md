# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
