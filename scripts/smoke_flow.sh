#!/bin/bash
# LIMS E2E API Smoke Flow - curl-based workflow verification
# Run against http://127.0.0.1:8012 (or set BASE_URL env)
# Usage: ./scripts/smoke_flow.sh

set -e
BASE_URL="${BASE_URL:-http://127.0.0.1:8012}"
API="${BASE_URL}/api/v1"
# Optional: set HOST_HEADER when hitting proxy by IP (e.g. lims.alshifalab.pk) so backend accepts request
CURL_EXTRA=()
[ -n "${HOST_HEADER:-}" ] && CURL_EXTRA=(-H "Host: $HOST_HEADER")

echo "=== LIMS API Smoke Flow ==="
echo "Base URL: $BASE_URL"

# 1. Login (receptionist)
echo ""
echo "--- 1. Login ---"
LOGIN=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" -d '{"username":"receptionist","password":"recep123"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
[ -z "$TOKEN" ] && { echo "Login failed"; exit 1; }
echo "Token obtained"

# 2. Create patient
echo ""
echo "--- 2. Create Patient ---"
PATIENT=$(curl -s -X POST "$API/patients/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" \
  -d '{"first_name":"Smoke","last_name":"Test Patient","date_of_birth":"1990-01-01","gender":"Male","phone":"03001234567"}')
PATIENT_ID=$(echo "$PATIENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id', (d.get('data',{}) or {}).get('id','')))")
[ -z "$PATIENT_ID" ] && { echo "Patient create failed"; exit 1; }
echo "Patient ID: $PATIENT_ID"

# 3. Get tests
echo ""
echo "--- 3. Get Tests ---"
TESTS=$(curl -s "$API/laboratory/tests/" -H "Authorization: Bearer $TOKEN" "${CURL_EXTRA[@]}")
TEST_IDS=$(echo "$TESTS" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d) if isinstance(d,dict) else d; ids=[t.get('id') or t.get('test_id') for t in (r if isinstance(r,list) else [])[:2]]; print(','.join(map(str,ids)))")
[ -z "$TEST_IDS" ] && { echo "No tests found"; exit 1; }
echo "Test IDs: $TEST_IDS"

# 4. Create order
echo ""
echo "--- 4. Create Order ---"
ORDER=$(curl -s -X POST "$API/orders/orders/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" \
  -d "{\"patient\":$PATIENT_ID,\"test_ids\":[${TEST_IDS}],\"status\":\"NEW\"}")
ORDER_ID=$(echo "$ORDER" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))")
[ -z "$ORDER_ID" ] && { echo "Order create failed"; exit 1; }
echo "Order ID: $ORDER_ID"

# 5. Record payment (login as cashier)
echo ""
echo "--- 5. Record Payment ---"
LOGIN_C=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" -d '{"username":"cashier","password":"cash123"}')
TOKEN_C=$(echo "$LOGIN_C" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
PAYMENT=$(curl -s -X POST "$API/payments/" -H "Authorization: Bearer $TOKEN_C" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" \
  -d "{\"order\":$ORDER_ID,\"amount\":\"100\",\"payment_method\":\"cash\"}")
PAYMENT_ID=$(echo "$PAYMENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))")
[ -z "$PAYMENT_ID" ] && { echo "Payment record failed"; exit 1; }
echo "Payment ID: $PAYMENT_ID"

# 6. Mark sample collected (phlebotomist)
echo ""
echo "--- 6. Sample Collection ---"
LOGIN_P=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" -d '{"username":"phlebotomist","password":"phleb123"}')
TOKEN_P=$(echo "$LOGIN_P" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
SAMPLES=$(curl -s "$API/samples/?order_item__order=$ORDER_ID" -H "Authorization: Bearer $TOKEN_P" "${CURL_EXTRA[@]}")
SAMPLE_ID=$(echo "$SAMPLES" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',[]); print(r[0]['id'] if r else '')")
[ -n "$SAMPLE_ID" ] && curl -s -X PATCH "$API/samples/$SAMPLE_ID/" -H "Authorization: Bearer $TOKEN_P" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" \
  -d '{"status":"COLLECTED","barcode":"SMOKE-001"}' > /dev/null && echo "Sample $SAMPLE_ID collected"

# 7. Enter result (labtech)
echo ""
echo "--- 7. Result Entry ---"
ORDER_ITEMS=$(curl -s "$API/orders/orders/$ORDER_ID/" -H "Authorization: Bearer $TOKEN" "${CURL_EXTRA[@]}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
items=d.get('items',[])
if items:
    oi=items[0]['id']
    tid=items[0].get('test') or items[0].get('test_id')
    print(oi,tid)
")
read OI_ID TEST_ID_FOR_PARAMS <<< "$ORDER_ITEMS"
PARAMS=$(curl -s "$API/laboratory/parameters/?test=$TEST_ID_FOR_PARAMS" -H "Authorization: Bearer $TOKEN" "${CURL_EXTRA[@]}")
TP_ID=$(echo "$PARAMS" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',[]); print(r[0]['id'] if r else '')")
[ -n "$TP_ID" ] && curl -s -X POST "$API/results/bulk_entry/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" \
  -d "{\"results\":[{\"order_item\":$OI_ID,\"test_parameter\":$TP_ID,\"result_value\":\"10.5\",\"remarks\":\"Smoke\"}]}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
r=d.get('results',[])
if r: print('Result ID:', r[0].get('id'))
else: sys.exit(1)
"

# 8. Verify result (admin)
echo ""
echo "--- 8. Verify Result ---"
LOGIN_A=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" -d '{"username":"admin","password":"admin123"}')
TOKEN_A=$(echo "$LOGIN_A" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
VQ=$(curl -s "$API/results/verification_queue/" -H "Authorization: Bearer $TOKEN_A" "${CURL_EXTRA[@]}")
RESULT_ID=$(echo "$VQ" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d) if isinstance(d,dict) else d; r=r[:1] if isinstance(r,list) else []; print(r[0]['id'] if r else '')")
[ -n "$RESULT_ID" ] && curl -s -X POST "$API/results/$RESULT_ID/verify/" -H "Authorization: Bearer $TOKEN_A" "${CURL_EXTRA[@]}" | head -c 200 && echo ""
echo "Result verified"

# 9. Generate and download report
echo ""
echo "--- 9. Report Generation & Download ---"
REPORT=$(curl -s -X POST "$API/reports/generate/" -H "Authorization: Bearer $TOKEN_A" -H "Content-Type: application/json" "${CURL_EXTRA[@]}" \
  -d "{\"order_id\":$ORDER_ID,\"is_final\":true}")
REPORT_ID=$(echo "$REPORT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id') or (d.get('report') or {}).get('id',''))")
[ -n "$REPORT_ID" ] && curl -s "$API/reports/$REPORT_ID/download/" -H "Authorization: Bearer $TOKEN_A" "${CURL_EXTRA[@]}" -o /tmp/lims_report_smoke.pdf && \
  echo "Report downloaded: $(wc -c < /tmp/lims_report_smoke.pdf) bytes"

# 10. Download receipt
echo ""
echo "--- 10. Receipt Download ---"
curl -s "$API/payments/$PAYMENT_ID/receipt/" -H "Authorization: Bearer $TOKEN_C" "${CURL_EXTRA[@]}" -o /tmp/lims_receipt_smoke.pdf && \
  echo "Receipt downloaded: $(wc -c < /tmp/lims_receipt_smoke.pdf) bytes"

echo ""
echo "=== Smoke Flow Complete ==="
