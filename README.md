# LIMS Scaffold

This repository contains the initial scaffold for a Laboratory Information Management System (LIMS) featuring a FastAPI backend, Next.js frontend, and PostgreSQL database orchestrated via Docker Compose.

## Getting Started

1. Build and start services:
   ```bash
   docker compose up -d --build
   ```
2. Verify the stack:
   - API health: http://localhost:8000/health should respond with `{ "status": "ok" }`
   - Frontend dashboard: http://localhost:3000 should display **"LIMS — Demo Dashboard"**
3. Stop the services:
   ```bash
   docker compose down
   ```

## Project Structure
```
backend/
  app/
    main.py
    routers/
      health.py
  requirements.txt
  Dockerfile
frontend/
  pages/
    index.tsx
  package.json
  Dockerfile
lims-content/
  reference_ranges.csv
  critical_values.csv
  delta_rules.csv
docs/
  Setup.md
  OpenAPI.md
.github/workflows/
  ci.yml
docker-compose.yml
Makefile
README.md
```

## Next Steps
Proceed to Stage A: Foundation & Setup to continue feature development.
