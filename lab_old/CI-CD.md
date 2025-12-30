# CI/CD Documentation

This document describes the continuous integration and continuous deployment (CI/CD) setup for the Al Shifa LIMS project.

## Overview

The project uses GitHub Actions for CI/CD with three main workflows:

1. **Backend CI** - Tests and validates the Django/Python backend
2. **Frontend CI** - Tests and validates the React/Vite frontend  
3. **Docker CI** - Validates Docker Compose configuration

All workflows run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

---

## 1. Backend CI Workflow

**File**: `.github/workflows/backend.yml`

### What it does

- Sets up Python 3.12 environment
- Installs backend dependencies from `requirements.txt`
- Runs code quality checks (ruff, black, isort)
- Executes test suite with coverage reporting (minimum 65% coverage)
- Validates Django migrations

### Running Backend Tests Locally

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run linters
ruff check . --exit-zero
black --check .
isort --check .

# Run tests with coverage
pytest -v --cov=. --cov-report=term-missing --cov-fail-under=65

# Check migrations
python manage.py makemigrations --check --dry-run
```

### Backend Test Coverage

Current coverage: **76.83%** (exceeds 65% requirement)

To improve coverage, focus on:
- `verify_api_connections.py` (0% coverage)
- `settings/views.py` (34.55% coverage)
- `settings/permissions.py` (62.07% coverage)

### Backend Environment Variables

The CI uses SQLite for testing (no database setup required). For local testing with PostgreSQL:

```bash
export DEBUG=True
export DJANGO_SECRET_KEY=test-secret-key
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=lims_test
export POSTGRES_USER=lims
export POSTGRES_PASSWORD=lims
```

---

## 2. Frontend CI Workflow

**File**: `.github/workflows/frontend.yml`

### What it does

- Sets up Node.js 20 environment
- Installs pnpm package manager (v8.15.9)
- Installs frontend dependencies
- Runs ESLint code linting
- Performs TypeScript type checking and production build
- Executes Vitest test suite

### Running Frontend Tests Locally

```bash
cd frontend

# Install pnpm if not already installed
npm install -g pnpm@8.15.9

# Install dependencies
pnpm install --frozen-lockfile

# Run linter
pnpm lint

# Type check and build
pnpm build

# Run tests
pnpm test -- --run
```

### Frontend Test Framework

- **Testing Library**: Vitest + React Testing Library
- **Test Location**: `frontend/src/**/*.test.{ts,tsx}`
- **Coverage Tool**: Vitest coverage (v8)

To run tests with coverage:
```bash
pnpm test:coverage
```

To run tests in watch mode:
```bash
pnpm test
```

---

## 3. Docker CI Workflow

**File**: `.github/workflows/docker.yml`

### What it does

- Validates `docker-compose.yml` syntax
- Creates `.env` file with required environment variables
- Runs `docker compose config` to ensure configuration is valid

### Running Docker Builds Locally

#### Full Stack Build and Run

```bash
# Create .env file (copy from .env.example and customize)
cp .env.example .env
nano .env  # Edit as needed

# Build all services
docker compose build

# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

#### Build Individual Services

```bash
# Build backend only
docker compose build backend

# Build frontend only  
docker compose build nginx

# Run backend in development mode
docker compose up backend
```

### Docker Services

The `docker-compose.yml` defines the following services:

1. **db** (PostgreSQL 16)
   - Database for the application
   - Data persisted in `pgdata` volume

2. **redis** (Redis 7)
   - Cache and message broker
   - Used by Celery for background tasks

3. **backend** (Django application)
   - Runs on port 8000 internally
   - Health check: `http://localhost:8000/api/health/`
   - Depends on: db, redis

4. **nginx** (Web server)
   - Serves frontend and proxies backend API
   - Exposes ports 80 (HTTP) and 443 (HTTPS)
   - Depends on: backend

### Docker Environment Variables

Required environment variables (set in `.env`):

```env
# Database
POSTGRES_USER=lims
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=lims

# Django
DEBUG=False
DJANGO_SECRET_KEY=<generate-with-django>
ALLOWED_HOSTS=yourdomain.com,localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://yourdomain.com
CSRF_TRUSTED_ORIGINS=http://yourdomain.com

# Redis
REDIS_URL=redis://redis:6379/0
```

To generate a Django secret key:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Troubleshooting CI Failures

### Backend CI Failures

**Test failures:**
```bash
# Run specific test
cd backend
pytest path/to/test_file.py::TestClass::test_method -v

# Run with more verbose output
pytest -vvs path/to/test_file.py
```

