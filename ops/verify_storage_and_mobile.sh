#!/usr/bin/env bash
# Verification script for media/uploads (Django) and mobile/APK static serving.
# Run from repo root: ./ops/verify_storage_and_mobile.sh

REPO_ROOT="${REPO_ROOT:-/home/munaim/srv/apps/lims}"
MEDIA_DIR="$REPO_ROOT/media"
UPLOADS_DIR="$REPO_ROOT/uploads"
MOBILE_DIST="$REPO_ROOT/mobile_app_dist"
MOBILE_APK="$REPO_ROOT/mobile_apk"
BASE_URL="${BASE_URL:-https://lims.alshifalab.pk}"
SUBDOMAIN_ENABLED="${SUBDOMAIN_ENABLED:-false}"

FAIL=0
CREATED_MEDIA_HEALTH=
CREATED_MOBILE_INDEX=
CREATED_APK_TEST=

cd "$REPO_ROOT" || exit 1

echo "=== Storage and Mobile Verification ==="
echo "Repo root: $REPO_ROOT"
echo ""

# --- A) Host checks ---
echo "--- A) Host checks ---"
for d in "$MEDIA_DIR" "$UPLOADS_DIR" "$MOBILE_DIST" "$MOBILE_APK"; do
  if [[ -d "$d" ]]; then
    echo "  OK dir exists: $d"
  else
    echo "  FAIL dir missing: $d"
    FAIL=1
  fi
done

echo "ok" > "$MEDIA_DIR/health.txt"
CREATED_MEDIA_HEALTH=1
echo "  Created $MEDIA_DIR/health.txt"

if [[ ! -f "$MOBILE_DIST/index.html" ]]; then
  echo '<!DOCTYPE html><html><head><title>Mobile</title></head><body>OK MOBILE</body></html>' > "$MOBILE_DIST/index.html"
  CREATED_MOBILE_INDEX=1
  echo "  Created $MOBILE_DIST/index.html (placeholder)"
else
  echo "  $MOBILE_DIST/index.html already exists (not overwritten)"
fi

echo "apk" > "$MOBILE_APK/test.txt"
CREATED_APK_TEST=1
echo "  Created $MOBILE_APK/test.txt"
echo ""

# --- B) Container checks ---
echo "--- B) Container checks ---"
BACKEND_CONTAINER=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E 'lims_backend|lims_backend_prod' | head -1)
if [[ -n "$BACKEND_CONTAINER" ]]; then
  for path in /app/media /app/uploads; do
    if docker exec "$BACKEND_CONTAINER" ls -la "$path" &>/dev/null; then
      echo "  OK container path exists: $path"
    else
      echo "  FAIL container path missing: $path"
      FAIL=1
    fi
  done
  if docker exec "$BACKEND_CONTAINER" cat /app/media/health.txt &>/dev/null; then
    echo "  OK container can read /app/media/health.txt"
  else
    echo "  FAIL container cannot read /app/media/health.txt"
    FAIL=1
  fi
else
  echo "  SKIP backend container not running (docker ps)"
fi
echo ""

# --- C) HTTP checks ---
echo "--- C) HTTP checks ---"
if curl -sI "$BASE_URL/media/health.txt" 2>/dev/null | head -1 | grep -q 200; then
  echo "  OK $BASE_URL/media/health.txt -> 200"
else
  echo "  FAIL $BASE_URL/media/health.txt (expected 200)"
  FAIL=1
fi

if curl -sI "$BASE_URL/mobile/index.html" 2>/dev/null | head -1 | grep -q 200; then
  echo "  OK $BASE_URL/mobile/index.html -> 200"
else
  # try /mobile/ as well
  if curl -sI "$BASE_URL/mobile/" 2>/dev/null | head -1 | grep -q 200; then
    echo "  OK $BASE_URL/mobile/ -> 200"
  else
    echo "  FAIL $BASE_URL/mobile/ (expected 200)"
    FAIL=1
  fi
fi

if curl -sI "$BASE_URL/apk/test.txt" 2>/dev/null | head -1 | grep -q 200; then
  echo "  OK $BASE_URL/apk/test.txt -> 200"
else
  echo "  FAIL $BASE_URL/apk/test.txt (expected 200)"
  FAIL=1
fi

if [[ "$SUBDOMAIN_ENABLED" == "true" ]]; then
  if curl -sI "https://mobile.lims.alshifalab.pk/" 2>/dev/null | head -1 | grep -q 200; then
    echo "  OK https://mobile.lims.alshifalab.pk/ -> 200"
  else
    echo "  FAIL https://mobile.lims.alshifalab.pk/ (expected 200)"
    FAIL=1
  fi
else
  echo "  SKIP subdomain (SUBDOMAIN_ENABLED not true)"
fi
echo ""

# --- D) Cleanup ---
echo "--- D) Cleanup ---"
[[ -n "$CREATED_MEDIA_HEALTH" ]] && rm -f "$MEDIA_DIR/health.txt" && echo "  Removed media/health.txt"
[[ -n "$CREATED_MOBILE_INDEX" ]] && rm -f "$MOBILE_DIST/index.html" && echo "  Removed mobile_app_dist/index.html (placeholder)"
[[ -n "$CREATED_APK_TEST" ]] && rm -f "$MOBILE_APK/test.txt" && echo "  Removed mobile_apk/test.txt"
echo ""

# --- Summary ---
if [[ $FAIL -eq 0 ]]; then
  echo "=== PASS ==="
  exit 0
else
  echo "=== FAIL (one or more checks failed) ==="
  exit 1
fi
