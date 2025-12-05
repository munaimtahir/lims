"""
Development-specific settings for LIMS project.
"""

from .base import *

DEBUG = True

# Email backend for development (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Development-specific middleware
INSTALLED_APPS += [
    'django_extensions',
]

# Detailed logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
