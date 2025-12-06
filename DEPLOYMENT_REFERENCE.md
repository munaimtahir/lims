# LIMS Docker SSH Deployment - Quick Reference Card

**Print this page and keep at your desk during deployment!**

---

## 📋 Quick Links

| Document | Purpose | Link |
|----------|---------|------|
| **Deployment Guide** | Step-by-step SSH deployment | SSH_DEPLOYMENT.md |
| **Troubleshooting** | Common issues and solutions | TROUBLESHOOTING.md |
| **Summary** | Overview and checklist | DEPLOYMENT_SUMMARY.md |
| **Configuration** | Environment template | .env.production.example |

---

## 🚀 One-Minute Startup

```bash
# 1. SSH into server
ssh ubuntu@your.server.ip
cd /opt/lims

# 2. Configure (first time only)
cp .env.production.example .env.production
nano .env.production  # Edit ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, etc.

# 3. Deploy
chmod +x deploy.sh health-check.sh
./deploy.sh

# 4. Verify
./health-check.sh --detailed
```

---

## 🔧 Essential Commands

### Deployment
```bash
./deploy.sh                    # Full deployment
./deploy.sh --migrate-only     # Migrations only
./deploy.sh --health-check     # Health check only
./deploy.sh --restart          # Restart services
```

### Docker Operations
```bash
docker compose ps              # Service status
docker compose logs -f         # View logs
docker compose logs backend    # Backend logs only
docker compose restart         # Restart all
docker compose restart backend # Restart specific service
```

### Database
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec -T db pg_dump -U postgres lims_db | gzip > backup.sql.gz
```

### Health & Monitoring
```bash
./health-check.sh              # All checks
./health-check.sh --quick      # Quick status
./health-check.sh --detailed   # Detailed report
./health-check.sh --monitor    # Live monitoring
```

---

## ⚙️ Critical Configuration

### ALLOWED_HOSTS
**Format**: `domain.com,www.domain.com,xxx.xxx.xxx.xxx`  
**Examples**:
```
example.com,www.example.com,192.168.1.100
lab.healthcare.gov,lab-test.healthcare.gov,203.0.113.45
```
**If missing**: "Bad Request (400)" errors

### CORS_ALLOWED_ORIGINS
**Format**: `https://domain.com,https://www.domain.com`  
**Examples**:
```
https://example.com,https://www.example.com
https://lab.healthcare.gov
```
**If missing**: Frontend cannot access API

### SECRET_KEY
**How to generate**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```
**Location**: .env.production
**NEVER share!**

### DB_PASSWORD
**How to generate**:
```bash
openssl rand -base64 32
```
**Must be**: 32+ characters, strong
**Location**: .env.production

---

## 🆘 Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| Bad Request (400) | "Domain not allowed" | Check ALLOWED_HOSTS in .env.production |
| CORS Errors | Frontend can't reach API | Check CORS_ALLOWED_ORIGINS matches frontend URL |
| Certificate Errors | HTTPS not working | Check domain resolves to server IP |
| Connection Refused | Can't access app | Check firewall allows 80/443, verify Caddy running |
| Database Error | Services won't start | Check DB_PASSWORD, ensure db container healthy |
| Static Files 404 | CSS/JS not loading | Run `docker compose exec backend python manage.py collectstatic --noinput` |

**More solutions**: See TROUBLESHOOTING.md

---

## 📊 Monitoring Commands

### Service Status
```bash
docker compose ps
./health-check.sh --quick
```

### Resource Usage
```bash
docker stats
df -h
free -h
```

### Logs & Errors
```bash
docker compose logs backend | grep ERROR
docker compose logs proxy | grep certificate
docker compose logs db | grep -i error
```

### Database Health
```bash
docker compose exec -T db pg_isready -U postgres
docker compose exec -T db psql -U postgres -d lims_db -c "SELECT 1;"
```

### API Health
```bash
curl http://localhost/api/v1/health/
curl -H "Host: your-domain.com" http://localhost/api/v1/health/
```

---

## 🔄 Deployment Workflow

```
1. SERVER SETUP (First Time Only)
   └─ Install Docker, git
   └─ Create /opt/lims
   └─ Configure firewall

2. CLONE & CONFIGURE
   └─ git clone → /opt/lims
   └─ Create .env.production
   └─ Set: ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, secrets

3. DEPLOY
   └─ ./deploy.sh
   └─ Validates, builds, starts, migrates, checks health

4. VERIFY
   └─ ./health-check.sh --detailed
   └─ Access: https://your-domain.com

