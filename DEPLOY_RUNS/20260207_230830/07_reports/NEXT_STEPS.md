# Post-Deployment Next Steps

## 1. Secrets Management
- Currently using `.env.production` in plain text. Consider migrating to AWS Secrets Manager, GitHub Secrets, or similar.

## 2. CI/CD Integration
- Add smoke tests to CI pipeline (e.g., GitHub Actions) to run after PR merge or deploy.

## 3. Database Backup
- Implement automated backups (already configured in docker-compose volumes, but need script/Cron).

## 4. Monitoring
- Setup monitoring for health endpoints (/api/v1/health/).
- Monitor Redis/Celery queue length.

## 5. Security Scanning
- Run OWASP ZAP or similar against the domain.
