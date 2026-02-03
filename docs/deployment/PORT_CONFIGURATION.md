# LIMS Port Configuration

## Overview

The LIMS application uses a two-tier Caddy proxy architecture to avoid port conflicts with other applications on the server.

## Architecture

```
Internet (Port 443/80)
    ↓
Host Caddy (System Service)
    ├─ sims.alshifalab.pk → 127.0.0.1:8080 (FMU-PLATFORM/SIMS)
    ├─ api.sims.alshifalab.pk → 127.0.0.1:8010 (FMU-PLATFORM/SIMS Backend)
    ├─ lims.alshifalab.pk → 127.0.0.1:8012 (LIMS/Portal)  ← THIS APPLICATION
    ├─ pgsims.alshifalab.pk → 127.0.0.1:8082 (PGSIMS Frontend)
    ├─ rims.alshifalab.pk → 127.0.0.1:8081 (RIMS)
    ├─ consult.alshifalab.pk → 127.0.0.1:8011 (Consult)
    └─ phc.alshifalab.pk → 127.0.0.1:8016 (PHC)
    ↓
LIMS Docker Containers
    ├─ lims_proxy (Internal Caddy) → 127.0.0.1:8012
    ├─ lims_frontend → frontend:80
    ├─ lims_backend → backend:8000
    ├─ lims_db → db:5432
    └─ lims_redis → redis:6379
```

## Port Assignment

### Host Caddy (Port 80/443)
- **Service**: System Caddy (`/etc/caddy/Caddyfile`)
- **Purpose**: Handles HTTPS/SSL termination for all applications
- **Domain Routing**:
  - `lims.alshifalab.pk` → `127.0.0.1:8012`

### LIMS Internal Proxy (Port 8012)
- **Service**: Docker container `lims_proxy`
- **Binding**: `127.0.0.1:8012:80` (localhost only)
- **Purpose**: Routes traffic between LIMS internal services
- **Configuration**: `/home/munaim/srv/apps/lims/Caddyfile`

### LIMS Backend (Port 8000)
- **Service**: Docker container `lims_backend`
- **Binding**: Internal Docker network only
- **Purpose**: Django REST API

### LIMS Frontend (Port 80)
- **Service**: Docker container `lims_frontend`
- **Binding**: Internal Docker network only
- **Purpose**: React SPA

### PostgreSQL (Port 5432)
- **Service**: Docker container `lims_db`
- **Binding**: Internal Docker network only
- **Purpose**: Database

### Redis (Port 6379)
- **Service**: Docker container `lims_redis`
- **Binding**: Internal Docker network only
- **Purpose**: Cache & Celery broker

## Port Conflicts Resolution

### Issue
Initially, LIMS attempted to bind to ports 80 and 443 directly, conflicting with the host Caddy service that manages multiple applications.

### Solution
1. **Removed direct port binding**: LIMS no longer binds to ports 80/443
2. **Assigned dedicated port**: LIMS now uses port 8012 (localhost only)
3. **Host Caddy routing**: Updated `/etc/caddy/Caddyfile` to route `lims.alshifalab.pk` → `127.0.0.1:8012`
4. **Separated from SIMS**: Previously, the portal was grouped with SIMS configuration - now has dedicated configuration

## Occupied Ports on Server

| Port | Application | Service |
|------|-------------|---------|
| 80   | Host Caddy | All HTTPS traffic |
| 443  | Host Caddy | All HTTPS traffic |
| 8010 | SIMS Backend | FMU-PLATFORM Backend API |
| 8011 | Consult | Referral System |
| **8012** | **LIMS/Portal** | **This Application** |
| 8014 | PGSIMS Backend | PGSIMS Backend API |
| 8015 | RIMS Backend | Radiology Backend API |
| 8016 | PHC | Accred-AI/PHC |
| 8080 | SIMS Frontend | FMU-PLATFORM Frontend |
| 8081 | RIMS Frontend | Radiology Frontend |
| 8082 | PGSIMS Frontend | PGSIMS Frontend |

