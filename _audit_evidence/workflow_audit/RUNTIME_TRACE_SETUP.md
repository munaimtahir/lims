# Runtime Trace Instrumentation - Setup Guide

**Generated:** 2026-02-19  
**Purpose:** Document runtime tracing implementation for workflow audit

---

## Overview

Runtime tracing has been added to the LIMS workflow to enable correlation-based debugging and audit trail analysis. The implementation is:
- **Lightweight:** Minimal performance overhead
- **Safe:** No business logic changes
- **Additive:** Can be removed without breaking existing functionality
- **Structured:** JSON-formatted logs for easy parsing

---

## Components Added

### 1. Workflow Audit Middleware

**File:** `/lims-backend/apps/audit/workflow_middleware.py`

**Features:**
- Generates unique `request_id` (UUID) for each HTTP request
- Stores `request_id` in context variable accessible to all service layers
- Logs structured JSON for workflow-critical endpoints
- Tracks request timing (duration in milliseconds)
- Captures tenant, user, and endpoint information

**Traced Endpoints:**
```python
TRACED_ENDPOINTS = [
    '/api/v1/patients/',
    '/api/v1/orders/',
    '/api/v1/samples/',
    '/api/v1/results/',
    '/api/v1/reports/',
]
```

**Usage:**
```python
from apps.audit.workflow_middleware import get_request_id, log_workflow_span

# Get current request ID
request_id = get_request_id()  # Returns UUID or None

# Log a workflow span
log_workflow_span("operation_name", {
    "key": "value",
    "order_id": "ORD-20260219-0001"
})
```

---

### 2. Service Layer Instrumentation

**Modified Files:**
- `/lims-backend/apps/orders/workflow.py`
- `/lims-backend/apps/results/services/transitions.py`

**Instrumented Functions:**
- `OrderWorkflowService.receive_sample()` - Sample receipt workflow
- `OrderWorkflowService._recalculate_order_status()` - Order status aggregation
- `OrderWorkflowService._transition_order()` - Order status transition
- `update_order_item_status()` - OrderItem status derivation

**Example Instrumentation:**
```python
# Before transition
log_workflow_span("receive_sample", {
    "sample_id": sample_id,
    "old_status": old_status,
    "new_status": "RECEIVED",
    "user": user.username if user else None,
    "location": location
})
```

---

### 3. Logging Configuration

**File:** `/lims-backend/config/settings/audit.py`

**Handler:**
```python
'workflow_trace': {
    'level': 'INFO',
    'class': 'logging.FileHandler',
    'filename': '_audit_evidence/workflow_audit/RUNTIME_TRACE.jsonl',
    'formatter': 'json',
}
```

**Loggers:**
- `apps.audit.workflow_middleware` - Request/response logging
- `apps.orders.workflow` - Order workflow operations
- `apps.results.services.transitions` - Result transitions

**Output Location:** `/_audit_evidence/workflow_audit/RUNTIME_TRACE.jsonl`

---

## Log Entry Schema

### Request Start
```json
{
  "event": "request_start",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1708304400.123,
  "method": "POST",
  "path": "/api/v1/samples/123/",
  "tenant": "main-hospital",
  "user": "admin",
  "user_id": 1
}
```

### Request End
```json
{
  "event": "request_end",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1708304400.456,
  "method": "POST",
  "path": "/api/v1/samples/123/",
  "status_code": 200,
  "duration_ms": 333.45,
  "tenant": "main-hospital",
  "user": "admin"
}
```

### Workflow Span
```json
{
  "event": "workflow_span",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1708304400.234,
  "span_name": "receive_sample",
  "details": {
    "sample_id": "SAM-001",
    "old_status": "COLLECTED",
    "new_status": "RECEIVED",
    "user": "lab_tech",
    "location": "main_lab"
  }
}
```

### Order Status Recalculation
```json
{
  "event": "workflow_span",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1708304400.345,
  "span_name": "recalculate_order_status",
  "details": {
    "order_id": "ORD-20260219-0001",
    "old_status": "COLLECTED",
    "new_status": "IN_PROCESS",
    "samples_count": 2,
    "samples_received": 2,
    "results_count": 5,
    "results_verified": 0
  }
}
```

### Order Status Transition
```json
{
  "event": "workflow_span",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1708304400.456,
  "span_name": "transition_order",
  "details": {
    "order_id": "ORD-20260219-0001",
    "old_status": "COLLECTED",
    "new_status": "IN_PROCESS",
    "user": "system"
  }
}
```

---

## Activation Instructions

### For Development/Testing

1. **Use audit settings:**
```bash
cd lims-backend
export DJANGO_SETTINGS_MODULE=config.settings.audit
python manage.py migrate
python manage.py runserver
```

