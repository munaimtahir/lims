# Production Deployment Guide for VPS (172.237.71.40)

## Overview

This document provides comprehensive instructions for deploying the Al Shifa LIMS application to the VPS with IP address **172.237.71.40**.

## ✅ Pre-Deployment Checklist

All configuration files have been optimized for production deployment:

- [x] All localhost references removed from production configs
- [x] Port 5173 (Vite dev server) removed from production configs
- [x] CORS/CSRF configured for VPS IP only
- [x] Frontend configured to use nginx proxy (`/api`)
- [x] Backend configured for production (DEBUG=False)
- [x] Nginx configured to serve on port 80
- [x] Docker Compose configured correctly
- [x] Multi-stage Docker builds implemented

## 🚀 Deployment Architecture

### Services

| Service | Image | Port (External) | Port (Internal) | Purpose |
|---------|-------|----------------|----------------|---------|
| nginx | Multi-stage (Node + Nginx) | 80 | 80 | Frontend serving + API reverse proxy |
| backend | Python 3.12-slim | 8000 | 8000 | Django API with Gunicorn |
| db | postgres:16 | - | 5432 | PostgreSQL database |
| redis | redis:7-alpine | - | 6379 | Cache and task queue |

### Network Flow

```
User Browser
    ↓
http://172.237.71.40:80 (nginx)
    ├─→ Frontend static files (/, /login, /lab, etc.)
    └─→ /api/* → http://backend:8000 (Django API)
            ├─→ postgres:5432 (database)
            └─→ redis:6379 (cache)
```

## 📋 Deployment Steps

### 1. Clone Repository on VPS

```bash
ssh user@172.237.71.40
cd /opt  # or your preferred directory
git clone https://github.com/munaimtahir/lab.git
cd lab
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with secure production values:

```bash
cp .env.example .env
```

**⚠️ CRITICAL SECURITY STEP: Generate secure credentials before deployment!**

```bash
# Generate secure Django secret key
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Generate secure database password
openssl rand -base64 32
```

Edit `.env` and update these critical values:
```bash
DJANGO_SECRET_KEY=<generated-secret-key>
POSTGRES_PASSWORD=<generated-password>
DEBUG=False  # MUST be False in production
ALLOWED_HOSTS=172.237.71.40,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://172.237.71.40,http://172.237.71.40:80
CSRF_TRUSTED_ORIGINS=http://172.237.71.40,http://172.237.71.40:80
```

### 3. Build and Deploy

```bash
# Build all services
docker compose build

# Start services
docker compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30

# Verify services are running
docker compose ps

# Check logs
docker compose logs -f
```

### 4. Initialize Database and Create Admin User

**⚠️ IMPORTANT: Do NOT use default credentials in production!**

```bash
# Optional: Seed master data (tests, parameters, reference ranges)
# from the Excel file if needed
docker compose exec backend python manage.py import_lims_master --dry-run
docker compose exec backend python manage.py import_lims_master

# Create a secure admin user (REQUIRED)
docker compose exec backend python manage.py createsuperuser

# Follow prompts to create admin with secure password
# Username: admin (or your choice)
# Email: your-email@example.com
# Password: <use a strong password, NOT admin123>
```

**Note**: The application includes a `seed_data` command that creates demo users with default passwords (admin/admin123, etc.). These are for development ONLY and should NEVER be used in production. The production Dockerfile does not run this command automatically.

### 5. Verify Deployment

#### Automated Smoke Tests (Recommended)

```bash
# Run comprehensive smoke tests
./scripts/smoke_test.sh

# Expected output:
# ✅ All smoke tests PASSED
# Deployment is healthy and ready for use!
```

#### Manual Verification

```bash
# Health check
curl http://172.237.71.40/api/health/

# Expected response:
# {"status":"healthy","timestamp":"...","database":"ok","redis":"ok"}

# Test frontend
curl -I http://172.237.71.40
# Expected: HTTP/1.1 200 OK

# Access frontend
# Open browser: http://172.237.71.40

# Login with your secure admin credentials (created in step 4)
```

## 🔒 Security Configuration

### Current Production Settings

All configuration files are set for production:

1. **`.env`**:
   - `VITE_API_URL=/api` (uses nginx proxy)
   - `ALLOWED_HOSTS=172.237.71.40` (VPS IP only)
   - `CORS_ALLOWED_ORIGINS=http://172.237.71.40,http://172.237.71.40:80`
   - `CSRF_TRUSTED_ORIGINS=http://172.237.71.40,http://172.237.71.40:80`
   - `DEBUG=False`

