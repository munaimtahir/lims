# LIMS Docker SSH Deployment Documentation Index

**Complete Deployment Guides for Production SSH-Based Deployment**

---

## 📚 Documentation Hub

All deployment-related documentation is now complete and organized. Use this index to navigate.

---

## 🎯 Start Here

### New to LIMS Deployment?
1. **First**: Read [DEPLOYMENT_SUMMARY.md](./DEPLOYMENT_SUMMARY.md) - 5 minute overview
2. **Then**: Follow [SSH_DEPLOYMENT.md](./SSH_DEPLOYMENT.md) - Complete step-by-step guide
3. **Bookmark**: [DEPLOYMENT_REFERENCE.md](./DEPLOYMENT_REFERENCE.md) - Quick reference for daily use
4. **Troubleshoot**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - When issues arise

---

## 📖 Documentation Guide

### 1. **DEPLOYMENT_SUMMARY.md** 
**📊 Overview & Executive Summary**
- 5-minute executive summary
- What has been completed
- File inventory
- Key features
- Quick start guide (4 phases)
- Security checklist
- Workflow diagram

**Who should read**: Everyone first
**Time to read**: 5-10 minutes
**Use case**: Understand the complete solution

---

### 2. **SSH_DEPLOYMENT.md**
**📋 Complete Deployment Guide**
- Server setup (prerequisites, installation)
- SSH configuration and key authentication
- Environment variables (critical for public IP/domain)
- Step-by-step deployment process
- HTTPS configuration with Let's Encrypt
- **Allowed Hosts & CORS configuration** (most important)
- Monitoring and health checks
- Rollback procedures
- Security best practices
- Quick reference commands

**Who should read**: DevOps, System Administrators
**Time to read**: 30-45 minutes
**Use case**: Complete reference during deployment

---

### 3. **DEPLOYMENT_REFERENCE.md**
**🔍 Quick Reference Card**
- One-minute startup guide
- Essential commands
- Critical configuration format
- Common issues quick-fix table
- Monitoring commands
- Deployment workflow
- Cron job setup
- Emergency procedures
- Endpoint list

**Who should read**: DevOps, On-call support
**Time to read**: 2-3 minutes
**Use case**: Quick lookup during daily operations

---

### 4. **TROUBLESHOOTING.md**
**🔧 Troubleshooting & Problem Solving**
- Quick reference commands (db, backend, system)
- 10 common issues with solutions:
  - Bad Request (400) errors
  - CORS errors
  - Connection refused
  - Database connection failed
  - High memory usage
  - HTTPS certificate issues
  - Static files not loading
  - Migrations not applied
  - Celery not processing
  - Frontend display issues
- Log analysis techniques
- Performance troubleshooting
- Security issue handling
- Data recovery procedures
- Debug mode instructions
- Escalation path

**Who should read**: Support, DevOps
**Time to read**: Variable (search as needed)
**Use case**: Problem diagnosis and resolution

---

## 🔧 Configuration Files

### **.env.production.example**
**Template for environment configuration**
- All required variables documented
- 50+ configuration options
- Comments explaining each variable
- Example values provided
- Security notes for sensitive values

**Use**: Copy to `.env.production` and customize

---

### **docker-compose.yml** (Enhanced)
**Production-grade Docker orchestration**
- All 6 services: db, redis, backend, celery, frontend, proxy
- Health checks for all services
- Volume mounts for logs and backups
- Logging configuration
- Resource limits
- Network configuration

**Changes from original**:
- Added container names
- Added restart policies
- Added logging drivers
- Added health checks
- Added explicit volume mounts
- Added environment documentation

---

### **Caddyfile** (Enhanced)
**HTTPS reverse proxy configuration**
- Automatic HTTPS/SSL support
- HTTP to HTTPS redirect
- Security headers (HSTS, X-Frame-Options, etc.)
- SPA routing (index.html fallback)
- Static and media file serving
- Compression (gzip)

**Features**:
- Automatic Let's Encrypt certificates
- Production-ready security headers
- Support for multiple domains
- Admin endpoint disabled for security

---

