# Smoke Test V2

## What PASS Means
All steps succeed:
- Login
- Create patient
- Create order with test(s)
- Enter results
- Verify results
- Publish order
- Generate report PDF
- Create payment
- Download receipt PDF
- (Optional) Catalog export and dry-run import

## Run (recommended)
```bash
docker compose exec -T backend python manage.py smoke_test_v2
```

## Run (override base URL)
Use this when running the command inside the backend container but hitting the proxy:
```bash
docker compose exec -T backend python manage.py smoke_test_v2 --base-url http://proxy --host-header localhost --forwarded-proto https
```

## Run (standalone script)
```bash
BASE_URL=http://localhost:8013 HOST_HEADER=localhost FORWARDED_PROTO=https ADMIN_USERNAME=admin ADMIN_PASSWORD=admin123 python smoke_test_v2.py
```

## Exit Codes
- `0` = PASS
- `1` = FAIL (first failing step terminates the run)
