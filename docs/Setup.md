# LIMS Project Setup

## Prerequisites
- Docker 24+
- Docker Compose Plugin

## Quick Start
1. Build and start the stack:
   ```bash
   docker compose up -d --build
   ```
2. Verify services:
   - API health: http://localhost:8000/health should return `{ "status": "ok" }`
   - Frontend: http://localhost:3000 should display **"LIMS — Demo Dashboard"**
3. Stop the stack when finished:
   ```bash
   docker compose down
   ```

## Directory Overview
- `backend/`: FastAPI service.
- `frontend/`: Next.js application.
- `lims-content/`: Reference laboratory data.
- `docs/`: Documentation.
