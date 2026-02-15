# Mobile App Deployment (LIMS)

This document describes how to deploy the mobile app build output (PWA/mobile web or native build artifacts) on the LIMS VPS.

## Host folders

| Folder | Purpose |
|--------|--------|
| `/home/munaim/srv/apps/lims/mobile_app_dist` | Static build output (PWA, mobile web, or SPA) |
| `/home/munaim/srv/apps/lims/mobile_apk` | APK (or other installable) files for download |

Create and set permissions if missing:

```bash
mkdir -p /home/munaim/srv/apps/lims/mobile_app_dist /home/munaim/srv/apps/lims/mobile_apk
sudo chown -R munaim:munaim /home/munaim/srv/apps/lims/mobile_app_dist /home/munaim/srv/apps/lims/mobile_apk
sudo chmod -R 775 /home/munaim/srv/apps/lims/mobile_app_dist /home/munaim/srv/apps/lims/mobile_apk
```

## Deploying the build output

1. **Static build output** (Flutter web, React Native web, Ionic, Expo web, etc.):
   - Build your app for web/static export.
   - Copy the **entire** build output (e.g. `build/`, `dist/`, `www/`) into:
     - **`/home/munaim/srv/apps/lims/mobile_app_dist`**
   - The app must be usable when the document root is `mobile_app_dist` (e.g. `index.html` at the root or correct base href).

2. **APK (or other installables)**:
   - Copy `.apk` (or `.aab`) files into:
     - **`/home/munaim/srv/apps/lims/mobile_apk`**
   - They will be available for download at `https://lims.alshifalab.pk/apk/<filename>`.

## URLs (Caddy)

- **Path-based (default):**
  - Mobile app: **https://lims.alshifalab.pk/mobile/**  
    Example: https://lims.alshifalab.pk/mobile/ or https://lims.alshifalab.pk/mobile/index.html
  - APK download: **https://lims.alshifalab.pk/apk/<file.apk>**

- **Subdomain (optional, when DNS is configured):**
  - Mobile app: **https://mobile.lims.alshifalab.pk/**  
  - Requires uncommenting the `mobile.lims.alshifalab.pk` block in `/home/munaim/srv/proxy/caddy/Caddyfile` and adding a DNS A record for `mobile.lims.alshifalab.pk`.

## Framework-agnostic notes

- No mobile framework (Flutter, React Native, Ionic, Expo, etc.) is required in this repo. Build your app elsewhere and copy artifacts into the folders above.
- Ensure your build uses a base path of `/mobile/` if you rely on path-based serving (e.g. `<base href="/mobile/">` or equivalent in your framework).

## Verification

After copying files, run:

```bash
./ops/verify_storage_and_mobile.sh
```

See [VERIFY_STORAGE_AND_MOBILE.md](./VERIFY_STORAGE_AND_MOBILE.md) for details.
