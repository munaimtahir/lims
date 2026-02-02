# Production Runbook (Docker)

## Prerequisites
- Docker + Docker Compose
- A `.env.production` file (see `.env.production.example`)
- Port 8012 available (proxy container)

## Bring Up the Stack
```bash
docker compose -f docker-compose.yml up -d
```

## Apply Migrations
```bash
docker compose exec -T backend python manage.py migrate
```

## Seed Minimal Catalog (if empty)
```bash
docker compose exec -T backend python manage.py seed_minimal_catalog
```

## Create Admin User
```bash
docker compose exec -T backend python manage.py createsuperuser
```

## Health Checks
```bash
curl -s http://localhost:8012/api/v1/health/
```

## Backups
Database backups are stored in `./backups`.

```bash
docker compose exec -T db pg_dump -U ${DB_USER:-postgres} ${DB_NAME:-lims_db} > backups/lims_db_$(date +%F).sql
```

## Restore
```bash
cat backups/lims_db_YYYY-MM-DD.sql | docker compose exec -T db psql -U ${DB_USER:-postgres} ${DB_NAME:-lims_db}
```

## Upgrades
1. Pull latest code.
2. Rebuild images:
```bash
docker compose build
```
3. Restart services:
```bash
docker compose up -d
```
4. Run migrations:
```bash
docker compose exec -T backend python manage.py migrate
```

## Production Verification (post-upgrade)
```bash
docker compose exec -T backend python manage.py smoke_test_v2
```