2. **Verify middleware loaded:**
```bash
python manage.py shell
>>> from django.conf import settings
>>> 'apps.audit.workflow_middleware.WorkflowAuditMiddleware' in settings.MIDDLEWARE
True
```

3. **Test workflow operation:**
```bash
# Trigger a sample receipt via API
curl -X PATCH http://localhost:8000/api/v1/samples/1/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"status": "RECEIVED"}'

# Check trace file
cat _audit_evidence/workflow_audit/RUNTIME_TRACE.jsonl | tail -10
```

### For Production (Optional)

**WARNING:** Only enable in production if performance impact is acceptable.

1. **Add to production settings:**
```python
# In config/settings/production.py
MIDDLEWARE = [
    ...
    'apps.audit.middleware.AuditLoggingMiddleware',
    'apps.audit.workflow_middleware.WorkflowAuditMiddleware',  # Add this
    ...
]

# Add logging configuration
LOGGING['handlers']['workflow_trace'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': '/var/log/lims/workflow_trace.jsonl',
    'maxBytes': 100 * 1024 * 1024,  # 100MB
    'backupCount': 10,
}
```

2. **Monitor log file size:**
```bash
# Set up log rotation
sudo logrotate -f /etc/logrotate.d/lims-workflow-trace
```

---

## Analysis Examples

### 1. Trace Single Request
```bash
# Find all events for a request_id
cat RUNTIME_TRACE.jsonl | grep '"request_id": "550e8400-e29b-41d4-a716-446655440000"'
```

### 2. Track Order Status Changes
```bash
# Find all status transitions for an order
cat RUNTIME_TRACE.jsonl | grep '"order_id": "ORD-20260219-0001"' | grep transition_order
```

### 3. Measure Performance
```bash
# Find slow requests (>1000ms)
cat RUNTIME_TRACE.jsonl | jq 'select(.duration_ms > 1000)'
```

### 4. User Activity Audit
```bash
# Find all operations by a user
cat RUNTIME_TRACE.jsonl | jq 'select(.user == "admin")'
```

### 5. Workflow Bottleneck Analysis
```bash
# Group by span_name and count
cat RUNTIME_TRACE.jsonl | jq -r '.span_name' | sort | uniq -c | sort -rn
```

---

## Performance Impact

**Benchmarks (estimated):**
- Middleware overhead: ~1-2ms per request
- `log_workflow_span()` call: ~0.5ms per call
- Log file write: ~0.1ms per line (async)

**Total overhead:** ~2-5ms per workflow request (negligible)

**Disk usage:** ~1-2MB per 1000 requests

---

## Removal Instructions

If tracing needs to be disabled:

1. **Remove middleware from settings:**
```python
# Remove from MIDDLEWARE list
'apps.audit.workflow_middleware.WorkflowAuditMiddleware',
```

2. **Remove logging configuration:**
```python
# Remove from LOGGING['handlers']
'workflow_trace': { ... }

# Remove from LOGGING['loggers']
'apps.audit.workflow_middleware': { ... }
```

3. **Remove log_workflow_span() calls (optional):**
```bash
# Find all calls
grep -r "log_workflow_span" lims-backend/apps/

# Remove or comment out
# log_workflow_span("operation", {...})
```

**Note:** Middleware and logging config can be removed immediately. Service layer instrumentation can be left in place (becomes no-op if middleware not loaded).

---

## Future Enhancements

### Recommended Additions

1. **OpenTelemetry Integration:**
   - Replace custom middleware with OpenTelemetry
   - Export traces to Jaeger/Zipkin for visualization
   - Add distributed tracing across frontend/backend

2. **Sampling:**
   - Only trace 10% of requests in production
   - Trace 100% of errors/slow requests

3. **Metrics:**
   - Track workflow operation counts (Prometheus)
   - Alert on abnormal status transitions

4. **Correlation with Audit Events:**
   - Link `request_id` to `AuditLog` entries
   - Enable full request→audit trail correlation

---

## Troubleshooting

### No logs generated
**Check:**
1. Middleware in MIDDLEWARE list?
2. LOGGING configuration present?
3. Directory `_audit_evidence/workflow_audit/` exists?
4. Write permissions on log file?

### request_id is None in spans
**Check:**
1. Middleware loaded before service calls?
2. Operation triggered via HTTP request (not management command)?

### Log file growing too large
**Solutions:**
1. Use `RotatingFileHandler` instead of `FileHandler`
2. Set `maxBytes` and `backupCount`
3. Add logrotate configuration
4. Enable sampling (only trace subset of requests)

---

**END OF RUNTIME_TRACE_SETUP.md**
