# LIMS Next Development Plan
## Go-Live Path for yourdomain.com

**Date:** 2026-01-08  
**Target Domain:** yourdomain.com  
**Priority:** Go-live blockers first, then enhancements

---

## Phase 1: Critical Configuration (Go-Live Blockers)

### Task 1.1: Add CSRF_TRUSTED_ORIGINS to Production Settings

**Priority**: 🔴 CRITICAL  
**File**: `lims-backend/config/settings/production.py`  
**Estimated Time**: 5 minutes

**Action**:
Add CSRF_TRUSTED_ORIGINS configuration after CORS configuration (around line 165):

```python
# ============================================
# CSRF CONFIGURATION
# ============================================
# CRITICAL FOR HTTPS DEPLOYMENT
# Django 4.0+ requires CSRF_TRUSTED_ORIGINS for HTTPS sites
# Must include the domain where the frontend is hosted

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')]
if not CSRF_TRUSTED_ORIGINS or CSRF_TRUSTED_ORIGINS == ['']:
    # Try to derive from CORS_ALLOWED_ORIGINS if not explicitly set
    if CORS_ALLOWED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
    else:
        logger.warning(
            "WARNING: CSRF_TRUSTED_ORIGINS not configured. "
            "CSRF protection may fail for HTTPS requests. "
            "Set CSRF_TRUSTED_ORIGINS to your frontend domain (e.g., https://yourdomain.com)"
        )

logger.info(f"Production CSRF_TRUSTED_ORIGINS configured: {CSRF_TRUSTED_ORIGINS}")
```

**Acceptance Criteria**:
- [ ] CSRF_TRUSTED_ORIGINS is defined in production.py
- [ ] Reads from environment variable CSRF_TRUSTED_ORIGINS
- [ ] Falls back to CORS_ALLOWED_ORIGINS if not set
- [ ] Logs configuration on startup
- [ ] No syntax errors

---

### Task 1.2: Create .env.production File

**Priority**: 🔴 CRITICAL  
**File**: `.env.production` (create new file)  
**Estimated Time**: 10 minutes

**Action**:
Create `.env.production` in the repository root with the following content:

```bash
# ============================================
# LIMS Production Environment Configuration
# Domain: yourdomain.com
# ============================================

# Django Security
SECRET_KEY=<GENERATE_NEW_SECURE_KEY>
DEBUG=False

# Domain Configuration
SERVER_NAME=yourdomain.com
ALLOWED_HOSTS=yourdomain.com,${SERVER_IP}
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=lims_db
DB_USER=postgres
DB_PASSWORD=<GENERATE_SECURE_PASSWORD>
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# SSL/HTTPS Configuration
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<YOUR_EMAIL>
EMAIL_HOST_PASSWORD=<YOUR_EMAIL_PASSWORD>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Frontend Configuration
VITE_API_BASE_URL=/api/v1/
REACT_APP_API_BASE_URL=/api/v1/

# Caddy Configuration
CADDY_DOMAIN=yourdomain.com
CADDY_DOMAINS_ADDITIONAL=

# Logging
LOG_LEVEL=INFO

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

**Replace Placeholders**:
- `<GENERATE_NEW_SECURE_KEY>`: Run `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- `<SERVER_PUBLIC_IP>`: Get from `curl ifconfig.me` or server admin
- `<GENERATE_SECURE_PASSWORD>`: Run `openssl rand -base64 32`
- `<YOUR_EMAIL>`: SMTP email address
- `<YOUR_EMAIL_PASSWORD>`: SMTP email password

**Acceptance Criteria**:
- [ ] `.env.production` file exists in repository root
- [ ] All placeholders replaced with actual values
- [ ] SECRET_KEY is strong (50+ characters)
- [ ] DB_PASSWORD is strong (32+ characters)
- [ ] ALLOWED_HOSTS includes yourdomain.com and server IP
- [ ] CSRF_TRUSTED_ORIGINS includes https://yourdomain.com
- [ ] CORS_ALLOWED_ORIGINS includes https://yourdomain.com
- [ ] File is NOT committed to git (add to .gitignore)

---

### Task 1.3: Update docker-compose.yml Environment Variables

**Priority**: 🔴 CRITICAL  
**File**: `docker-compose.yml`  
**Estimated Time**: 5 minutes

