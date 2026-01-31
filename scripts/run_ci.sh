#!/usr/bin/env bash
set -euo pipefail

docker compose up -d
docker compose exec -T backend python manage.py migrate
docker compose exec -T backend pip install -r requirements/development.txt
docker compose exec -T backend env DJANGO_SETTINGS_MODULE=config.settings.development python -m pytest
docker compose exec -T backend python manage.py catalog_round_trip_verify
docker compose exec -T backend python manage.py smoke_test_v2
