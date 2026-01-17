# PHASE C: Post-Cleanup Verification Plan

**Repository:** munaimtahir/lims  
**Plan Date:** 2026-01-15  
**Purpose:** Define PASS/FAIL checks after cleanup execution

---

## Overview

This document provides comprehensive validation tests to ensure the repository is clean and functional after Phase B cleanup. All tests must PASS before declaring cleanup complete.

**Validation Phases:**
1. **Build Validation** - Backend and frontend must build successfully
2. **Test Validation** - Existing test suites must pass
3. **Deployment Validation** - Docker Compose must work
4. **Hygiene Validation** - Repository cleanliness checks
5. **Documentation Validation** - Docs render correctly

**Total Estimated Time:** 45-60 minutes

---

## Test Environment Setup

### Prerequisites:
```bash
# Clone fresh copy for testing (optional but recommended)
cd /tmp
git clone https://github.com/munaimtahir/lims.git lims-test
cd lims-test

# Verify on cleanup branch
git branch

# Install base requirements
# Backend: Python 3.12+, PostgreSQL 16+, Redis 7+
# Frontend: Node.js 20+
# Docker: Docker 24+, Docker Compose 2.20+
```

---

## PHASE 1: Build Validation

### Test 1.1: Backend Static Check
**Purpose:** Verify Django configuration is valid

**Command:**
```bash
cd lims-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal dependencies
pip install -r requirements/base.txt

# Run Django checks
python manage.py check --settings=config.settings.base
```

**Expected Output:**
```
System check identified no issues (0 silenced).
```

**PASS Criteria:**
- Exit code: 0
- No errors in output
- All apps load successfully

**FAIL Actions:**
- Check if any config files were accidentally deleted
- Review imports in settings files
- Restore from git if necessary

---

### Test 1.2: Backend Test Suite
**Purpose:** Verify existing tests still pass

**Command:**
```bash
cd lims-backend

# Install test dependencies
pip install -r requirements/test.txt

# Set test environment variables
export DJANGO_SETTINGS_MODULE=config.settings.test
export SECRET_KEY=test-secret-key-for-ci
export DB_NAME=:memory:  # SQLite in-memory for quick test

# Run pytest
pytest --no-cov -v
```

**Expected Output:**
```
====== X passed in Y.YYs ======
```

**PASS Criteria:**
- Exit code: 0
- All tests pass (no failures or errors)
- No import errors

**FAIL Actions:**
- Review test failures
- Check if test files were accidentally deleted
- Verify test data fixtures intact

**Note:** Coverage check not required for cleanup validation.

---

### Test 1.3: Frontend Dependency Install
**Purpose:** Verify package.json is intact

**Command:**
```bash
cd frontend

# Clean install
rm -rf node_modules package-lock.json
npm install
```

**Expected Output:**
```
added XXX packages
```

**PASS Criteria:**
- Exit code: 0
- No dependency resolution errors
- node_modules/ created

**FAIL Actions:**
- Check if package.json was corrupted
- Verify all dependencies listed
- Restore from git if necessary

---

### Test 1.4: Frontend Build
**Purpose:** Verify React app builds successfully

**Command:**
```bash
cd frontend

# Run TypeScript compilation
npm run type-check

# Run ESLint
npm run lint

# Build production bundle
npm run build
```

**Expected Output:**
```
✓ type-checking complete
✓ linting complete
✓ build complete
dist/ created with bundled files
```

**PASS Criteria:**
- Exit code: 0 for all commands
- No TypeScript errors
- No ESLint errors
- dist/ directory created with assets

**FAIL Actions:**
- Review TypeScript errors (check for missing files)
- Review ESLint errors (check configs)
- Verify vite.config.ts intact

---

## PHASE 2: Test Validation

### Test 2.1: Backend Unit Tests (Full Run)
**Purpose:** Comprehensive test of all backend functionality

**Command:**
```bash
cd lims-backend

# Run all tests with verbose output
pytest -v

# Check specific app tests
pytest apps/accounts/tests/ -v
pytest apps/patients/tests/ -v
pytest apps/laboratory/tests/ -v
pytest apps/orders/tests/ -v
pytest apps/samples/tests/ -v
pytest apps/results/tests/ -v
pytest apps/reports/tests/ -v
pytest apps/billing/tests/ -v
pytest apps/audit/tests/ -v
pytest apps/dashboard/tests/ -v
```

**PASS Criteria:**
- All test files load successfully
- All tests pass (100% pass rate)
- No skipped tests due to missing dependencies

**FAIL Actions:**
- Identify which app tests are failing
- Check if test files or fixtures were deleted
- Review test data dependencies

