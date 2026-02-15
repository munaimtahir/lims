#!/usr/bin/env bash
set -euo pipefail

PROJECT="lims"
docker ps --filter "label=com.docker.compose.project=$PROJECT"
