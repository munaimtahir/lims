# Core LIMS v1.0 - Production Deployment Guide

**Version:** 1.0.0  
**Date:** January 2026  
**Status:** ✅ Production Validated

---

## Overview

This guide covers the validated deployment method for Core LIMS v1.0 using Docker Compose with Caddy reverse proxy. This configuration has been successfully deployed and smoke-tested with 92.3% pass rate (24/26 tests).

## Architecture

```
Internet (HTTPS/443 or Custom Port)
    ↓
Host Caddy (Optional: SSL Termination)
    ↓
Docker Container: lims_proxy (Caddy)
    ├── / → lims_frontend:80 (React SPA)
    ├── /api/* → lims_backend:8000 (Django REST API)
    ├── /admin/* → lims_backend:8000 (Django Admin)
    ├── /static/* → lims_backend:8000 (Static Files)
    └── /media/* → lims_backend:8000 (Media Files)
    ↓
Backend: lims_backend (Gunicorn on 0.0.0.0:8000 internal)
    ↓
    ├── Database: lims_db (PostgreSQL 16)
    ├── Cache/Broker: lims_redis (Redis 7)
    └── Background Tasks: lims_celery (Celery Worker)
```

**Key Security Feature:** Backend binds to `0.0.0.0:8000` inside the container but is NOT exposed to the host. Only the Caddy proxy is exposed (port 8012 on 127.0.0.1).

---

## Prerequisites

### Hardware Requirements
- **RAM:** Minimum 2GB, Recommended 4GB+
- **Storage:** Minimum 10GB free space
- **CPU:** 2 cores minimum

### Software Requirements
- **Docker:** Version 24+
- **Docker Compose:** Version 2.20+
- **OS:** Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)

### Network Requirements
- Port 8012 available (or configure custom port)
- (Optional) Port 443 for HTTPS if using host-level Caddy

---

## Installation Steps

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Log out and log back in for group changes to take effect

# Verify installation
docker --version
docker compose version
```

### 2. Clone Repository

```bash
git clone https://github.com/munaimtahir/lims.git
cd lims
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
nano .env
```

**Required Environment Variables:**

```env
# ===================================
# CRITICAL SECURITY SETTINGS
# ===================================

# Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY=<your-generated-secret-key>

# Generate with: openssl rand -base64 32
DB_PASSWORD=<your-generated-db-password>

# MUST include all domains and IPs that will access the system
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,your-server-ip

# MUST match your frontend URL(s)
CORS_ALLOWED_ORIGINS=http://localhost:8012,https://yourdomain.com

# MUST match your frontend URL(s)
CSRF_TRUSTED_ORIGINS=http://localhost:8012,https://yourdomain.com

# ===================================
# DATABASE CONFIGURATION
# ===================================
DB_NAME=lims_db
DB_USER=postgres
DB_HOST=db
DB_PORT=5432

# ===================================
# APPLICATION SETTINGS
# ===================================
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

For complete environment variable documentation, see [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md).

### 4. Build and Start Services

```bash
# Build all Docker images
docker compose build

# Start all services in detached mode
docker compose up -d

# Wait for services to initialize (15-20 seconds)
sleep 15

# Check service status (all should show "healthy" or "running")
docker compose ps
```

**Expected Output:**
```
NAME            SERVICE    STATUS       PORTS
lims_backend    backend    healthy      -
lims_celery     celery     running      -
lims_db         db         healthy      -
lims_frontend   frontend   running      -
lims_proxy      proxy      healthy      127.0.0.1:8012->80/tcp
lims_redis      redis      healthy      -
```

### 5. Initialize Database

```bash
# Run migrations (sets up database schema)
docker compose exec backend python manage.py migrate

# Seed test catalog (11 tests with parameters and reference ranges)
docker compose exec backend python manage.py seed_test_catalog --clear

# Create demo users for all roles (OPTIONAL - for testing only)
docker compose exec backend python manage.py create_demo_users
```

**Demo Users Created:**
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin (full access) |
| receptionist | recep123 | Receptionist |
| cashier | cash123 | Cashier |
| phlebotomist | phleb123 | Phlebotomist |
| labtech | labtech123 | Lab Technician |
| pathologist | patho123 | Pathologist |
| manager | manager123 | Manager |