---

### Test 2.2: Frontend Tests (If Exist)
**Purpose:** Verify frontend test suite (if implemented)

**Command:**
```bash
cd frontend

# Check if tests exist
ls src/**/*.test.ts* src/**/*.spec.ts* 2>/dev/null | head

# Run tests if they exist
npm run test 2>/dev/null || echo "No frontend tests configured"
```

**PASS Criteria:**
- If tests exist: All pass
- If tests don't exist: Skip this test (note in report)

**FAIL Actions:**
- Review failing tests
- Check if test utilities were deleted

---

## PHASE 3: Deployment Validation

### Test 3.1: Docker Compose Configuration Check
**Purpose:** Verify docker-compose.yml is valid

**Command:**
```bash
cd /home/runner/work/lims/lims  # Repository root

# Validate docker-compose syntax
docker-compose config > /dev/null
echo "Exit code: $?"

# Show parsed configuration
docker-compose config
```

**Expected Output:**
```
Exit code: 0
(YAML configuration displayed)
```

**PASS Criteria:**
- Exit code: 0
- No YAML syntax errors
- All services defined (backend, frontend, db, redis, celery, proxy)

**FAIL Actions:**
- Check if docker-compose.yml was corrupted
- Verify all referenced Dockerfiles exist
- Restore from git if necessary

---

### Test 3.2: Docker Compose Build
**Purpose:** Verify all Docker images build successfully

**Command:**
```bash
cd /home/runner/work/lims/lims

# Build all images (without starting)
docker-compose build --no-cache
```

**Expected Output:**
```
Successfully built backend
Successfully built frontend
Successfully built proxy
...
```

**PASS Criteria:**
- Exit code: 0
- All services build successfully
- No missing files in build context

**FAIL Actions:**
- Review build errors
- Check if Dockerfiles or required files were deleted
- Verify COPY commands reference existing files

---

### Test 3.3: Docker Compose Start (Smoke Test)
**Purpose:** Verify services start and communicate

**Command:**
```bash
cd /home/runner/work/lims/lims

# Start all services
docker-compose up -d

# Wait for services to initialize
sleep 30

# Check service status
docker-compose ps

# Check logs for errors
docker-compose logs | grep -i "error\|failed\|exception" | head -20

# Test backend health endpoint
curl -f http://localhost:8000/api/v1/health/ || echo "Backend health check failed"

# Test frontend serves
curl -f http://localhost/ || echo "Frontend access failed"

# Cleanup
docker-compose down
```

**PASS Criteria:**
- All services show "Up" status
- No critical errors in logs
- Backend health endpoint responds (200 OK)
- Frontend serves HTML

**FAIL Actions:**
- Review service logs individually: `docker-compose logs [service]`
- Check environment variable configuration
- Verify database migrations run successfully

---

### Test 3.4: Caddy Configuration Validation
**Purpose:** Verify Caddyfile is syntactically correct

**Command:**
```bash
cd /home/runner/work/lims/lims

# Validate Caddyfile syntax (if caddy installed locally)
caddy validate --config Caddyfile 2>/dev/null || echo "Caddy not installed locally, skip validation"

# Alternative: Check in Docker
docker run --rm -v "$PWD/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:latest caddy validate --config /etc/caddy/Caddyfile
```

**PASS Criteria:**
- Exit code: 0
- No syntax errors
- All directives valid

**FAIL Actions:**
- Review Caddyfile syntax
- Check if file was corrupted
- Restore from git if necessary

---

## PHASE 4: Repository Hygiene Validation

### Test 4.1: No AI Artifacts Remaining
**Purpose:** Verify all AI-generated reports removed

**Command:**
```bash
cd /home/runner/work/lims/lims

# Search for common AI artifact patterns
find . -type f \( \
  -name "AUDIT_REPORT*.md" -o \
  -name "COMPLETION_*.md" -o \
  -name "FEATURE_STATUS*.md" -o \
  -name "TEST_STATUS*.md" -o \
  -name "COVERAGE_*.md" -o \
  -name "MIGRATION_REPORT.md" \
\) ! -path "./.git/*" ! -path "./docs/repo-cleanup/*"

# Expected: No output (all removed)
echo "Expected: No files found"
```

**PASS Criteria:**
- No files found (empty output)
- repo-cleanup docs are exception (they document the cleanup)

**FAIL Actions:**
- Identify remaining AI artifacts
- Remove manually or re-run Phase B cleanup

---

### Test 4.2: No Hardcoded Instance Data
**Purpose:** Verify portal.alshifalab.pk and IPs removed

