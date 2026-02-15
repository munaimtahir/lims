# Storage and Mobile Wiring — What Changed

Summary of changes for **Section A** (media/uploads) and **Section B** (mobile app static + APK).

## Files Edited

### 1. `docker-compose.prod.yml`
- **Backup:** `docker-compose.prod.yml.bak.YYYYMMDDHHMM` (create before further edits)
- **Changes:**
  - **backend:** Bind mounts:
    - `/home/munaim/srv/apps/lims/media:/app/media:rw`
    - `/home/munaim/srv/apps/lims/uploads:/app/uploads:rw`
  - **celery** and **celery-beat:** Same media + uploads mounts (no `/app/mobile`)
- **Note:** Current running stack may be from `docker-compose.yml` (containers named `lims_backend`, not `lims_backend_prod`). To apply prod mounts, run:
  ```bash
  cd /home/munaim/srv/apps/lims
  docker compose -f docker-compose.prod.yml up -d
  ```
  Or restart only backend/celery/beat after switching to prod compose.

### 2. Django settings
- **`lims-backend/config/settings/base.py`**
  - `MEDIA_URL = "/media/"`
  - `MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/app/media")`
  - `UPLOADS_ROOT = os.getenv("UPLOADS_ROOT", "/app/uploads")`
  - Removed `MOBILE_ROOT`.
- **`lims-backend/config/settings/production.py`**
  - `MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")`

### 3. Caddyfile (host)
- **Path:** `/home/munaim/srv/proxy/caddy/Caddyfile`
- **Backup:** Create before further edits (e.g. `Caddyfile.bak.YYYYMMDDHHMM`)
- **In `lims.alshifalab.pk` block (before reverse_proxy):**
  - **`/media/*`** — served from host: `root * /home/munaim/srv/apps/lims/media` + `file_server` (required).
  - **`/mobile/*`** — served from host: `root * /home/munaim/srv/apps/lims/mobile_app_dist` + `file_server` (path-based default).
  - **`/apk/*`** — served from host: `root * /home/munaim/srv/apps/lims/mobile_apk` + `file_server`.
- **Removed:** `handle /media/* { reverse_proxy ... }` (media now served directly by host Caddy).
- **Optional (commented):** Subdomain block for `mobile.lims.alshifalab.pk` with instructions to uncomment when DNS is ready.

### 4. New / updated files
- **`docs/ops/MOBILE_DEPLOY.md`** — Where to put mobile build output and APK; URLs (path-based and subdomain).
- **`docs/ops/VERIFY_STORAGE_AND_MOBILE.md`** — How to run and interpret the verification script.
- **`ops/verify_storage_and_mobile.sh`** — Executable script: host dirs, test files, container checks, HTTP checks, cleanup, PASS/FAIL summary.
- **`lims-backend/apps/core/tests/test_storage_settings.py`** — Unit tests: `MEDIA_URL == "/media/"`, `MEDIA_ROOT` ends with `/media` or is `/app/media`, `UPLOADS_ROOT` default `/app/uploads`.

## Caddy validate and reload

```bash
sudo caddy validate --config /home/munaim/srv/proxy/caddy/Caddyfile
# Expected: "Valid configuration"
sudo systemctl reload caddy
```

## Verification

```bash
cd /home/munaim/srv/apps/lims
./ops/verify_storage_and_mobile.sh
```

**Expected after full apply:**  
- Host dirs exist; container sees `/app/media` and `/app/uploads`; HTTP 200 for `/media/health.txt`, `/mobile/index.html`, `/apk/test.txt`.  
If production compose is not in use yet, container checks for `/app/uploads` and `/app/media/health.txt` may fail until backend is restarted with prod compose. If Caddy cannot read `/home/munaim/srv/apps/lims/media`, `/media/health.txt` may 404; ensure Caddy process has read access to that path.

## Services that received mounts

- **backend** — `media`, `uploads`
- **celery** — `media`, `uploads`
- **celery-beat** — `media`, `uploads`  
No mounts for `mobile_app_dist` or `mobile_apk` (served only by Caddy from host).

## Caddy routes

| Route       | Source (host path)           | Status   |
|------------|-----------------------------|----------|
| `/media/*` | `.../lims/media`             | Enabled  |
| `/mobile/*`| `.../lims/mobile_app_dist`  | Enabled  |
| `/apk/*`   | `.../lims/mobile_apk`       | Enabled  |
| `mobile.lims.alshifalab.pk` | same as `/mobile/*` | Commented (enable when DNS ready) |

---

## TODO checklist (manual confirmation)

- [ ] **Production compose in use:** Run with `-f docker-compose.prod.yml` and restart backend/celery/celery-beat so `/app/media` and `/app/uploads` mounts are applied.
- [ ] **Caddy reload:** After editing Caddyfile, run `sudo caddy validate` and `sudo systemctl reload caddy`.
- [ ] **Media 200:** If `/media/health.txt` still 404, confirm Caddy can read `/home/munaim/srv/apps/lims/media` (user/permissions).
- [ ] **Admin upload test:** Upload a file via Django admin and confirm it appears under host `media/` and at `https://lims.alshifalab.pk/media/...`.
- [ ] **Report PDF:** Confirm report PDF generation writes to the expected path and file is accessible via `/media/...` if applicable.
- [ ] **DNS for mobile subdomain:** When ready, add A record for `mobile.lims.alshifalab.pk`, then uncomment the `mobile.lims.alshifalab.pk` block in Caddyfile and reload Caddy.
- [ ] **Replace placeholder:** Replace any placeholder `mobile_app_dist/index.html` with the real mobile app build and verify `https://lims.alshifalab.pk/mobile/` (and optionally `https://mobile.lims.alshifalab.pk/`).