**⚠️ PRODUCTION WARNING:** For production, do NOT use demo users. Create production users with strong passwords:

```bash
docker compose exec backend python manage.py createsuperuser
```

### 6. Verify Deployment

```bash
# Test health endpoint
curl http://localhost:8012/api/v1/health/

# Expected output:
# {"status":"healthy","service":"LIMS Backend","database":"connected"}

# View service logs
docker compose logs backend
docker compose logs celery
docker compose logs frontend
```

### 7. Access the Application

- **Application:** http://localhost:8012
- **Admin Panel:** http://localhost:8012/admin/
- **API Documentation:** http://localhost:8012/api/docs/
- **Health Check:** http://localhost:8012/api/v1/health/

---

## Configuration Options

### Custom Port Configuration

To change the exposed port from 8012 to another port:

1. Edit `docker-compose.yml`:
```yaml
proxy:
  ports:
    - "127.0.0.1:YOUR_PORT:80"  # Change 8012 to YOUR_PORT
```

2. Update `.env` to include new port in CORS/CSRF origins:
```env
CORS_ALLOWED_ORIGINS=http://localhost:YOUR_PORT
CSRF_TRUSTED_ORIGINS=http://localhost:YOUR_PORT
```

3. Restart services:
```bash
docker compose down
docker compose up -d
```

### HTTPS/SSL Configuration

For production with HTTPS, configure host-level Caddy (outside Docker):

1. Install Caddy on host:
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

2. Configure `/etc/caddy/Caddyfile`:
```caddyfile
yourdomain.com {
    reverse_proxy localhost:8012
    
    # Optional: custom headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
    }
    
    # Automatic HTTPS with Let's Encrypt
    tls your-email@example.com
}
```

3. Restart host Caddy:
```bash
sudo systemctl restart caddy
```

### Reverse Proxy Behind Another Service

If you're behind nginx or another reverse proxy, ensure these headers are forwarded:
- `X-Forwarded-For`
- `X-Forwarded-Proto`
- `X-Forwarded-Host`

Example nginx configuration:
```nginx
location / {
    proxy_pass http://localhost:8012;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header Host $host;
}
```

---

## Service Management

### Start/Stop Services

```bash
# Stop all services
docker compose down

# Start all services
docker compose up -d

# Restart specific service
docker compose restart backend

# Stop and remove ALL data (⚠️ WARNING: destroys database)
docker compose down -v
```

### View Logs

```bash
# All services (follow mode)
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery

# Last 100 lines
docker compose logs --tail=100 backend

# Since specific time
docker compose logs --since 2026-01-17T10:00:00
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart (preserves database)
docker compose build
docker compose up -d

# Run migrations (if any)
docker compose exec backend python manage.py migrate
```

---

## Maintenance Operations

### Database Backup

```bash
# Create backup
docker compose exec db pg_dump -U postgres lims_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Create compressed backup
docker compose exec db pg_dump -U postgres lims_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Database Restore

```bash
# Restore from backup
docker compose exec -T db psql -U postgres lims_db < backup_20260117_120000.sql

# Restore from compressed backup
gunzip < backup_20260117_120000.sql.gz | docker compose exec -T db psql -U postgres lims_db
```

### Clear Cache

```bash
# Clear Redis cache
docker compose exec redis redis-cli FLUSHDB

# Clear Django cache
docker compose exec backend python manage.py clear_cache
```

### Collect Static Files

```bash
# Collect static files (if modified)
docker compose exec backend python manage.py collectstatic --noinput
```

---

## Troubleshooting

### Services Not Starting

**Check service status:**
```bash
docker compose ps
```

**Check logs for errors:**
```bash
docker compose logs backend
docker compose logs db
```

**Common issues:**
- Port 8012 already in use → Change port in docker-compose.yml
- Database connection failed → Check DB_PASSWORD in .env matches docker-compose.yml
- Permission denied → Ensure user is in docker group: `sudo usermod -aG docker $USER`

### Backend Shows "Unhealthy"

The backend may show "unhealthy" in `docker ps` due to health check timing, but if the API responds, it's working:

```bash
# Test API directly
curl http://localhost:8012/api/v1/health/

# If returns {"status":"healthy",...}, system is operational
```

### Database Connection Errors

```bash
# Test database connectivity
docker compose exec db pg_isready -U postgres