## Available Ports
If port 8012 needs to change in the future, these ports are available:
- 8017, 8018, 8019, 8020, 8021, 8022, etc.

## Configuration Files

### Docker Compose
**File**: `/home/munaim/srv/apps/lims/docker-compose.yml`

```yaml
proxy:
  image: caddy:2-alpine
  container_name: lims_proxy
  restart: unless-stopped
  ports:
    # Expose only to localhost on port 8012
    - "127.0.0.1:8012:80"
```

### Host Caddyfile
**File**: `/etc/caddy/Caddyfile`

```caddyfile
lims.alshifalab.pk {
    encode gzip zstd
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    # Proxy to LIMS Docker container
    reverse_proxy 127.0.0.1:8012 {
        header_up Host {host}
        header_up X-Real-IP {remote}
        header_up X-Forwarded-For {remote}
        header_up X-Forwarded-Proto {scheme}
        header_up X-Forwarded-Host {host}
    }
}
```

### Internal Caddyfile
**File**: `/home/munaim/srv/apps/lims/Caddyfile`

```caddyfile
:80 {
    # Routes requests to backend (port 8000) or frontend (port 80)
    # See file for full configuration
}
```

## Changing the Port

If you need to change LIMS to use a different port:

1. **Update Docker Compose**:
   ```bash
   # Edit docker-compose.yml
   # Change: - "127.0.0.1:8012:80"
   # To:     - "127.0.0.1:NEWPORT:80"
   ```

2. **Update Host Caddy**:
   ```bash
   sudo nano /etc/caddy/Caddyfile
   # Find lims.alshifalab.pk block
   # Change: reverse_proxy 127.0.0.1:8012
   # To:     reverse_proxy 127.0.0.1:NEWPORT
   
   # Validate and reload
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   ```

3. **Update Deployment Scripts**:
   ```bash
   # Update scripts/both.sh
   # Change all instances of :8012 to :NEWPORT
   ```

4. **Restart LIMS**:
   ```bash
   cd /home/munaim/srv/apps/lims
   docker compose down
   docker compose up -d
   ```

## Testing

### Local Access
```bash
# Test LIMS proxy health
curl http://localhost:8012/health

# Test frontend
curl http://localhost:8012/

# Test API
curl http://localhost:8012/api/v1/health/
```

### Public Access (requires DNS)
```bash
# Test via domain (HTTPS)
curl https://lims.alshifalab.pk/health
curl https://lims.alshifalab.pk/api/v1/health/
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
sudo ss -tlnp | grep :8012
sudo lsof -i :8012

# If another process is using it, choose a different port
```

### Caddy Not Routing
```bash
# Check host Caddy status
sudo systemctl status caddy

# Check host Caddy logs
sudo journalctl -u caddy -f

# Validate Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

### LIMS Containers Not Starting
```bash
# Check container status
docker compose ps

# Check container logs
docker compose logs proxy
docker compose logs backend
docker compose logs frontend
```

## Security Notes

1. **Localhost binding**: Port 8012 is bound to `127.0.0.1` only, not accessible from external network
2. **Host Caddy handles SSL**: All SSL/TLS termination happens at host Caddy
3. **No direct exposure**: Internal services (backend, db, redis) are only accessible within Docker network
4. **Security headers**: Applied by host Caddy for all public traffic

## References

- Main documentation: `/home/munaim/srv/apps/lims/docs/ops/DEPLOYMENT.md`
- Deployment script: `/home/munaim/srv/apps/lims/scripts/both.sh`
- Docker Compose: `/home/munaim/srv/apps/lims/docker-compose.yml`
- Host Caddyfile: `/etc/caddy/Caddyfile`
- Internal Caddyfile: `/home/munaim/srv/apps/lims/Caddyfile`
