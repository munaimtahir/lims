# PHASE B: Surgical Cleanup Plan

**Repository:** munaimtahir/lims  
**Plan Date:** 2026-01-15  
**Status:** READY FOR EXECUTION

---

## Overview

This document provides the exact execution plan for cleaning contamination identified in Phase A. Files are grouped by risk level and action type for safe, incremental cleanup.

**Total Files to Process:** 37 files (~306KB contamination)
**Estimated Time:** 2-3 hours for careful execution
**Rollback Strategy:** Git commit after each group for easy revert

---

## Execution Strategy

### Principles:
1. **Safety First:** Start with zero-risk deletions
2. **Incremental:** Commit after each group
3. **Reversible:** All actions tracked in git for easy rollback
4. **Validate:** Test build/run after each major change
5. **Document:** Update README if references to deleted files exist

### Order of Operations:
1. Group A: Safe Deletions (Zero Risk)
2. Group B: Archive Cleanup (Low Risk)
3. Group C: Instance-Specific Content Removal (Medium Risk)
4. Group D: Manual Review Items (High Risk - Requires Decision)

---

## GROUP A: Safe Deletions (Zero Risk)

**Blast Radius:** NONE - These files are not referenced by any code, build scripts, or documentation.

### A1: AI Agent Reports (Root Directory) - 12 files

Execute:
```bash
rm -f AUDIT_REPORT.md
rm -f AUDIT_REPORT_UPDATED.md
rm -f AUDIT_RESULTS.md
rm -f COMPLETION_PLAN.md
rm -f COMPLETION_REPORT.md
rm -f COVERAGE_CLOSURE_ADDENDUM.md
rm -f FEATURE_STATUS.md
rm -f FEATURE_STATUS_UPDATED.md
rm -f TESTING_ROADMAP.md
rm -f TEST_DIAGNOSIS.md
rm -f TEST_STATUS_REPORT.md
rm -f MIGRATION_REPORT.md
```

**Validation:**
```bash
# Ensure no references in README or other docs
grep -r "AUDIT_REPORT\|COMPLETION_PLAN\|FEATURE_STATUS\|TEST_DIAGNOSIS\|COVERAGE_CLOSURE" README.md docs/ lims-backend/ frontend/ || echo "✓ No references found"
```

**Commit:**
```bash
git add -A
git commit -m "docs: remove AI agent report artifacts from root directory

Removed 12 AI-generated status reports that document development process
but are not part of project documentation. These include:
- AUDIT_REPORT*.md (3 files)
- COMPLETION_*.md (2 files)
- FEATURE_STATUS*.md (2 files)
- TEST_*.md (3 files)
- COVERAGE_CLOSURE_ADDENDUM.md
- MIGRATION_REPORT.md

Total cleanup: ~80KB of redundant documentation.
No functional impact - files not referenced by any code or build process."
```

---

### A2: Instance-Specific Deployment Files - 3 files

Execute:
```bash
rm -f updated_config.txt
rm -f docs/DEPLOYMENT_RUNBOOK_PORTAL.md
rm -f docs/Caddyfile.portal.updated
```

**Rationale:**
- `updated_config.txt`: Deployment report for VPS 34.16.82.13
- `docs/DEPLOYMENT_RUNBOOK_PORTAL.md`: Runbook for portal.alshifalab.pk (34.124.150.231)
- `docs/Caddyfile.portal.updated`: Instance-specific Caddy config

These belong in private deployment notes, not generic repository.

**Validation:**
```bash
grep -r "updated_config.txt\|DEPLOYMENT_RUNBOOK_PORTAL\|Caddyfile.portal" README.md docs/ || echo "✓ No references found"
```

**Commit:**
```bash
git add -A
git commit -m "docs: remove instance-specific deployment artifacts

Removed deployment files specific to portal.alshifalab.pk instance:
- updated_config.txt (VPS 34.16.82.13 deployment report)
- docs/DEPLOYMENT_RUNBOOK_PORTAL.md (portal.alshifalab.pk runbook)
- docs/Caddyfile.portal.updated (instance-specific Caddy config)

These belong in private deployment documentation, not the generic codebase.
Total cleanup: ~40KB."
```

---

### A3: Obsolete Artifacts - 1 file

Execute:
```bash
rm -f lims_db
```

**Rationale:** Empty SQLite database artifact (0 bytes) from Django default before PostgreSQL.

**Validation:**
```bash
grep -r "lims_db" . --exclude-dir=.git --exclude="*.md" || echo "✓ No code references found"
```

