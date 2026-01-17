# LIMS Redeployment Scripts for Bug Fixing

This directory contains three deployment scripts designed for quick redeployment after bug fixes during the development/testing phase.

## Scripts Overview

### 1. `frontend.sh` - Frontend-Only Redeployment
**When to use:** When you've fixed bugs in the frontend code (React/TypeScript files)

**What it does:**
- ✓ Stops frontend and proxy containers if running
- ✓ Rebuilds frontend Docker image (no cache)
- ✓ Restarts frontend and proxy services
- ✓ Ensures backend/db/redis are running
- ✓ Verifies superuser admin/admin123 exists
- ✓ Tests public access to the application

**Usage:**
```bash
cd /home/munaim/srv/apps/lims
./scripts/frontend.sh
```

**Typical duration:** 2-3 minutes

---

### 2. `backend.sh` - Backend-Only Redeployment
**When to use:** When you've fixed bugs in the backend code (Python/Django files)

**What it does:**
- ✓ Ensures database and Redis are running
- ✓ Stops backend and Celery containers if running
- ✓ Rebuilds backend Docker images (no cache)
- ✓ Restarts backend and Celery services
- ✓ Runs database migrations
- ✓ Collects static files
- ✓ Ensures superuser admin/admin123 exists
- ✓ Starts proxy if needed for public access
- ✓ Tests API endpoints

**Usage:**
```bash
cd /home/munaim/srv/apps/lims
./scripts/backend.sh
```

**Typical duration:** 3-4 minutes

---

### 3. `both.sh` - Full Application Redeployment
**When to use:** When you've fixed bugs affecting both frontend and backend, or when you want a clean restart

**What it does:**
- ✓ Stops ALL LIMS services
- ✓ Rebuilds ALL Docker images (no cache)
- ✓ Starts services in proper order:
  1. Infrastructure (database, Redis)
  2. Backend (backend, Celery)
  3. Frontend (frontend, proxy)
- ✓ Runs database migrations
- ✓ Collects static files
- ✓ Ensures superuser admin/admin123 exists
- ✓ Comprehensive health checks on all services
- ✓ Tests full application access

**Usage:**
```bash
cd /home/munaim/srv/apps/lims
./scripts/both.sh
```

**Typical duration:** 5-7 minutes

---

## Access Information

After running any of these scripts, the application will be available at:

- **Frontend:** http://localhost:8013/
- **Backend API:** http://localhost:8013/api/v1/
- **API Documentation:** http://localhost:8013/api/docs/
- **Django Admin:** http://localhost:8013/admin/

### Test Credentials (Created/Reset by Scripts)
- **Username:** `admin`
- **Password:** `admin123`

---

## Logs

Each script creates a timestamped log file in the `/home/munaim/srv/apps/lims/logs/` directory:

- `frontend_redeploy_YYYYMMDD_HHMMSS.log` - Frontend deployment logs
- `backend_redeploy_YYYYMMDD_HHMMSS.log` - Backend deployment logs
- `full_redeploy_YYYYMMDD_HHMMSS.log` - Full deployment logs

The log files contain:
- All command outputs
- Error messages
- Verification results
- Service health checks

---

## Script Features

### Color-Coded Output
- 🔵 **BLUE** - Informational messages
- 🟢 **GREEN** - Success messages
- 🟡 **YELLOW** - Warnings
- 🔴 **RED** - Errors

### Automatic Checks
- Docker installation and running status
- Environment file existence (creates default if missing)
- Container status verification
- Service health checks
- Public access verification

### Safe Execution
- Error handling with line number reporting
- Comprehensive logging
- Non-destructive (preserves database data)
- Automatic cleanup of stopped containers

---

## Environment File

All scripts use `/home/munaim/srv/apps/lims/.env.production` for configuration.

If the file doesn't exist, the scripts will create a default one with these settings:
```bash
# Django Settings
SECRET_KEY=change-me-in-production
DB_NAME=lims_db
DB_USER=postgres
DB_PASSWORD=changeme
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=portal.alshifalab.pk,localhost,127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://portal.alshifalab.pk
CSRF_TRUSTED_ORIGINS=https://portal.alshifalab.pk

# Frontend
VITE_API_BASE_URL=/api/v1/
REACT_APP_API_BASE_URL=/api/v1/

# Server
SERVER_NAME=portal.alshifalab.pk

# Logging
LOG_LEVEL=INFO
```

**⚠️ Important:** Update the SECRET_KEY and DB_PASSWORD before production use!

---

## Troubleshooting

### Script Fails to Start
**Check:**
1. Docker is installed and running: `docker info`
2. You're in the correct directory: `pwd` should show `/home/munaim/srv/apps/lims`
3. Script is executable: `ls -l scripts/*.sh`

### Services Not Accessible After Deployment
**Try:**
1. Check container status: `docker compose ps`
2. Check logs: `docker compose logs <service-name>`
3. Verify port 8013 is not blocked: `netstat -tuln | grep 8013`
4. Wait 30 seconds for services to fully initialize

### Admin Login Not Working
**Solution:**
The scripts automatically reset the admin password to `admin123`. If it still doesn't work:
```bash
docker compose exec backend python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> admin = User.objects.get(username='admin')
>>> admin.set_password('admin123')
>>> admin.save()
>>> exit()
```

### Database Connection Errors
**Check:**
1. Database container is running: `docker ps | grep lims_db`
2. Database is healthy: `docker compose exec db pg_isready -U postgres`
3. Wait for database initialization (can take 30 seconds on first start)

---

## Quick Reference

### Stop All Services
```bash
docker compose down
```

### View All Logs
```bash
docker compose logs -f
```

### View Specific Service Logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f proxy
```

### Check Container Status
```bash
docker compose ps
```

### Access Backend Shell
```bash
docker compose exec backend python manage.py shell
```

### Run Django Management Commands
```bash
docker compose exec backend python manage.py <command>
```

---

## Best Practices

1. **Always run scripts from the project root directory**
   ```bash
   cd /home/munaim/srv/apps/lims
   ```

2. **Review logs after deployment**
   - Check the timestamped log file in `logs/` directory
   - Verify all services started successfully

3. **Test the application after deployment**
   - Access the frontend
   - Try logging in with admin/admin123
   - Test key functionality affected by your bug fix

4. **Use the appropriate script for your changes**
   - Frontend changes only? Use `frontend.sh`
   - Backend changes only? Use `backend.sh`
   - Both or unsure? Use `both.sh`

5. **Keep environment file secure**
   ```bash
   chmod 600 .env.production
   ```

---

## Script Architecture

### Frontend Script Flow
```
Check Prerequisites → Stop Frontend Services → Rebuild Frontend → 
Start Services → Ensure Superuser → Verify → Show Summary
```

### Backend Script Flow
```
Check Prerequisites → Start Infrastructure → Stop Backend Services → 
Rebuild Backend → Start Services → Run Migrations → Ensure Superuser → 
Verify → Show Summary
```

### Both Script Flow
```
Check Prerequisites → Stop ALL Services → Rebuild ALL Images → 
Start Infrastructure → Start Backend → Run Migrations → 
Start Frontend → Ensure Superuser → Verify ALL → Show Summary
```

---

## Support

For issues or questions:
1. Check the log files in `/home/munaim/srv/apps/lims/logs/`
2. Review container logs: `docker compose logs <service>`
3. Check container status: `docker compose ps`
4. Verify environment configuration in `.env.production`

---

**Last Updated:** January 2026  
**Version:** 1.0.0
