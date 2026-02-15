# Verification: Storage and Mobile Serving

This guide describes how to verify that media/uploads (Django file storage) and mobile/APK static serving are correctly wired.

## Script

Run from the repo root:

```bash
./ops/verify_storage_and_mobile.sh
```

The script will:

1. **Host checks**
   - Confirm directories exist: `media`, `uploads`, `mobile_app_dist`, `mobile_apk`
   - Create test files: `media/health.txt`, `mobile_app_dist/index.html`, `mobile_apk/test.txt`

2. **Container checks** (if backend container is running)
   - Confirm backend sees `/app/media` and `/app/uploads`
   - Read `health.txt` from `/app/media`

3. **HTTP checks**
   - `curl -I https://lims.alshifalab.pk/media/health.txt` → expect 200
   - `curl -I https://lims.alshifalab.pk/mobile/index.html` → expect 200 (or `/mobile/`)
   - `curl -I https://lims.alshifalab.pk/apk/test.txt` → expect 200
   - If subdomain is enabled: `curl -I https://mobile.lims.alshifalab.pk/` → expect 200

4. **Cleanup**
   - Remove only the test files created by the script

## Expected result

A clear **PASS** or **FAIL** summary at the end. Fix any failing step before considering the setup complete.

## Manual checks (optional)

- Upload a file via Django admin or API and confirm it appears under `media/` on the host and is accessible at `https://lims.alshifalab.pk/media/...`
- Replace placeholder `mobile_app_dist/index.html` with a real mobile build and confirm `https://lims.alshifalab.pk/mobile/` serves it.
