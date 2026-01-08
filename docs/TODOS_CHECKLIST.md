# LIMS Deployment Checklist
## Go-Live Tasks for portal.alshifalab.pk

**Date Created:** 2026-01-08  
**Target Domain:** portal.alshifalab.pk  
**Status:** Ready for execution

---

## 🔴 Go-Live Blockers (Must Complete Before Deployment)

### Configuration Tasks

- [ ] **Task 1.1**: Add CSRF_TRUSTED_ORIGINS to `lims-backend/config/settings/production.py`
  - [ ] Add CSRF_TRUSTED_ORIGINS configuration section
  - [ ] Read from CSRF_TRUSTED_ORIGINS environment variable
  - [ ] Fall back to CORS_ALLOWED_ORIGINS if not set
  - [ ] Add logging for configuration
  - [ ] Verify no syntax errors

- [ ] **Task 1.2**: Create `.env.production` file in repository root
  - [ ] Generate secure SECRET_KEY (50+ characters)
  - [ ] Generate secure DB_PASSWORD (32+ characters)
  - [ ] Set SERVER_NAME=portal.alshifalab.pk
  - [ ] Set ALLOWED_HOSTS=portal.alshifalab.pk,<SERVER_IP>
  - [ ] Set CSRF_TRUSTED_ORIGINS=https://portal.alshifalab.pk
  - [ ] Set CORS_ALLOWED_ORIGINS=https://portal.alshifalab.pk
  - [ ] Set DEFAULT_FROM_EMAIL=noreply@portal.alshifalab.pk
  - [ ] Set CADDY_DOMAIN=portal.alshifalab.pk
  - [ ] Configure all other required variables
  - [ ] Add .env.production to .gitignore (if not already)

- [ ] **Task 1.3**: Verify docker-compose.yml environment variable references
  - [ ] Backend service uses .env.production
  - [ ] Celery service uses .env.production
  - [ ] Frontend service uses .env.production
  - [ ] Proxy service uses SERVER_NAME variable

### Deployment Tasks

- [ ] **Task 1.4**: Investigate container health issues
  - [ ] Check backend logs for errors
  - [ ] Test backend health endpoint: `/api/v1/health/`
  - [ ] Check proxy logs for errors
  - [ ] Test proxy health endpoint: `/health`
  - [ ] Fix any identified issues
  - [ ] Verify containers show as healthy

- [ ] **Task 1.5**: Run database migrations
  - [ ] Execute: `docker compose exec backend python manage.py migrate`
  - [ ] Verify migrations complete successfully
  - [ ] Check for any migration errors
  - [ ] Verify database schema is current

- [ ] **Task 1.6**: Collect static files
  - [ ] Execute: `docker compose exec backend python manage.py collectstatic --noinput`
  - [ ] Verify files collected to `/app/staticfiles`
  - [ ] Check for any collection errors

---

## 🟡 Should Do (Recommended Before Go-Live)

### Testing Tasks

- [ ] **Task 2.1**: Run backend tests (quick smoke test)
  - [ ] Execute: `docker compose exec backend pytest -x -v --tb=short`
  - [ ] Record test results (passing/failing counts)
  - [ ] Verify critical tests pass (auth, health, basic CRUD)
  - [ ] Document any critical test failures

- [ ] **Task 2.2**: Build frontend
  - [ ] Execute: `docker compose build frontend`
  - [ ] Verify build completes successfully
  - [ ] Check for build warnings/errors
  - [ ] Verify VITE_API_BASE_URL is set correctly in build

- [ ] **Task 2.3**: Restart all services
  - [ ] Execute: `docker compose restart`
  - [ ] Wait for services to start (30-60 seconds)
  - [ ] Verify all containers show as "Up" in `docker compose ps`
  - [ ] Verify health checks pass after restart

- [ ] **Task 2.4**: Run curl smoke tests
  - [ ] Test frontend: `curl -k https://portal.alshifalab.pk/ -I`
    - [ ] Returns 200 OK or 301/302 redirect
  - [ ] Test API health: `curl -k https://portal.alshifalab.pk/api/v1/health/`
    - [ ] Returns JSON with status
  - [ ] Test admin: `curl -k https://portal.alshifalab.pk/admin/ -I`
    - [ ] Redirects to login (not 400/500 error)
  - [ ] Verify all requests use HTTPS

---

## 🟢 Post-Deployment Verification

### Domain & Security Verification

