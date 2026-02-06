# Results Form Fix - Technical Handover

## Issue Summary
**Problem**: Result form not loading - showing "Initializing form..." indefinitely
**Error**: HTTP 405 Method Not Allowed on `/api/v1/results/ensure/` endpoint

## Root Cause
The frontend was making a **GET** request to `/api/v1/results/ensure/?order_item_id=1`, but the backend endpoint only accepts **POST** requests (as indicated by the server response: `allow: POST, OPTIONS`).

## Technical Details

### Backend Configuration (Correct)
File: `/lims-backend/apps/results/views.py`
```python
@action(detail=False, methods=["post"])  # ✓ POST only
def ensure(self, request):
    """Ensure result rows exist for an order item."""
    order_item = self._get_order_item_from_request(request)
    results = ensure_test_results(order_item)
    serializer = self.get_serializer(results, many=True)
    return Response({"results": serializer.data})
```

The `_get_order_item_from_request` method already handles both query params and request body:
```python
order_item_id = request.query_params.get("order_item_id") or request.data.get("order_item_id")
```

### Frontend Fix Applied
File: `/frontend/src/api/services/resultApi.ts`

**Before (Incorrect)**:
```typescript
getByOrderItem: (orderItemId: number) => 
  apiClient.get<{ results: TestResult[] }>(`/results/ensure?order_item_id=${orderItemId}`),
```

**After (Fixed)**:
```typescript
getByOrderItem: (orderItemId: number) => 
  apiClient.post<{ results: TestResult[] }>('/results/ensure/', { order_item_id: orderItemId }),
```

### Additional Improvements
File: `/frontend/src/pages/results/ResultsPage.tsx`

Added error handling to display API errors to users:
```typescript
const { data, isLoading, isError, error } = useQuery({
  queryKey: ['results', orderItemId],
  queryFn: () => resultApi.getByOrderItem(orderItemId),
  enabled: !!orderItemId,
});

// Display error message if API call fails
if (isError) return <div className={styles.message} style={{ color: '#ef4444' }}>
  Error: {(error as Error).message}
</div>;
```

## Changes Made

### 1. Frontend API Service
- **File**: `/frontend/src/api/services/resultApi.ts`
- **Change**: Changed `getByOrderItem` from GET to POST method
- **Impact**: Now correctly calls the backend endpoint

### 2. Frontend Results Page
- **File**: `/frontend/src/pages/results/ResultsPage.tsx`
- **Change**: Added error state handling and display
- **Impact**: Users now see meaningful error messages instead of infinite loading

### 3. Docker Rebuild
- **Action**: Rebuilt frontend Docker image with `--no-cache` flag
- **Command**: `docker compose --env-file .env.production build --no-cache frontend`
- **Action**: Recreated frontend container
- **Command**: `docker compose --env-file .env.production up -d frontend`

## Verification Steps

1. **Navigate to Results Page**: Go to the results worklist
2. **Click "Enter Results"**: Select any order item
3. **Expected Behavior**: 
   - Form should load with all test parameters
   - No longer shows "Initializing form..." indefinitely
   - If there's an error, it displays a clear error message

## API Contract

### Endpoint: `/api/v1/results/ensure/`
- **Method**: POST (only)
- **Request Body**: 
  ```json
  {
    "order_item_id": 1
  }
  ```
- **Response**: 
  ```json
  {
    "results": [
      {
        "id": 1,
        "test_parameter": 1,
        "parameter_name": "Hemoglobin",
        "result_value": "",
        "unit": "g/dL",
        "status": "DRAFT",
        ...
      }
    ]
  }
  ```

## Deployment Status
- ✅ Code changes committed
- ✅ Frontend Docker image rebuilt
- ✅ Frontend container recreated and running
- ✅ Changes are live on production

## Testing Recommendations

1. **Happy Path**: Enter results for a normal order item
2. **Error Handling**: Try with invalid order_item_id to verify error display
3. **Network Issues**: Test with slow network to ensure loading states work
4. **Multiple Parameters**: Test with panels that have many parameters

## Related Files
- `/frontend/src/api/services/resultApi.ts` - API service definitions
- `/frontend/src/pages/results/ResultsPage.tsx` - Results page component
- `/lims-backend/apps/results/views.py` - Backend endpoint implementation
- `/lims-backend/apps/results/services/expected_results.py` - Result creation logic

## Notes
- The backend was already correctly configured to accept POST requests
- The issue was purely a frontend API client misconfiguration
- Error handling improvements will help diagnose future API issues faster
