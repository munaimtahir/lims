# LIMS Deployment Strategy

## Overview
The LIMS application uses a strict Docker-based deployment strategy. This ensures consistency across development and production environments and eliminates "virtualenv vs. system" conflicts.

## Architecture
- **Proxy (Caddy)**: Single entry point. Handles internal routing and serves static/media files directly.
- **Backend (Django)**: API and Admin. Runs via Gunicorn.
- **Frontend (React)**: SPA. Served via Caddy/Nginx within its own container or reversed proxied.
- **Database (PostgreSQL)**: Persistent storage.
- **Redis/Celery**: Async task queue.

## deployment Rules
1. **Container-First**: All application code runs inside Docker containers. Do NOT run `python manage.py` or `npm start` on the host directly for production.
2. **Volumes & Permissions**:
   - `media/` directory permissions are automatically fixed by the container entrypoint (`bootstrap_prod.sh`).
   - Static files are collected to a shared volume (`static_files`) and served by the Proxy container.
3. **Configuration**:
   - All environment-specific config is managed via `.env` files and `docker-compose.yml`.
   - No manual patching of files on the server.

## Directory Structure
- `/lims-backend`: Django app.
- `/frontend`: React app.
- `/config`: Unified configuration.
- `docker-compose.yml`: Single source of truth for services.

## How to Deploy
1. **Build & Start**:
   ```bash
   docker compose up -d --build
   ```
2. **Logs**:
   ```bash
   docker compose logs -f
   ```
3. **Database Migrations**:
   Automatically handled by `backend` container startup. 

## Troubleshooting
- **Permission Denied (Media)**: The container entrypoint automatically fixes ownership of `/app/media` to `appuser:appuser` (1000:1000). If issues persist, ensure the host volume is not immutable.
- **Static Files Missing**: Ensure the `static_files` volume is populated. Restarting `backend` triggers `collectstatic`.

## User Management
System runs as `appuser` inside containers (UID 1000). 
Host files in `media/` should be writable by UID 1000 or the group.