- [ ] **Task 3.1**: Verify domain configuration
  - [ ] DNS resolves: `nslookup portal.alshifalab.pk`
  - [ ] HTTPS certificate valid: `openssl s_client -connect portal.alshifalab.pk:443`
  - [ ] No mixed content warnings in browser
  - [ ] Frontend loads without CORS errors
  - [ ] Browser shows valid SSL certificate

### Workflow Testing

- [ ] **Task 3.2**: Test critical workflows
  - [ ] **User Login**
    - [ ] Admin can log in via `/admin/`
    - [ ] JWT token received and stored
    - [ ] Token works for authenticated API calls
  - [ ] **Patient Registration**
    - [ ] Create new patient via API/Frontend
    - [ ] Search existing patient
    - [ ] Update patient information
  - [ ] **Order Creation**
    - [ ] Create new order
    - [ ] Add tests to order
    - [ ] Verify totals calculated correctly
    - [ ] Order ID auto-generated
  - [ ] **Payment Processing**
    - [ ] Record payment for order
    - [ ] Generate receipt PDF
    - [ ] Verify receipt downloads correctly
    - [ ] Verify receipt contains correct information
  - [ ] **Sample Collection**
    - [ ] Mark sample as collected
    - [ ] Update sample status
    - [ ] Verify sample tracking works
  - [ ] **Result Entry**
    - [ ] Enter test results
    - [ ] Verify auto-flagging works (H/L flags)
    - [ ] Submit results for verification
  - [ ] **Result Verification**
    - [ ] Pathologist can view verification queue
    - [ ] Verify/reject results
    - [ ] Digital signature works
  - [ ] **Report Generation**
    - [ ] Generate PDF report
    - [ ] Verify PDF downloads
    - [ ] Check PDF formatting (headers, tables, signatures)
    - [ ] Verify report contains all results

### Monitoring

- [ ] **Task 3.3**: Monitor logs for 24 hours
  - [ ] Watch backend logs: `docker compose logs -f backend`
  - [ ] Watch proxy logs: `docker compose logs -f proxy`
  - [ ] Check for errors: `docker compose logs backend | grep -i error`
  - [ ] Check for CSRF errors
  - [ ] Check for CORS errors
  - [ ] Check for database connection errors
  - [ ] Document any issues found

---

## 🟢 Nice to Have (Post-Go-Live Enhancements)

### Code Quality

- [ ] **Task 4.1**: Fix failing backend tests
  - [ ] Review failing test list (30 known failures)
  - [ ] Prioritize critical test failures
  - [ ] Fix test issues one by one
  - [ ] Verify all tests pass
  - [ ] Maintain or improve test coverage

### Performance Optimization

- [ ] **Task 4.2**: Optimize PDF generation
  - [ ] Review PDF generation performance
  - [ ] Test with large reports (many tests)
  - [ ] Optimize memory usage
  - [ ] Add error handling for edge cases
  - [ ] Verify PDF generation < 3 seconds for standard reports

### Monitoring & Operations

- [ ] **Task 4.3**: Add monitoring & alerts
  - [ ] Set up health check monitoring
  - [ ] Configure alerts for critical errors
  - [ ] Set up log aggregation
  - [ ] Create dashboard for system status
  - [ ] Set up backup monitoring

- [ ] **Task 4.4**: Document deployment procedures
  - [ ] Create deployment runbook
  - [ ] Document rollback procedures
  - [ ] Document troubleshooting steps
  - [ ] Create operator guide

---

## Quick Reference Commands

### Docker Commands
```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f proxy

# Restart services
docker compose restart

# Execute commands in containers
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend pytest -x -v --tb=short
```

### Testing Commands
```bash
# Test frontend
curl -k https://portal.alshifalab.pk/ -I

# Test API health
curl -k https://portal.alshifalab.pk/api/v1/health/

# Test admin
curl -k https://portal.alshifalab.pk/admin/ -I

# Test DNS
nslookup portal.alshifalab.pk

# Test SSL certificate
openssl s_client -connect portal.alshifalab.pk:443
```

### Environment Setup
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Generate DB_PASSWORD
openssl rand -base64 32

# Get server public IP
curl ifconfig.me
```

---

## Progress Tracking

**Started**: _______________  
**Completed**: _______________  
**Total Time**: _______________

**Go-Live Blockers**: 0/6 completed  
**Should Do**: 0/4 completed  
**Post-Deployment**: 0/3 completed  
**Nice to Have**: 0/4 completed

---

## Notes

- All tasks in "Go-Live Blockers" must be completed before deployment
- Tasks in "Should Do" are recommended but not strictly required
- Tasks in "Post-Deployment" should be completed within 24 hours of go-live
- Tasks in "Nice to Have" can be done as time permits

**Last Updated**: 2026-01-08
