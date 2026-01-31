from .production import *
import os

# Override Database for CI/Local verification using SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable some production checks for CI
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