5. MONITOR
   └─ Add to cron: */5 * * * * ./health-check.sh
   └─ Review logs daily
   └─ Backup weekly
```

---

## 📈 Cron Job Setup

### Health Check Every 5 Minutes
```bash
crontab -e
# Add:
*/5 * * * * cd /opt/lims && ./health-check.sh >> logs/health-check.log 2>&1
```

### Backup Database Daily at 2 AM
```bash
0 2 * * * cd /opt/lims && ./deploy.sh --backup-db >> logs/backup.log 2>&1
```

### Check Disk Space Daily at 3 AM
```bash
0 3 * * * df -h >> /opt/lims/logs/disk-usage.log
```

---

## 🔒 Security Checklist

- [ ] SSH key authentication enabled
- [ ] Password authentication disabled
- [ ] Firewall configured (22, 80, 443 only)
- [ ] HTTPS enabled and automatic certificate working
- [ ] ALLOWED_HOSTS includes domain + public IP
- [ ] CORS restricted to frontend domain
- [ ] SECRET_KEY is strong and unique
- [ ] DB_PASSWORD is strong (32+ chars)
- [ ] DEBUG=False in production
- [ ] Regular backups scheduled
- [ ] Monitoring configured
- [ ] Email alerts enabled

---

## 📞 Emergency Contacts

**Quick Fixes**:
1. Check TROUBLESHOOTING.md
2. Review relevant logs
3. Run health check: `./health-check.sh --detailed`

**Escalation**:
1. Collect logs: `docker compose logs > diagnostic.log`
2. Check disk/memory: `df -h && free -h`
3. Open GitHub issue with logs

---

## 🎯 Key Endpoints

| Endpoint | URL | Purpose |
|----------|-----|---------|
| Frontend | https://your-domain.com | User interface |
| API | https://your-domain.com/api/v1/ | REST API |
| Admin | https://your-domain.com/admin | Django admin |
| Health | https://your-domain.com/health | Health check |
| Docs | https://your-domain.com/api/docs | API documentation |

---

## 📝 Environment Variables (Minimum Required)

```bash
# Secret & Security
SECRET_KEY=<generated>
DB_PASSWORD=<generated>

# Server Config
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,xxx.xxx.xxx.xxx
SERVER_NAME=your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Database
DB_NAME=lims_db
DB_USER=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# SSL/HTTPS
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

See .env.production.example for all options.

---

## 🚨 Emergency Procedures

### Service Not Starting
```bash
# Check logs
docker compose logs

# Validate environment
docker compose config

# Restart with clean state
docker compose down
docker compose up -d

# If database issues:
docker compose logs db
docker compose restart db
```

### Disk Full
```bash
# Check usage
df -h

# Clean Docker
docker system prune -a

# Clean old logs
find logs/ -mtime +30 -delete

# Clean old backups
find backups/ -mtime +30 -delete
```

### Database Corruption
```bash
# Restore from backup
gunzip < backups/lims_db_TIMESTAMP.sql.gz | \
  docker compose exec -T db psql -U postgres lims_db

# Or start fresh (DATA LOSS!)
docker volume rm lims_postgres_data
docker compose up -d db
docker compose exec backend python manage.py migrate
```

### Cannot Access HTTPS
```bash
# Check certificate
echo | openssl s_client -servername your-domain.com -connect localhost:443

# Check domain resolves
nslookup your-domain.com

# Check Caddy
docker compose logs proxy

# Force certificate renewal
docker compose exec proxy caddy renew --force
```

---

## 📚 Documentation Files

```
/opt/lims/
├── SSH_DEPLOYMENT.md          ← Start here! Complete guide
├── TROUBLESHOOTING.md          ← Common issues & solutions
├── DEPLOYMENT_SUMMARY.md       ← Overview & architecture
├── DEPLOYMENT_REFERENCE.md     ← This file!
├── .env.production.example     ← Configuration template
├── docker-compose.yml          ← Services configuration
├── Caddyfile                   ← Reverse proxy config
├── deploy.sh                   ← Deployment automation
├── health-check.sh             ← Monitoring script
├── logs/                       ← Application logs
│   ├── django.log
│   ├── security.log
│   ├── health-check.log
│   └── ...
└── backups/                    ← Database backups
    ├── lims_db_20240601_020000.sql.gz
    ├── lims_db_20240602_020000.sql.gz
    └── ...
```

---

**Last Updated**: December 6, 2024  
**Version**: 1.0.0  
**Status**: Production Ready  

Keep this handy during deployment and monitoring!