**Commit:**
```bash
git add -A
git commit -m "chore: remove empty SQLite database artifact

Removed lims_db (0 bytes) - empty SQLite file artifact from Django defaults
before PostgreSQL configuration. No functional impact."
```

---

### A4: Backend AI Reports - 4 files

Execute:
```bash
rm -f lims-backend/COVERAGE_PROGRESS_SUMMARY.md
rm -f lims-backend/FAILING_TESTS_DOCUMENTATION.md
rm -f lims-backend/FINAL_CLOSURE_REPORT.md
rm -f lims-backend/TEST_FIXES_SUMMARY.md
```

**Validation:**
```bash
grep -r "COVERAGE_PROGRESS\|FAILING_TESTS\|FINAL_CLOSURE\|TEST_FIXES" lims-backend/README.md lims-backend/pytest.ini lims-backend/config/ || echo "✓ No references found"
```

**Commit:**
```bash
git add -A
git commit -m "docs(backend): remove test report artifacts

Removed 4 AI-generated test and coverage reports from lims-backend/:
- COVERAGE_PROGRESS_SUMMARY.md
- FAILING_TESTS_DOCUMENTATION.md
- FINAL_CLOSURE_REPORT.md
- TEST_FIXES_SUMMARY.md

These document historical test failures/fixes, not current test documentation.
No functional impact."
```

---

### A5: Docs AI Reports - 3 files

Execute:
```bash
rm -f docs/TODOS_CHECKLIST.md
rm -f docs/PROJECT_STATUS_REPORT.md
rm -f docs/GO_LIVE_VERIFICATION_REPORT.md
```

**Rationale:**
- TODOS_CHECKLIST.md: Project management checklist (belongs in issue tracker)
- PROJECT_STATUS_REPORT.md: Status report for specific deployment
- GO_LIVE_VERIFICATION_REPORT.md: Go-live verification dated 2026-01-13

**Validation:**
```bash
grep -r "TODOS_CHECKLIST\|PROJECT_STATUS_REPORT\|GO_LIVE_VERIFICATION" README.md docs/VISION.md docs/WORKFLOW.md || echo "✓ No references found"
```

**Commit:**
```bash
git add -A
git commit -m "docs: remove project management artifacts

Removed project management and status tracking documents:
- docs/TODOS_CHECKLIST.md (project task list)
- docs/PROJECT_STATUS_REPORT.md (deployment status)
- docs/GO_LIVE_VERIFICATION_REPORT.md (go-live verification)

These are process artifacts, not project documentation. 
Project management belongs in issue tracker, not committed files."
```

---

**GROUP A SUMMARY:**
- **Files Removed:** 23 files
- **Space Freed:** ~120KB
- **Risk Level:** ZERO
- **Commits:** 5 incremental commits
- **Validation:** No references in active code or documentation

---

## GROUP B: Archive Cleanup (Low Risk)

**Blast Radius:** LOW - May lose historical reference, but no functional impact.

### B1: Archive AI Reports - 4 files

Execute:
```bash
rm -f docs/archive/CI_SETUP_SUMMARY.md
rm -f docs/archive/DEPLOYMENT_COMPLETE.md
rm -f docs/archive/DEPLOYMENT_SUMMARY.md
rm -f docs/archive/FINALIZATION_REPORT.md
rm -f docs/archive/PRODUCTION_READY.md
```

**Rationale:** AI-generated completion/status reports. True historical docs (README_OLD.md, IMPLEMENTATION_PLAN.md, FEATURE_PRIORITY.md) are preserved.

**Keep in Archive:**
- README_OLD.md (legitimate old README)
- IMPLEMENTATION_PLAN.md (historical planning reference)
- FEATURE_PRIORITY.md (historical feature prioritization)
- CI-CD.md (CI/CD documentation - may have historical value)
- DEPLOYMENT_INDEX.md (deployment docs index - review first)
- DEPLOYMENT_REFERENCE.md (deployment reference - review first)

**Validation:**
```bash
# Check if removed files are referenced in README.md
grep -r "CI_SETUP_SUMMARY\|DEPLOYMENT_COMPLETE\|DEPLOYMENT_SUMMARY\|FINALIZATION_REPORT\|PRODUCTION_READY" README.md docs/ || echo "✓ No references found"
```