**Action**:
Verify that docker-compose.yml correctly references `.env.production`:

1. Check `backend` service has `env_file: - .env.production`
2. Check `celery` service has `env_file: - .env.production`
3. Check `frontend` service has `env_file: - .env.production`
4. Check `proxy` service uses `CADDY_DOMAIN: ${SERVER_NAME:-localhost}`

**Current Status**: ✅ Already configured correctly

**Acceptance Criteria**:
- [ ] All services reference `.env.production`
- [ ] Environment variables are not hardcoded
- [ ] Defaults are safe fallbacks

---

### Task 1.4: Investigate Container Health Issues

**Priority**: 🟠 HIGH  
**Files**: Container logs  
**Estimated Time**: 15 minutes

**Action**:
1. Check backend health:
   ```bash
   docker compose logs backend | tail -50
   docker compose exec backend curl -f http://localhost:8000/api/v1/health/
   ```

2. Check proxy health:
   ```bash
   docker compose logs proxy | tail -50
   docker compose exec proxy curl -f http://localhost/health
   ```

3. Check if health check endpoints are accessible:
   - Backend: `/api/v1/health/`
   - Proxy: `/health`

**Acceptance Criteria**:
- [ ] Backend health endpoint responds with 200 OK
- [ ] Proxy health endpoint responds with 200 OK
- [ ] Containers show as healthy in `docker compose ps`
- [ ] No critical errors in logs

---

### Task 1.5: Run Database Migrations

**Priority**: 🟠 HIGH  
**Command**: `docker compose exec backend python manage.py migrate`  
**Estimated Time**: 5 minutes

**Action**:
```bash
cd /home/munaim/srv/apps/lims
docker compose exec backend python manage.py migrate
```

**Acceptance Criteria**:
- [ ] Migrations run successfully
- [ ] No migration errors
- [ ] Database schema is up to date

---

### Task 1.6: Collect Static Files

**Priority**: 🟠 HIGH  
**Command**: `docker compose exec backend python manage.py collectstatic --noinput`  
**Estimated Time**: 2 minutes

**Action**:
```bash
docker compose exec backend python manage.py collectstatic --noinput
```

**Acceptance Criteria**:
- [ ] Static files collected successfully
- [ ] Files are in `/app/staticfiles` volume
- [ ] No errors during collection

---

## Phase 2: Testing & Verification

### Task 2.1: Run Backend Tests (Quick Smoke Test)

**Priority**: 🟡 MEDIUM  
**Command**: `docker compose exec backend pytest -x -v --tb=short`  
**Estimated Time**: 10 minutes

**Action**:
```bash
docker compose exec backend pytest -x -v --tb=short
```

**Acceptance Criteria**:
- [ ] Tests run without import errors
- [ ] Critical tests pass (auth, health, basic CRUD)
- [ ] Test summary recorded in report

**Note**: Some tests may fail (30 failing tests known). Focus on critical path tests.

---

### Task 2.2: Build Frontend

**Priority**: 🟡 MEDIUM  
**Command**: `docker compose build frontend`  
**Estimated Time**: 5 minutes

**Action**:
```bash
docker compose build frontend
```

**Acceptance Criteria**:
- [ ] Frontend builds successfully
- [ ] No build errors
- [ ] VITE_API_BASE_URL is set correctly in build

---

### Task 2.3: Restart All Services

**Priority**: 🟡 MEDIUM  
**Command**: `docker compose restart`  
**Estimated Time**: 2 minutes

**Action**:
```bash
docker compose restart
docker compose ps  # Verify all services are up
```

**Acceptance Criteria**:
- [ ] All services restart successfully
- [ ] All containers show as "Up" in `docker compose ps`
- [ ] Health checks pass after restart

---

### Task 2.4: Smoke Tests with curl

**Priority**: 🟡 MEDIUM  
**Commands**: See below  
**Estimated Time**: 5 minutes

**Action**:
```bash
# Test frontend (should return HTML)
curl -k https://yourdomain.com/ -I

# Test API health endpoint
curl -k https://yourdomain.com/api/v1/health/

# Test admin (should redirect to login)
curl -k https://yourdomain.com/admin/ -I
```

