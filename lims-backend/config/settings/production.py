"""
Production-specific settings for LIMS project.

This configuration is designed for SSH-based Docker deployment.
It enforces security best practices and requires explicit configuration
of critical settings via environment variables.

Critical Environment Variables:
    - SECRET_KEY: Django secret key (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    - DB_PASSWORD: PostgreSQL password
    - ALLOWED_HOSTS: Comma-separated list including domain and public IP
    - CORS_ALLOWED_ORIGINS: Comma-separated list of allowed frontend origins
    
See .env.production.example for complete configuration template.
"""

from .base import *
import os
import logging

# ============================================
# DEBUG SETTINGS
# ============================================
DEBUG = False


# ============================================
# SECRET KEY AND SECURITY VALIDATION
# ============================================

# Validate SECRET_KEY
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "CRITICAL: SECRET_KEY environment variable must be set in production. "
        "Generate with: python3 -c \"import secrets; print(secrets.token_urlsafe(50))\""
    )

# Validate DB_PASSWORD
DB_PASSWORD = os.environ.get('DB_PASSWORD')
if not DB_PASSWORD:
    raise ValueError(
        "CRITICAL: DB_PASSWORD environment variable must be set in production. "
        "Generate with: openssl rand -base64 32"
    )


# ============================================
# ALLOWED HOSTS CONFIGURATION
# ============================================
# CRITICAL FOR SSH DEPLOYMENT ON PUBLIC IP
# Must include:
#   - Your domain name (e.g., your-domain.com)
#   - www subdomain if using (e.g., www.your-domain.com)
#   - Public IP address of your server
# Format: "domain.com,www.domain.com,xxx.xxx.xxx.xxx"

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',')]
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['']:
    raise ValueError(
        "CRITICAL: ALLOWED_HOSTS environment variable must be set in production. "
        "Must include your domain and public IP. "
        "Format: 'your-domain.com,www.your-domain.com,xxx.xxx.xxx.xxx'"
    )

# Log allowed hosts for debugging
logger = logging.getLogger(__name__)
logger.info(f"Production ALLOWED_HOSTS configured: {ALLOWED_HOSTS}")


# ============================================
# HTTPS/SSL SETTINGS
# ============================================
# Configure for deployment behind Caddy reverse proxy with SSL termination

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_REDIRECT_EXEMPT = [r'^api/v1/health/$']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security) - tell browsers to always use HTTPS
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# ============================================
# DATABASE CONFIGURATION
# ============================================
# PostgreSQL is the production database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'lims_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': DB_PASSWORD,
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'ATOMIC_REQUESTS': True,  # Use transactions for views
    }
}


# ============================================
# CACHE CONFIGURATION
# ============================================
# Redis for caching and session storage

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
        'KEY_PREFIX': 'lims',
        'TIMEOUT': 300,  # Default timeout 5 minutes
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'retry_on_timeout': True,
                'max_connections': 50,
            },
        },
    }
}

# Use database for sessions (more reliable than Redis for critical operations)
# Redis cache is still used for general caching
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# ============================================
# CORS CONFIGURATION
# ============================================
# CRITICAL FOR FRONTEND INTEGRATION
# Controls which origins can make cross-origin requests
# Must match the domain where your frontend is hosted

CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')]
if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == ['']:
    logger.warning(
        "WARNING: CORS_ALLOWED_ORIGINS not configured. "
        "Frontend may not be able to communicate with API. "
        "Set CORS_ALLOWED_ORIGINS to your frontend domain (e.g., https://your-domain.com)"
    )

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

logger.info(f"Production CORS_ALLOWED_ORIGINS configured: {CORS_ALLOWED_ORIGINS}")


# ============================================
# CSRF TRUSTED ORIGINS CONFIGURATION
# ============================================
# CRITICAL FOR HTTPS DEPLOYMENT
# Django 4.0+ requires CSRF_TRUSTED_ORIGINS for HTTPS sites
# Must include the protocol (https://) and domain

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')]
if not CSRF_TRUSTED_ORIGINS or CSRF_TRUSTED_ORIGINS == ['']:
    # Fallback to CORS_ALLOWED_ORIGINS if CSRF_TRUSTED_ORIGINS not explicitly set
    if CORS_ALLOWED_ORIGINS and CORS_ALLOWED_ORIGINS != ['']:
        CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
        logger.info(f"CSRF_TRUSTED_ORIGINS not set, using CORS_ALLOWED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
    else:
        logger.warning(
            "WARNING: CSRF_TRUSTED_ORIGINS not configured. "
            "CSRF protection may fail for HTTPS requests. "
            "Set CSRF_TRUSTED_ORIGINS to your domain (e.g., https://yourdomain.com)"
        )

logger.info(f"Production CSRF_TRUSTED_ORIGINS configured: {CSRF_TRUSTED_ORIGINS}")


# ============================================
# STATIC AND MEDIA FILES
# ============================================

STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

# Use whitenoise for efficient static file serving
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Enable GZIP compression for whitenoise
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = True


# ============================================
# EMAIL CONFIGURATION
# ============================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', f'noreply@{os.environ.get("SERVER_NAME", "lims.local")}')

# Verify email configuration in production
if EMAIL_HOST_USER and not EMAIL_HOST_PASSWORD:
    logger.warning("WARNING: EMAIL_HOST_USER is set but EMAIL_HOST_PASSWORD is not. Email sending may fail.")


# ============================================
# CELERY CONFIGURATION
# ============================================

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes


# ============================================
# LOGGING CONFIGURATION
# ============================================
# Comprehensive logging for production debugging

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {name} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        # Django core logging
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        # Security-related logging
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security.DisallowedHost': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Database logging (verbose in production)
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Set to DEBUG for SQL query logging
            'propagate': False,
        },
        # REST Framework logging
        'rest_framework': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        # Celery logging
        'celery': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(exist_ok=True)


# ============================================
# SECURITY MIDDLEWARE CONFIGURATION
# ============================================

# Content Security Policy (if django-csp is installed)
try:
    CSP_DEFAULT_SRC = ("'self'",)
    CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # May need to be adjusted
    CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # May need to be adjusted
except Exception:
    pass


# ============================================
# PRODUCTION SUMMARY
# ============================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("LIMS Production Configuration Loaded")
    logger.info("=" * 60)
    logger.info(f"Debug Mode: {DEBUG}")
    logger.info(f"Allowed Hosts: {ALLOWED_HOSTS}")
    logger.info(f"CORS Origins: {CORS_ALLOWED_ORIGINS}")
    logger.info(f"Database: {DATABASES['default']['NAME']}@{DATABASES['default']['HOST']}")
    logger.info(f"Redis: {os.environ.get('REDIS_URL', 'redis://redis:6379/0')}")
    logger.info(f"Email Backend: {EMAIL_BACKEND}")
    logger.info("=" * 60)
