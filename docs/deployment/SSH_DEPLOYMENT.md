# LIMS Docker-Based SSH Deployment Guide

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Status**: Production Ready  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Server Setup](#server-setup)
5. [SSH Configuration](#ssh-configuration)
6. [Environment Variables](#environment-variables)
7. [Deployment Process](#deployment-process)
8. [HTTPS Configuration](#https-configuration)
9. [Allowed Hosts & CORS Configuration](#allowed-hosts--cors-configuration)
10. [Monitoring & Health Checks](#monitoring--health-checks)
11. [Rollback Procedures](#rollback-procedures)
12. [Troubleshooting](#troubleshooting)
13. [Security Best Practices](#security-best-practices)

---

## Overview

This guide provides a comprehensive, documented approach for deploying the LIMS application to a remote server via SSH using Docker and Docker Compose. The deployment supports:

- ✅ **SSH-based remote access and management**
- ✅ **Public IP/Domain integration**
- ✅ **HTTPS with SSL/TLS termination (Caddy)**
- ✅ **Allowed hosts and CORS configuration**
- ✅ **Automated deployment scripts**
- ✅ **Health checks and monitoring**
- ✅ **Production-grade security**
- ✅ **Easy rollback procedures**

---

## Architecture

```
┌─────────────────┐
│  Local Machine  │
│                 │
│  SSH Client     │
└────────┬────────┘
         │ SSH (Port 22)
         │
┌────────▼──────────────────────────────────┐
│  Remote Server (Public IP: xxx.xxx.xxx.xxx)│
│                                             │
│  ┌──────────────────────────────────────┐ │
│  │  Docker Host with Containers         │ │
│  │                                      │ │
│  │  ┌────────────────────────────────┐ │ │
│  │  │  Caddy (Port 80/443)           │ │ │
│  │  │  - Reverse Proxy               │ │ │
│  │  │  - HTTPS Termination           │ │ │
│  │  │  - Static File Serving         │ │ │
│  │  └────────────────────────────────┘ │ │
│  │           ↓                          │ │
│  │  ┌────────────────────────────────┐ │ │
│  │  │  Frontend (React + Nginx)      │ │ │
│  │  │  - React SPA (Port 80)         │ │ │
│  │  └────────────────────────────────┘ │ │
│  │                                      │ │
│  │  ┌────────────────────────────────┐ │ │
│  │  │  Backend (Django + Gunicorn)   │ │ │
│  │  │  - REST API (Port 8000)        │ │ │
│  │  └────────────────────────────────┘ │ │
│  │                                      │ │
│  │  ┌────────────────────────────────┐ │ │
│  │  │  Celery Workers                │ │ │
│  │  │  - Async Tasks                 │ │ │
│  │  └────────────────────────────────┘ │ │
│  │                                      │ │
│  │  ┌────────────────────────────────┐ │ │
│  │  │  PostgreSQL                    │ │ │
│  │  │  - Primary Data Store          │ │ │
│  │  └────────────────────────────────┘ │ │
│  │                                      │ │
│  │  ┌────────────────────────────────┐ │ │
│  │  │  Redis                         │ │ │
│  │  │  - Cache & Message Broker      │ │ │
│  │  └────────────────────────────────┘ │ │
│  │                                      │ │
│  └──────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
         ↑
         │ HTTPS (Port 443)
         │
    ┌────┴─────┐
    │  Browser  │
    └───────────┘
```

---

## Prerequisites

### Local Machine Requirements
- SSH client (built-in on Linux/macOS, PuTTY or Windows Terminal on Windows)
- Git for cloning the repository
- Basic terminal/shell knowledge

### Remote Server Requirements
- Ubuntu 22.04 LTS or later (or similar Linux distribution)
- Minimum 2GB RAM (4GB recommended)
- Minimum 20GB disk space
- Public IP address or domain name
- Ports 22 (SSH), 80 (HTTP), 443 (HTTPS) accessible
- Root or sudo access

### Software to Install on Server
- Docker 20.10+
- Docker Compose 2.0+
- Git
- wget/curl

---

## Server Setup

### Step 1: Initial Server Preparation

SSH into your server:

```bash
ssh root@your.server.ip
# Or if using a different user:
ssh ubuntu@your.server.ip
```

Update system packages:

```bash
sudo apt update && sudo apt upgrade -y
```

Install required software:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Install Git
sudo apt install -y git

# Install essential utilities
sudo apt install -y curl wget nano htop

# Verify installations
docker --version
docker compose version
git --version
```

### Step 2: Create Application Directory Structure

```bash
# Create app directory
sudo mkdir -p /opt/lims
sudo chown $USER:$USER /opt/lims

# Create required subdirectories
mkdir -p /opt/lims/{backups,logs,data/postgres,data/redis}

# Set appropriate permissions
chmod 755 /opt/lims
chmod 755 /opt/lims/{backups,logs,data,data/postgres,data/redis}
```

### Step 3: Configure Firewall

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Verify rules
sudo ufw status
```

### Step 4: Configure SSH Key-Based Authentication (Optional but Recommended)

```bash
# On local machine, generate SSH key (if not already done)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub ubuntu@your.server.ip

# Test connection (should not ask for password)
ssh ubuntu@your.server.ip
```

---

## SSH Configuration

### SSH Config File (Optional - for convenience)

Create or edit `~/.ssh/config` on your **local machine**:

```plaintext
Host lims-prod
    HostName your.server.ip
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    Port 22
    StrictHostKeyChecking accept-new
    UserKnownHostsFile ~/.ssh/known_hosts
```

Now you can connect with:

```bash
ssh lims-prod
```

### Disable Password Authentication (Optional but Recommended)

On the server, edit `/etc/ssh/sshd_config`:

```bash
sudo nano /etc/ssh/sshd_config
```

Find and modify these lines:

```plaintext
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Restart SSH:

```bash
sudo systemctl restart ssh
```

---

## Environment Variables

### Step 1: Create `.env.production` File

SSH into the server and create the environment file:

```bash
ssh ubuntu@your.server.ip

# Navigate to application directory
cd /opt/lims

# Create .env.production file
cat > .env.production << 'EOF'
# ============================================
# LIMS Production Environment Configuration
# ============================================

# Application Settings
SECRET_KEY=your-production-secret-key-here-change-this
DEBUG=False

# Server Configuration - CRITICAL FOR PUBLIC IP/DOMAIN
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,xxx.xxx.xxx.xxx
PUBLIC_IP=xxx.xxx.xxx.xxx
SERVER_NAME=your-domain.com

# Database Configuration
DB_NAME=lims_db
DB_USER=postgres
DB_PASSWORD=your-secure-postgres-password-change-this
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# CORS Configuration - CRITICAL FOR FRONTEND
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
CORS_ALLOW_CREDENTIALS=True

# SSL/HTTPS Configuration
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_ACCEPT_CONTENT=json
CELERY_TASK_SERIALIZER=json

# Application Settings
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Logging
LOG_LEVEL=INFO

# Domain for Caddy
CADDY_DOMAIN=your-domain.com
EOF
```

### Step 2: Secure the Environment File

```bash
# Set restrictive permissions (readable only by owner)
chmod 600 .env.production

# Verify contents (optional)
cat .env.production
```

### Step 3: Generate Secure SECRET_KEY

```bash
# Generate a strong SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Copy the output and update .env.production
nano .env.production
```

---

## Deployment Process

### Step 1: Clone Repository

```bash
cd /opt/lims

# Clone the repository
git clone https://github.com/munaimtahir/lims.git .

# Verify structure
ls -la
```

### Step 2: Review docker-compose.yml

Before deploying, review the `docker-compose.yml` to ensure it's configured for production:

```bash
cat docker-compose.yml
```

Key sections to verify:
- Services list (db, redis, backend, frontend, proxy)
- Volume mounts
- Environment variable references
- Port mappings

### Step 3: Build and Start Services

```bash
# Load environment variables
export $(cat .env.production | xargs)

# Build Docker images
docker compose -f docker-compose.yml build

# Start services in background
docker compose -f docker-compose.yml up -d

# Verify all services are running
docker compose -f docker-compose.yml ps
```

Expected output:
```
NAME                COMMAND                  SERVICE      STATUS       PORTS
lims-backend-1      "gunicorn config.wsgi"   backend      Up 2 mins    8000/tcp
lims-celery-1       "celery -A config worker" celery      Up 2 mins
lims-db-1           "postgres"               db           Up 2 mins    5432/tcp
lims-frontend-1     "nginx -g daemon off;"   frontend     Up 2 mins    80/tcp
lims-proxy-1        "caddy run"              proxy        Up 2 mins    0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
lims-redis-1        "redis-server"           redis        Up 2 mins    6379/tcp
```

### Step 4: Run Database Migrations

```bash
# Apply migrations
docker compose exec backend python manage.py migrate

# Create superuser (interactive)
docker compose exec backend python manage.py createsuperuser

# Load sample data (optional)
docker compose exec backend python create_sample_data.py

# Collect static files
docker compose exec backend python manage.py collectstatic --noinput
```

### Step 5: Verify Deployment

```bash
# Check service logs
docker compose logs -f

# Test API endpoint
curl http://localhost/api/v1/health/

# Test from another machine (replace with your IP)
curl http://your.server.ip/api/v1/health/
```

---

## HTTPS Configuration

### Step 1: Update Caddyfile for HTTPS

On the server, create or update the `Caddyfile`:

```bash
cat > /opt/lims/Caddyfile << 'EOF'
{
    # Global options
    admin off
    log {
        level info
    }
}

# Redirect HTTP to HTTPS
:80 {
    redir https://{host}{uri} permanent
}

# HTTPS configuration
your-domain.com, www.your-domain.com {
    # Enable compression
    encode gzip

    # Frontend - React SPA
    @frontend {
        not path /api/* /admin/* /static/* /media/*
    }
    handle @frontend {
        reverse_proxy frontend:80 {
            header_up Host {upstream_hostport}
        }
        # SPA fallback
        error 404 /index.html
    }

    # Backend API
    handle /api/* {
        reverse_proxy backend:8000 {
            header_up Host {upstream_hostport}
            header_up X-Forwarded-Proto https
            header_up X-Forwarded-For {remote_host}
        }
    }

    # Django Admin
    handle /admin/* {
        reverse_proxy backend:8000 {
            header_up Host {upstream_hostport}
            header_up X-Forwarded-Proto https
            header_up X-Forwarded-For {remote_host}
        }
    }

    # Static files
    handle /static/* {
        reverse_proxy backend:8000 {
            header_up Host {upstream_hostport}
        }
    }

    # Media files
    handle /media/* {
        reverse_proxy backend:8000 {
            header_up Host {upstream_hostport}
        }
    }

    # Health check endpoint
    handle /health {
        respond "OK" 200
    }
}
EOF
```

### Step 2: Copy Caddyfile to Container Volume

```bash
# Mount the Caddyfile in docker-compose.yml
# Verify volume mount in docker-compose.yml:
# volumes:
#   - ./Caddyfile:/etc/caddy/Caddyfile
#   - caddy_data:/data
#   - caddy_config:/config

# Restart Caddy service
docker compose restart proxy
```

### Step 3: Verify HTTPS Certificate

```bash
# Check Caddy logs for certificate issuance
docker compose logs proxy | grep -i cert

# Test HTTPS connection
curl https://your-domain.com/health

# Check certificate validity
echo | openssl s_client -servername your-domain.com -connect your.server.ip:443 2>/dev/null | openssl x509 -noout -dates
```

---

## Allowed Hosts & CORS Configuration

### Understanding the Three Layers

The LIMS deployment has three critical layers for host/origin validation:

#### Layer 1: Django ALLOWED_HOSTS
Controls which Host headers Django accepts (security against Host header attacks)

#### Layer 2: CORS Settings  
Controls which origins can make cross-origin requests from browsers

#### Layer 3: Caddy Reverse Proxy
Controls which domain names resolve to the application

### Configuration Steps

#### 1. Update Django ALLOWED_HOSTS

In `.env.production`, ensure proper configuration:

```bash
# Format: comma-separated list, NO SPACES
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,192.168.1.100

# Verify in settings/production.py:
# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
```

#### 2. Update CORS Settings

In `.env.production`:

```bash
# Format: comma-separated URLs, include protocol
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# If frontend and backend on same domain:
CORS_ALLOWED_ORIGINS=https://your-domain.com

# For development/testing:
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost
```

#### 3. Configure Caddy Server Names

In `Caddyfile`:

```caddy
# Ensure domain matches ALLOWED_HOSTS
your-domain.com, www.your-domain.com {
    # ... rest of configuration
}
```

#### 4. Update Frontend API Base URL

In `frontend/src/api/client.ts`:

```typescript
// Production: Relative URL (same domain as frontend)
const API_BASE_URL = '/api/v1/';

// Or absolute URL if using separate domain
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://api.your-domain.com/api/v1/';
```

### Testing Configuration

```bash
# Test from your domain
curl -H "Host: your-domain.com" https://your-domain.com/api/v1/health/

# Test with IP address (should fail if not in ALLOWED_HOSTS)
curl https://xxx.xxx.xxx.xxx/api/v1/health/

# Test CORS headers
curl -i -X OPTIONS https://your-domain.com/api/v1/auth/login/ \
  -H "Origin: https://your-domain.com" \
  -H "Access-Control-Request-Method: POST"
```

Expected response should include:
```
Access-Control-Allow-Origin: https://your-domain.com
Access-Control-Allow-Credentials: true
```

---

## Monitoring & Health Checks

### Step 1: Create Health Check Script

```bash
cat > /opt/lims/health-check.sh << 'EOF'
#!/bin/bash

# LIMS Health Check Script
# Monitors all services and provides status report

set -e

DOMAIN="${1:-localhost}"
LOG_FILE="/opt/lims/logs/health-check.log"

# Create log directory if needed
mkdir -p /opt/lims/logs

# Function to log
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "========== LIMS Health Check =========="

# Check Docker services
log_message "Checking Docker services..."
docker compose ps

# Check Backend API
log_message "Checking Backend API..."
if curl -sf http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
    log_message "✓ Backend API: OK"
else
    log_message "✗ Backend API: FAILED"
fi

# Check Database
log_message "Checking Database..."
docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_message "✓ PostgreSQL: OK"
else
    log_message "✗ PostgreSQL: FAILED"
fi

# Check Redis
log_message "Checking Redis..."
docker compose exec -T redis redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    log_message "✓ Redis: OK"
else
    log_message "✗ Redis: FAILED"
fi

# Check Caddy HTTPS
log_message "Checking Caddy HTTPS..."
if curl -sf https://$DOMAIN/health > /dev/null 2>&1; then
    log_message "✓ Caddy (HTTPS): OK"
else
    log_message "✗ Caddy (HTTPS): FAILED (may not have valid cert yet)"
fi

# Check disk usage
log_message "Checking disk usage..."
DISK_USAGE=$(df /opt/lims | awk 'NR==2 {print $5}')
log_message "Disk usage: $DISK_USAGE"

# Check memory usage
log_message "Checking memory usage..."
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | tee -a "$LOG_FILE"

log_message "========== Health Check Complete =========="
EOF

chmod +x /opt/lims/health-check.sh
```

### Step 2: Set Up Automated Monitoring

Create a cron job for regular health checks:

```bash
# Edit crontab
crontab -e

# Add this line (runs every 5 minutes)
*/5 * * * * /opt/lims/health-check.sh your-domain.com > /dev/null 2>&1

# Or for daily reports (runs daily at 00:00)
0 0 * * * /opt/lims/health-check.sh your-domain.com | mail -s "LIMS Daily Health Check" admin@example.com
```

### Step 3: Monitor Container Logs

```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f proxy

# View last 100 lines
docker compose logs --tail=100

# Save logs to file
docker compose logs > /opt/lims/logs/docker-compose.log 2>&1
```

---

## Rollback Procedures

### Step 1: Backup Before Deployment

```bash
# Create dated backup
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T db pg_dump -U postgres lims_db > /opt/lims/backups/lims_db_$BACKUP_DATE.sql

# Compress backup
gzip /opt/lims/backups/lims_db_$BACKUP_DATE.sql

# Verify backup
ls -lh /opt/lims/backups/

# Backup database volume
docker run --rm -v lims_postgres_data:/data -v /opt/lims/backups:/backup alpine tar czf /backup/postgres_volume_$BACKUP_DATE.tar.gz -C /data .
```

### Step 2: Create Rollback Script

```bash
cat > /opt/lims/rollback.sh << 'EOF'
#!/bin/bash

# LIMS Rollback Script
# Restores application to previous state

set -e

BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -lh /opt/lims/backups/
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will restore your database to a previous state."
echo "Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no) " -n 3 -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Rollback cancelled"
    exit 1
fi

echo "Starting rollback..."

# Stop services
docker compose down

# Restore database
echo "Restoring database..."
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U postgres lims_db
else
    cat "$BACKUP_FILE" | docker compose exec -T db psql -U postgres lims_db
fi

# Start services
docker compose up -d

echo "Rollback complete!"
echo "Services restarting. Please wait..."
sleep 10
docker compose ps
EOF

chmod +x /opt/lims/rollback.sh
```

### Step 3: Quick Rollback Options

```bash
# Rollback to previous git commit
git revert HEAD
git push

# Rebuild and restart services
docker compose down
docker compose build --no-cache
docker compose up -d

# Or simply restart containers (if only config changed)
docker compose restart

# Restore from database backup
/opt/lims/rollback.sh /opt/lims/backups/lims_db_20240101_000000.sql.gz
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Connection refused" when accessing application

```bash
# Check if services are running
docker compose ps

# Start services if not running
docker compose up -d

# Check service logs
docker compose logs proxy backend
```

#### Issue: "ALLOWED_HOSTS" error

```bash
# Verify ALLOWED_HOSTS in environment
grep ALLOWED_HOSTS .env.production

# Update if needed
nano .env.production

# Restart backend service
docker compose restart backend

# Test with curl
curl -H "Host: your-domain.com" http://localhost/api/v1/health/
```

#### Issue: CORS errors in browser console

```bash
# Verify CORS configuration
grep CORS_ALLOWED_ORIGINS .env.production

# Check backend logs for CORS errors
docker compose logs backend | grep -i cors

# Verify Origin header in browser request
# (Check Network tab in browser DevTools)
```

#### Issue: HTTPS certificate not issued

```bash
# Check Caddy logs
docker compose logs proxy | grep -i "certificate\|error\|https"

# Ensure domain resolves to server IP
nslookup your-domain.com

# Verify DNS propagation
dig your-domain.com +short

# Restart Caddy
docker compose restart proxy
```

#### Issue: Database connection failed

```bash
# Check database service
docker compose ps db

# Check database logs
docker compose logs db

# Test database connection
docker compose exec -T db psql -U postgres -c "SELECT 1;"

# Reset database (CAUTION - data loss!)
docker volume rm lims_postgres_data
docker compose up -d db
docker compose exec backend python manage.py migrate
```

#### Issue: Out of disk space

```bash
# Check disk usage
df -h

# Find large files
du -sh /opt/lims/*

# Clean Docker images and containers
docker system prune -a --volumes

# Clean old logs
find /opt/lims/logs -mtime +30 -delete

# Check backups size
du -sh /opt/lims/backups/*
```

#### Issue: High memory usage

```bash
# Check container memory usage
docker stats

# Check specific service
docker compose stats --no-stream backend

# Reduce memory limits in docker-compose.yml
# Add deploy.resources.limits.memory: 512m

# Restart services
docker compose restart
```

---

## Security Best Practices

### 1. Secret Management

```bash
# Store secrets securely
chmod 600 .env.production
chmod 600 /opt/lims/backups/*.sql.gz

# Rotate SECRET_KEY periodically
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Never commit .env files
echo ".env*" >> .gitignore
```

### 2. Firewall Configuration

```bash
# Restrict SSH access by IP (if possible)
sudo ufw delete allow 22/tcp
sudo ufw allow from 203.0.113.0/24 to any port 22/tcp

# Or use fail2ban for brute-force protection
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 3. Database Security

```bash
# Use strong passwords (minimum 32 characters)
openssl rand -base64 32

# Backup database regularly
# (Already configured in health-check.sh)

# Restrict database access
# - db service only accessible within Docker network
# - Verify in docker-compose.yml
```

### 4. SSL/TLS Configuration

```bash
# Enable HSTS (HTTP Strict Transport Security)
# Add to Caddyfile:
header Strict-Transport-Security "max-age=31536000; includeSubDomains"

# Use secure cookies
SECURE_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
```

### 5. Regular Updates

```bash
# Update Docker images regularly
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull caddy:2-alpine

# Rebuild and restart services
docker compose build --pull
docker compose up -d
```

### 6. Monitoring and Logging

```bash
# Enable audit logging
# Already configured in production.py

# Monitor logs for suspicious activity
docker compose logs backend | grep -i "error\|warning\|unauthorized"

# Set up log rotation
cat > /etc/logrotate.d/lims << 'EOF'
/opt/lims/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 $USER $USER
}
EOF
```

---

## Quick Reference Commands

### Deployment Commands

```bash
# SSH into server
ssh ubuntu@your.server.ip

# Navigate to app directory
cd /opt/lims

# View status
docker compose ps

# View logs
docker compose logs -f

# Rebuild services
docker compose build --no-cache

# Start services
docker compose up -d

# Stop services
docker compose down

# Execute command in container
docker compose exec backend python manage.py createsuperuser

# View resource usage
docker stats

# Backup database
docker compose exec -T db pg_dump -U postgres lims_db | gzip > /opt/lims/backups/lims_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore database
docker compose exec -T db psql -U postgres lims_db < /opt/lims/backups/lims_db_TIMESTAMP.sql

# Run health check
/opt/lims/health-check.sh your-domain.com
```

### Debugging Commands

```bash
# Get inside a container
docker compose exec backend bash

# Check network connectivity
docker compose exec backend curl http://db:5432

# View container environment variables
docker compose config | grep -A 20 'backend:'

# Check Caddy configuration
docker compose exec proxy cat /etc/caddy/Caddyfile

# Verify DNS resolution inside container
docker compose exec backend nslookup db
```

---

## Maintenance Schedule

### Daily
- ✅ Monitor health check logs
- ✅ Check error logs for issues
- ✅ Verify HTTPS certificate is valid

### Weekly
- ✅ Backup database
- ✅ Review disk usage
- ✅ Check for Docker image updates

### Monthly
- ✅ Update Docker images
- ✅ Rotate logs
- ✅ Review security settings
- ✅ Test rollback procedure

### Quarterly
- ✅ Full security audit
- ✅ Disaster recovery drill
- ✅ Performance optimization review

---

## Support & Troubleshooting Links

- [Docker Documentation](https://docs.docker.com/)
- [Django Production Guide](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [LIMS GitHub Issues](https://github.com/munaimtahir/lims/issues)

---

**Document End**

For additional support, please refer to the main README.md or contact the development team.