# If fails, restart database
docker compose restart db

# Check database logs
docker compose logs db
```

### Frontend Not Loading

```bash
# Check frontend logs
docker compose logs frontend

# Check nginx status
docker compose exec frontend nginx -t

# Restart frontend
docker compose restart frontend
```

### Celery Tasks Not Processing

```bash
# Check Celery worker status
docker compose logs celery

# Restart Celery worker
docker compose restart celery

# Test Redis connection
docker compose exec redis redis-cli ping
# Expected output: PONG
```

### PDF Generation Issues

Currently, PDF download endpoints return 404 (known limitation in v1.0). PDF generation works but download endpoints need fixing in v1.1. Reports and receipts are generated in database records.

---

## Security Checklist

Before going to production, verify:

- [ ] `DEBUG=False` in .env
- [ ] `SECRET_KEY` is strong and unique (50+ characters)
- [ ] `DB_PASSWORD` is strong and unique (32+ characters)
- [ ] `ALLOWED_HOSTS` includes only your actual domains/IPs
- [ ] `CORS_ALLOWED_ORIGINS` includes only your frontend URLs
- [ ] Demo users are disabled or removed
- [ ] Production superuser created with strong password
- [ ] HTTPS/SSL configured (if public-facing)
- [ ] Firewall configured (only necessary ports open)
- [ ] Regular backups scheduled
- [ ] Monitoring and alerting configured

---

## Performance Tuning

### Database Optimization

```bash
# Analyze database
docker compose exec db psql -U postgres lims_db -c "ANALYZE;"

# Vacuum database
docker compose exec db psql -U postgres lims_db -c "VACUUM ANALYZE;"
```

### Gunicorn Workers

Edit `lims-backend/Dockerfile` to adjust workers:
```dockerfile
# Default: 4 workers
# Formula: (2 x CPU cores) + 1
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### Redis Memory Limit

Edit `docker-compose.yml`:
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

---

## Monitoring

### Health Checks

```bash
# API health endpoint
curl http://localhost:8012/api/v1/health/

# Check all service health
docker compose ps
```

### Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats lims_backend
```

### Disk Usage

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## Production Deployment Checklist

Use this checklist before going live:

1. **Environment Setup**
   - [ ] .env file created with production values
   - [ ] All required environment variables set
   - [ ] Secrets generated securely

2. **Services**
   - [ ] All services built successfully
   - [ ] All services showing healthy/running status
   - [ ] Health endpoint returns 200 OK

3. **Database**
   - [ ] Migrations completed successfully
   - [ ] Test catalog seeded
   - [ ] Production superuser created
   - [ ] Demo users removed/disabled

4. **Security**
   - [ ] DEBUG=False
   - [ ] Strong SECRET_KEY and DB_PASSWORD
   - [ ] ALLOWED_HOSTS configured correctly
   - [ ] CORS/CSRF origins configured correctly
   - [ ] Backend NOT publicly exposed (only proxy)

5. **Testing**
   - [ ] Smoke test executed (see docs/qa/SMOKE_TEST.md)
   - [ ] All critical workflows tested manually
   - [ ] User login verified for all roles

6. **Infrastructure**
   - [ ] HTTPS/SSL configured (if public)
   - [ ] Firewall rules configured
   - [ ] Backup strategy implemented
   - [ ] Monitoring configured

7. **Documentation**
   - [ ] Deployment notes recorded
   - [ ] Admin credentials documented securely
   - [ ] Support contact information configured

---

## See Also

- [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md) - Complete environment variable reference
- [DEPLOYMENT_SUCCESS.md](./DEPLOYMENT_SUCCESS.md) - Production deployment validation report
- [../qa/SMOKE_TEST.md](../qa/SMOKE_TEST.md) - Smoke testing procedures
- [../qa/SECURITY_VERIFICATION_REPORT.md](../qa/SECURITY_VERIFICATION_REPORT.md) - Security validation
- [../../FINAL_SMOKE_TEST_REPORT.md](../../FINAL_SMOKE_TEST_REPORT.md) - Complete test results

---

**Deployment Guide Version:** 1.0.0  
**Last Updated:** January 2026  
**Validated Configuration:** Docker Compose with Caddy reverse proxy
