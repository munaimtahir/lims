# LIMS Port Conflict Resolution - Summary

## Date: January 18, 2026

## Issue
The LIMS Docker container `lims_proxy` was attempting to bind to ports 80 and 443, which conflicted with the host Caddy server that manages multiple applications (SIMS, PGSIMS, RIMS, Consult, PHC, Portal).

## Root Cause
- Host Caddy runs as a system service and binds to ports 80/443 to handle HTTPS/SSL termination for all applications
- LIMS was originally configured to bind directly to ports 80/443, creating a port conflict
- The host Caddyfile had `lims.alshifalab.pk` grouped with SIMS configuration (ports 8080/8010) but LIMS wasn't actually running on those ports

## Solution Implemented

### 1. Port Assignment
- **Assigned dedicated port**: LIMS now uses **port 8012** (localhost binding only: `127.0.0.1:8012`)
- **Host Caddy routing**: Updated `/etc/caddy/Caddyfile` to route traffic:
  - `lims.alshifalab.pk` → `127.0.0.1:8012`

### 2. Architecture Changes
**Before:**
```
Internet (80/443) → Host Caddy → CONFLICT ← LIMS Docker trying to bind 80/443
```

**After:**
```
Internet (80/443) → Host Caddy → 127.0.0.1:8012 → LIMS Docker (lims_proxy)
                                                    ↓
                                                  Backend/Frontend containers
```

### 3. Configuration Updates

#### docker-compose.yml
```yaml
proxy:
  ports:
    - "127.0.0.1:8012:80"  # Changed from "80:80" and "443:443"
```

#### /etc/caddy/Caddyfile
- **Removed** old LIMS domain from SIMS block (was pointing to ports 8080/8010)
- **Added** dedicated LIMS/Portal block:
```caddyfile
lims.alshifalab.pk {
    encode gzip zstd
    header { /* security headers */ }
    reverse_proxy 127.0.0.1:8012 { /* forwarding config */ }
}
```

#### Internal Caddyfile (/home/munaim/srv/apps/lims/Caddyfile)
- Updated header comments to reflect internal-only role
- Kept configuration as-is (routes between internal services)

#### scripts/both.sh
- Updated all test URLs from `:8012` to `:8012`
- Updated all access URLs in summary output

#### README.md
- Updated all port references from `:8012` to `:8012`
- Added link to PORT_CONFIGURATION.md documentation

### 4. Documentation Created
- **New file**: `docs/deployment/PORT_CONFIGURATION.md`
  - Complete port mapping table for all applications
  - Architecture diagrams
  - Troubleshooting guide
  - Port change instructions

## Verification Results

### Container Status
All containers running successfully:
```
lims_db         → healthy
lims_redis      → healthy
lims_backend    → running (health: starting)
lims_celery     → running
lims_frontend   → running
lims_proxy      → healthy (127.0.0.1:8012->80/tcp)
```

### Port Binding
```bash
$ sudo ss -tlnp | grep :8012
LISTEN 0 4096 127.0.0.1:8012 0.0.0.0:* users:(("docker-proxy",pid=1176886,fd=7))
```
✅ Port 8012 bound correctly to localhost only

### Endpoint Tests
```bash
✅ http://localhost:8012/health → OK
✅ http://localhost:8012/api/v1/health/ → {"status":"healthy",...}
✅ http://localhost:8012/ → Frontend HTML (200)
✅ http://localhost:8012/admin/ → Django admin (302 redirect)
```

### Host Caddy
```bash
$ sudo systemctl status caddy
● caddy.service - Caddy
   Active: active (running)
   
$ sudo caddy validate --config /etc/caddy/Caddyfile
Valid configuration
```
✅ Host Caddy running and configuration valid

## Port Allocation on Server

| Port | Application | Purpose |
|------|-------------|---------|
| 80   | Host Caddy | HTTP (redirects to HTTPS) |
| 443  | Host Caddy | HTTPS/SSL termination for all apps |
| 8010 | SIMS Backend | FMU-PLATFORM Backend API |
| 8011 | Consult | Referral System |
| **8012** | **LIMS/Portal** | **This Application** ✅ |
| 8014 | PGSIMS Backend | PGSIMS Backend API |
| 8015 | RIMS Backend | Radiology Backend API |
| 8016 | PHC | Accred-AI/PHC |
| 8080 | SIMS Frontend | FMU-PLATFORM Frontend |
| 8081 | RIMS Frontend | Radiology Frontend |
| 8082 | PGSIMS Frontend | PGSIMS Frontend |

