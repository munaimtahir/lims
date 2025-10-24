# Contributing to LIMS

Thanks for your interest in contributing to this Laboratory Information Management System (LIMS). This document explains how to set up a development environment, how we expect contributions to be made, and our review process.

## Quick links
- Repo: https://github.com/munaimtahir/lims
- Default branch: `main`
- CI: GitHub Actions (backend + frontend checks)

## Getting started (quick)
1. Create a branch from `main`:
   - feature branches: `feature/short-description`
   - bugfix branches: `fix/short-description`
2. Run services locally (Docker Compose):
   ```bash
   docker compose up -d --build
   ```
3. Run backend tests:
   ```bash
   cd backend
   pytest
   ```
4. Run frontend build:
   ```bash
   cd frontend
   npm ci
   npm run build
   ```

## Code style & checks
- Python: black, ruff, isort, mypy
- TypeScript/JS: eslint, prettier, tsc
- Use `pre-commit` hooks locally (see `.pre-commit-config.yaml`)

## Pull requests
- Base PRs against `main`.
- Keep changes focused and small.
- Include tests for new functionality.
- Use the PR template and ensure CI passes before merge.
- At least one approving review is required.

## Tests
- Add unit tests for critical logic.
- For backend use `pytest` and factories where appropriate.
- For frontend consider unit tests and recommend e2e later (Playwright/Cypress).

## Security & secrets
- Do not commit secrets or API keys.
- Use environment variables and `.env` files locally (add to `.gitignore`).

## Communication
- Use issues to discuss large features or design changes before implementation.
