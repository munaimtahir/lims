# LIMS Workflow Call Graph - End-to-End Static Trace

**Generated:** 2026-02-19  
**Purpose:** Complete workflow trace from UI routes → API calls → backend views → services → DB mutations

---

## Table of Contents
1. [Patient Registration Workflow](#1-patient-registration-workflow)
2. [Order Creation Workflow](#2-order-creation-workflow)
3. [Sample Collection Workflow](#3-sample-collection-workflow)
4. [Result Entry Workflow](#4-result-entry-workflow)
5. [Result Verification Workflow](#5-result-verification-workflow)
6. [Report Publishing Workflow](#6-report-publishing-workflow)
7. [Status Transition Summary](#7-status-transition-summary)

---

## 1. Patient Registration Workflow

### 1.1 UI Route
**Path:** `/dashboard/registration`  
**Component:** `/frontend/src/pages/registration/RegistrationPage.tsx`

### 1.2 Primary UI Actions

#### Action 1: Search Existing Patient
**Button:** "Search" (auto-triggered on phone input)  
**Handler:** `handlePhoneChange` (line 82-88)  
**API Client Call:** `patientApi.lookup()` (line 203)

```typescript
// File: /frontend/src/api/patients.ts
lookup: async (params: { mobile?: string; mrn?: string }) => {
  const response = await api.get<Patient[]>('/patients/lookup/', { params });
  return response.data;
}
```

**HTTP Request:**
- **Method:** GET
- **Endpoint:** `/api/v1/patients/lookup/`
- **Query Params:** `{ mobile: "0333-1234567" }`

**Backend View:**  
**File:** `/lims-backend/apps/patients/views.py:277-343`  
**ViewSet:** `PatientViewSet`  
**Action:** `@action(detail=False, methods=['get'])`

```python
def lookup(self, request):
    # Line 277-343: Search by mobile/mrn/name/cnic
    queryset = Patient.objects.filter(tenant=tenant)
    if mobile:
        queryset = queryset.filter(mobile__icontains=mobile)
    # ... additional filters ...
    patients = queryset[:10]
    return Response(serializer.data)
```

**Serializer:** `PatientSerializer` (lines 100, 132)  
**DB Models Touched:**
- **Patient** (SELECT): `id, mobile, full_name, mr_number, cnic, date_of_birth`

**Status Fields Changed:** None (read-only)

---

#### Action 2: Create New Patient
**Button:** "Create Registration" (line 550-561)  
**Handler:** `handleSubmit` (line 227)  
**API Client Call:** `patientApi.create()`

```typescript
// File: /frontend/src/api/patients.ts
create: async (patient: Partial<Patient>) => {
  const response = await api.post<Patient>('/patients/', patient);
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/patients/`
- **Payload:**
```json
{
  "mobile": "0333-1234567",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-01",
  "age_years": 33,
  "age_months": 0,
  "age_days": 0,
  "gender": "M",
  "father_husband_name": "Father Name",
  "cnic": "12345-1234567-1",
  "address": "123 Main St",
  "referred_by": "Dr. Smith",
  "consultant": "Dr. Jones",
  "category": "GENERAL",
  "branch": 1  // if enable_collection_centers is true
}
```

**Backend View:**  
**File:** `/lims-backend/apps/patients/views.py:108-129`  
**ViewSet:** `PatientViewSet`  
**Method:** `create`

```python
def create(self, request, *args, **kwargs):
    # Line 111: Explicitly set ordered_by to current user
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
```

**Serializer:** `PatientSerializer`  
**File:** `/lims-backend/apps/patients/serializers.py`

**Service Functions Called:** 
- Auto-generation of `mr_number` (MRN) via model save
- Auto-generation of `registration_number` via model save

**DB Models Touched:**
- **Patient** (INSERT):
  - `mobile`, `full_name`, `date_of_birth`, `gender`, `cnic`, `address`
  - `mr_number` (auto-generated)
  - `registration_number` (auto-generated)
  - `tenant` (auto-set from request)
  - `branch` (if enabled)
  - `created_by`, `updated_by`

**Status Fields Changed:** None (Patient has no status field)

**Audit Events:** 
- Type: `PATIENT_CREATED`
- File: `/lims-backend/apps/patients/views.py:120`

**Side Effects:**
- Navigate to Create Order page with `patient_id` (frontend line 229)

---

## 2. Order Creation Workflow

### 2.1 UI Route
**Path:** `/dashboard/orders/create`  
**Component:** `/frontend/src/pages/orders/CreateOrderPage.tsx`

### 2.2 Primary UI Actions

#### Action 1: Search Tests/Panels
**Input:** Test search autocomplete (line 74)  
**Handler:** `handleTestSearch` (debounced 200ms)  
**API Client Call:** `laboratoryApi.searchTests()`

```typescript
// File: /frontend/src/api/laboratory.ts
searchTests: async (query: string, limit = 20) => {
  const response = await api.get('/laboratory/tests/search/', {
    params: { q: query, limit }
  });
  return response.data;
}
```

**HTTP Request:**
- **Method:** GET
- **Endpoint:** `/api/v1/laboratory/tests/search/`
- **Query Params:** `{ q: "Albumin", limit: 20 }`

**Backend View:**  
**File:** `/lims-backend/apps/laboratory/views.py:219-312`  
**ViewSet:** `TestViewSet`  
**Action:** `@action(detail=False, methods=['get'])`

```python
def search(self, request):
    # Lines 243-312: Search tests and panels
    query = request.query_params.get('q', '')
    limit = int(request.query_params.get('limit', 50))
    
    tests = Test.objects.filter(
        name__icontains=query,
        is_active=True,
        tenant=tenant
    )[:limit]
    
    panels = TestPanel.objects.filter(
        name__icontains=query,
        is_active=True,
        tenant=tenant
    )[:limit]
    
    return Response({
        'tests': [...],
        'panels': [...]
    })
```

**DB Models Touched:**
- **Test** (SELECT): `id, name, code, price, sample_type, is_active`
- **TestPanel** (SELECT): `id, name, description, total_price, is_active`

**Status Fields Changed:** None (read-only)

---

#### Action 2: Create Order
**Button:** "Create Order" (line 274-280)  
**Handler:** `handleSubmit` (line 100)  
**API Client Call:** `orderApi.create()`

```typescript
// File: /frontend/src/api/orders.ts
create: async (order: Partial<Order>) => {
  const response = await api.post<Order>('/orders/orders/', order);
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/orders/orders/`
- **Payload:**
```json
{
  "patient": 123,
  "test_ids": [1, 2, 3],
  "panel_ids": [4],
  "discount": 500,
  "paid_amount": 2500,
  "referred_by": "Dr. Smith",
  "collection_branch": 1  // if enable_collection_centers is true
}
```

**Backend View:**  
**File:** `/lims-backend/apps/orders/views.py:108-129`  
**ViewSet:** `OrderViewSet`  
**Method:** `create`

```python
def create(self, request, *args, **kwargs):
    # Line 111: Set ordered_by
    serializer = self.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    self.perform_create(serializer)
    headers = self.get_success_headers(serializer.data)
    return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
```

**Serializer:** `OrderSerializer`  
**File:** `/lims-backend/apps/orders/serializers.py`

**Service Functions Called:**
1. Auto-generation of `order_id` (format: `ORD-YYYYMMDD-XXXX`)
2. Auto-generation of `lab_number` if branch enabled
3. Auto-calculation of `total_amount` from test prices
4. Auto-calculation of `net_amount` = total - discount

**DB Models Touched:**

**Order** (INSERT):
```python
# Fields written:
- order_id (auto-generated: "ORD-20260219-0001")
- patient_id (from request)
- status = "NEW"
- total_amount (calculated from tests/panels)
- discount (from request)
- net_amount (total - discount)
- paid_amount (from request)
- is_paid (calculated: paid_amount >= net_amount)
- referred_by (from request)
- collection_branch (if enabled)
- processing_branch (auto-set from user)
- tenant (auto-set from request)
- ordered_by (current user)
- created_by, updated_by
```

**OrderItem** (INSERT - multiple):
```python
# Created for each test/panel:
- order_id
- test_id (or panel_id)
- price (from test/panel)
- status = "NEW" (inherited from order)
- tenant
```

**Payment** (INSERT - if paid_amount > 0):
```python
# Auto-created via Order.update_payment_status():
- order_id
- amount = paid_amount
- payment_method = "CASH" (default)
- paid_by (current user)
- tenant
```

**Status Fields Changed:**
- **Order.status:** `null` → `"NEW"`
- **OrderItem.status:** `null` → `"NEW"` (for each item)

**Audit Events:**
- Type: `ORDER_CREATED`
- Additional: `PAYMENT_RECORDED` if paid_amount > 0

**Side Effects:**
1. **If `is_paid = True`**: Auto-create samples via `ensure_samples_for_paid_order()`
   - File: `/lims-backend/apps/samples/services.py`
   - Creates `Sample` for each `OrderItem` with `status = "PENDING"`

2. Navigate to print receipt or order list (frontend line 102-108)

---

## 3. Sample Collection Workflow

### 3.1 UI Route
**Path:** `/dashboard/collection`  
**Component:** `/frontend/src/pages/collection/CollectionWorklistPage.tsx`

### 3.2 Primary UI Actions

#### Action 1: Get Collection Worklist
**Trigger:** Page load  
**Handler:** `useQuery` (line 247)  
**API Client Call:** `sampleApi.getCollectionWorklist()`

```typescript
// File: /frontend/src/api/samples.ts
getCollectionWorklist: async () => {
  const response = await api.get('/samples/pending_collections/');
  return response.data;
}
```

**HTTP Request:**
- **Method:** GET
- **Endpoint:** `/api/v1/samples/pending_collections/`

**Backend View:**  
**File:** `/lims-backend/apps/samples/views.py:54-76`  
**ViewSet:** `SampleViewSet`  
**Action:** `@action(detail=False, methods=['get'])`

```python
def pending_collections(self, request):
    # Lines 61-68: Filter pending samples
    samples = Sample.objects.filter(
        status__in=[SampleStatus.PENDING, SampleStatus.POSTPONED],
        tenant=request.tenant
    ).select_related(
        'order_item__order__patient',
        'order_item__test'
    ).prefetch_related(...)
    
    serializer = self.get_serializer(samples, many=True)
    return Response(serializer.data)
```

**DB Models Touched:**
- **Sample** (SELECT): All samples with status PENDING or POSTPONED
- **OrderItem** (JOIN)
- **Order** (JOIN)
- **Patient** (JOIN)
- **Test** (JOIN)

**Status Fields Changed:** None (read-only)

---

#### Action 2: Mark Sample as Collected and Received
**Button:** "Confirm & Mark Received" (line 149-160)  
**Handler:** `handleConfirm` (line 313-326)  
**API Client Call:** `sampleApi.updateStatus()`

```typescript
// File: /frontend/src/api/samples.ts
updateStatus: async (id: number, data: UpdateSampleStatusRequest) => {
  const response = await api.patch(`/samples/${id}/`, data);
  return response.data;
}
```

**HTTP Request:**
- **Method:** PATCH
- **Endpoint:** `/api/v1/samples/{id}/`
- **Payload:**
```json
{
  "status": "RECEIVED",
  "barcode": "BAR-001",
  "notes": "Collected at home",
  "collection_source": "Home Collection",
  "collected_at": "2026-02-19T10:30:00Z",
  "received_at": "2026-02-19T10:30:00Z"
}
```

**Backend View:**  
**File:** `/lims-backend/apps/samples/views.py:78-93`  
**ViewSet:** `SampleViewSet`  
**Method:** `perform_update`

```python
def perform_update(self, serializer):
    # Lines 82-93
    sample = serializer.instance
    if 'status' in serializer.validated_data:
        new_status = serializer.validated_data['status']
        transition_sample_state(
            sample=sample,
            new_status=new_status,
            user=self.request.user,
            reason=serializer.validated_data.get('notes')
        )
    serializer.save()
    
    # Ensure test results created
    if sample.status in [SampleStatus.COLLECTED, SampleStatus.RECEIVED]:
        ensure_test_results(sample.order_item)
```

**Service Functions Called:**

1. **`transition_sample_state()`**  
   **File:** `/lims-backend/apps/samples/services.py:84-164`
   ```python
   def transition_sample_state(sample, new_status, user, reason=None):
       # Lines 84-164: Validates transition rules
       valid_transitions = {
           SampleStatus.PENDING: [COLLECTED, POSTPONED],
           SampleStatus.COLLECTED: [RECEIVED, REJECTED],
           SampleStatus.POSTPONED: [COLLECTED, REJECTED],
           SampleStatus.RECEIVED: [REJECTED],
       }
       
       # Set timestamps
       if new_status == SampleStatus.COLLECTED:
           sample.collected_at = timezone.now()
           sample.collected_by = user
       elif new_status == SampleStatus.RECEIVED:
           sample.received_at = timezone.now()
           sample.received_by = user
       
       sample.status = new_status
       sample.save()
       
       emit_audit_event(
           event_type='SAMPLE_STATUS_CHANGED',
           entity_type='sample',
           entity_id=sample.id,
           user=user,
           tenant=sample.tenant,
           details={'old_status': old_status, 'new_status': new_status}
       )
   ```

2. **`ensure_test_results()`**  
   **File:** `/lims-backend/apps/results/services/result_generation.py`
   ```python
   def ensure_test_results(order_item):
       # Create TestResult for each parameter if not exists
       parameters = order_item.test.parameters.all()
       for param in parameters:
           TestResult.objects.get_or_create(
               order_item=order_item,
               test_parameter=param,
               defaults={
                   'status': ResultStatus.DRAFT,
                   'tenant': order_item.tenant
               }
           )
   ```

**DB Models Touched:**

**Sample** (UPDATE):
```python
- status: "PENDING" → "RECEIVED"
- collected_at: null → "2026-02-19T10:30:00Z"
- collected_by: null → user_id
- received_at: null → "2026-02-19T10:30:00Z"
- received_by: null → user_id
- barcode: null → "BAR-001"
- notes: updated
```

**TestResult** (INSERT - multiple):
```python
# One for each TestParameter in the Test:
- order_item_id
- test_parameter_id
- status = "DRAFT"
- tenant
- result_value: null
```

**Order** (UPDATE - cascaded):
```python
# Via OrderWorkflowService._recalculate_order_status()
# Triggered by sample status change
- status: "NEW" → "COLLECTED" (if all samples collected)
        or "NEW" → "IN_PROCESS" (if sample received)
```

**Status Fields Changed:**
- **Sample.status:** `"PENDING"` → `"RECEIVED"`
- **Order.status:** `"NEW"` → `"IN_PROCESS"` (via recalculation)

**Audit Events:**
- Type: `SAMPLE_STATUS_CHANGED`
- Details: `{old_status: "PENDING", new_status: "RECEIVED"}`

**Side Effects:**
1. Query invalidation for collection worklist (frontend line 333-335)
2. Order status recalculation
3. Test results auto-creation

---

## 4. Result Entry Workflow

### 4.1 UI Route
**Path:** `/dashboard/worklist` → `/dashboard/results`  
**Component:** `/frontend/src/pages/worklist/ResultEntryWorklistPage.tsx` → `/frontend/src/pages/results/ResultsPage.tsx`

### 4.2 Primary UI Actions

#### Action 1: Get Result Entry Worklist
**Trigger:** Page load  
**Handler:** `useQuery` (line 14)  
**API Client Call:** `resultApi.getWorklist()`

```typescript
// File: /frontend/src/api/results.ts
getWorklist: async () => {
  const response = await api.get('/results/worklist/');
  return response.data;
}
```

**HTTP Request:**
- **Method:** GET
- **Endpoint:** `/api/v1/results/worklist/`

**Backend View:**  
**File:** `/lims-backend/apps/results/views.py:160-293`  
**ViewSet:** `TestResultViewSet`  
**Action:** `@action(detail=False, methods=['get'])`

```python
def worklist(self, request):
    # Lines 187-239: Complex aggregation query
    # Returns OrderItems that need result entry
    order_items = OrderItem.objects.filter(
        order__status__in=['COLLECTED', 'IN_PROCESS'],
        tenant=tenant
    ).annotate(
        total_params=Count('test__parameters'),
        entered_params=Count(
            'results',
            filter=Q(results__status__in=['ENTERED', 'VERIFIED', 'FINAL'])
        )
    ).filter(
        Q(entered_params=0) |  # No results entered
        Q(entered_params__lt=F('total_params'))  # Partial entry
    )
    
    serializer = OrderItemSerializer(order_items, many=True)
    return Response(serializer.data)
```

**DB Models Touched:**
- **OrderItem** (SELECT with aggregation)
- **Test** (JOIN)
- **TestParameter** (COUNT)
- **TestResult** (COUNT)
- **Order** (JOIN)
- **Patient** (JOIN)

**Status Fields Changed:** None (read-only)

---

#### Action 2: Bulk Result Entry
**Button:** "Save Results" (in ResultsPage)  
**Handler:** `handleSaveResults`  
**API Client Call:** `resultApi.bulkEntry()`

```typescript
// File: /frontend/src/api/results.ts
bulkEntry: async (data: BulkResultEntryRequest) => {
  const response = await api.post('/results/bulk_entry/', data);
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/results/bulk_entry/`
- **Payload:**
```json
{
  "order_item_id": 123,
  "results": [
    {
      "parameter_id": 1,
      "result_value": "4.5",
      "unit": "g/dL",
      "remarks": "Normal range"
    },
    {
      "parameter_id": 2,
      "result_value": "95",
      "unit": "mg/dL"
    }
  ]
}
```

**Backend View:**  
**File:** `/lims-backend/apps/results/views.py:485-613`  
**ViewSet:** `TestResultViewSet`  
**Action:** `@action(detail=False, methods=['post'])`

```python
@action(detail=False, methods=['post'])
def bulk_entry(self, request):
    # Lines 502-613: Create or update results
    with transaction.atomic():
        for result_data in request.data.get('results', []):
            parameter_id = result_data['parameter_id']
            result_value = result_data.get('result_value')
            
            # Find or create result
            result, created = TestResult.objects.get_or_create(
                order_item=order_item,
                test_parameter_id=parameter_id,
                defaults={
                    'status': ResultStatus.DRAFT,
                    'tenant': tenant
                }
            )
            
            # Update result
            result.result_value = result_value
            result.status = ResultStatus.ENTERED
            result.entered_by = request.user
            result.entered_at = timezone.now()
            result.save()
            
            # Emit audit event
            emit_audit_event(
                event_type='RESULT_VALUE_UPDATED',
                entity_type='result',
                entity_id=result.id,
                user=request.user,
                details={'value': result_value, 'parameter': param_name}
            )
        
        # Recompute formulas
        recompute_formulas_for_order_item(order_item)
        
        # Update order item status
        update_order_item_status(order_item)
        
        return Response({'status': 'success'})
```

**Service Functions Called:**

1. **`recompute_formulas_for_order_item()`**  
   **File:** `/lims-backend/apps/results/services/formula_engine.py`
   ```python
   def recompute_formulas_for_order_item(order_item):
       # Calculates derived parameters (e.g., A/G Ratio)
       formula_params = order_item.test.parameters.filter(is_formula=True)
       for param in formula_params:
           value = evaluate_formula(param.formula, order_item)
           result = TestResult.objects.get(
               order_item=order_item,
               test_parameter=param
           )
           result.result_value = value
           result.status = ResultStatus.ENTERED
           result.save()
   ```

2. **`update_order_item_status()`**  
   **File:** `/lims-backend/apps/results/services/transitions.py:216-263`
   ```python
   def update_order_item_status(order_item):
       # Lines 216-263: Derive status from results
       results = order_item.results.all()
       
       if all(r.status == 'FINAL' for r in results):
           order_item.status = 'VERIFIED'
       elif any(r.status in ['VERIFIED', 'ENTERED'] for r in results):
           order_item.status = 'IN_PROCESS'
       else:
           order_item.status = 'NEW'
       
       order_item.save()
       
       # Trigger order recalculation
       OrderWorkflowService._recalculate_order_status(order_item.order)
   ```

**DB Models Touched:**

**TestResult** (INSERT or UPDATE - multiple):
```python
# For each parameter:
- result_value: null → "4.5"
- status: "DRAFT" → "ENTERED"
- entered_by: null → user_id
- entered_at: null → "2026-02-19T11:00:00Z"
- unit: updated
- remarks: updated
```

**OrderItem** (UPDATE):
```python
# Via update_order_item_status():
- status: "NEW" → "IN_PROCESS"
```

**Order** (UPDATE):
```python
# Via _recalculate_order_status():
- status: "IN_PROCESS" (maintained or changed based on all items)
```

**Status Fields Changed:**
- **TestResult.status:** `"DRAFT"` → `"ENTERED"` (for each result)
- **OrderItem.status:** `"NEW"` → `"IN_PROCESS"`
- **Order.status:** Recalculated (typically remains `"IN_PROCESS"`)

**Audit Events:**
- Type: `RESULT_VALUE_UPDATED` (for each parameter)
- Details: `{value: "4.5", parameter: "Albumin"}`

**Side Effects:**
1. Formula recalculation for derived parameters
2. Order item status cascades to order status
3. Query invalidation for worklist

---

## 5. Result Verification Workflow

### 5.1 UI Route
**Path:** `/dashboard/verification`  
**Component:** `/frontend/src/pages/review/VerificationQueuePage.tsx`

### 5.2 Primary UI Actions

#### Action 1: Get Verification Queue
**Trigger:** Page load  
**Handler:** `useQuery` (line 16)  
**API Client Call:** `resultApi.getVerificationQueue()`

```typescript
// File: /frontend/src/api/results.ts
getVerificationQueue: async () => {
  const response = await api.get('/results/verification_queue/');
  return response.data;
}
```

**HTTP Request:**
- **Method:** GET
- **Endpoint:** `/api/v1/results/verification_queue/`

**Backend View:**  
**File:** `/lims-backend/apps/results/views.py:402-482`  
**ViewSet:** `TestResultViewSet`  
**Action:** `@action(detail=False, methods=['get'])`

```python
def verification_queue(self, request):
    # Lines 408-482: Group results by order
    results = TestResult.objects.filter(
        status__in=['ENTERED', 'VERIFIED'],
        order_item__order__status__in=['IN_PROCESS', 'VERIFIED'],
        tenant=tenant
    ).select_related(
        'order_item__order__patient',
        'order_item__test',
        'test_parameter'
    ).order_by('-entered_at')
    
    # Group by order
    orders_map = {}
    for result in results:
        order = result.order_item.order
        if order.id not in orders_map:
            orders_map[order.id] = {
                'order': order,
                'items': [],
                'pending_verification_count': 0
            }
        # ... grouping logic ...
    
    return Response(list(orders_map.values()))
```

**DB Models Touched:**
- **TestResult** (SELECT)
- **OrderItem** (JOIN)
- **Order** (JOIN)
- **Patient** (JOIN)
- **Test** (JOIN)
- **TestParameter** (JOIN)

**Status Fields Changed:** None (read-only)

---

#### Action 2: Verify Single Result
**Button:** "Verify" (line 324-348)  
**Handler:** `handleVerify` (line 54)  
**API Client Call:** `resultApi.verify()`

```typescript
// File: /frontend/src/api/results.ts
verify: async (id: number) => {
  const response = await api.post(`/results/${id}/verify/`);
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/results/{id}/verify/`
- **Payload:** None

**Backend View:**  
**File:** `/lims-backend/apps/results/views.py:689-724`  
**ViewSet:** `TestResultViewSet`  
**Action:** `@action(detail=True, methods=['post'])`

```python
@action(detail=True, methods=['post'])
def verify(self, request, pk=None):
    # Lines 694-724
    result = self.get_object()
    
    # Lock result
    result = TestResult.objects.select_for_update().get(pk=pk)
    
    # Validate status
    if result.status not in [ResultStatus.ENTERED, ResultStatus.READY]:
        raise ValidationError("Only ENTERED/READY results can be verified")
    
    # Transition state
    transition_result_state(
        result=result,
        new_status=ResultStatus.VERIFIED,
        user=request.user
    )
    
    serializer = self.get_serializer(result)
    return Response(serializer.data)
```

**Service Functions Called:**

1. **`transition_result_state()`**  
   **File:** `/lims-backend/apps/results/services/transitions.py:14-116`
   ```python
   def transition_result_state(result, new_status, user):
       # Lines 14-116: Validates transition rules
       valid_transitions = {
           ResultStatus.DRAFT: [ENTERED],
           ResultStatus.ENTERED: [VERIFIED, READY],
           ResultStatus.READY: [VERIFIED],
           ResultStatus.VERIFIED: [FINAL],
           ResultStatus.FINAL: [],  # Immutable
       }
       
       old_status = result.status
       result.status = new_status
       
       # Set verification timestamp
       if new_status == ResultStatus.VERIFIED:
           result.verified_at = timezone.now()
           result.verified_by = user
       
       result.save()
       
       # Emit audit event
       emit_audit_event(
           event_type='RESULT_STATUS_CHANGED',
           entity_type='result',
           entity_id=result.id,
           user=user,
           details={'old_status': old_status, 'new_status': new_status}
       )
       
       # Update order item status
       update_order_item_status(result.order_item)
   ```

**DB Models Touched:**

**TestResult** (UPDATE):
```python
- status: "ENTERED" → "VERIFIED"
- verified_by: null → user_id
- verified_at: null → "2026-02-19T12:00:00Z"
```

**OrderItem** (UPDATE):
```python
# Via update_order_item_status():
- status: "IN_PROCESS" → "VERIFIED" (if all results verified)
```

**Order** (UPDATE):
```python
# Via _recalculate_order_status():
- status: "IN_PROCESS" → "VERIFIED" (if all items verified)
```

**Status Fields Changed:**
- **TestResult.status:** `"ENTERED"` → `"VERIFIED"`
- **OrderItem.status:** `"IN_PROCESS"` → `"VERIFIED"` (if all results done)
- **Order.status:** `"IN_PROCESS"` → `"VERIFIED"` (if all items done)

**Audit Events:**
- Type: `RESULT_STATUS_CHANGED`
- Details: `{old_status: "ENTERED", new_status: "VERIFIED"}`

---

#### Action 3: Bulk Verify Results
**Button:** "Verify All" (line 275)  
**Handler:** `handleVerifyAll` (line 84)  
**API Client Call:** `resultApi.bulkVerify()`

```typescript
// File: /frontend/src/api/results.ts
bulkVerify: async (result_ids: number[]) => {
  const response = await api.post('/results/bulk-verify/', { result_ids });
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/results/bulk-verify/`
- **Payload:**
```json
{
  "result_ids": [1, 2, 3, 4, 5]
}
```

**Backend View:**  
**File:** `/lims-backend/apps/results/views.py:727-768`  
**ViewSet:** `TestResultViewSet`  
**Action:** `@action(detail=False, methods=['post'])`

```python
@action(detail=False, methods=['post'])
def bulk_verify(self, request):
    # Lines 741-768: Bulk verification with transaction
    result_ids = request.data.get('result_ids', [])
    
    with transaction.atomic():
        results = TestResult.objects.select_for_update().filter(
            id__in=result_ids,
            tenant=tenant
        )
        
        for result in results:
            transition_result_state(
                result=result,
                new_status=ResultStatus.VERIFIED,
                user=request.user
            )
        
        return Response({
            'status': 'success',
            'verified_count': len(results)
        })
```

**Service Functions Called:**
- Same as single verify: `transition_result_state()` (called for each result)
- `update_order_item_status()` (called after each result)

**DB Models Touched:**
- **TestResult** (UPDATE - multiple): Same fields as single verify
- **OrderItem** (UPDATE - multiple): Status updated for affected items
- **Order** (UPDATE - multiple): Status recalculated for affected orders

**Status Fields Changed:**
- **TestResult.status:** `"ENTERED"` → `"VERIFIED"` (for each result)
- **OrderItem.status:** Updated based on all its results
- **Order.status:** `"IN_PROCESS"` → `"VERIFIED"` (if all items verified)

**Audit Events:**
- Type: `RESULT_STATUS_CHANGED` (for each result)

---

#### Action 4: Reject/Return Result
**Button:** "Return Order" (line 278)  
**Handler:** `handleReject` (line 71)  
**API Client Call:** `resultApi.reject()`

```typescript
// File: /frontend/src/api/results.ts
reject: async (id: number, reason: string) => {
  const response = await api.post(`/results/${id}/reject/`, { reason });
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/results/{id}/reject/`
- **Payload:**
```json
{
  "reason": "Result value out of expected range, needs re-entry"
}
```

**Backend View:**  
**File:** `/lims-backend/apps/results/views.py:616-657`  
**ViewSet:** `TestResultViewSet`  
**Action:** `@action(detail=True, methods=['post'])`

```python
@action(detail=True, methods=['post'])
def reject(self, request, pk=None):
    # Lines 626-657
    result = self.get_object()
    reason = request.data.get('reason')
    
    if not reason:
        raise ValidationError("Rejection reason is required")
    
    result = TestResult.objects.select_for_update().get(pk=pk)
    
    # Transition back to ENTERED
    transition_result_state(
        result=result,
        new_status=ResultStatus.ENTERED,
        user=request.user
    )
    
    result.verification_notes = reason
    result.save()
    
    serializer = self.get_serializer(result)
    return Response(serializer.data)
```

**Status Fields Changed:**
- **TestResult.status:** `"VERIFIED"` → `"ENTERED"`
- **TestResult.verification_notes:** Updated with reason

**Audit Events:**
- Type: `RESULT_STATUS_CHANGED`
- Details: `{old_status: "VERIFIED", new_status: "ENTERED", reason: "..."}`

---

## 6. Report Publishing Workflow

### 6.1 UI Route
**Path:** `/dashboard/verification` (same as verification)  
**Component:** `/frontend/src/pages/review/VerificationQueuePage.tsx`

### 6.2 Primary UI Actions

#### Action 1: Generate Draft Report (Preview)
**Button:** "Preview" (line 265)  
**Handler:** `handleGenerateReport` (line 158)  
**API Client Call:** `reportApi.generate()`

```typescript
// File: /frontend/src/api/reports.ts
generate: async (data: { order_id: number; is_final: boolean }) => {
  const response = await api.post('/reports/generate/', data);
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/reports/generate/`
- **Payload:**
```json
{
  "order_id": 123,
  "is_final": false
}
```

**Backend View:**  
**File:** `/lims-backend/apps/reports/views.py:320-404`  
**ViewSet:** `ReportViewSet`  
**Action:** `@action(detail=False, methods=['post'])`

```python
@action(detail=False, methods=['post'])
def generate(self, request):
    # Lines 336-398
    order_id = request.data.get('order_id')
    is_final = request.data.get('is_final', False)
    
    # Get order
    order = Order.objects.select_for_update().get(id=order_id, tenant=tenant)
    
    # Validate order status
    if order.status not in ['VERIFIED', 'PUBLISHED']:
        raise ValidationError("Order must be VERIFIED to generate report")
    
    # Check for blockers
    blockers = collect_report_blockers(order)
    if blockers:
        return Response({
            'status': 'blocked',
            'blockers': blockers
        }, status=400)
    
    # Generate PDF
    pdf_file, template_name = generate_v2_report(
        order=order,
        generated_by=request.user
    )
    
    # Create Report record
    report = Report.objects.create(
        order=order,
        report_file=pdf_file,
        template_name=template_name,
        status=ReportStatus.DRAFT,
        generated_by=request.user,
        tenant=tenant
    )
    
    # Transition to FINAL if requested
    if is_final:
        transition_report_state(
            report=report,
            new_status=ReportStatus.FINAL,
            user=request.user
        )
    
    serializer = self.get_serializer(report)
    return Response(serializer.data)
```

**Service Functions Called:**

1. **`collect_report_blockers()`**  
   **File:** `/lims-backend/apps/reports/logic.py`
   ```python
   def collect_report_blockers(order):
       blockers = []
       
       # Check if all results verified
       results = TestResult.objects.filter(order_item__order=order)
       required_results = results.filter(test_parameter__is_required=True)
       
       if required_results.filter(status__lt=ResultStatus.VERIFIED).exists():
           blockers.append("Not all required results are verified")
       
       if not results.filter(status=ResultStatus.VERIFIED).exists():
           blockers.append("No verified results found")
       
       return blockers
   ```

2. **`generate_v2_report()`**  
   **File:** `/lims-backend/apps/reports/logic.py`
   ```python
   def generate_v2_report(order, generated_by):
       # Collect data
       patient = order.patient
       results = TestResult.objects.filter(
           order_item__order=order,
           status__in=[ResultStatus.VERIFIED, ResultStatus.FINAL]
       ).select_related('test_parameter', 'order_item__test')
       
       # Render template
       template = get_template('reports/v2_report.html')
       html_content = template.render({
           'order': order,
           'patient': patient,
           'results': results,
           'generated_by': generated_by,
           'generated_at': timezone.now()
       })
       
       # Generate PDF
       pdf_file = weasyprint.HTML(string=html_content).write_pdf()
       
       # Save to file storage
       filename = f"report_{order.order_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
       file_path = default_storage.save(f"reports/{filename}", pdf_file)
       
       return file_path, 'v2_report.html'
   ```

3. **`transition_report_state()`**  
   **File:** `/lims-backend/apps/reports/services.py`
   ```python
   def transition_report_state(report, new_status, user):
       valid_transitions = {
           ReportStatus.DRAFT: [FINAL, CANCELLED],
           ReportStatus.FINAL: [AMENDED],
           ReportStatus.AMENDED: [],  # Terminal
           ReportStatus.CANCELLED: []  # Terminal
       }
       
       old_status = report.status
       report.status = new_status
       
       if new_status == ReportStatus.FINAL:
           report.verified_by = user
           report.verified_at = timezone.now()
       
       report.save()
       
       emit_audit_event(
           event_type='REPORT_STATUS_CHANGED',
           entity_type='report',
           entity_id=report.id,
           user=user,
           details={'old_status': old_status, 'new_status': new_status}
       )
   ```

**DB Models Touched:**

**Report** (INSERT):
```python
- order_id
- report_file: "reports/report_ORD-20260219-0001_20260219_120000.pdf"
- report_number: "RPT-20260219-0001" (auto-generated)
- template_name: "v2_report.html"
- status: "DRAFT" → "FINAL" (if is_final=true)
- generated_by: user_id
- verified_by: user_id (if is_final=true)
- verified_at: timestamp (if is_final=true)
- tenant
```

**Status Fields Changed:**
- **Report.status:** `null` → `"DRAFT"` → `"FINAL"` (if is_final=true)

**Audit Events:**
- Type: `REPORT_GENERATED`
- Type: `REPORT_STATUS_CHANGED` (if transitioned to FINAL)

---

#### Action 2: Publish Report (Finalize)
**Button:** "Publish Report" (line 268-274)  
**Handler:** `handlePublishReport` (line 183)  
**API Client Call:** `orderApi.publishReport()`

```typescript
// File: /frontend/src/api/orders.ts
publishReport: async (orderId: number) => {
  const response = await api.post(`/orders/orders/${orderId}/publish-report/`);
  return response.data;
}
```

**HTTP Request:**
- **Method:** POST
- **Endpoint:** `/api/v1/orders/orders/{id}/publish-report/`
- **Payload:** None

**Backend View:**  
**File:** `/lims-backend/apps/orders/views.py:291-360`  
**ViewSet:** `OrderViewSet`  
**Action:** `@action(detail=True, methods=['post'])`

```python
@action(detail=True, methods=['post'])
def publish_report(self, request, pk=None):
    # Lines 291-360
    order = self.get_object()
    
    # Lock order
    order = Order.objects.select_for_update().get(pk=pk)
    
    # Validate order status
    if order.status != 'VERIFIED':
        raise ValidationError("Order must be VERIFIED to publish")
    
    # Check for blockers
    blockers = collect_report_blockers(order)
    if blockers:
        return Response({
            'status': 'blocked',
            'blockers': blockers
        }, status=400)
    
    # Generate report if not exists
    report = Report.objects.filter(order=order, status=ReportStatus.FINAL).first()
    if not report:
        pdf_file, template_name = generate_v2_report(order, request.user)
        report = Report.objects.create(
            order=order,
            report_file=pdf_file,
            template_name=template_name,
            status=ReportStatus.DRAFT,
            generated_by=request.user,
            tenant=order.tenant
        )
        
        # Transition to FINAL
        transition_report_state(
            report=report,
            new_status=ReportStatus.FINAL,
            user=request.user
        )
    
    # Transition order to PUBLISHED
    transition_visit_state(
        order=order,
        new_status='PUBLISHED',
        user=request.user
    )
    
    return Response({
        'status': 'success',
        'report_id': report.id,
        'order_status': order.status
    })
```

**Service Functions Called:**
- `collect_report_blockers()` (same as above)
- `generate_v2_report()` (if no FINAL report exists)
- `transition_report_state()` (same as above)
- `transition_visit_state()` (for order status)

**`transition_visit_state()`**  
**File:** `/lims-backend/apps/orders/services.py:14-65`
```python
def transition_visit_state(order, new_status, user):
    valid_transitions = {
        'NEW': ['COLLECTED', 'CANCELLED'],
        'COLLECTED': ['IN_PROCESS', 'CANCELLED'],
        'IN_PROCESS': ['VERIFIED', 'CANCELLED'],
        'VERIFIED': ['PUBLISHED', 'CANCELLED'],
        'PUBLISHED': [],  # Terminal
        'CANCELLED': []  # Terminal
    }
    
    old_status = order.status
    order.status = new_status
    order.save()
    
    emit_audit_event(
        event_type='ORDER_STATUS_CHANGED',
        entity_type='order',
        entity_id=order.id,
        user=user,
        details={'old_status': old_status, 'new_status': new_status}
    )
```

**DB Models Touched:**

**Order** (UPDATE):
```python
- status: "VERIFIED" → "PUBLISHED"
```

**Report** (INSERT if not exists, UPDATE if exists):
```python
# If new:
- All fields as in generate action
- status: "FINAL"

# If exists:
- No change (already FINAL)
```

**Status Fields Changed:**
- **Order.status:** `"VERIFIED"` → `"PUBLISHED"`
- **Report.status:** `"DRAFT"` → `"FINAL"` (if newly created)

**Audit Events:**
- Type: `ORDER_STATUS_CHANGED`
- Details: `{old_status: "VERIFIED", new_status: "PUBLISHED"}`
- Type: `REPORT_STATUS_CHANGED` (if new report created)

**Side Effects:**
1. PDF file generated and saved to storage
2. Report record created with PDF reference
3. Order marked as complete workflow
4. Query invalidation for verification queue and reports list

---

## 7. Status Transition Summary

### 7.1 Order Status Flow

```
NEW → COLLECTED → IN_PROCESS → VERIFIED → PUBLISHED
 ↓        ↓            ↓           ↓
 └────────┴────────────┴───────────┴──→ CANCELLED
```

**Trigger Points:**
- `NEW` → `COLLECTED`: All samples collected (via `_recalculate_order_status`)
- `COLLECTED` → `IN_PROCESS`: Any sample received OR any result entered (via `_recalculate_order_status`)
- `IN_PROCESS` → `VERIFIED`: All required results verified (via `_recalculate_order_status`)
- `VERIFIED` → `PUBLISHED`: Explicit publish action (via `transition_visit_state`)
- Any → `CANCELLED`: Explicit cancellation

**Recalculation Logic:**  
**File:** `/lims-backend/apps/orders/workflow.py`
```python
def _recalculate_order_status(order):
    samples = order.order_items.prefetch_related('samples').all()
    results = TestResult.objects.filter(order_item__order=order)
    
    # Check samples
    all_collected = all(
        sample.status in [SampleStatus.COLLECTED, SampleStatus.RECEIVED]
        for item in samples for sample in item.samples.all()
    )
    
    any_received = any(
        sample.status == SampleStatus.RECEIVED
        for item in samples for sample in item.samples.all()
    )
    
    # Check results
    all_verified = results.filter(
        test_parameter__is_required=True
    ).count() > 0 and results.filter(
        test_parameter__is_required=True,
        status__gte=ResultStatus.VERIFIED
    ).count() == results.filter(test_parameter__is_required=True).count()
    
    # Status logic
    if all_verified:
        order.status = 'VERIFIED'
    elif any_received or results.filter(status__gte=ResultStatus.ENTERED).exists():
        order.status = 'IN_PROCESS'
    elif all_collected:
        order.status = 'COLLECTED'
    else:
        order.status = 'NEW'
    
    order.save()
```

---

### 7.2 Sample Status Flow

```
PENDING → COLLECTED → RECEIVED
   ↓          ↓          ↓
   ↓          └──→ REJECTED
   ↓
   └──→ POSTPONED → COLLECTED → RECEIVED
                        ↓
                        └──→ REJECTED
```

**Transition Rules:**  
**File:** `/lims-backend/apps/samples/services.py:84-164`

---

### 7.3 TestResult Status Flow

```
DRAFT → ENTERED → READY → VERIFIED → FINAL
         ↑                    ↓
         └────────────────────┘
         (reject/return)
```

**Transition Rules:**  
**File:** `/lims-backend/apps/results/services/transitions.py:14-116`

**Note:** `FINAL` is immutable and terminal.

---

### 7.4 Report Status Flow

```
DRAFT → FINAL → AMENDED
  ↓
  └──→ CANCELLED
```

**Transition Rules:**  
**File:** `/lims-backend/apps/reports/services.py`

**Note:** `AMENDED` creates a new report and marks the original. Both become immutable.

---

## Summary Tables

### Complete Workflow Status Changes

| Step | Action | Sample Status | Order Status | Result Status | Report Status |
|------|--------|--------------|--------------|---------------|---------------|
| 1. Order Created | POST /orders/orders/ | - | NEW | - | - |
| 2. Payment Received | POST /payments/ | PENDING (created) | NEW | DRAFT (created) | - |
| 3. Sample Collected | PATCH /samples/{id}/ | PENDING → COLLECTED | NEW → COLLECTED | DRAFT | - |
| 4. Sample Received | PATCH /samples/{id}/ | COLLECTED → RECEIVED | COLLECTED → IN_PROCESS | DRAFT | - |
| 5. Result Entered | POST /results/bulk_entry/ | RECEIVED | IN_PROCESS | DRAFT → ENTERED | - |
| 6. Result Verified | POST /results/{id}/verify/ | RECEIVED | IN_PROCESS → VERIFIED | ENTERED → VERIFIED | - |
| 7. Report Generated (Preview) | POST /reports/generate/ | RECEIVED | VERIFIED | VERIFIED | null → DRAFT |
| 8. Report Published | POST /orders/{id}/publish-report/ | RECEIVED | VERIFIED → PUBLISHED | VERIFIED → FINAL | DRAFT → FINAL |

---

### DB Mutations Per Action

| Action | Models Touched | Fields Written | Rows |
|--------|----------------|----------------|------|
| Create Patient | Patient | 15+ fields + auto MRN | 1 INSERT |
| Create Order | Order, OrderItem, Payment | order_id, status, items, payment | 1+N+1 INSERTs |
| Pay Order | Payment, Sample, TestResult | payment, samples, results | 1+N+M INSERTs |
| Collect Sample | Sample, Order | status, collected_at/by | 1+1 UPDATEs |
| Receive Sample | Sample, Order | status, received_at/by | 1+1 UPDATEs |
| Enter Results | TestResult, OrderItem, Order | result_value, status, entered_at/by | N UPDATEs |
| Verify Result | TestResult, OrderItem, Order | status, verified_at/by | 1+1+1 UPDATEs |
| Bulk Verify | TestResult, OrderItem, Order | status, verified_at/by | N+M+K UPDATEs |
| Publish Report | Report, Order | report_file, status | 1 INSERT + 1 UPDATE |

---

**END OF WORKFLOW_CALL_GRAPH.md**
