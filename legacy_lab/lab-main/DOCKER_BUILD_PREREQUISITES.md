# Docker Build Prerequisites Checklist

This document outlines all prerequisites and dependencies required for successful Docker deployment of the Al Shifa LIMS application.

## ✅ Fixed Issues

### 1. TypeScript Compilation Error (RESOLVED)
**Issue**: Docker build failed with error:
```
src/test/setup.ts(6,1): error TS2591: Cannot find name 'process'. 
Do you need to install type definitions for node?
```

**Root Cause**: The test setup file uses `process.env`, but `tsconfig.app.json` didn't include node types.

**Solution**: Added `"node"` to the types array in `frontend/tsconfig.app.json`:
```json
"types": ["vite/client", "node"]
```

**Status**: ✅ FIXED - Build now succeeds

## 📋 Complete Prerequisites Checklist

### 1. System Requirements

#### Required Software
- [x] **Docker**: Version 20.10+ with Docker Compose V2
- [x] **Git**: For repository cloning
- [x] **OpenSSL**: For generating secure credentials (optional but recommended)

#### Network Requirements
- [x] Internet access for pulling base images:
  - `node:20-slim` (for frontend build)
  - `python:3.12-slim` (for backend)
  - `nginx:alpine` (for serving)
  - `postgres:16` (for database)
  - `redis:7-alpine` (for cache)

### 2. Build Dependencies

#### Frontend Dependencies
- [x] **Node.js packages**: Installed via pnpm from `frontend/package.json`
  - All 54 dependencies listed (React, TypeScript, Vite, etc.)
  - All dependencies are pinned to specific versions
- [x] **TypeScript configuration**: Fixed to include node types
  - `tsconfig.json` - Main configuration
  - `tsconfig.app.json` - App configuration (now includes node types)
  - `tsconfig.node.json` - Node configuration
- [x] **@types/node**: Version 24.6.0+ (already in devDependencies)

#### Backend Dependencies
- [x] **Python packages**: Installed via pip from `backend/requirements.txt`
  - All 46 dependencies listed (Django, DRF, Gunicorn, etc.)
  - All dependencies are pinned to specific versions
- [x] **System packages** (installed in Dockerfile):
  - `gcc` - For compiling Python extensions
  - `postgresql-client` - For database interactions
  - `curl` - For healthchecks

### 3. Configuration Files

#### Required Files (Committed to Repository)
- [x] `docker-compose.yml` - Main orchestration file
- [x] `nginx/Dockerfile` - Multi-stage build for frontend + nginx
- [x] `backend/Dockerfile` - Backend build
- [x] `frontend/Dockerfile` - Frontend development build
- [x] `nginx/nginx.conf` - Nginx configuration
- [x] `.env.example` - Environment template

#### Required Files (Created Before Deployment)
- [x] `.env` - Must be created from `.env.example` with production values

Required environment variables in `.env`:
```bash
# Security (MUST be changed for production)
DJANGO_SECRET_KEY=<generate-with-django-command>
POSTGRES_PASSWORD=<generate-with-openssl>
DEBUG=False

# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=lims
POSTGRES_USER=lims

# Redis
REDIS_URL=redis://redis:6379/0

# Network (Update with your IP/domain)
ALLOWED_HOSTS=172.237.71.40,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://172.237.71.40,http://172.237.71.40:80
CSRF_TRUSTED_ORIGINS=http://172.237.71.40,http://172.237.71.40:80

# Frontend
VITE_API_URL=/api
```

### 4. Build Process Verification

#### Steps to Verify Build Works
```bash
# 1. Create .env file
cp .env.example .env
# Edit .env with your values

# 2. Validate docker-compose configuration
docker compose config --quiet

# 3. Build all services
docker compose build

# 4. Start services
docker compose up -d

# 5. Check all services are running
docker compose ps

# 6. Run health checks
curl http://localhost/api/health/
```

#### Expected Build Output
- ✅ Frontend builds without TypeScript errors
- ✅ Backend dependencies install successfully
- ✅ Django static files collected
- ✅ Nginx image created successfully
- ✅ All services start and pass health checks

### 5. Common Build Issues and Solutions

#### Issue: pnpm install fails
**Solution**: Ensure pnpm version 8.15.9 is used (specified in Dockerfile)

#### Issue: TypeScript compilation fails
**Solution**: Verified fixed - node types now included in tsconfig.app.json

#### Issue: Backend dependencies fail to install
**Solution**: System packages (gcc, postgresql-client) are included in backend Dockerfile

#### Issue: Nginx fails to start
**Solution**: Ensure frontend build completed successfully and dist/ directory exists

#### Issue: Database connection fails
**Solution**: Ensure PostgreSQL service is healthy before backend starts (configured in docker-compose.yml)

### 6. CI/CD Integration

#### GitHub Actions Workflows
- [x] `.github/workflows/frontend.yml` - Frontend CI (lint, build, test)
- [x] `.github/workflows/backend.yml` - Backend CI
- [x] `.github/workflows/docker.yml` - Docker build validation
- [x] `.github/workflows/codeql.yml` - Security scanning

All workflows now pass with the TypeScript fix applied.

### 7. Production Deployment Checklist

Before deploying to production:

- [ ] Generate secure `DJANGO_SECRET_KEY`
  ```bash
  python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
  ```

- [ ] Generate secure `POSTGRES_PASSWORD`
  ```bash
  openssl rand -base64 32
  ```

- [ ] Set `DEBUG=False` in .env

- [ ] Update `ALLOWED_HOSTS` with your actual IP/domain

- [ ] Update `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`

- [ ] Run smoke tests after deployment
  ```bash
  ./scripts/smoke_test.sh
  ```

- [ ] Create admin user (DO NOT use default credentials)
  ```bash
  docker compose exec backend python manage.py createsuperuser
  ```

### 8. Documentation References

- **Production Deployment**: See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Local Setup**: See [SETUP.md](SETUP.md)
- **General Info**: See [README.md](README.md)

## 🎯 Summary

All prerequisites for successful Docker deployment are now in place:

1. ✅ **TypeScript compilation issue FIXED** - node types added to tsconfig.app.json
2. ✅ **All dependencies properly specified** - Frontend (54 packages), Backend (46 packages)
3. ✅ **Docker configurations optimized** - Multi-stage builds, health checks
4. ✅ **Environment configuration documented** - .env.example with all required variables
5. ✅ **Build process verified** - Successfully builds all services
6. ✅ **CI/CD pipelines configured** - GitHub Actions workflows in place

The application is now ready for Docker deployment following the instructions in PRODUCTION_DEPLOYMENT.md.
