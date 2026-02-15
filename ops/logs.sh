#!/usr/bin/env bash
set -euo pipefail

PROJECT="lims"
docker compose -p "$PROJECT" logs --tail=200
