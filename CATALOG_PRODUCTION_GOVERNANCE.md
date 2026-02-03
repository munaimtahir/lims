# Catalog Production Governance

## Frozen Scope
- Catalog business logic, API contracts, and import/export semantics are frozen; no functional or schema changes are part of this phase.
- Existing endpoint surface (paths, shapes, auth) remains unchanged; only operational hardening is allowed.

## Configurable Surface
- Environment variables (production settings): `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, database/Redis credentials, email settings, JWT lifetimes.
- Deployment volumes: `./lims-backend/media` → `/app/media`, `./logs` → `/app/logs`, `static_files` named volume → `/app/staticfiles` and `/srv/static`.
- Runtime toggles already present (e.g., `SECURE_SSL_REDIRECT`, log level) but must be set explicitly in `.env.production`.

## Mandatory Pre-Deployment Inputs
- Set `ALLOWED_HOSTS` to explicit domains/IPs; wildcards and localhost-only values fail fast in production settings.
- Set `CSRF_TRUSTED_ORIGINS` to explicit HTTPS origins (comma-separated with scheme).
- Provide `CORS_ALLOWED_ORIGINS` matching the frontend domain(s).
- Provide database credentials (`DB_PASSWORD` at minimum) and `SECRET_KEY`.
- Ensure host directories exist and are writable: `./lims-backend/media` for user-generated assets, `./logs` for application logs.

## Test Tooling Parity (Environment Lock)
- `pytest` and `pytest-django` are now pinned in `requirements/production*.txt` to mirror `requirements/development.txt`; production images can run verification tests without ad-hoc installs.
- Test tooling intentionally remains absent from `requirements/base.txt` to avoid inflating runtime dependencies for non-test installs.

## Intentional Deferrals
- No changes to catalog logic, schemas, or API contracts.
- No refactors or dependency upgrades beyond the minimal additions for test parity.
- Static file handling left as-is (whitenoise + `static_files` volume) pending future CDN/offload decision.

## Known Failure Modes & Signals
- Missing or invalid `ALLOWED_HOSTS` (wildcard/localhost-only) → process startup `ValueError` during settings load.
- Missing/invalid `CSRF_TRUSTED_ORIGINS` (empty, wildcard, non-HTTPS) → process startup `ValueError` during settings load.
- Omitted required env vars in `docker-compose.yml` (`:?` expansions) → docker compose configuration error before containers start.
- Absent host directories for `media` or `logs` → container start failure with volume mount errors or runtime file write errors; directories must be created with write permissions.

## Responsibility Boundaries
- Platform/Ops: provide correct env vars, maintain volume mounts/backups (`./lims-backend/media`, `./logs`, database/redis volumes), and operate Caddy/SSL termination.
- Application Team: maintain test tooling pins, monitor startup failures related to configuration validation, and ensure no functional changes slip into the frozen catalog surface.
- Shared: respond to explicit startup failures by supplying required configuration rather than bypassing checks.