### **config/settings/production.py** (Enhanced)
**Django production configuration**
- Comprehensive security settings
- HTTPS/SSL configuration
- CORS and ALLOWED_HOSTS setup
- Database and Redis configuration
- Celery configuration
- Email configuration
- Advanced logging (file, console, security logs)
- HSTS headers
- Whitenoise static file handling

**Key improvements**:
- Added detailed comments explaining each setting
- Added configuration validation
- Added comprehensive logging setup
- Added security headers
- Added performance optimizations

---

## 🚀 Automation Scripts

### **deploy.sh**
**One-command deployment automation**
- Validates prerequisites (Docker, Docker Compose, Git)
- Validates environment variables
- Checks disk space
- Updates repository
- Backs up database
- Builds Docker images
- Starts services
- Runs migrations
- Performs health checks
- Reports status

**Usage**:
```bash
./deploy.sh                    # Full deployment
./deploy.sh --migrate-only     # Migrations only
./deploy.sh --health-check     # Health check only
./deploy.sh --restart          # Restart services
```

---

### **health-check.sh**
**Comprehensive health monitoring**
- Service status checks
- API health verification
- Database connectivity
- Redis connectivity
- Frontend accessibility
- Disk space monitoring
- Memory usage monitoring
- Docker resource usage
- Log analysis
- Backup verification
- Detailed and quick modes
- Live monitoring mode
- Email alert support

**Usage**:
```bash
./health-check.sh              # All checks
./health-check.sh --quick      # Fast status
./health-check.sh --detailed   # Full report
./health-check.sh --monitor    # Live monitoring
```

---

## 🗺️ Documentation Map

```
Documentation Structure:
├── For Understanding
│   ├── DEPLOYMENT_SUMMARY.md ......... What was done & overview
│   └── README.md ..................... Project features
│
├── For Deployment (Step-by-Step)
│   └── SSH_DEPLOYMENT.md ............ Complete guide (13 sections)
│       ├── Prerequisites
│       ├── Server Setup
│       ├── SSH Configuration
│       ├── Environment Variables
│       ├── Deployment Process
│       ├── HTTPS Configuration
│       ├── Allowed Hosts & CORS
│       ├── Monitoring
│       ├── Rollback
│       ├── Troubleshooting
│       └── Security Best Practices
│
├── For Quick Reference
│   └── DEPLOYMENT_REFERENCE.md ...... Quick lookup card
│       ├── Essential commands
│       ├── Critical config
│       ├── Common issues quick-fix
│       └── Emergency procedures
│
├── For Problem Solving
│   └── TROUBLESHOOTING.md ........... Issues & solutions
│       ├── Common issues (10 solutions)
│       ├── Log analysis
│       ├── Performance tuning
│       ├── Security issues
│       ├── Data recovery
│       └── Debug procedures
│
└── For Configuration
    ├── .env.production.example ....... Environment template
    ├── docker-compose.yml ........... Service definitions
    ├── Caddyfile .................... Reverse proxy
    └── config/settings/production.py . Django settings
```

---

## 🎯 Quick Start (TL;DR)

```bash
# 1. Server setup (first time)
ssh ubuntu@server.ip
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo apt install -y docker-compose-plugin git

# 2. Clone and configure
mkdir -p /opt/lims && cd /opt/lims
git clone https://github.com/your-org/lims.git .
cp .env.production.example .env.production
nano .env.production  # Set: ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, secrets

# 3. Deploy
chmod +x deploy.sh health-check.sh
./deploy.sh

# 4. Verify
./health-check.sh --detailed

# 5. Monitor (add to crontab)
crontab -e
# Add: */5 * * * * /opt/lims/health-check.sh >> /opt/lims/logs/health-check.log 2>&1
```

**Full details**: See SSH_DEPLOYMENT.md

---

## 🔐 Critical Configuration

### ALLOWED_HOSTS (For Public IP Support)
**This is crucial! Without this, you get "Bad Request (400)" errors**

Format: `domain.com,www.domain.com,xxx.xxx.xxx.xxx`

Must include:
- Your domain name (e.g., `example.com`)
- Any subdomains (e.g., `www.example.com`)
- Your server's public IP address
- Local IPs if needed (e.g., `192.168.1.100`)