**Coverage failures:**
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser to see uncovered lines
```

**Linter failures:**
```bash
# Auto-fix code formatting
black .
isort .

# See what ruff would fix
ruff check . --fix
```

### Frontend CI Failures

**Build failures:**
```bash
# Check TypeScript errors
pnpm build

# Fix with --mode development for better error messages
pnpm build:dev
```

**Lint failures:**
```bash
# Auto-fix linting issues where possible
pnpm lint --fix
```

**Test failures:**
```bash
# Run tests with more detail
pnpm test -- --reporter=verbose

# Run specific test file
pnpm test -- path/to/test.test.ts
```

### Docker CI Failures

**Configuration validation failures:**
```bash
# Validate docker-compose.yml locally
docker compose config

# Check for syntax errors
docker compose config --quiet

# If validation passes locally but fails in CI, check:
# 1. All required .env variables are set in workflow
# 2. File paths in volumes are correct
# 3. Service names don't conflict
```

---

## CI/CD Best Practices

### Before Committing Code

1. **Run tests locally** - Ensure all tests pass
2. **Check code formatting** - Run linters and formatters
3. **Review coverage** - Aim to maintain or increase coverage
4. **Test Docker build** - If changing Docker files, build locally first

### Writing Tests

1. **Backend Tests**
   - Use Django TestCase for database-dependent tests
   - Use pytest fixtures for reusable test data
   - Mock external dependencies (APIs, file system)
   - Test both success and failure cases

2. **Frontend Tests**
   - Use React Testing Library best practices
   - Test user interactions, not implementation details
   - Mock API calls with MSW or similar
   - Test accessibility with screen reader queries

### Maintaining CI Performance

1. **Cache dependencies** - Both workflows use caching (pip, pnpm)
2. **Concurrency** - Workflows cancel previous runs on new pushes
3. **Timeout limits** - All jobs have 15-minute timeout
4. **Minimal scope** - Workflows only trigger on relevant file changes

---

## Deployment

### Development Environment

```bash
cd infra
docker-compose up
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/api/health/

### Production Environment

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for complete production deployment instructions.

Quick deployment:
```bash
# 1. Clone repository
git clone https://github.com/munaimtahir/lab.git
cd lab

# 2. Configure environment
cp .env.example .env
# Edit .env with production settings

# 3. Build and start services
docker compose build
docker compose up -d

# 4. Create admin user
docker compose exec backend python manage.py createsuperuser

# 5. Import master data
docker compose exec backend python manage.py import_lims_master
```

---

## Monitoring CI Status

### Workflow Status Badges

The README.md includes status badges for all three workflows:

![Backend CI](https://github.com/munaimtahir/lab/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/munaimtahir/lab/workflows/Frontend%20CI/badge.svg)
![Docker CI](https://github.com/munaimtahir/lab/workflows/Docker%20CI/badge.svg)

### Viewing Workflow Runs

1. Go to the [Actions tab](https://github.com/munaimtahir/lab/actions)
2. Click on a workflow to see its runs
3. Click on a specific run to see detailed logs
4. Each job can be expanded to see individual step outputs

### Notifications

GitHub automatically notifies you of failed workflow runs via:
- Email (if enabled in GitHub settings)
- GitHub web notifications
- GitHub mobile app notifications

---

## Workflow Triggers

### Path Filters

Workflows only run when relevant files change:

**Backend CI** triggers on changes to:
- `backend/**`
- `.github/workflows/backend.yml`

**Frontend CI** triggers on changes to:
- `frontend/**`
- `.github/workflows/frontend.yml`

**Docker CI** triggers on changes to:
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `nginx/Dockerfile`
- `docker-compose.yml`
- `.github/workflows/docker.yml`

### Manual Triggers

You can manually trigger workflows from the Actions tab:
1. Go to Actions
2. Select the workflow
3. Click "Run workflow"
4. Select the branch

---

## Contributing

When contributing to this project:

1. Create a feature branch from `develop`
2. Make changes and commit with descriptive messages
3. Ensure all CI checks pass
4. Create a pull request to `develop`
5. Address any CI failures or review comments
6. Merge after approval and successful CI

---

## Support

For questions or issues with CI/CD:
1. Check this documentation first
2. Review workflow logs in GitHub Actions
3. Check [SETUP.md](SETUP.md) for environment setup
4. Open an issue on GitHub with CI logs attached
