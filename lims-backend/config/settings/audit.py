import os

from .base import *

# Audit/Test settings to ensure gates can run without production env vars
DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-audit-gate-test-key-12345")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Production requirements relaxed for audit
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["http://localhost", "http://127.0.0.1"]
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Avoid production DB password check if production is imported (though we shouldn't really import production here)
DB_PASSWORD = os.environ.get("DB_PASSWORD", "audit_pass")
