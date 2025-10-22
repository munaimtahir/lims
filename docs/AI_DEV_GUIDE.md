# 🤖 AI Developer Guide — LIMS Project

## Overview
This repository is a cloud-based **Medical Laboratory Information Management System (LIMS)**.
Stack:
- FastAPI backend (Python 3.11)
- Next.js frontend (TypeScript + React 18)
- PostgreSQL database
- Docker Compose orchestration
- GitHub Actions for CI/CD

## Philosophy
- Simple, modular, reproducible.
- Backend = logic, Frontend = UI.
- Use environment variables, not secrets in code.
- All development reproducible via Docker.

## Folder Layout
```
backend/
frontend/
lims-content/
docs/
.github/workflows/
```

## Agent Permissions
✅ Add new routes, components, docs, tests.  
🚫 Modify clinical CSVs in `lims-content/` without human approval.  
🚫 Hardcode credentials.  
🚫 Push directly to main or skip CI.

## Workflow
1. Create feature branch.
2. Implement and test locally with Docker.
3. Commit and push with clear message.
4. CI must pass before merge.

## Agent Behavior
- Explain structure changes before applying.
- Maintain comments and docstrings.
- Use type hints consistently.
- Add minimal tests when logic changes.

## Next Steps
1. Verify `/health` and dashboard work.
2. Proceed to Stage A (Foundation & Setup).
3. Build patient registration and QC engine.
