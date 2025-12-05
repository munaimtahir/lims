# CI/CD Documentation

This document describes the GitHub Actions workflows used in this repository for continuous integration and security scanning.

## Overview

The repository uses 4 GitHub Actions workflows to ensure code quality, run tests, and maintain security:

1. **Backend CI** - Tests and validates Python/Django backend
2. **Frontend CI** - Tests and validates React/TypeScript frontend  
3. **Docker CI** - Validates Docker Compose configuration
4. **CodeQL Security Scan** - Automated security vulnerability scanning

## Workflows

### Backend CI

**File:** `.github/workflows/backend.yml`

**Purpose:** Validates Python backend code quality, runs tests with coverage, and checks for pending migrations.

**Triggers:**
- Push to `main` or `develop` branches (when backend files change)
- Pull requests (when backend files change)

**Jobs:**
- **Linting:** Runs `ruff`, `black`, and `isort` to check code style
- **Testing:** Runs pytest with 99% coverage requirement
- **Migrations:** Checks for pending Django migrations

**Required Secrets/Variables:** None

**Caching:** Uses pip cache for faster dependency installation

**Timeout:** 15 minutes

**Common Failures:**
- **Lint failures:** Run `black backend/`, `isort backend/`, and fix `ruff` errors locally
- **Test failures:** Check test output and fix failing tests
- **Coverage below 99%:** Add tests for uncovered code
- **Pending migrations:** Run `python manage.py makemigrations` if intentional

### Frontend CI

**File:** `.github/workflows/frontend.yml`

**Purpose:** Validates React/TypeScript frontend code quality, type safety, and runs tests.

**Triggers:**
- Push to `main` or `develop` branches (when frontend files change)
- Pull requests (when frontend files change)

**Jobs:**
- **Linting:** Runs ESLint
- **Type Checking & Build:** Runs TypeScript compiler and Vite build
- **Testing:** Runs Vitest tests

**Required Secrets/Variables:** None

**Caching:** Uses pnpm cache for faster dependency installation

**Timeout:** 15 minutes

**Common Failures:**
- **Lint failures:** Run `pnpm lint` locally and fix issues
- **Type errors:** Run `pnpm build` locally and fix TypeScript errors
- **Test failures:** Run `pnpm test` locally and fix failing tests

### Docker CI

**File:** `.github/workflows/docker.yml`

**Purpose:** Validates Docker Compose configuration syntax.

**Triggers:**
- Push to `main` or `develop` branches (when Docker files change)
- Pull requests (when Docker files change)

**Jobs:**
- **Validate Compose:** Runs `docker compose config --quiet` to validate syntax

**Required Secrets/Variables:** None

**Caching:** None

**Timeout:** 10 minutes

**Common Failures:**
- **Invalid YAML:** Check `docker-compose.yml` syntax
- **Missing .env variables:** Ensure all referenced variables are documented

### CodeQL Security Scan

**File:** `.github/workflows/codeql.yml`

**Purpose:** Automated security vulnerability scanning for JavaScript and Python code.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Weekly schedule (Mondays at midnight UTC)

**Jobs:**
- **Analyze:** Runs CodeQL analysis for both JavaScript and Python

**Required Secrets/Variables:** None (uses GitHub's built-in CodeQL)

**Caching:** None

**Timeout:** 30 minutes

**Common Failures:**
- **Security vulnerabilities found:** Review CodeQL alerts in Security tab and address them
- **Build failures:** Ensure code compiles correctly (checked by Autobuild step)

## Running Workflows Manually

Some workflows support manual triggering via `workflow_dispatch`. To run manually:

1. Go to Actions tab in GitHub
2. Select the workflow
3. Click "Run workflow"
4. Select branch and confirm

Currently, none of the workflows have `workflow_dispatch` enabled, but this can be added if needed.

## Local Testing

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run linters
ruff check . --exit-zero
black --check .
isort --check .

# Fix formatting
black .
isort .

# Run tests
pytest -v --cov=. --cov-report=term-missing --cov-fail-under=99

# Check migrations
python manage.py makemigrations --check --dry-run
```

### Frontend

```bash
cd frontend

# Install dependencies
pnpm install

# Run linter
pnpm lint

# Type check and build
pnpm build

# Run tests
pnpm test -- --run
```

### Docker

```bash
# Create .env file first
cp .env.example .env

# Validate docker-compose.yml
docker compose config --quiet
```

## Concurrency Control

All workflows use concurrency groups to prevent multiple runs on the same branch:
- For push events, previous runs are cancelled
- For pull requests, runs are cancelled when new commits are pushed
- Scheduled runs are not cancelled

## Permissions

All workflows use least-privilege permissions:
- **Backend, Frontend, Docker CI:** `contents: read` only
- **CodeQL:** `contents: read`, `actions: read`, `security-events: write`

## Action Versions

All workflows use pinned action versions for security and stability:
- `actions/checkout@v4` - Latest stable checkout action
- `actions/setup-node@v4` - Latest stable Node.js setup
- `actions/setup-python@v5` - Latest stable Python setup
- `pnpm/action-setup@v4` - Latest stable pnpm setup
- `github/codeql-action/*@v3` - Latest stable CodeQL actions

## Maintenance

### Updating Dependencies

When updating Python or JavaScript dependencies:
1. Update `requirements.txt` or `package.json`
2. Test locally to ensure everything works
3. Commit and push - CI will validate automatically

### Updating Workflow Actions

To update GitHub Actions:
1. Check for new versions in the GitHub Actions marketplace
2. Update version in workflow files
3. Test on a feature branch before merging to main

### Adding New Workflows

When adding new workflows:
1. Follow the existing patterns (concurrency, permissions, timeouts)
2. Add documentation to this file
3. Ensure least-privilege permissions
4. Add appropriate caching where applicable
5. Set reasonable timeouts

## Troubleshooting

### Workflow Not Triggering

Check:
- The file paths in the `paths` filter match your changes
- You're pushing to the correct branch (`main` or `develop`)
- The workflow file has valid YAML syntax

### Slow Workflow Runs

- Check if caching is enabled and working properly
- Review dependency installation times
- Consider splitting large workflows into smaller jobs

### Permission Errors

- Ensure the workflow has the minimum required permissions
- Check if repository settings allow the workflow to access required resources

## Support

For issues with CI/CD:
1. Check this documentation first
2. Review the specific workflow run logs in the Actions tab
3. Open an issue with workflow run link and error details
