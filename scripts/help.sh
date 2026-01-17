#!/bin/bash
###############################################################################
# Quick Start Guide for LIMS Redeployment Scripts
# 
# This is a helper script to display usage information
###############################################################################

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════════════╗
║                LIMS Redeployment Scripts - Quick Guide                   ║
╚══════════════════════════════════════════════════════════════════════════╝

Three scripts are available for redeploying after bug fixes:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. FRONTEND ONLY (frontend.sh)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Use when: Fixed bugs in React/Frontend code
   Duration: ~2-3 minutes
   Command:  ./scripts/frontend.sh

   What it does:
   ✓ Stops frontend & proxy containers
   ✓ Rebuilds frontend (no cache)
   ✓ Restarts frontend services
   ✓ Verifies access & superuser

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. BACKEND ONLY (backend.sh)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Use when: Fixed bugs in Django/Python code
   Duration: ~3-4 minutes
   Command:  ./scripts/backend.sh

   What it does:
   ✓ Ensures DB & Redis are running
   ✓ Stops backend & Celery containers
   ✓ Rebuilds backend (no cache)
   ✓ Runs migrations & collectstatic
   ✓ Restarts backend services
   ✓ Verifies API access & superuser

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. FULL APPLICATION (both.sh)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Use when: Fixed bugs in both frontend & backend, or need clean restart
   Duration: ~5-7 minutes
   Command:  ./scripts/both.sh

   What it does:
   ✓ Stops ALL services
   ✓ Rebuilds ALL images (no cache)
   ✓ Starts services in proper order
   ✓ Runs migrations & collectstatic
   ✓ Comprehensive verification
   ✓ Tests full application access

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCESS INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

After deployment, access the application at:

   Frontend:     http://localhost:8013/
   API:          http://localhost:8013/api/v1/
   API Docs:     http://localhost:8013/api/docs/
   Admin Panel:  http://localhost:8013/admin/

Test Credentials (auto-created/reset):
   Username: admin
   Password: admin123

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOGS & TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Logs are saved in: /home/munaim/srv/apps/lims/logs/
   - frontend_redeploy_TIMESTAMP.log
   - backend_redeploy_TIMESTAMP.log
   - full_redeploy_TIMESTAMP.log

View live logs:        docker compose logs -f
View service logs:     docker compose logs -f <service-name>
Check status:          docker compose ps
Stop all:              docker compose down

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Always run from project root: cd /home/munaim/srv/apps/lims
✓ Use appropriate script for your changes to save time
✓ Check logs if services don't start properly
✓ Wait 30 seconds if services show as "starting"
✓ Both scripts rebuild with --no-cache for clean builds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For detailed documentation, see: scripts/README_REDEPLOYMENT.md

EOF
