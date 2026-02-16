# Deploy LIMS

## Required file for deployment

Create an env file at the **repo root** with at least:

- `SECRET_KEY` – e.g. `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DB_PASSWORD` – PostgreSQL password (same value is used by the `db` container and backend)
- `ALLOWED_HOSTS` – comma-separated (e.g. `lims.alshifalab.pk,api.lims.alshifalab.pk,localhost,127.0.0.1`)
- `CORS_ALLOWED_ORIGINS` – comma-separated (e.g. `https://lims.alshifalab.pk,https://api.lims.alshifalab.pk`)
- `CSRF_TRUSTED_ORIGINS` – comma-separated HTTPS origins

**Option A – use `.env.production`**

```bash
cp .env.production.example .env.production
# Edit .env.production and set the variables above
```

**Option B – use `.env`**

Copy the same variables into a `.env` file at the repo root.

## Deploy with Docker Compose

From the repo root:

```bash
./deploy.sh
```

Or manually:

```bash
# If using .env.production
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# If using .env (default)
docker compose -f docker-compose.prod.yml up -d
```

Migrations run automatically when the backend container starts (`bootstrap_prod.sh`).

## Local migrations (without Docker)

From `lims-backend/` with no database configured:

- Development settings use **SQLite** when `DB_PASSWORD` is not set (or set `USE_SQLITE=1`).
- Run: `python manage.py migrate`

To use PostgreSQL locally, set `DB_PASSWORD` (and optionally `DB_NAME`, `DB_USER`, `DB_HOST`) in `lims-backend/.env` or in the environment.
