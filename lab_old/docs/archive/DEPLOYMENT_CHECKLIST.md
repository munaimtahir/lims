# Production Deployment Checklist for VPS (172.237.71.40)

## ✅ Pre-Deployment Verification

Run the verification script before deployment:

```bash
./verify-deployment.sh
```

This script validates all production configurations and ensures:
- ✓ No localhost references in production configs
- ✓ No development port (5173) in production configs
- ✓ CORS/CSRF configured correctly for VPS IP
- ✓ Frontend configured to use nginx proxy
- ✓ Docker services properly configured
- ✓ All Dockerfiles are production-ready

## 📋 Deployment Steps Checklist

### Step 1: Pre-Deployment ☐

- [ ] Read [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) completely
- [ ] SSH access to VPS (172.237.71.40) is working
- [ ] Docker and Docker Compose are installed on VPS
- [ ] Ports 80 and 8000 are available on VPS
- [ ] Firewall is configured to allow HTTP traffic on port 80

### Step 2: Clone and Verify ☐

```bash
# On VPS
git clone https://github.com/munaimtahir/lab.git
cd lab
chmod +x verify-deployment.sh
./verify-deployment.sh
```

- [ ] Repository cloned successfully
- [ ] Verification script shows all checks passed

### Step 3: Configure Security ☐

```bash
# Generate secure credentials
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
openssl rand -base64 32
```

Edit `.env` and update:

- [ ] DJANGO_SECRET_KEY updated with generated key
- [ ] POSTGRES_PASSWORD updated with generated password
- [ ] DEBUG=False (verify, should already be set)
- [ ] ALLOWED_HOSTS=172.237.71.40 (verify, should already be set)
- [ ] VITE_API_URL=/api (verify, should already be set)

### Step 4: Build and Deploy ☐

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps
```

- [ ] All images built successfully
- [ ] All services started successfully
- [ ] All services show "Up" status

### Step 5: Verify Deployment ☐

```bash
# Health check
curl http://172.237.71.40/api/health/

# Check logs
docker compose logs -f
```

- [ ] Health check returns healthy status
- [ ] No errors in logs
- [ ] Frontend accessible at http://172.237.71.40
- [ ] Can login with admin/admin123
- [ ] API endpoints working correctly

### Step 6: Post-Deployment Security ☐

```bash
# Change default admin password
docker compose exec backend python manage.py changepassword admin
```

- [ ] Default admin password changed
- [ ] Firewall rules configured (if applicable)
- [ ] Database backup strategy implemented
- [ ] Monitoring/logging configured (optional)

## 🔍 Verification Tests

### Frontend Tests

Open in browser:

- [ ] http://172.237.71.40 - Main page loads
- [ ] http://172.237.71.40/login - Login page loads
- [ ] Login with admin credentials works
- [ ] http://172.237.71.40/lab - Lab page accessible after login
- [ ] http://172.237.71.40/admin - Django admin accessible

### API Tests

```bash
# Health check
curl http://172.237.71.40/api/health/
# Expected: {"status":"healthy",...}

# Login
curl -X POST http://172.237.71.40/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Expected: {"access":"...","refresh":"..."}
```

- [ ] Health endpoint responds correctly
- [ ] Login endpoint works
- [ ] Can retrieve JWT tokens

### Service Tests

```bash
# Check all services
docker compose ps

# Check backend health
docker compose exec backend python manage.py check

# Check database connection
docker compose exec db psql -U lims -d lims -c "SELECT version();"

# Check redis connection
docker compose exec redis redis-cli ping
```

- [ ] All services running
- [ ] Backend Django check passes
- [ ] Database connection works
- [ ] Redis connection works

## 📊 Configuration Summary

### URLs

| Purpose | URL |
|---------|-----|
| Frontend | http://172.237.71.40 |
| Backend API | http://172.237.71.40/api |
| Backend Direct | http://172.237.71.40:8000 |
| Django Admin | http://172.237.71.40/admin |
| Health Check | http://172.237.71.40/api/health/ |

### Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| nginx | Multi-stage build | 80 | Frontend + API proxy |
| backend | Python 3.12 | 8000 | Django API |
| db | PostgreSQL 16 | Internal | Database |
| redis | Redis 7 | Internal | Cache |

### Configuration Files

| File | Status | Description |
|------|--------|-------------|
| `.env` | ✅ Production-ready | Main configuration |
| `backend/.env` | ✅ Production-ready | Backend-specific config |
| `frontend/.env` | ✅ Production-ready | Frontend-specific config |
| `docker-compose.yml` | ✅ Production-ready | Service orchestration |
| `nginx/nginx.conf` | ✅ Production-ready | Web server config |
| `nginx/Dockerfile` | ✅ Production-ready | Frontend build |
| `backend/Dockerfile` | ✅ Production-ready | Backend build |

## 🚨 Troubleshooting

If something goes wrong, refer to [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) Troubleshooting section.

Quick troubleshooting commands:

```bash
# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop and remove everything
docker compose down

# Rebuild and restart
docker compose build
docker compose up -d
```

## 📝 Notes

- **Default Credentials**: admin / admin123 (change immediately after first login)
- **Architecture**: Nginx serves frontend on port 80 and proxies API requests to backend
- **Production Mode**: DEBUG=False, no localhost references, no development ports
- **Security**: Remember to change default passwords and keep credentials secure
- **Backup**: Set up regular database backups using pg_dump
- **Updates**: Pull latest code, rebuild images, and restart services

## ✅ Deployment Complete

Once all checkboxes are marked, your LIMS application is successfully deployed and ready for production use!

For ongoing maintenance and updates, refer to [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).