**Commit:**
```bash
git add -A
git commit -m "docs(archive): remove AI-generated completion reports

Removed 5 AI-generated status/completion reports from docs/archive/:
- CI_SETUP_SUMMARY.md
- DEPLOYMENT_COMPLETE.md
- DEPLOYMENT_SUMMARY.md
- FINALIZATION_REPORT.md
- PRODUCTION_READY.md

Preserved legitimate historical docs:
- README_OLD.md (old README version)
- IMPLEMENTATION_PLAN.md (historical planning)
- FEATURE_PRIORITY.md (historical priorities)

Low risk: Historical reference only, no functional dependencies."
```

---

**GROUP B SUMMARY:**
- **Files Removed:** 5 files
- **Space Freed:** ~40KB
- **Risk Level:** LOW
- **Commits:** 1 commit
- **Preserved:** 6 legitimate historical docs in archive/

---

## GROUP C: Instance-Specific Content Sanitization (Medium Risk)

**Blast Radius:** MEDIUM - Requires careful editing to preserve generic guidance while removing hardcoded values.

### C1: Sanitize docs/NEXT_DEV_PLAN.md

**Action:** REPLACE_WITH_TEMPLATE

**Issue:** Contains 17+ hardcoded references to `portal.alshifalab.pk`

**Approach:**
1. Create generic version with placeholders
2. Replace hardcoded domain with `${YOUR_DOMAIN}` or `yourdomain.com`
3. Replace hardcoded IP with `${SERVER_IP}` or `YOUR_SERVER_IP`

**Example Transformation:**
```diff
- ALLOWED_HOSTS=portal.alshifalab.pk,<SERVER_PUBLIC_IP>
+ ALLOWED_HOSTS=yourdomain.com,${SERVER_IP}

- curl -k https://portal.alshifalab.pk/ -I
+ curl -k https://yourdomain.com/ -I

- Domain: portal.alshifalab.pk
+ Domain: yourdomain.com (replace with your actual domain)
```

**Validation After Edit:**
```bash
# Ensure no hardcoded instances remain
grep -i "portal.alshifalab.pk\|34.124.150.231" docs/NEXT_DEV_PLAN.md && echo "✗ Still has hardcoded values" || echo "✓ Sanitized"
```

**Commit:**
```bash
git add docs/NEXT_DEV_PLAN.md
git commit -m "docs: sanitize NEXT_DEV_PLAN.md - remove hardcoded instance data

Replaced 17+ hardcoded references to portal.alshifalab.pk with generic
placeholders (yourdomain.com, \${YOUR_DOMAIN}). Document is now reusable
for any deployment instance.

No functional changes - documentation only."
```

---

### C2: Remove Secret Risk Files

