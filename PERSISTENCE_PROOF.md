# PERSISTENCE_PROOF

## Host Paths
- Media: `./lims-backend/media` ↔ `/app/media`
- Logs: `./logs` ↔ `/app/logs`

## Procedure
1) Created durability markers inside backend container:
```
docker compose --env-file .env.production exec -T backend sh -c 'ts=$(date +%Y%m%d%H%M%S); echo media-durability-$ts > /app/media/durability_${ts}.txt; echo log-durability-$ts > /app/logs/durability_${ts}.log'
```
   - Example timestamp: 20260203133130
2) Restarted & recreated stack:
```
docker compose --env-file .env.production restart
docker compose --env-file .env.production up -d --force-recreate
```
3) Verified persistence:
   - Container: `ls /app/media` → durability_20260203133130.txt present
   - Container: `ls /app/logs` → durability_20260203133130.log present
   - Host: `cat lims-backend/media/durability_20260203133130.txt` → media-durability-20260203133130
   - Host: `cat logs/durability_20260203133130.log` → log-durability-20260203133130

## Conclusion
- Media and log data persist across restart and forced container recreation via host bind mounts.
- Backup targets: `./lims-backend/media` (user assets) and `./logs` (application logs); include in scheduled backups alongside DB/Redis volumes.
