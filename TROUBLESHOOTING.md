# LIMS Docker SSH Deployment - Troubleshooting & Rollback Guide

**Date**: December 2024  
**Version**: 1.0.0  

---

## Table of Contents

1. [Quick Reference Commands](#quick-reference-commands)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Rollback Procedures](#rollback-procedures)
4. [Log Analysis](#log-analysis)
5. [Performance Troubleshooting](#performance-troubleshooting)
6. [Security Issues](#security-issues)
7. [Data Recovery](#data-recovery)
8. [Debug Mode](#debug-mode)

---

## Quick Reference Commands

### Service Management

```bash
# SSH into server
ssh ubuntu@your.server.ip

# Navigate to app directory
cd /opt/lims

# Check service status
docker compose ps

# View all logs
docker compose logs

# View specific service logs
docker compose logs -f backend
docker compose logs -f proxy
docker compose logs -f db

# Restart all services
docker compose restart

# Stop services
docker compose down

# Start services
docker compose up -d

# Rebuild services
docker compose build --no-cache
docker compose up -d
```

### Database Commands

```bash
# Access database shell
docker compose exec db psql -U postgres -d lims_db

# Backup database
docker compose exec -T db pg_dump -U postgres lims_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore database
gunzip < backup_file.sql.gz | docker compose exec -T db psql -U postgres lims_db

# Get database size
docker compose exec -T db psql -U postgres -c "SELECT pg_size_pretty(pg_database.datsize) FROM pg_database WHERE datname = 'lims_db';"

# Get table sizes
docker compose exec -T db psql -U postgres -d lims_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 20;"
```

### Backend Commands

```bash
# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser

# Collect static files
docker compose exec backend python manage.py collectstatic --noinput

# Run management commands
docker compose exec backend python manage.py <command>

# Access Django shell
docker compose exec backend python manage.py shell
```

### System Commands

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Monitor docker containers
docker stats

# Check network connectivity
docker compose exec backend curl -I http://db:5432

# List all volumes
docker volume ls

# Inspect volume details
docker volume inspect lims_postgres_data
```

---

## Common Issues & Solutions

### Issue 1: "Bad Request (400)" Error

**Symptom**: Accessing site returns "Bad Request. The domain you requested is not allowed."

**Cause**: ALLOWED_HOSTS misconfiguration

**Solution**:

```bash
# Check current ALLOWED_HOSTS
grep ALLOWED_HOSTS .env.production

# Edit and update ALLOWED_HOSTS
nano .env.production

# Must include:
# - Your domain (your-domain.com)
# - www subdomain (www.your-domain.com)
# - Public IP address (xxx.xxx.xxx.xxx)
# Format: "domain.com,www.domain.com,xxx.xxx.xxx.xxx"

# Restart backend service
docker compose restart backend

# Test with curl
curl -H "Host: your-domain.com" http://localhost/api/v1/health/
```

### Issue 2: CORS Errors in Browser Console

**Symptom**: `Access to XMLHttpRequest at 'http://localhost:8000/api/...' from origin 'http://localhost:3000' has been blocked by CORS policy`

**Cause**: CORS_ALLOWED_ORIGINS not properly configured

**Solution**:

```bash
# Check CORS configuration
grep CORS_ALLOWED_ORIGINS .env.production

# Edit if needed
nano .env.production

# Must match your frontend URL:
# CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Restart backend
docker compose restart backend

# Test CORS headers
curl -i -X OPTIONS http://localhost/api/v1/auth/login/ \
  -H "Origin: https://your-domain.com" \
  -H "Access-Control-Request-Method: POST"

# Should see:
# Access-Control-Allow-Origin: https://your-domain.com
# Access-Control-Allow-Credentials: true
```

### Issue 3: "Connection refused" on Port 80 or 443

**Symptom**: Cannot access application via HTTP/HTTPS

**Cause**: Caddy service not running or port conflict

**Solution**:

```bash
# Check if Caddy is running
docker compose ps proxy

# Check if ports are in use
netstat -tlnp | grep ":80\|:443"
# or
ss -tlnp | grep ":80\|:443"

# Kill conflicting process if needed
sudo lsof -i :80  # Find process using port 80
sudo kill -9 <PID>

# Restart Caddy
docker compose restart proxy

# Verify port availability
curl -v http://localhost/health
```

### Issue 4: Database Connection Failed

**Symptom**: `could not connect to server: Connection refused`

**Cause**: PostgreSQL not running or misconfigured

**Solution**:

```bash
# Check database service
docker compose ps db

# Check database logs
docker compose logs db

# Ensure environment variables are set
grep DB_ .env.production

# If database is corrupted, reinitialize:
# WARNING: This will delete data!
docker compose down
docker volume rm lims_postgres_data
docker compose up -d db

# Wait for database to initialize
sleep 10

# Run migrations
docker compose exec backend python manage.py migrate
```

### Issue 5: High Memory Usage

**Symptom**: Services becoming slow or unresponsive

**Cause**: Memory leak or unlimited resource usage

**Solution**:

```bash
# Check memory usage
docker stats --no-stream

# Check which container is using most memory
docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# Restart problematic service
docker compose restart backend

# Limit memory in docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 512m

# For database specifically:
# db:
#   ...
#   deploy:
#     resources:
#       limits:
#         memory: 1g

# Rebuild and restart
docker compose build
docker compose up -d
```

### Issue 6: HTTPS Certificate Not Issued

**Symptom**: Can access via HTTP but not HTTPS, or certificate errors

**Cause**: Domain not resolving to server, or Caddy misconfiguration

**Solution**:

```bash
# Verify domain resolves to server
nslookup your-domain.com
dig your-domain.com +short

# Expected: Should show your public IP

# Check Caddy logs for certificate errors
docker compose logs proxy | grep -i "certificate\|error\|acme"

# Verify Caddyfile syntax
docker compose exec proxy caddy validate --config /etc/caddy/Caddyfile

# Restart Caddy to retry certificate
docker compose restart proxy

# Monitor certificate issuance
docker compose logs -f proxy | grep -i certificate
```

### Issue 7: Static Files Not Loading (404 Errors)

**Symptom**: CSS/JS files return 404

**Cause**: Static files not collected

**Solution**:

```bash
# Collect static files
docker compose exec backend python manage.py collectstatic --noinput --clear

# Restart backend
docker compose restart backend

# Verify static files exist
docker compose exec backend ls -la staticfiles/

# Check whitenoise is configured
docker compose exec backend python manage.py check

# If issue persists, rebuild
docker compose build backend
docker compose up -d backend
```

### Issue 8: Migrations Not Applied

**Symptom**: Database schema missing or outdated

**Cause**: Migrations not run

**Solution**:

```bash
# Check migration status
docker compose exec backend python manage.py showmigrations

# Run pending migrations
docker compose exec backend python manage.py migrate

# If migrations are stuck, check database
docker compose exec -T db psql -U postgres -d lims_db -c "SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 5;"

# If needed, reset database (WARNING: DATA LOSS)
docker compose exec backend python manage.py migrate --plan
docker compose exec backend python manage.py migrate <app_name> zero  # Rollback specific app
docker compose exec backend python manage.py migrate  # Reapply
```

### Issue 9: Celery Tasks Not Processing

**Symptom**: Async tasks not running (e.g., PDFs not generating)

**Cause**: Celery worker not running

**Solution**:

```bash
# Check celery service
docker compose ps celery

# Check celery logs
docker compose logs celery

# Restart celery
docker compose restart celery

# Verify Redis connectivity
docker compose exec celery python -c "from celery import Celery; app = Celery(); app.conf.broker_url='redis://redis:6379/0'; print(app.broker_connection().connection)"

# Check pending tasks
docker compose exec -T redis redis-cli LLEN celery

# Monitor celery
docker compose exec celery celery -A config inspect active
docker compose exec celery celery -A config inspect stats
```

### Issue 10: Frontend Not Displaying Correctly

**Symptom**: Blank page or styling issues

**Cause**: Frontend build issues or API connectivity

**Solution**:

```bash
# Check frontend service
docker compose ps frontend

# Check frontend logs
docker compose logs frontend

# Verify API is accessible from frontend
docker compose exec frontend curl -v http://backend:8000/api/v1/health/

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend

# Check browser console for errors (open DevTools → Console)
# Common issues:
# - API base URL wrong
# - CORS issues
# - JavaScript bundle loading issues

# Verify environment variables
docker compose config | grep -A 20 'frontend:'
```

---

## Rollback Procedures

### Full Database Rollback

```bash
# List available backups
ls -lh /opt/lims/backups/

# Restore from backup (choose backup file)
BACKUP_FILE="/opt/lims/backups/lims_db_20240101_120000.sql.gz"

# Stop services (optional, can restore while running)
docker compose down

# Restore database
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U postgres lims_db

# Start services
docker compose up -d

# Verify restore
docker compose exec backend python manage.py migrate
```

### Rollback to Previous Git Commit

```bash
# View commit history
git log --oneline -20

# Revert to specific commit
git revert <commit-hash>
git push origin main

# Redeploy
./deploy.sh
```

### Rollback Services Only (Keep Data)

```bash
# Stop services
docker compose down

# Restore previous images (if available)
git checkout HEAD~1 docker-compose.yml
git checkout HEAD~1 Caddyfile

# Restart
docker compose up -d

# Check if issues persist
./health-check.sh
```

### Emergency Database Restore

```bash
# If database is corrupted and needs emergency restore:

# 1. Ensure backup exists
ls -lh /opt/lims/backups/ | sort -k 6,7 | tail -5

# 2. Stop all services
docker compose down

# 3. Remove corrupted volume
docker volume rm lims_postgres_data

# 4. Start database fresh
docker compose up -d db

# 5. Wait for initialization
sleep 30

# 6. Restore from backup
BACKUP_FILE="/opt/lims/backups/lims_db_20240101_120000.sql.gz"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U postgres lims_db

# 7. Start all services
docker compose up -d

# 8. Verify
./health-check.sh --detailed
```

---

## Log Analysis

### View Real-Time Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100

# Specific time window
docker compose logs --since "2024-01-01T00:00:00"

# Save to file
docker compose logs > /opt/lims/logs/docker-compose-$(date +%Y%m%d_%H%M%S).log
```

### Search Logs for Errors

```bash
# View error logs
docker compose logs backend | grep -i error

# Count errors
docker compose logs backend | grep -c "ERROR"

# View last error with context
docker compose logs backend | grep -i error -B 2 -A 2

# View Django exceptions
docker compose logs backend | grep "Exception\|Traceback" -A 10

# View database errors
docker compose logs db | grep -i "error\|fatal"
```

### Analyze Logs for Patterns

```bash
# Slow queries
docker compose logs backend | grep "slow query"

# Failed login attempts
docker compose logs backend | grep "login.*fail\|authentication.*denied"

# API errors
docker compose logs backend | grep "HTTP.*40\|HTTP.*50"

# Memory issues
docker compose logs | grep -i "memory\|out of\|exceeded"
```

---

## Performance Troubleshooting

### Database Query Optimization

```bash
# Enable query logging
# In settings/production.py, set:
# LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'

# Then restart
docker compose restart backend

# View slow queries
docker compose logs backend | grep "Query took"

# Check slow query log in PostgreSQL
docker compose exec -T db psql -U postgres -d lims_db << EOF
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 20;
EOF
```

### Optimize Redis

```bash
# Monitor Redis memory
docker compose exec -T redis redis-cli info memory

# Clear expired keys
docker compose exec -T redis redis-cli FLUSHDB ASYNC

# Check for large keys
docker compose exec -T redis redis-cli --bigkeys

# Analyze memory usage by type
docker compose exec -T redis redis-cli info stats
```

### Monitor API Performance

```bash
# Use curl with timing information
curl -w "Total time: %{time_total}s\n" http://localhost/api/v1/health/

# Monitor API response times
docker compose logs backend | grep "GET\|POST\|PUT\|DELETE" | awk '{print $NF}'

# Check for N+1 queries
# In Django settings, enable query logging and look for repeated patterns
```

---

## Security Issues

### Unauthorized Access Attempts

```bash
# View security logs
docker compose logs | grep -i "unauthorized\|forbidden"

# Check failed login attempts
docker compose logs backend | grep "login" | grep -i "fail"

# View requests from suspicious IPs
docker compose logs proxy | grep "Access denied\|400\|401\|403"

# Review all logs in security log file
cat /opt/lims/logs/security.log | tail -50
```

### SSL/TLS Certificate Issues

```bash
# View certificate expiration
echo | openssl s_client -servername your-domain.com -connect localhost:443 2>/dev/null | openssl x509 -noout -dates

# Check certificate validity
curl -vI https://your-domain.com 2>&1 | grep "certificate"

# Renew certificate (Caddy does this automatically)
docker compose restart proxy

# Force certificate renewal
docker compose exec proxy caddy renew --force
```

### Update Security

```bash
# Check for updates to Docker images
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull caddy:2-alpine

# Update Python packages
docker compose exec backend pip install --upgrade pip
docker compose exec backend pip install -r requirements.txt

# Apply security patches
docker compose build --no-cache
docker compose up -d
```

---

## Data Recovery

### Recover Deleted Records

```bash
# Check if record is in a backup
BACKUP_FILE="/opt/lims/backups/lims_db_20240101_120000.sql.gz"

# Create temporary database from backup
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U postgres -d lims_db_recovery

# Query for deleted record
docker compose exec -T db psql -U postgres -d lims_db_recovery -c "SELECT * FROM your_table WHERE id = <deleted_id>;"

# Restore if found
# Copy the record data and manually insert into current database
```

### Point-in-Time Recovery (PITR)

```bash
# PostgreSQL keeps WAL (Write-Ahead Logs) for recovery
# To recover to a specific point in time:

# 1. Stop services
docker compose down

# 2. Create recovery configuration
docker compose exec db mkdir -p /var/lib/postgresql/wal_archive

# 3. Restore with PITR
# This is advanced - refer to PostgreSQL documentation
# https://www.postgresql.org/docs/current/continuous-archiving.html
```

---

## Debug Mode

### Enable Django Debug Mode (NOT FOR PRODUCTION)

```bash
# Edit .env.production (ONLY FOR DEBUGGING)
DEBUG=True

# Restart
docker compose restart backend

# WARNING: This exposes sensitive information!
# Disable immediately after debugging
```

### Enable Verbose Logging

```bash
# Set LOG_LEVEL to DEBUG
LOG_LEVEL=DEBUG

# Restart
docker compose restart backend celery

# View debug logs
docker compose logs -f backend | grep "DEBUG"

# Disable after debugging
LOG_LEVEL=INFO
docker compose restart backend celery
```

### Debug with Python Shell

```bash
# Access Django shell
docker compose exec backend python manage.py shell

# Query database
from apps.patients.models import Patient
patient = Patient.objects.first()
print(patient)

# Test API
from rest_framework.test import APIClient
client = APIClient()
response = client.get('/api/v1/patients/')
print(response.status_code)
print(response.data)
```

### Debug with Database Queries

```bash
# See all SQL queries
docker compose exec -T db psql -U postgres -d lims_db << EOF
SET log_statement = 'all';
-- run your operations
-- then check:
SELECT query FROM pg_stat_statements LIMIT 20;
EOF
```

---

## Escalation Path

If issues persist after trying these solutions:

1. **Collect diagnostic information**:
   ```bash
   docker compose logs > /opt/lims/logs/diagnostic_$(date +%Y%m%d_%H%M%S).log
   docker stats > /opt/lims/logs/stats_$(date +%Y%m%d_%H%M%S).log
   df -h > /opt/lims/logs/disk_$(date +%Y%m%d_%H%M%S).log
   free -h > /opt/lims/logs/memory_$(date +%Y%m%d_%H%M%S).log
   ```

2. **Check system resources**:
   ```bash
   # Is server out of disk space, RAM, or CPU?
   df -h
   free -h
   top
   ```

3. **Review deployment guide**:
   - SSH_DEPLOYMENT.md - Complete setup and configuration guide
   - .env.production.example - Configuration template

4. **Contact support**:
   - GitHub Issues: https://github.com/munaimtahir/lims/issues
   - Include diagnostic logs
   - Include steps to reproduce
   - Include LIMS version

---

**Document End**

Last Updated: December 2024  
For SSH deployment support, refer to SSH_DEPLOYMENT.md
