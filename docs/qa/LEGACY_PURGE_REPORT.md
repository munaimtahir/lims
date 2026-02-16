# Legacy Purge Report

## Canonical Status Vocabulary

### Order Status (Order.STATUS_CHOICES)
- `NEW`
- `COLLECTED`
- `IN_PROCESS`
- `VERIFIED`
- `PUBLISHED`
- `CANCELLED`

### Test Result Status (TestResult.VERIFICATION_STATUS)
- `DRAFT`
- `ENTERED`
- `VERIFIED`
- `FINAL`

### Sample Status (SampleStatus)
- `PENDING`
- `COLLECTED`
- `RECEIVED`
- `REJECTED`
- `POSTPONED`

## Legacy Artifacts Identified

### Models
- `apps.samples.models.SampleCollection`: Explicitly marked as DEPRECATED and kept for backward compatibility. Uses lowercase statuses (`pending`, `collected`, `received`, `rejected`).

### Potential Logic
- Need to check for `normalize_status` or similar functions in services.
- Need to check for lowercase string literals in serializers/tests.