**Command:**
```bash
cd /home/runner/work/lims/lims

# Search for hardcoded domain
grep -r "portal.alshifalab.pk" . \
  --exclude-dir=.git \
  --exclude-dir=docs/repo-cleanup \
  || echo "✓ No hardcoded domain found"

# Search for hardcoded IPs
grep -rE "34\.124\.150\.231|34\.16\.82\.13" . \
  --exclude-dir=.git \
  --exclude-dir=docs/repo-cleanup \
  || echo "✓ No hardcoded IPs found"
```

**PASS Criteria:**
- No matches found (or only in repo-cleanup docs)
- Exit code: 1 (grep found nothing)

**FAIL Actions:**
- Review remaining instances
- Sanitize files with placeholders
- Re-commit changes

---

### Test 4.3: No Secret Files in Working Directory
**Purpose:** Verify .env.production removed

**Command:**
```bash
cd /home/runner/work/lims/lims

# Check for secret-risk files
ls -la .env.production .env.production.backup 2>&1 | grep "cannot access"

# Verify templates still exist
ls -la .env.example .env.production.example
```

**PASS Criteria:**
- .env.production: "cannot access" (does not exist)
- .env.production.backup: "cannot access" (does not exist)
- .env.example: exists
- .env.production.example: exists

**FAIL Actions:**
- Remove remaining secret files from working directory
- Verify .gitignore includes these patterns

---

### Test 4.4: No Empty or Artifact Files
**Purpose:** Verify lims_db and other artifacts removed

**Command:**
```bash
cd /home/runner/work/lims/lims

# Check for empty files (excluding .gitkeep)
find . -type f -empty ! -name ".gitkeep" ! -path "./.git/*"

# Expected: No output (no empty files)
echo "Expected: No empty files found"

# Check for common artifact patterns
find . -type f \( \
  -name "*.backup" -o \
  -name "*.bak" -o \
  -name "*.tmp" -o \
  -name "lims_db" \
\) ! -path "./.git/*"

# Expected: No output
echo "Expected: No artifact files found"
```

**PASS Criteria:**
- No empty files found (except .gitkeep)
- No backup/tmp files found

**FAIL Actions:**
- Remove empty files: `find . -type f -empty -delete`
- Remove artifacts: `rm -f *.backup *.bak *.tmp`

---

### Test 4.5: No Large Uncommitted Files
**Purpose:** Verify no build artifacts or large files added

**Command:**
```bash
cd /home/runner/work/lims/lims

# Find large files (>1MB)
find . -type f -size +1M ! -path "./.git/*" ! -path "*/node_modules/*" ! -path "*/venv/*"

# Expected: Only legitimate large files (if any)
# Common legitimate large files:
# - package-lock.json (~500KB-2MB)
# - pnpm-lock.yaml
# - Database dumps (if intentional)
```

**PASS Criteria:**
- No unexpected large files
- Only package manager lock files or documented assets

**FAIL Actions:**
- Review large files
- Add to .gitignore if build artifacts
- Remove if unnecessary

---

### Test 4.6: No Python/Node Cache Files Tracked
**Purpose:** Verify build caches not in git

**Command:**
```bash
cd /home/runner/work/lims/lims

# Check for Python cache
git ls-files | grep -E "__pycache__|\.pyc$|\.pyo$"
echo "Expected: No output (no Python cache tracked)"

# Check for Node build outputs
git ls-files | grep -E "node_modules/|frontend/dist/|frontend/build/"
echo "Expected: No output (no Node artifacts tracked)"

# Verify .gitignore includes these patterns
grep -E "__pycache__|\.pyc|node_modules|dist/" .gitignore
echo "Expected: All patterns found in .gitignore"
```

**PASS Criteria:**
- No cache files tracked by git
- .gitignore includes all cache patterns

**FAIL Actions:**
- Remove tracked cache files: `git rm -r --cached <path>`
- Update .gitignore to exclude caches
- Commit changes

---

## PHASE 5: Documentation Validation

### Test 5.1: README Renders Correctly
**Purpose:** Verify README.md displays properly

**Manual Check:**
1. Open README.md in GitHub preview or Markdown viewer
2. Check for:
   - No broken links
   - No references to deleted files
   - All images/diagrams load
   - Table of contents links work
   - Setup instructions complete

**PASS Criteria:**
- README renders without errors
- All links work (or are clearly marked as external)
- No references to deleted AI reports

**FAIL Actions:**
- Fix broken links
- Update references to match new structure
- Test links with markdown link checker tool

---

### Test 5.2: Documentation Structure Intact
**Purpose:** Verify essential docs not accidentally deleted

