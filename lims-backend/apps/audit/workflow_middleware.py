"""
Enhanced middleware for workflow audit tracing.

Adds:
- Request ID correlation for tracing workflow calls
- Structured JSON logging for workflow transitions
- Timing information for performance analysis
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Context variable for request ID
_request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return _request_id_context.get()


class WorkflowAuditMiddleware(MiddlewareMixin):
    """
    Middleware for workflow audit tracing.
    
    Attaches a unique request_id to each request and logs structured information
    about workflow-related endpoints.
    """
    
    # Endpoints to trace (workflow-critical paths)
    TRACED_ENDPOINTS = [
        '/api/v1/patients/',
        '/api/v1/orders/',
        '/api/v1/samples/',
        '/api/v1/results/',
        '/api/v1/reports/',
    ]
    
    def process_request(self, request):
        """Attach request_id and log request start."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        _request_id_context.set(request_id)
        
        # Store start time for timing
        request._workflow_audit_start = time.time()
        
        # Log request start for traced endpoints
        if self._should_trace(request):
            self._log_request_start(request)
        
        return None
    
    def process_response(self, request, response):
        """Log request completion."""
        if self._should_trace(request):
            duration_ms = (time.time() - getattr(request, '_workflow_audit_start', time.time())) * 1000
            self._log_request_end(request, response, duration_ms)
        
        # Clean up context
        _request_id_context.set(None)
        
        return response
    
    def _should_trace(self, request):
        """Check if request should be traced."""
        path = request.path
        return any(path.startswith(endpoint) for endpoint in self.TRACED_ENDPOINTS)
    
    def _log_request_start(self, request):
        """Log structured request start."""
        log_entry = {
            "event": "request_start",
            "request_id": request.request_id,
            "timestamp": time.time(),
            "method": request.method,
            "path": request.path,
            "tenant": getattr(request, 'tenant', None).__str__() if hasattr(request, 'tenant') else None,
            "user": request.user.username if hasattr(request, 'user') and request.user.is_authenticated else None,
            "user_id": request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
        }
        logger.info(json.dumps(log_entry))
    
    def _log_request_end(self, request, response, duration_ms):
        """Log structured request completion."""
        log_entry = {
            "event": "request_end",
            "request_id": request.request_id,
            "timestamp": time.time(),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "tenant": getattr(request, 'tenant', None).__str__() if hasattr(request, 'tenant') else None,
            "user": request.user.username if hasattr(request, 'user') and request.user.is_authenticated else None,
        }
        logger.info(json.dumps(log_entry))


def log_workflow_span(span_name: str, details: dict = None):
    """
    Log a workflow span for tracing.
    
    Args:
        span_name: Name of the workflow operation (e.g., "update_order_status")
        details: Additional context (e.g., {"order_id": 123, "old_status": "NEW", "new_status": "VERIFIED"})
    """
    request_id = get_request_id()
    
    log_entry = {
        "event": "workflow_span",
        "request_id": request_id,
        "timestamp": time.time(),
        "span_name": span_name,
        "details": details or {},
    }
    logger.info(json.dumps(log_entry))
