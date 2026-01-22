#!/bin/bash
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=config.settings.ci
export SECRET_KEY=django-insecure-test-key
export DB_PASSWORD=dummy
export ALLOWED_HOSTS=*
export ERROR_LOG_FILE=./logs/error.log

cd lims-backend

mkdir -p logs

echo "--- CHECK ---"
python manage.py check || exit 1

echo "--- SHOWMIGRATIONS ---"
python manage.py showmigrations

echo "--- MAKEMIGRATIONS (Detect Drift) ---"
python manage.py makemigrations

echo "--- MIGRATE ---"
python manage.py migrate
