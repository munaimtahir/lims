# 🤝 Contributing — LIMS Project

## Branch Model
- `main`: stable release
- `feature/*`: new features
- `hotfix/*`: urgent fixes

## Pull Requests
- Run `docker compose up -d --build` before PR.
- Ensure `/health` and dashboard are accessible.
- CI must pass before merging.
- Add a short summary of changes.

## Versioning
Follow Semantic Versioning (v0.1.0 → v1.0.0).

## Deployment
Future deployment targets include Render, Railway, and Fly.io.
Environment configuration handled through `.env`.