**Acceptance Criteria**:
- [ ] Frontend returns 200 OK or 301/302 redirect
- [ ] API health endpoint returns JSON with status
- [ ] Admin redirects to login (not 400/500 error)
- [ ] All requests use HTTPS

---

## Phase 3: Post-Deployment Verification

### Task 3.1: Verify Domain Configuration

**Priority**: 🟡 MEDIUM  
**Action**: Manual verification  
**Estimated Time**: 5 minutes

**Checklist**:
- [ ] DNS resolves correctly: `nslookup yourdomain.com`
- [ ] HTTPS certificate is valid: `openssl s_client -connect yourdomain.com:443`
- [ ] No mixed content warnings in browser console
- [ ] Frontend loads without CORS errors

---

### Task 3.2: Test Critical Workflows

**Priority**: 🟡 MEDIUM  
**Action**: Manual testing  
**Estimated Time**: 30 minutes

**Test Scenarios**:
1. **User Login**
   - [ ] Admin can log in
   - [ ] JWT token is received
   - [ ] Token works for API calls

2. **Patient Registration**
   - [ ] Create new patient
   - [ ] Search existing patient
   - [ ] Update patient information

3. **Order Creation**
   - [ ] Create new order
   - [ ] Add tests to order
   - [ ] Verify totals calculated correctly

4. **Payment Processing**
   - [ ] Record payment
   - [ ] Generate receipt PDF
   - [ ] Verify receipt downloads

5. **Result Entry**
   - [ ] Enter test results
   - [ ] Verify auto-flagging works
   - [ ] Submit for verification

6. **Report Generation**
   - [ ] Generate PDF report
   - [ ] Verify PDF downloads
   - [ ] Check PDF formatting

**Acceptance Criteria**:
- [ ] All critical workflows complete without errors
- [ ] No console errors in browser
- [ ] API calls return expected responses

---

### Task 3.3: Monitor Logs

**Priority**: 🟡 MEDIUM  
**Action**: Monitor for 24 hours  
**Estimated Time**: Ongoing

**Action**:
```bash
# Watch backend logs
docker compose logs -f backend

# Watch proxy logs
docker compose logs -f proxy

# Check for errors
docker compose logs backend | grep -i error
docker compose logs proxy | grep -i error
```

**Acceptance Criteria**:
- [ ] No critical errors in logs
- [ ] No CSRF errors
- [ ] No CORS errors
- [ ] No database connection errors

---

## Phase 4: Nice-to-Have Enhancements

### Task 4.1: Fix Failing Backend Tests

**Priority**: 🟢 LOW  
**File**: Various test files  
**Estimated Time**: 2-4 hours

**Action**:
- Review failing tests
- Fix test issues
- Ensure all tests pass

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Test coverage maintained or improved

---

### Task 4.2: Optimize PDF Generation

**Priority**: 🟢 LOW  
**File**: `apps/reports/utils.py`  
**Estimated Time**: 1-2 hours

**Action**:
- Review PDF generation performance
- Optimize for large reports
- Add error handling

**Acceptance Criteria**:
- [ ] PDF generation is fast (< 3 seconds)
- [ ] Large reports don't cause memory issues
- [ ] Error handling is robust

---

### Task 4.3: Add Monitoring & Alerts

**Priority**: 🟢 LOW  
**Action**: Set up monitoring  
**Estimated Time**: 2-4 hours

**Action**:
- Set up health check monitoring
- Configure alerts for critical errors
- Set up log aggregation

**Acceptance Criteria**:
- [ ] Health checks monitored
- [ ] Alerts configured
- [ ] Logs aggregated

---

## Summary

### Go-Live Blockers (Must Complete)
1. ✅ Add CSRF_TRUSTED_ORIGINS to production.py
2. ✅ Create .env.production with yourdomain.com
3. ✅ Investigate and fix container health issues
4. ✅ Run migrations
5. ✅ Collect static files

### Should Do (Recommended)
1. ✅ Run backend tests
2. ✅ Build frontend
3. ✅ Restart services
4. ✅ Run smoke tests

### Nice to Have (Post-Deployment)
1. Fix failing tests
2. Optimize PDF generation
3. Add monitoring

---

**Estimated Total Time for Go-Live**: 1-2 hours  
**Next Steps**: Start with Phase 1 tasks, then proceed to Phase 2
