#!/bin/sh
set -e

# Ensure database migrations are applied and admin user exists deterministically.
python manage.py migrate --noinput
python manage.py shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); u,created=User.objects.get_or_create(username='admin', defaults={'email':'admin@example.com','is_staff':True,'is_superuser':True}); u.is_staff=True; u.is_superuser=True; u.set_password('admin123'); u.save(); print('admin bootstrap: created' if created else 'admin bootstrap: ensured')"

exec "$@"
