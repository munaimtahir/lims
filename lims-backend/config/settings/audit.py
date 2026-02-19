import os
import tempfile

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

# Use temporary directory for media during audit/tests to avoid permission issues
MEDIA_ROOT = tempfile.mkdtemp()
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Avoid production DB password check if production is imported (though we shouldn't really import production here)
DB_PASSWORD = os.environ.get("DB_PASSWORD", "audit_pass")

# Workflow Audit Tracing
# Add workflow audit middleware
if 'apps.audit.middleware.AuditLoggingMiddleware' in MIDDLEWARE:
    # Add workflow middleware after audit middleware
    idx = MIDDLEWARE.index('apps.audit.middleware.AuditLoggingMiddleware')
    MIDDLEWARE.insert(idx + 1, 'apps.audit.workflow_middleware.WorkflowAuditMiddleware')

# Workflow trace logging configuration
AUDIT_EVIDENCE_DIR = os.path.join(BASE_DIR.parent, '_audit_evidence', 'workflow_audit')
os.makedirs(AUDIT_EVIDENCE_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'workflow_trace': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(AUDIT_EVIDENCE_DIR, 'RUNTIME_TRACE.jsonl'),
            'formatter': 'json',
        },
    },
    'loggers': {
        'apps.audit.workflow_middleware': {
            'handlers': ['workflow_trace', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.orders.workflow': {
            'handlers': ['workflow_trace', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.results.services.transitions': {
            'handlers': ['workflow_trace', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