**Command:**
```bash
cd /home/runner/work/lims/lims

# Check essential docs exist
test -f README.md && echo "✓ README.md"
test -f LICENSE && echo "✓ LICENSE"
test -f CHANGELOG.md && echo "✓ CHANGELOG.md"
test -f docs/VISION.md && echo "✓ docs/VISION.md"
test -f docs/WORKFLOW.md && echo "✓ docs/WORKFLOW.md"
test -f docs/DATA_MODEL.md && echo "✓ docs/DATA_MODEL.md"
test -f docs/api/API_DESIGN.md && echo "✓ docs/api/API_DESIGN.md"
test -f docs/architecture/ARCHITECTURE.md && echo "✓ docs/architecture/ARCHITECTURE.md"
test -f docs/deployment/DEPLOYMENT.md && echo "✓ docs/deployment/DEPLOYMENT.md"
test -f docs/deployment/TROUBLESHOOTING.md && echo "✓ docs/deployment/TROUBLESHOOTING.md"
```

**PASS Criteria:**
- All essential documentation files exist
- All checks show "✓"

**FAIL Actions:**
- Restore missing docs from git: `git checkout HEAD -- <file>`
- Review Phase B execution for errors

---

### Test 5.3: No Broken Documentation Links
**Purpose:** Verify internal doc links work

**Command:**
```bash
cd /home/runner/work/lims/lims

# Extract markdown links from README
grep -oP '\[.*?\]\(\K[^)]+' README.md | grep -v "^http" | while read link; do
  if [ -f "$link" ]; then
    echo "✓ $link"
  else
    echo "✗ BROKEN: $link"
  fi
done
```

