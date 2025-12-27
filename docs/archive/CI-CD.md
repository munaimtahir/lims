# CI/CD Documentation

This document describes the Continuous Integration and Deployment workflows for the LIMS (Laboratory Information Management System) application.

## Overview

The LIMS project uses GitHub Actions for automated testing, building, and deployment. The CI/CD pipeline is split into three separate workflows:

1. **Backend CI** - Django/Python backend testing and linting
2. **Frontend CI** - React/Vite frontend building and linting
3. **Docker CI** - Docker image builds and sanity checks

## Workflows

### 1. Backend CI (`backend-ci.yml`)

**Purpose**: Ensures the Django backend code quality and functionality.

**Triggers**:
- Push to `main` or `develop` branches (when backend files change)
- Pull requests to `main` or `develop` branches (when backend files change)

**What it does**:
1. Sets up Python 3.12 environment
2. Installs dependencies from `requirements/development.txt`
3. Runs flake8 linting (max line length: 120, excludes migrations)
4. Runs pytest test suite with coverage
5. Generates coverage report (minimum 70% threshold)
6. Uploads coverage artifacts

**Key Features**:
- Uses PostgreSQL 16 service for integration tests
- Can fall back to SQLite for faster CI runs
- Caches pip dependencies for faster builds
- Enforces code quality standards

### 2. Frontend CI (`frontend-ci.yml`)

**Purpose**: Validates the React/Vite frontend builds correctly and meets code standards.

**Triggers**:
- Push to `main` or `develop` branches (when frontend files change)
- Pull requests to `main` or `develop` branches (when frontend files change)

**What it does**:
1. Sets up Node.js 20 environment
2. Installs dependencies using `npm ci`
3. Runs ESLint for code quality
4. Runs TypeScript type checking
5. Builds production bundle with Vite
6. Uploads build artifacts

**Key Features**:
- Uses npm ci for reproducible builds
- Caches npm dependencies
- Validates TypeScript types
- Ensures production build succeeds

### 3. Docker CI (`docker-ci.yml`)

**Purpose**: Verifies Docker images build successfully and pass basic sanity checks.

**Triggers**:
- Push to `main` or `develop` branches (when Docker files change)
- Pull requests to `main` or `develop` branches (when Docker files change)
- Tags matching `v*` pattern

**What it does**:
1. Validates `docker-compose.yml` configuration
2. Builds backend Docker image
3. Tests backend image (Python version, Django import)
4. Builds frontend Docker image
5. Tests frontend image (nginx serving)
6. Builds full stack with docker-compose (smoke test)
7. Cleans up Docker resources

**Key Features**:
- Uses Docker Buildx for efficient builds
- Performs basic sanity checks on images
- Validates docker-compose configuration
- Cleans up resources to save disk space

## Running Tests Locally

### Backend Tests

```bash
# Navigate to backend directory
cd lims-backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Run linting
flake8 apps/ --max-line-length=120 --exclude=migrations

# Run tests with coverage
export DB_ENGINE=django.db.backends.sqlite3
export DB_NAME=test.db
export SECRET_KEY=test-secret-key
export DEBUG=True
coverage run -m pytest apps/ -v
coverage report --fail-under=70

# Or run tests with Django's test runner
python manage.py test
```

### Frontend Tests

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm ci

# Run linting
npm run lint

# Run TypeScript type checking
npx tsc --noEmit

# Build production bundle
npm run build

# Run development server (for manual testing)
npm run dev
```

### Docker Builds

```bash
# Validate docker-compose configuration
docker compose config --quiet

# Build backend image
cd lims-backend
docker build -t lims-backend:local -f Dockerfile .

# Build frontend image
cd ../frontend
docker build -t lims-frontend:local -f Dockerfile .

# Build entire stack
cd ..
docker compose build

# Run stack locally
docker compose up

# Or run in detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Environment Variables

### Backend CI Environment Variables

- `DB_ENGINE`: Database engine (default: `django.db.backends.sqlite3` for CI)
- `DB_NAME`: Database name (default: `test.db` for CI)
- `SECRET_KEY`: Django secret key (use test key for CI)
- `DEBUG`: Debug mode (default: `True` for CI)
- `DJANGO_SETTINGS_MODULE`: Settings module (default: `config.settings.development`)

### Frontend CI Environment Variables

No special environment variables required for CI. The build process uses defaults.

### Docker CI Environment Variables

Docker images use environment variables from `.env.production` in production. For CI, default values or test values are used.

## Workflow Status

Check the status of workflows on the [Actions tab](https://github.com/munaimtahir/lims/actions) of the GitHub repository.

### Current Status

All three workflows should pass with the following indicators:
- ✅ Backend CI - Tests passing with >70% coverage
- ✅ Frontend CI - Builds successfully with no errors
- ✅ Docker CI - Images build and pass sanity checks

## Maintenance

### Adding New Tests

**Backend**:
1. Create test files in `apps/<app_name>/tests/`
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures and Django test utilities
4. Ensure coverage stays above 70%

**Frontend**:
1. Tests can be added using Vitest (if configured)
2. Currently focuses on build and lint validation

### Updating Dependencies

**Backend**:
- Update `requirements/base.txt` for production dependencies
- Update `requirements/development.txt` for test/dev dependencies
- Update `requirements/production.txt` for deployment-specific packages

**Frontend**:
- Update `package.json` with new dependencies
- Run `npm install` to update `package-lock.json`
- Commit both files

### Modifying Workflows

1. Edit workflow files in `.github/workflows/`
2. Test changes on a feature branch first
3. Verify workflows pass before merging to main
4. Use appropriate triggers to avoid unnecessary runs

## Troubleshooting

### Backend CI Failures

**Import errors or missing modules**:
- Check `requirements/development.txt` includes all necessary packages
- Verify package versions are compatible

**Test failures**:
- Check if database migrations are needed
- Verify test data setup is correct
- Check for environment-specific issues

**Coverage failures**:
- Add tests for uncovered code
- Or adjust coverage threshold in workflow (not recommended)

### Frontend CI Failures

**Build failures**:
- Check for TypeScript errors: `npx tsc --noEmit`
- Verify all dependencies are in `package.json`
- Check for missing environment variables

**Lint failures**:
- Run `npm run lint` locally to see issues
- Fix reported issues or update ESLint config if needed

### Docker CI Failures

**Build failures**:
- Check Dockerfile syntax
- Verify base images are accessible
- Check for missing dependencies in requirements/package.json

**Sanity check failures**:
- Verify images expose correct ports
- Check for missing environment variables
- Verify services start correctly

## Best Practices

1. **Run tests locally** before pushing code
2. **Keep dependencies updated** but test thoroughly
3. **Maintain high code coverage** (>70% for backend)
4. **Fix CI failures immediately** - don't let them accumulate
5. **Use feature branches** for development
6. **Review workflow logs** when failures occur
7. **Keep Dockerfiles optimized** for faster builds
8. **Use caching** in workflows to speed up builds

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Vite Documentation](https://vitejs.dev/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
