# Rerun Commands

## Deployment
```bash
cd /home/munaim/srv/apps/lims
docker compose --env-file .env.production up -d
sudo systemctl reload caddy
```

## Validate Health
```bash
curl -I https://lims.alshifalab.pk/
curl -I https://lims.alshifalab.pk/api/v1/health/
```

## E2E Smoke (Post-Deploy)
```bash
cd /home/munaim/srv/apps/lims/e2e
npm ci
PLAYWRIGHT_BASE_URL=https://lims.alshifalab.pk npx playwright test smoke --workers=1
```

## Debugging
- Check Caddy Logs: `sudo journalctl -u caddy -f`
- Check App Logs: `docker compose logs -f --tail=100`
