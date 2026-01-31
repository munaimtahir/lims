# Development Runbook

## Prerequisites
- Docker + Docker Compose
- Port 8013 available (proxy)

## Start the Stack (local)
```bash
docker compose up -d
```

## Apply Migrations
```bash
docker compose exec -T backend python manage.py migrate
```

## Seed Minimal Catalog (if empty)
```bash
docker compose exec -T backend python manage.py seed_minimal_catalog
```

## Create/Reset Admin User
```bash
docker compose exec -T backend python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u,created=User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com','is_staff':True,'is_superuser':True}); u.set_password('admin123'); u.is_staff=True; u.is_superuser=True; u.save(); print('created' if created else 'updated')"
```

## Access
- UI: `http://localhost:8013/`
- API: `http://localhost:8013/api/v1/`
- Health: `http://localhost:8013/api/v1/health/`

## Common Dev Commands
```bash
# Run backend tests
docker compose exec -T backend pytest

# Catalog round-trip verification
docker compose exec -T backend python manage.py catalog_round_trip_verify

# Smoke test v2
docker compose exec -T backend python manage.py smoke_test_v2
```

## Stop
```bash
docker compose down
```
