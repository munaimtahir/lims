#!/bin/bash
set -e

# Fix permissions if running as root
if [ "$(id -u)" = "0" ]; then
    echo "Running as root. Fixing permissions..."
    mkdir -p /app/media /app/staticfiles /app/logs
    chown -R appuser:appuser /app/media /app/staticfiles /app/logs
    
    # Switch to appuser for Django commands
    exec gosu appuser "$0" "$@"
fi

# Ensure database migrations are applied and admin user exists deterministically.
# Ensure static files are collected (fixes missing manifest in production)
python manage.py collectstatic --noinput --clear

# Ensure database migrations are applied and admin user exists deterministically.
python manage.py migrate --noinput
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u,created=User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com','full_name':'System Admin','role':'Admin','is_staff':True,'is_superuser':True}); u.is_staff=True; u.is_superuser=True; u.role='Admin'; u.full_name = u.full_name or 'System Admin'; u.set_password('admin123'); u.save(); print('admin bootstrap: created' if created else 'admin bootstrap: ensured')"

exec "$@"