2. **`backend/.env`**:
   - Same security settings as root `.env`
   - No localhost references
   - No development ports

3. **`frontend/.env`**:
   - `VITE_API_URL=/api` (nginx proxy)
   - Production-ready configuration

4. **`docker-compose.yml`**:
   - Backend exposes port 8000 (for direct access if needed)
   - Nginx exposes port 80 (primary access point)
   - All environment variables default to production values

### Security Recommendations

1. **⚠️ NEVER Use Default Demo Credentials in Production**:
   - The `seed_data` command creates demo users (admin/admin123, reception/reception123, etc.)
   - These are for development and testing ONLY
   - Always create secure admin users using `createsuperuser` command
   - If you accidentally ran `seed_data` in production:
     ```bash
     # Change password for admin user immediately
     docker compose exec backend python manage.py changepassword admin
     
     # Or delete demo users and create secure ones
     docker compose exec backend python manage.py shell
     >>> from users.models import User
     >>> User.objects.filter(username__in=['admin', 'reception', 'tech', 'pathologist']).delete()
     >>> exit()
     docker compose exec backend python manage.py createsuperuser
     ```

2. **Enable HTTPS** (Recommended for production):
   - Obtain SSL certificate (Let's Encrypt)
   - Update nginx configuration for SSL
   - Update CORS/CSRF origins to use https://

3. **Firewall Configuration**:
   ```bash
   # Allow HTTP
   sudo ufw allow 80/tcp
   
   # Allow HTTPS (when configured)
   sudo ufw allow 443/tcp
   
   # Optional: Allow backend direct access for debugging
   sudo ufw allow 8000/tcp
   ```

4. **Database Backups**:
   ```bash
   # Create backup
   docker compose exec db pg_dump -U lims lims > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # Restore backup
   docker compose exec -T db psql -U lims lims < backup_file.sql
   ```

## 🔧 Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nginx
docker compose logs -f backend
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose build
docker compose up -d
```

### Database Migrations

```bash
# Migrations are run automatically on container start
# To run manually:
docker compose exec backend python manage.py migrate
```

## 🧪 Testing Endpoints

### Backend API

```bash
# Health check
curl http://172.237.71.40/api/health/

# Login
curl -X POST http://172.237.71.40/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get patients (requires authentication)
curl http://172.237.71.40/api/patients/ \
  -H "Authorization: Bearer <access_token>"
```

### Frontend

- Main page: http://172.237.71.40/
- Login page: http://172.237.71.40/login
- Lab page: http://172.237.71.40/lab
- Admin panel: http://172.237.71.40/admin

## 📊 Monitoring

### Container Status

```bash
docker compose ps
```

### Resource Usage

```bash
docker stats
```

### Database Status

```bash
docker compose exec db psql -U lims -d lims -c "SELECT version();"
```

### Redis Status

```bash
docker compose exec redis redis-cli ping
# Should respond: PONG
```

## 🐛 Troubleshooting

### Issue: Frontend shows blank page

**Solution**: Check nginx logs
```bash
docker compose logs nginx
```

### Issue: API returns 502 Bad Gateway

**Solution**: Check if backend is running
```bash
docker compose ps backend
docker compose logs backend
```

### Issue: Database connection failed

**Solution**: Check database health
```bash
docker compose exec db pg_isready -U lims
```

### Issue: CORS errors

**Solution**: Verify CORS configuration matches your access URL
```bash
docker compose exec backend env | grep CORS
```

## 📚 Additional Resources

- [README.md](README.md) - General project information
- [SETUP.md](SETUP.md) - Local development setup
- [.env.example](.env.example) - Environment variable documentation

## 🎯 Quick Reference

### URLs

- **Frontend**: http://172.237.71.40
- **Backend API**: http://172.237.71.40/api
- **Backend Direct**: http://172.237.71.40:8000 (optional)
- **Admin Panel**: http://172.237.71.40/admin

### Admin Access

- Use the secure admin credentials you created during deployment (step 4)
- **⚠️ NEVER use default demo credentials (admin/admin123) in production**

### Key Files

- **Production config**: `.env`
- **Docker compose**: `docker-compose.yml`
- **Nginx config**: `nginx/nginx.conf`
- **Backend Dockerfile**: `backend/Dockerfile`
- **Nginx Dockerfile**: `nginx/Dockerfile`

---

**Note**: This configuration is optimized for production deployment on VPS with IP 172.237.71.40. No localhost or development port references exist in production configuration files.
