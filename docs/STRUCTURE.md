# Project Structure Documentation

This document describes the standardized directory structure of the LIMS project.

## Directory Organization

### Root Directory

The root directory contains essential files plus a small set of utility scripts and sample data files used for catalog/import validation:

- `README.md` - Main project documentation
- `LICENSE` - License file
- `CHANGELOG.md` - Version history
- `docker-compose.yml` - Docker orchestration
- `Caddyfile` - Reverse proxy configuration
- `.gitignore` - Git ignore rules
- `.github/workflows/` - CI/CD pipeline configurations
- `smoke_test.py` and related scripts - Standalone smoke test runners
- `LIMS_TestCatalog_*.xlsx`, `source_catalog.xlsx`, `test_catalog.xlsx` - Sample catalog files

### Source Code Directories

- **`lims-backend/`** - Django backend application
  - Contains all Django apps, configuration, and backend code
  - Follows Django best practices for project structure

- **`frontend/`** - React frontend application
  - Contains React components, pages, and frontend code
  - Uses Vite as build tool

### Documentation (`docs/`)

All documentation is organized in the `docs/` directory:

- **`docs/architecture/`** - Architecture documentation
  - `ARCHITECTURE.md` - Complete system architecture

- **`docs/api/`** - API documentation
  - `API_DESIGN.md` - RESTful API specification

- **`docs/ops/`** - Operations and runbooks
  - `DEPLOYMENT.md` - Production deployment guide
  - `ENVIRONMENT_VARIABLES.md` - Environment configuration
  - `WORKFLOWS.md` - CI/CD workflow overview
  - `RUNBOOK_DEV.md` - Development runbook
  - `RUNBOOK_PROD.md` - Production runbook
  - `PRODUCTION_READINESS_CHECKLIST.md` - Production readiness validation

- **`docs/reports/`** - Current reports and audits
  - `SMOKE_TEST_REPORT.md` - Latest smoke test summary
  - `PRODUCTION_READINESS_REPORT.md` - Production readiness report
  - `REPOSITORY_AUDIT.md` - Repository audit summary

- **`docs/catalog/`** - Test catalog documentation
  - `README.md` - Catalog overview and import guidance
  - `PRINT_TEMPLATES_GUIDE.md` - Print template setup

### Root docs files
  - `DATA_MODEL.md` - Database schema
  - `WORKFLOW.md` - Laboratory workflows
  - `VISION.md` - Project vision and goals
  - `LEGACY_LAB.md` - Legacy code reference guide

### Scripts (`scripts/`)

Utility scripts for deployment and maintenance:

- `deploy.sh` - Production deployment script
- `health-check.sh` - Health monitoring script
- `validate_system.sh` - System validation script

## Standard Structure Benefits

1. **Clarity** - Easy to find files and understand project organization
2. **Maintainability** - Clear separation of concerns
3. **Scalability** - Structure supports growth
4. **Standards Compliance** - Follows international best practices for project structure

## File Naming Conventions

- Documentation files use `UPPERCASE.md` format
- Scripts use `kebab-case.sh` format
- Source code follows language-specific conventions

## Migration Notes

If you're migrating from the old structure:

- Legacy code removed from the repository; use external archives if needed
- Documentation moved from root to `docs/` with subdirectories
- Scripts moved from root to `scripts/`
- All paths in documentation have been updated

## References

- Main README: [`README.md`](../README.md)
- Legacy code guide: [`docs/LEGACY_LAB.md`](./LEGACY_LAB.md)
- Architecture: [`docs/architecture/ARCHITECTURE.md`](./architecture/ARCHITECTURE.md)