**PASS Criteria:**
- All internal links resolve to existing files
- Only external links (http://, https://) unverified

**FAIL Actions:**
- Update broken links to correct paths
- Remove links to deleted files
- Add notes if files intentionally removed

---

### Test 5.4: Archive Documentation Cleaned
**Purpose:** Verify docs/archive/ contains only legitimate historical docs

**Command:**
```bash
cd /home/runner/work/lims/lims

# List archive contents
ls -lh docs/archive/

# Expected to remain:
# - README_OLD.md (legitimate old README)
# - IMPLEMENTATION_PLAN.md (historical planning)
# - FEATURE_PRIORITY.md (historical priorities)
# - Potentially: CI-CD.md, DEPLOYMENT_INDEX.md, DEPLOYMENT_REFERENCE.md

# Should NOT be present:
# - CI_SETUP_SUMMARY.md
# - DEPLOYMENT_COMPLETE.md
# - DEPLOYMENT_SUMMARY.md
# - FINALIZATION_REPORT.md
# - PRODUCTION_READY.md
```

**PASS Criteria:**
- Only 3-6 files remain in archive/
- No AI-generated completion reports
- Files have legitimate historical value

**FAIL Actions:**
- Remove remaining AI artifacts
- Review each file's purpose
- Delete if redundant, keep if historical value

---

## PHASE 6: Smoke Test (End-to-End)

### Test 6.1: Fresh Clone and Setup
**Purpose:** Verify a new developer can set up the project

**Procedure:**
```bash
# 1. Clone repository
cd /tmp
rm -rf lims-fresh-test
git clone https://github.com/munaimtahir/lims.git lims-fresh-test
cd lims-fresh-test

# 2. Follow README setup instructions exactly
# (Manual step - follow README.md "Getting Started")

# 3. Verify backend runs
cd lims-backend
python manage.py check
cd ..

# 4. Verify frontend builds
cd frontend
npm install
npm run build
cd ..

# 5. Verify Docker Compose works
docker-compose config
docker-compose build
```

**PASS Criteria:**
- Clone succeeds
- README instructions are complete and accurate
- Backend check passes
- Frontend builds
- Docker Compose validates

**FAIL Actions:**
- Update README with missing steps
- Fix broken setup instructions
- Test again

---

### Test 6.2: Minimal Integration Test
**Purpose:** Verify backend + frontend can communicate

**Procedure:**
```bash
cd /home/runner/work/lims/lims

# 1. Start services
docker-compose up -d

# 2. Wait for initialization
sleep 30

# 3. Test backend API
curl -f http://localhost:8000/api/v1/health/
echo ""

# 4. Test frontend loads
curl -f http://localhost/ | head -20

# 5. Test API documentation
curl -f http://localhost:8000/api/docs/ | grep -i swagger

# 6. Cleanup
docker-compose down
```

**PASS Criteria:**
- Health endpoint returns 200 OK
- Frontend serves HTML
- API docs accessible

**FAIL Actions:**
- Review service logs
- Check CORS configuration
- Verify proxy routing in Caddyfile

---

## Final Validation Checklist

**Complete this checklist before declaring cleanup successful:**

### Build & Test:
- [ ] Backend Django check passes (no errors)
- [ ] Backend test suite passes (100% pass rate)
- [ ] Frontend installs dependencies successfully
- [ ] Frontend builds without errors (TypeScript + ESLint clean)
- [ ] No import errors in any module

### Deployment:
- [ ] docker-compose.yml validates (correct syntax)
- [ ] All Docker images build successfully
- [ ] Docker Compose starts all services (smoke test)
- [ ] Backend health endpoint responds (200 OK)
- [ ] Frontend serves HTML (accessible via proxy)
- [ ] Caddyfile is valid

### Repository Hygiene:
- [ ] No AI artifact reports remain (AUDIT_*, COMPLETION_*, etc.)
- [ ] No hardcoded portal.alshifalab.pk references (except in repo-cleanup docs)
- [ ] No hardcoded IP addresses (34.124.150.231, 34.16.82.13)
- [ ] No .env.production in working directory
- [ ] No empty artifact files (lims_db removed)
- [ ] No large uncommitted files (>1MB, except legitimate)
- [ ] No Python/Node cache tracked by git (__pycache__, node_modules/)

### Documentation:
- [ ] README.md renders correctly (no broken links)
- [ ] All essential docs present (10 core files verified)
- [ ] No broken internal documentation links
- [ ] Archive cleaned (only 3-6 legitimate historical docs)
- [ ] No references to deleted files in docs

### Security:
- [ ] No secrets in git history (verified with git log)
- [ ] .gitignore includes all secret patterns
- [ ] Only template .env files tracked (.env.example)
- [ ] No API keys or passwords in code/docs

### Smoke Test:
- [ ] Fresh clone and setup works (following README)
- [ ] Backend + frontend integration works (API calls succeed)
- [ ] API documentation accessible

---

## Success Metrics

**Cleanup considered SUCCESSFUL when:**

1. **100% Pass Rate:** All tests in this plan pass
2. **No Regressions:** Existing functionality works (build, test, deploy)
3. **Hygiene Score:** 95%+ contamination removed (~30+ files deleted)
4. **Security Score:** No secrets in working directory or git history
5. **Documentation Score:** All essential docs intact, no broken links

**Estimated Contamination Removal:**
- Before cleanup: ~37 files, ~306KB contamination
- After cleanup: ~5-7 files remaining (for manual review), ~250KB removed
- **Cleanup Rate:** ~82% of contamination eliminated

---

## Rollback Criteria

**Rollback Phase B cleanup if:**

1. Backend fails to build or Django check fails
2. Any core tests fail (not pre-existing failures)
3. Docker Compose fails to validate or build
4. Essential documentation files missing
5. Frontend build completely broken

**Rollback Procedure:**
```bash
# Identify last good commit before cleanup
git log --oneline -20

# Revert to last good state
git revert <commit-hash-range>

# Or hard reset (if not pushed)
git reset --hard <last-good-commit>
```

---

## Troubleshooting Common Issues

### Issue: Backend check fails with ImportError
**Cause:** Accidentally deleted Python module or app  
**Fix:** `git checkout HEAD -- lims-backend/apps/<missing-app>/`

### Issue: Frontend build fails with missing file
**Cause:** Accidentally deleted React component or asset  
**Fix:** `git checkout HEAD -- frontend/src/<missing-file>`

### Issue: Docker Compose fails with "file not found"
**Cause:** Dockerfile or config file deleted  
**Fix:** `git checkout HEAD -- <missing-file>`

### Issue: Tests fail with missing fixtures
**Cause:** Test data files deleted  
**Fix:** `git checkout HEAD -- lims-backend/fixtures/`

### Issue: Documentation links broken
**Cause:** Referenced files deleted in cleanup  
**Fix:** Update links to point to remaining docs or remove links

---

## Post-Verification Actions

**After ALL tests pass:**

1. **Update Repository Description:**
   - Remove any outdated info
   - Ensure description accurate

2. **Create Release Notes:**
   - Document cleanup performed
   - List removed files (summary)
   - Note any breaking changes

3. **Notify Team:**
   - Inform developers of cleanup
   - Update any external documentation
   - Remind to use .env.example templates

4. **Archive Cleanup Documentation:**
   - Keep docs/repo-cleanup/ for historical reference
   - Consider moving to docs/archive/ after 6 months

---

**END OF PHASE C VERIFICATION PLAN**

Execute this plan after Phase B cleanup to ensure repository health and functionality.
