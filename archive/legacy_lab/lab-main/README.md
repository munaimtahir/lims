# Al Shifa LIMS — Laboratory Information Management System

![Backend CI](https://github.com/munaimtahir/lab/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/munaimtahir/lab/workflows/Frontend%20CI/badge.svg)
![Docker CI](https://github.com/munaimtahir/lab/workflows/Docker%20CI/badge.svg)

A production-ready Laboratory Information Management System (LIMS) for Al Shifa Laboratory with complete workflow automation, PDF reporting, and role-based access control.

## 🚀 Quick Start

### Local Development

```bash
# Start the entire stack (backend + frontend + database + redis)
cd infra && docker-compose up

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Health Check: http://localhost:8000/api/health/

# Development demo credentials: admin / admin123 (for local testing only)
```

### VPS/Production Deployment

**📋 For complete production deployment instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)**

Quick deployment on VPS (172.237.71.40):

```bash
# 1. Clone the repository
git clone https://github.com/munaimtahir/lab.git
cd lab

# 2. Copy .env.example to .env and configure with secure credentials
cp .env.example .env
# Edit .env and update:
# - DJANGO_SECRET_KEY (generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
# - POSTGRES_PASSWORD (generate with: openssl rand -base64 32)
# - Verify DEBUG=False

# 3. Build and start services
docker compose build
docker compose up -d

# 4. Create secure admin user (REQUIRED - do NOT use default demo credentials)
docker compose exec backend python manage.py createsuperuser

# 5. Import master data (tests, parameters, reference ranges)
docker compose exec backend python manage.py import_lims_master --dry-run  # Test first
docker compose exec backend python manage.py import_lims_master             # Actual import

# 6. Access the application
# Frontend: http://172.237.71.40 (served via nginx on port 80)
# Backend API: http://172.237.71.40/api/ (proxied through nginx)
# Health Check: http://172.237.71.40/api/health/
```

### Import LIMS Master Data

After deployment, import the test catalog, parameters, and reference ranges:

```bash
# Test the import first (no changes saved)
docker compose exec backend python manage.py import_lims_master --dry-run

# Perform the actual import
docker compose exec backend python manage.py import_lims_master
```

This imports 987 tests, 1161 parameters, and reference ranges from the Excel file at `backend/seed_data/AlShifa_LIMS_Master.xlsx`.

**📖 For detailed instructions, see [LIMS Master Data Import Guide](backend/LIMS_IMPORT.md)**

> **✅ Production Ready**: This repository is configured for production deployment on VPS IP **172.237.71.40**.
> 
> **⚠️ Security Requirements for Production**:
> 1. **NEVER use default demo credentials** (admin/admin123 is for development only)
> 2. Always create secure admin users with `python manage.py createsuperuser`
> 3. Generate strong passwords: `openssl rand -base64 32`
> 4. Generate secret key: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
> 5. Verify `DEBUG=False` in production `.env` file
> 6. Never commit `.env` to version control (already in .gitignore)

## 🌐 Deployment Configuration

This application is designed to work seamlessly in both local development and VPS/production environments with **no code changes required**. All configuration is handled via environment variables.

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Active configuration (not in git) |
| `.env.example` | Production/VPS template with documentation |
| `infra/.env.example` | Local development template |
| `frontend/.env.development` | Frontend local dev defaults |
| `frontend/.env.production` | Frontend production defaults |

### Key Environment Variables

**Frontend Configuration:**
```bash
# The frontend automatically uses smart defaults:
# - Production builds: /api (nginx proxy)
# - Development mode: http://localhost:8000 (direct backend)

# You can override with VITE_API_URL environment variable:
# For production with nginx proxy:
VITE_API_URL=/api

# For direct backend access (development):
VITE_API_URL=http://localhost:8000

# For a VPS without a reverse proxy:
VITE_API_URL=http://<your_vps_ip>:8000
```

**Backend Configuration:**
```bash
# Allowed hosts (comma-separated)
ALLOWED_HOSTS=<your_domain_or_ip>,localhost,127.0.0.1

# CORS origins (comma-separated)
CORS_ALLOWED_ORIGINS=http://<your_domain_or_ip>,http://localhost:5173

# CSRF trusted origins (comma-separated)
CSRF_TRUSTED_ORIGINS=http://<your_domain_or_ip>,http://localhost:5173
```

## 🏗️ Architecture

- **Backend**: Python 3.12, Django 5.2, Django REST Framework, PostgreSQL 16, Redis 7. A modular architecture with separate apps for each major feature.
- **Frontend**: React 19, TypeScript, Vite, TailwindCSS. A modern, component-based architecture with a focus on reusability and performance.
- **Authentication**: JWT with token blacklisting and role-based access control.
- **Infrastructure**: Docker Compose for container orchestration, with health checks for all services.
- **CI/CD**: GitHub Actions for automated testing, linting, and building of Docker images on every push and pull request.

## ✨ Complete LIMS Workflow

1. **Patient Registration**: Auto-generated MRN, Pakistani ID validation, and offline registration support.
2. **Order Creation**: Multi-test orders with tracking and priority settings.
3. **Sample Collection**: Barcode generation and phlebotomy workflow.
4. **Sample Receiving**: Lab acceptance and rejection workflow.
5. **Result Entry**: Technologist interface for entering results.
6. **Result Verification**: Pathologist review and verification of results.
7. **Result Publishing**: Final authorization and publishing of results.
8. **PDF Reports**: Automated generation of PDF reports with Al Shifa branding and digital signatures.
9. **Report Download**: Secure delivery and download of reports.

## 📊 Test Coverage

- **Backend**: 99.1% coverage with 106 tests passing.
- **Frontend**: 60 tests passing (Vitest + React Testing Library).
- **CI/CD**: Automated testing on all pull requests and commits to the `main` branch.

| Module | Tests | Coverage |
|--------|-------|----------|
| Authentication | 7 | 100% |
| Patients | 22 | 100% |
| Catalog | 3 | 100% |
| Orders | 4 | 100% |
| Samples | 12 | 100% |
| Results | 15 | 100% |
| Reports | 12 | 100% |
| Health | 6 | 100% |
| Seed Data | 4 | 100% |
| Core Settings | 3 | 100% |
| **Total** | **87** | **100%** |

## 👥 Demo Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Full access |
| reception | reception123 | Patients, Orders |
| tech | tech123 | Result entry |
| pathologist | path123 | Verification, Reports |

## 🔧 Local Development

### Environment Setup

```bash
# 1. Create your environment configuration
cp .env.example .env
# Edit .env with your local settings (passwords, secrets)

# 2. Start with Docker (recommended)
cd infra && docker-compose up
```

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

### Code Quality and Linting

This project uses `pre-commit` to enforce code quality and consistency. To set up the pre-commit hooks, run:
```bash
pip install pre-commit
pre-commit install
```

## 🧪 Testing

```bash
# Backend tests (99% coverage)
cd backend
pytest -v --cov=. --cov-report=term-missing

# Frontend tests
cd frontend
pnpm test

# E2E tests
pnpm playwright test
```

## 📚 Documentation

- [API Reference](docs/API.md)
- [Frontend Guide](docs/FRONTEND.md)
- [Data Model](docs/DATA_MODEL.md)
- [Test Coverage](docs/TESTS_COVERAGE.md)
- [LIMS Master Data Import](backend/LIMS_IMPORT.md) - Import tests, parameters, and reference ranges from Excel

## 🏥 Health Check

```bash
curl http://localhost:8000/api/health/
# {"status": "healthy", "database": "healthy", "cache": "healthy"}
```

## 🔐 Security

- JWT authentication with token blacklisting
- Role-based access control (5 roles) with granular permissions
- Input validation (CNIC, phone, DOB)
- Zero dependency vulnerabilities
- State machine workflow enforcement to prevent unauthorized state transitions

## 🎯 API Endpoints

### Authentication
- `POST /api/auth/login/` - Login
- `POST /api/auth/refresh/` - Refresh token
- `POST /api/auth/logout/` - Logout

### Patients
- `GET/POST /api/patients/` - List/Create
- `GET /api/patients/:id/` - Details

### Orders & Samples
- `GET/POST /api/orders/` - List/Create
- `POST /api/samples/:id/collect/` - Collect
- `POST /api/samples/:id/receive/` - Receive

### Results
- `POST /api/results/:id/enter/` - Enter
- `POST /api/results/:id/verify/` - Verify
- `POST /api/results/:id/publish/` - Publish

### Reports
- `POST /api/reports/generate/:order_id/` - Generate PDF
- `GET /api/reports/:id/download/` - Download

See [docs/API.md](docs/API.md) for complete documentation.

## 📊 Project Stats

- **166 tests passing** (100% pass rate)
- **99% backend code coverage**
- **10 complete modules**
- **40+ API endpoints**
- **Zero security vulnerabilities**
- **Production-ready**

---

**Al Shifa Laboratory** | **Version 1.0.0** | Production-Ready ✅