**Available ports for future use**: 8017, 8018, 8019, 8020, etc.

## Files Modified

### Configuration Files
1. `/home/munaim/srv/apps/lims/docker-compose.yml`
   - Changed proxy port binding from `80:80, 443:443` to `127.0.0.1:8012:80`
   - Updated comments

2. `/home/munaim/srv/apps/lims/Caddyfile`
   - Updated header comments

3. `/etc/caddy/Caddyfile` (Host)
   - Removed old lims domain from SIMS block
   - Added dedicated LIMS/Portal configuration block

### Scripts
4. `/home/munaim/srv/apps/lims/scripts/both.sh`
   - Updated verification URLs (8012 → 8012)
   - Updated access URLs in summary

### Documentation
5. `/home/munaim/srv/apps/lims/README.md`
   - Updated all port references (8012 → 8012)
   - Added link to PORT_CONFIGURATION.md

6. `/home/munaim/srv/apps/lims/docs/deployment/PORT_CONFIGURATION.md` (NEW)
   - Comprehensive port documentation
   - Architecture diagrams
   - Troubleshooting guide

7. `/home/munaim/srv/apps/lims/docs/deployment/PORT_CONFLICT_RESOLUTION.md` (THIS FILE)
   - Summary of issue and resolution

### Backups Created
- `/etc/caddy/Caddyfile.backup.20260118_035913`

## Testing with Deployment Script

The `both.sh` deployment script should now work without port conflicts:

```bash
cd /home/munaim/srv/apps/lims
./scripts/both.sh
```

Expected results:
- ✅ All containers start successfully
- ✅ No port conflict errors
- ✅ Proxy accessible on port 8012
- ✅ All health checks pass
- ✅ Application accessible via `http://localhost:8012`

## Public Access

When DNS is properly configured, the application will be accessible via:
- **Frontend**: https://lims.alshifalab.pk:8012
- **API**: https://lims.alshifalab.pk:8012/api/v1/
- **API Docs**: https://lims.alshifalab.pk:8012/api/docs/
- **Admin**: https://lims.alshifalab.pk:8012/admin/

Host Caddy handles:
- HTTPS/SSL termination
- Certificate management (Let's Encrypt)
- Security headers
- Traffic routing to port 8012

## Security Notes

1. **No direct exposure**: Port 8012 is bound to `127.0.0.1` only
2. **SSL handled by host**: All SSL/TLS at host Caddy level
3. **Internal services isolated**: Backend, DB, Redis only accessible within Docker network
4. **Security headers**: Applied by host Caddy for all public traffic

## Conflict Resolution Checklist

- ✅ Identified port conflict (80/443 used by host Caddy)
- ✅ Assigned unique port (8012) for LIMS
- ✅ Updated docker-compose.yml
- ✅ Separated LIMS from SIMS in host Caddyfile
- ✅ Added dedicated LIMS configuration to host Caddyfile
- ✅ Validated host Caddyfile syntax
- ✅ Reloaded host Caddy
- ✅ Updated all deployment scripts
- ✅ Updated all documentation
- ✅ Created backup of host Caddyfile
- ✅ Tested all endpoints
- ✅ Verified no conflicts remain

## Conclusion

The port conflict has been successfully resolved. LIMS now uses port 8012 exclusively and coexists peacefully with all other applications on the server. The two-tier Caddy architecture ensures proper SSL termination and routing without conflicts.

## Next Steps

1. **Test full deployment**: Run `./scripts/both.sh` to verify complete rebuild cycle
2. **Monitor logs**: Check for any issues after deployment
3. **DNS configuration**: Ensure `lims.alshifalab.pk` points to the server IP
4. **SSL certificates**: Host Caddy will auto-provision Let's Encrypt certificates

## Contact

For questions or issues related to this configuration:
- Documentation: `/home/munaim/srv/apps/lims/docs/deployment/`
- Logs: `/home/munaim/srv/apps/lims/logs/`
- Container logs: `docker compose logs [service]`
