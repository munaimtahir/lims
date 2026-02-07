import os

# Set required env vars before importing production settings
# These are only used during import validation and will be overridden by test DB config
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-not-for-production")
os.environ.setdefault("DB_PASSWORD", "test-db-password-for-ci-only")

from .production import *

# Override Database for CI/Local verification.
# Prefer a dedicated Postgres test DB when provided to stay closer to prod schema.
# Fallback to lightweight in-memory SQLite for ad-hoc runs.
TEST_DB_URL = os.environ.get("TEST_DB_URL")
TEST_DB_HOST = os.environ.get("TEST_DB_HOST")

if TEST_DB_URL or TEST_DB_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("TEST_DB_NAME", "lims_test_db"),
            "USER": os.environ.get("TEST_DB_USER", "postgres"),
            "PASSWORD": os.environ.get("TEST_DB_PASSWORD", "testpass"),
            "HOST": TEST_DB_HOST or os.environ.get("TEST_DB_HOST", "localhost"),
            "PORT": os.environ.get("TEST_DB_PORT", "5432"),
            "CONN_MAX_AGE": 0,
            "ATOMIC_REQUESTS": True,
        }
    }
else:
    # SQLite fallback for quick local checks (schema differences may surface FK issues)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
            "MIGRATE": True,  # allow migrations so schema matches models
        }
    }

# Explicitly set DEBUG to True for test environment (or development)
DEBUG = True

# Disable some production checks for CI
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]

# Override logging for CI to avoid permission errors and simplify output
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {asctime} {name} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",  # Use INFO level for console output in CI
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",  # Use INFO level for root in CI
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "rest_framework": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {  # Add logging for custom apps
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Use temporary directory for media files during tests to avoid permission issues
import tempfile
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), "lims_test_media")

# Disable HTTPS redirect in test context to avoid 301s during local/CI HTTP calls
SECURE_SSL_REDIRECT = False
