# PROD_ENV_CONFIG_VALIDATION

## Inputs
- Source: `.env.production` (updated with lims.alshifalab.pk)
- Key values:
  - ALLOWED_HOSTS=lims.alshifalab.pk,www.lims.alshifalab.pk,203.0.113.10
  - CORS_ALLOWED_ORIGINS=https://lims.alshifalab.pk,https://www.lims.alshifalab.pk
  - CSRF_TRUSTED_ORIGINS=https://lims.alshifalab.pk,https://www.lims.alshifalab.pk
  - DATABASE_URL=postgres://postgres:changeme@db:5432/lims_db
  - SECRET_KEY set (non-default)

## Validation Command
```
docker compose --env-file .env.production config
```
- Result: **PASS** (no unresolved `${VAR}` placeholders). Only docker warning about `version` key being obsolete.
- Output stored at `/tmp/compose_config_final.yaml` for reference.

## Notes
- Environment values are production-formatted (no localhost/wildcards).
- Enforced placeholders (`:?`) satisfied for ALLOWED_HOSTS / CSRF / CORS.
