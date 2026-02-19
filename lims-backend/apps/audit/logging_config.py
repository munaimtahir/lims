"""
Logging configuration for workflow audit tracing.

Add this to Django settings to enable JSON logging to RUNTIME_TRACE.jsonl:

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'workflow_trace': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '_audit_evidence/workflow_audit/RUNTIME_TRACE.jsonl',
            'formatter': 'json',
        },
    },
    'loggers': {
        'apps.audit.workflow_middleware': {
            'handlers': ['workflow_trace'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.orders.workflow': {
            'handlers': ['workflow_trace'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.results.services.transitions': {
            'handlers': ['workflow_trace'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
"""

# This file documents the logging configuration
# Actual implementation should be added to settings/base.py or settings/audit.py
