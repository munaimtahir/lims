# PROD_BOOT_VERIFICATION

## Build & Boot
```
docker compose --env-file .env.production down -v
docker compose --env-file .env.production up -d --build
```
- Result: **PASS** (all images rebuilt, stack started).

## Container Health
```
docker compose --env-file .env.production ps
```
- backend: Up (health: starting → healthy shortly after)
- proxy: Up (healthy)
- db, redis: healthy

## Django Integrity Checks
```
docker compose --env-file .env.production exec -T backend python manage.py check
```
- Result: **PASS** (System check identified no issues)

```
docker compose --env-file .env.production exec -T backend python manage.py migrate
```
- Result: **PASS** (all migrations applied to fresh DB)

## Health Endpoint
```
curl -H "Host: lims.alshifalab.pk" http://localhost:8000/api/v1/health/
```
- HTTP 200 OK
- Body: {"status":"healthy","service":"LIMS Backend","database":"connected"}

## Observations
- Only repeated docker-compose warning: `version` key is obsolete (non-blocking).
