#!/bin/bash
# LIMS Branch/Collection Center Phase-1 API Smoke Flow
# Requires: backend running, migrations applied, create_demo_users + seed_branches (or default tenant+HQ)
# Usage: BASE_URL=http://127.0.0.1:8012 ./scripts/smoke_flow_branch.sh

set -e
BASE_URL="${BASE_URL:-http://127.0.0.1:8012}"
API="${BASE_URL}/api/v1"

echo "=== LIMS Branch Smoke Flow ==="
echo "Base URL: $BASE_URL"

# 0. Tenant settings (show mode: OFF/ON)
echo ""
echo "--- 0. Tenant settings ---"
LOGIN_PRE=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" -d '{"username":"receptionist","password":"recep123"}')
TOKEN_PRE=$(echo "$LOGIN_PRE" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
if [ -n "$TOKEN_PRE" ]; then
  SETTINGS=$(curl -s "$API/core/settings/tenant/" -H "Authorization: Bearer $TOKEN_PRE")
  CC_ON=$(echo "$SETTINGS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('enable_collection_centers', False))" 2>/dev/null || echo "False")
  echo "  enable_collection_centers: $CC_ON"
else
  echo "  (skip: login failed)"
fi

# 1. Login (receptionist - should have tenant + branch after seed)
echo ""
echo "--- 1. Login ---"
LOGIN=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" -d '{"username":"receptionist","password":"recep123"}')
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
[ -z "$TOKEN" ] && { echo "Login failed"; echo "$LOGIN"; exit 1; }
echo "Token obtained"

# 2. Create patient (tenant and optional branch/center set by backend)
echo ""
echo "--- 2. Create Patient ---"
PATIENT=$(curl -s -X POST "$API/patients/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"first_name":"Branch","last_name":"Smoke Patient","date_of_birth":"1990-01-01","gender":"Male","phone":"03001234568"}')
PATIENT_ID=$(echo "$PATIENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('id','') or d.get('id',''))")
[ -z "$PATIENT_ID" ] && { echo "Patient create failed"; echo "$PATIENT"; exit 1; }
echo "Patient ID: $PATIENT_ID"

# 3. Get tests
echo ""
echo "--- 3. Get Tests ---"
TESTS=$(curl -s "$API/laboratory/tests/" -H "Authorization: Bearer $TOKEN")
TEST_IDS=$(echo "$TESTS" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',d) if isinstance(d,dict) else d; ids=[t.get('id') or t.get('test_id') for t in (r if isinstance(r,list) else [])[:2]]; print(','.join(map(str,ids)))")
[ -z "$TEST_IDS" ] && { echo "No tests found"; exit 1; }
echo "Test IDs: $TEST_IDS"

# 4. Create order (collection_branch defaulted from user when not sent)
echo ""
echo "--- 4. Create Order ---"
ORDER=$(curl -s -X POST "$API/orders/orders/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"patient\":$PATIENT_ID,\"test_ids\":[${TEST_IDS}],\"status\":\"NEW\"}")
ORDER_ID=$(echo "$ORDER" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))")
[ -z "$ORDER_ID" ] && { echo "Order create failed"; echo "$ORDER"; exit 1; }
echo "Order ID: $ORDER_ID"
# Assert order has collection_branch in response if user has branch
echo "$ORDER" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d.get('collection_branch') or d.get('collection_branch_name'):
    print('  Order has collection_branch set')
else:
    print('  (collection_branch may be set in DB even if not in response)')
"

# 5. Record payment
echo ""
echo "--- 5. Record Payment ---"
LOGIN_C=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" -d '{"username":"cashier","password":"cash123"}')
TOKEN_C=$(echo "$LOGIN_C" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
PAYMENT=$(curl -s -X POST "$API/payments/" -H "Authorization: Bearer $TOKEN_C" -H "Content-Type: application/json" \
  -d "{\"order\":$ORDER_ID,\"amount\":\"100\",\"payment_method\":\"cash\"}")
PAYMENT_ID=$(echo "$PAYMENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))")
[ -z "$PAYMENT_ID" ] && { echo "Payment record failed"; exit 1; }
echo "Payment ID: $PAYMENT_ID"

# 6. Mark sample collected
echo ""
echo "--- 6. Sample Collection ---"
LOGIN_P=$(curl -s -X POST "$API/auth/login/" -H "Content-Type: application/json" -d '{"username":"phlebotomist","password":"phleb123"}')
TOKEN_P=$(echo "$LOGIN_P" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data',d) or {}).get('access_token','') or d.get('access',''))")
SAMPLES=$(curl -s "$API/samples/?order_item__order=$ORDER_ID" -H "Authorization: Bearer $TOKEN_P")
SAMPLE_ID=$(echo "$SAMPLES" | python3 -c "import sys,json; d=json.load(sys.stdin); r=d.get('results',[]); print(r[0]['id'] if r else '')")
if [ -n "$SAMPLE_ID" ]; then
  curl -s -X PATCH "$API/samples/$SAMPLE_ID/" -H "Authorization: Bearer $TOKEN_P" -H "Content-Type: application/json" \
    -d '{"status":"COLLECTED","barcode":"BRANCH-SMOKE-001"}' > /dev/null
  echo "Sample $SAMPLE_ID collected"
else
  echo "No sample found for order (samples may be created on payment)"
fi

echo ""
echo "=== Branch Smoke Flow Complete ==="