Example:
```
example.com,www.example.com,203.0.113.45
```

**See**: SSH_DEPLOYMENT.md → "Allowed Hosts & CORS Configuration"

---

### CORS_ALLOWED_ORIGINS (For Frontend Integration)
**This is crucial! Without this, frontend cannot communicate with API**

Format: `https://domain.com,https://www.domain.com`

Must include:
- Frontend domain(s) with HTTPS protocol
- Include all variations users will access

Example:
```
https://example.com,https://www.example.com
```

**See**: SSH_DEPLOYMENT.md → "Allowed Hosts & CORS Configuration"

---

## 🔗 Integration Guide

### How Everything Works Together

1. **User** → Accesses `https://your-domain.com` in browser
2. **Caddy** → Automatically:
   - Obtains SSL certificate from Let's Encrypt
   - Serves frontend (React SPA)
   - Routes API calls to Django backend
   - Adds security headers
3. **Django** → Checks:
   - Request Host is in ALLOWED_HOSTS ✓
   - Request Origin is in CORS_ALLOWED_ORIGINS ✓
   - Processes API request
4. **Database** → Stores/retrieves data
5. **Response** → Sent back through Caddy to user

---

## 📊 File Changes Summary

### New Files Created
- ✅ SSH_DEPLOYMENT.md (comprehensive guide)
- ✅ TROUBLESHOOTING.md (problem solving)
- ✅ DEPLOYMENT_SUMMARY.md (overview)
- ✅ DEPLOYMENT_REFERENCE.md (quick reference)
- ✅ DEPLOYMENT_INDEX.md (this file)
- ✅ deploy.sh (automation script)
- ✅ health-check.sh (monitoring script)
- ✅ .env.production.example (config template)

### Files Enhanced
- ✅ docker-compose.yml (production optimizations)
- ✅ Caddyfile (HTTPS support)
- ✅ config/settings/production.py (comprehensive settings)

---

## ✅ Verification Checklist

After deployment, verify:

```bash
# 1. Services running
docker compose ps
# Expected: All services should show "Up"

# 2. Health check passes
./health-check.sh --detailed
# Expected: All checks should pass

# 3. API responds
curl https://your-domain.com/api/v1/health/
# Expected: HTTP 200

# 4. Frontend loads
curl -I https://your-domain.com
# Expected: HTTP 200

# 5. HTTPS certificate valid
echo | openssl s_client -servername your-domain.com -connect your-server-ip:443
# Expected: Certificate valid dates shown

# 6. Database accessible
docker compose exec -T db pg_isready -U postgres
# Expected: "accepting connections"

# 7. CORS configured
curl -i https://your-domain.com/api/v1/auth/login/ \
  -H "Origin: https://your-domain.com" \
  -H "Access-Control-Request-Method: POST"
# Expected: Access-Control headers in response
```

---

## 🆘 Need Help?

### By Problem Type

| Issue | See | Time |
|-------|-----|------|
| Don't know where to start | DEPLOYMENT_SUMMARY.md | 5 min |
| Need complete guide | SSH_DEPLOYMENT.md | 30 min |
| Need quick commands | DEPLOYMENT_REFERENCE.md | 2 min |
| Debugging an issue | TROUBLESHOOTING.md | Variable |
| Understanding why | SSH_DEPLOYMENT.md + TROUBLESHOOTING.md | 15+ min |

---

## 📞 Support Resources

- **GitHub Issues**: https://github.com/munaimtahir/lims/issues
- **Docker Docs**: https://docs.docker.com/
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **Caddy Docs**: https://caddyserver.com/docs/

---

## 🎉 You're All Set!

The LIMS application is now fully configured for production SSH-based deployment. All documentation is complete and ready to use.

**Next Steps**:
1. Read DEPLOYMENT_SUMMARY.md (5 minutes)
2. Follow SSH_DEPLOYMENT.md (30 minutes)
3. Run `./deploy.sh` (15 minutes)
4. Verify with `./health-check.sh` (2 minutes)

---

**Version**: 1.0.0  
**Last Updated**: December 6, 2024  
**Status**: ✅ Production Ready  
**Next Steps**: Review SSH_DEPLOYMENT.md and deploy!
