# Project Structure Documentation

This document describes the standardized directory structure of the LIMS project.

## Directory Organization

### Root Directory

The root directory contains only essential files:

- `README.md` - Main project documentation
- `LICENSE` - License file
- `CHANGELOG.md` - Version history
- `docker-compose.yml` - Docker orchestration
- `Caddyfile` - Reverse proxy configuration
- `.gitignore` - Git ignore rules
- `.github/workflows/` - CI/CD pipeline configurations

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

- **`docs/deployment/`** - Deployment guides
  - `DEPLOYMENT.md` - Production deployment guide
  - `SSH_DEPLOYMENT.md` - SSH deployment instructions
  - `TROUBLESHOOTING.md` - Troubleshooting guide

- **`docs/archive/`** - Archived documentation
  - Historical and redundant documentation files
  - Kept for reference but not actively maintained

- **Root docs files:**
  - `DATA_MODEL.md` - Database schema
  - `WORKFLOW.md` - Laboratory workflows
  - `VISION.md` - Project vision and goals
  - `TEST_CATALOG_EXPANDED.md` - Complete test catalog
  - `LEGACY_LAB.md` - Legacy code reference guide

### Archive (`archive/`)

- **`archive/legacy_lab/`** - Legacy code reference
  - Contains the original LIMS implementation
  - Preserved for reference and data migration purposes
  - **NOT** part of the active application
  - See `docs/LEGACY_LAB.md` for usage guidelines

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

- Legacy code moved from `legacy_lab/` to `archive/legacy_lab/`
- Documentation moved from root to `docs/` with subdirectories
- Scripts moved from root to `scripts/`
- All paths in documentation have been updated

## References

- Main README: [`README.md`](../README.md)
- Legacy code guide: [`docs/LEGACY_LAB.md`](./LEGACY_LAB.md)
- Architecture: [`docs/architecture/ARCHITECTURE.md`](./architecture/ARCHITECTURE.md)