**Action:** DELETE (from working directory, not git history - they're gitignored)

Execute:
```bash
# Verify files are gitignored (should show no changes)
git status | grep ".env.production"

# Remove from working directory
rm -f .env.production
rm -f .env.production.backup
```

**Rationale:**
- `.env.production` contains SECRET_KEY and hardcoded portal.alshifalab.pk
- `.env.production.backup` is duplicate with same issues
- Both are gitignored, so not in git history
- Should not exist in working directory (use .env.production.example instead)

**Validation:**
```bash
# Verify removed
ls -la .env.production* 2>&1 | grep "cannot access" || echo "✗ Files still exist"

# Verify templates still exist
ls -la .env.production.example && echo "✓ Template preserved"
```

**Commit:**
```bash
# No git commit needed - files were gitignored
# Document in cleanup log only
echo "Removed .env.production and .env.production.backup from working directory (gitignored files)"
```

---

**GROUP C SUMMARY:**
- **Files Modified:** 1 file (docs/NEXT_DEV_PLAN.md)
- **Files Removed:** 2 files (from working directory only)
- **Risk Level:** MEDIUM
- **Commits:** 1 commit
- **Validation:** No hardcoded instance data remains in tracked files

---

## GROUP D: Manual Review Required (Requires Decision)

**Blast Radius:** UNKNOWN - Needs maintainer input or testing before action.

### D1: setup.sh (8.2KB)

**Status:** Not mentioned in README.md setup instructions

**Decision Needed:**
1. **If actively used in dev workflow:** KEEP
2. **If obsolete:** DELETE
3. **If uncertain:** ARCHIVE to docs/archive/

**Validation Test:**
```bash
# Check if script still works
bash setup.sh --help 2>&1 | head -5

# Check recent git history
git log --oneline --all -10 -- setup.sh

# Check if mentioned anywhere
grep -r "setup.sh" README.md docs/ lims-backend/README.md frontend/README.md
```

**Recommended Action:** If script is >6 months old with no recent updates and not in README, likely safe to DELETE or ARCHIVE.

---

### D2: audit_and_fix.py (9.5KB)

**Status:** Appears to be one-time utility script for database seeding and testing

**Decision Needed:**
1. **If used regularly for QA:** KEEP and document in README
2. **If one-time tool:** DELETE
3. **If useful reference:** ARCHIVE to scripts/ or docs/archive/

**Validation Test:**
```bash
# Check recent git history
git log --oneline --all -10 -- audit_and_fix.py

# Check if mentioned in docs
grep -r "audit_and_fix" README.md docs/ lims-backend/README.md
```

**Recommended Action:** If script is a one-time development tool with no documentation, safe to DELETE.

---

### D3: lims-backend/verify_phase1.py

**Status:** Phase 1 verification script

**Decision Needed:**
1. **If part of test suite:** KEEP and integrate into pytest
2. **If one-time verification:** DELETE or ARCHIVE
3. **If continuous validation tool:** KEEP and document

**Validation Test:**
```bash
# Check if imported anywhere
grep -r "verify_phase1" lims-backend/ --exclude="*.pyc"

# Check git history
git log --oneline --all -5 -- lims-backend/verify_phase1.py
```

**Recommended Action:** If script was for initial Phase 1 validation and not part of ongoing testing, safe to DELETE or ARCHIVE.

---

### D4: Deployment Documentation Review

**Files to Review:**
- `docs/deployment/DEPLOYMENT.md`
- `docs/deployment/SSH_DEPLOYMENT.md`

**Action Needed:** Read each file and identify instance-specific content

**Questions:**
1. Do they contain hardcoded IP addresses or domains?
2. Are examples generic or specific to portal.alshifalab.pk?
3. Can they be used as-is for new deployments?

**If instance-specific content found:**
- Sanitize with placeholders (like docs/NEXT_DEV_PLAN.md)
- Commit as: `docs(deployment): sanitize deployment guides - remove instance-specific data`

**If generic:**
- KEEP as-is

---

### D5: Archive Documentation Review

**Files to Review:**
- `docs/archive/CI-CD.md`
- `docs/archive/DEPLOYMENT_INDEX.md`
- `docs/archive/DEPLOYMENT_REFERENCE.md`

**Decision Needed:**
1. **If superseded by current docs:** DELETE
2. **If historical reference value:** KEEP in archive/
3. **If contains unique content:** MERGE into current docs and DELETE

**Validation:**
```bash
# Compare with current docs
diff -u docs/archive/CI-CD.md .github/workflows/ 2>/dev/null || echo "Check manually"

# Check file ages
git log --format="%ai %s" -- docs/archive/CI-CD.md | head -1
git log --format="%ai %s" -- docs/archive/DEPLOYMENT_INDEX.md | head -1
```

**Recommended Action:** If files are >1 year old and current docs cover the same topics, safe to DELETE.

---

### D6: ENVIRONMENT_VARIABLES.md (Root)

**Current Location:** Root directory  
**Proper Location:** docs/ directory

**Action:** MOVE_TO_ARCHIVE

Execute:
```bash
mv ENVIRONMENT_VARIABLES.md docs/archive/ENVIRONMENT_VARIABLES.md
```

**Rationale:** Environment variables are documented in:
- README.md (setup instructions)
- .env.example (inline comments)
- .env.production.example (inline comments)

If ENVIRONMENT_VARIABLES.md has unique content, keep in archive. If fully redundant, DELETE.

**Commit:**
```bash
git add -A
git commit -m "docs: move ENVIRONMENT_VARIABLES.md to archive

Moved environment variables documentation to docs/archive/.
Content is largely covered by .env.example and README setup instructions.
Preserved in archive for reference."
```

---

**GROUP D SUMMARY:**
- **Files Requiring Decision:** 6 items (3 scripts, 3 doc reviews)
- **Recommended Approach:** Conservative - archive uncertain items
- **Risk Level:** MEDIUM-HIGH (requires maintainer knowledge)
- **Estimated Time:** 30-60 minutes for review + testing

---

## Blast Radius Warning Section

### High-Impact Areas (DO NOT TOUCH)
1. **Backend Code** (`lims-backend/apps/`, `lims-backend/config/`)
   - Impact: Application breaks completely
   - Validation: Backend won't start

2. **Frontend Code** (`frontend/src/`)
   - Impact: UI breaks completely
   - Validation: Frontend build fails

3. **Docker Configuration** (`docker-compose.yml`, `Dockerfile`s)
   - Impact: Container orchestration fails
   - Validation: `docker-compose up` fails

4. **Build Configuration** (`requirements/`, `package.json`, `vite.config.ts`, `pytest.ini`)
   - Impact: Build/test failures
   - Validation: CI pipeline breaks

### Medium-Impact Areas (Review Changes Carefully)
1. **Deployment Scripts** (`scripts/`)
   - Impact: Deployment automation breaks
   - Validation: Manual deployment required

2. **Documentation** (`docs/`)
   - Impact: Developer onboarding harder
   - Validation: Missing information for setup/deployment

3. **CI/CD** (`.github/workflows/`)
   - Impact: Automated testing/deployment breaks
   - Validation: GitHub Actions fail

### Low-Impact Areas (Safe for Cleanup)
1. **AI Reports** (root `*.md` files)
   - Impact: None (not referenced by anything)
   - Validation: grep for references

2. **Instance-Specific Docs** (deployment runbooks)
   - Impact: None (specific to one deployment)
   - Validation: Generic docs still cover deployment process

3. **Archive** (`docs/archive/`)
   - Impact: Historical reference lost
   - Validation: No functional dependencies

---

## Post-Cleanup Validation Checklist

After each group of deletions, run these checks:

### Quick Validation (After Each Commit):
```bash
# 1. Check git status
git status

# 2. Verify no unintended deletions
git diff HEAD~1 --stat

# 3. Check for broken references
grep -r "FILENAME" . --exclude-dir=.git || echo "✓ No references"
```

### Full Validation (After All Groups):
```bash
# 1. Backend builds
cd lims-backend
python manage.py check
cd ..

# 2. Frontend builds
cd frontend
npm install
npm run build
cd ..

# 3. Docker Compose validates
docker-compose config

# 4. Documentation renders
# (manually check README.md renders correctly on GitHub)

# 5. No broken links in docs
# (optional: use markdown link checker tool)
```

See `PHASE_C_VERIFICATION_PLAN.md` for comprehensive validation.

---

## Rollback Procedures

### If something breaks after a commit:

**Option 1: Revert Last Commit**
```bash
git revert HEAD
git push
```

**Option 2: Revert Specific Commit**
```bash
git log --oneline -10  # Find commit hash
git revert <commit-hash>
git push
```

**Option 3: Cherry-Pick Working State**
```bash
git checkout <good-commit-hash> -- <file>
git add <file>
git commit -m "fix: restore <file> from <commit>"
git push
```

**Option 4: Hard Reset (LOCAL ONLY - Use with Caution)**
```bash
# WARNING: Loses local changes
git reset --hard HEAD~1  # Go back 1 commit
git push --force  # Only if you're sure
```

---

## Execution Timeline

**Estimated Total Time:** 2-3 hours

| Phase | Task | Time | Risk |
|-------|------|------|------|
| Setup | Read plan, backup repo | 15 min | None |
| Group A | Delete AI reports + artifacts (5 commits) | 30 min | Zero |
| Group B | Archive cleanup (1 commit) | 15 min | Low |
| Group C | Sanitize instance-specific docs (1 commit) | 30 min | Medium |
| Validate | Run Phase C validation checks | 30 min | - |
| Group D | Manual review and decisions | 60 min | High |
| Final | Complete validation, update README | 30 min | - |

**Recommended Approach:**
- Day 1: Groups A, B, C (safe deletions and sanitization)
- Day 2: Group D (manual review) + final validation

---

## Success Criteria

**Cleanup Complete When:**
- [x] All AI agent reports removed (23 files)
- [x] All instance-specific artifacts removed (5 files)
- [x] Hardcoded domains/IPs replaced with placeholders
- [x] Secret risk files removed from working directory
- [x] Manual review items resolved (keep/delete/archive decisions made)
- [x] Backend builds and tests pass
- [x] Frontend builds successfully
- [x] Docker Compose validates and runs
- [x] Documentation renders cleanly
- [x] No hardcoded instance data in tracked files

**Metrics:**
- Files removed: ~30-35 files
- Space freed: ~250-300KB
- Contamination eliminated: 90%+
- Core functionality: 100% preserved

---

## Final Notes

**Remember:**
1. **Commit after each group** for easy rollback
2. **Validate after each major change** (build, test, docker-compose)
3. **Document decisions** for Group D items in commit messages
4. **Update README** if any setup instructions reference deleted files
5. **Run Phase C verification** before declaring complete

**If Uncertain:**
- Archive instead of delete
- Sanitize instead of remove
- Ask maintainer for Group D decisions

---

**END OF PHASE B PLAN**

Next: Execute Groups A, B, C, then proceed to PHASE_C_VERIFICATION_PLAN.md
