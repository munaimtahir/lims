#!/usr/bin/env bash
# ==============================================================================
# Production Deployment Smoke Test
# ==============================================================================
# This script performs basic smoke tests on a deployed instance to verify
# that the frontend and backend are accessible and responding correctly.
#
# Usage:
#   ./scripts/smoke_test.sh [BASE_URL]
#
# Example:
#   ./scripts/smoke_test.sh http://172.237.71.40
#   ./scripts/smoke_test.sh  # defaults to http://172.237.71.40
# ==============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://172.237.71.40}"
TIMEOUT=10

echo -e "${BLUE}=========================================="
echo "Production Smoke Test"
echo "==========================================${NC}"
echo ""
echo "Testing deployment at: ${BASE_URL}"
echo ""

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing ${name}... "
    
    if response=$(curl -fsS --max-time "${TIMEOUT}" -w "\n%{http_code}" "${url}" 2>&1); then
        # Extract status code from last line
        status_code=$(echo "$response" | tail -n1)
        
        if [ "$status_code" = "$expected_status" ]; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP ${status_code})"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (Expected HTTP ${expected_status}, got ${status_code})"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed or timeout)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test function with content check
test_endpoint_content() {
    local name="$1"
    local url="$2"
    local expected_content="$3"
    
    echo -n "Testing ${name}... "
    
    if response=$(curl -fsS --max-time "${TIMEOUT}" "${url}" 2>&1); then
        if echo "$response" | grep -q "$expected_content"; then
            echo -e "${GREEN}✓ PASS${NC} (contains '${expected_content}')"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (Response does not contain '${expected_content}')"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed or timeout)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. Frontend Tests"
echo "----------------------------------------"

# Test 1: Frontend root
test_endpoint "Frontend root (HTML)" "${BASE_URL}/"

# Test 2: Frontend should serve HTML with expected content
test_endpoint_content "Frontend HTML content" "${BASE_URL}/" "<!doctype html>"

echo ""
echo "2. Backend API Tests"
echo "----------------------------------------"

# Test 3: Backend health endpoint (via nginx proxy)
test_endpoint_content "Backend health (via proxy)" "${BASE_URL}/api/health/" "healthy"

# Test 4: Backend auth endpoint should be accessible
test_endpoint "Backend auth endpoint" "${BASE_URL}/api/auth/login/" "405"  # POST-only, so GET returns 405

# Test 5: Verify no double /api/api/ issue
echo -n "Testing no double /api/api/ bug... "
if curl -fsS --max-time "${TIMEOUT}" "${BASE_URL}/api/api/health/" 2>&1 | grep -q "Not Found"; then
    echo -e "${GREEN}✓ PASS${NC} (correctly returns 404 for /api/api/)"
    PASSED=$((PASSED + 1))
else
    response=$(curl -fsS --max-time "${TIMEOUT}" -w "\n%{http_code}" "${BASE_URL}/api/api/health/" 2>&1 || true)
    status_code=$(echo "$response" | tail -n1)
    if [ "$status_code" = "404" ]; then
        echo -e "${GREEN}✓ PASS${NC} (correctly returns 404 for /api/api/)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (double /api/api/ path should not exist)"
        FAILED=$((FAILED + 1))
    fi
fi

echo ""
echo "3. Static Assets Tests"
echo "----------------------------------------"

# Test 6: Admin panel should be accessible (even if requires login)
test_endpoint "Admin panel" "${BASE_URL}/admin/" "200"

echo ""
echo -e "${BLUE}=========================================="
echo "Test Results"
echo "==========================================${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All smoke tests PASSED${NC}"
    echo ""
    echo "Passed: ${PASSED}"
    echo "Failed: ${FAILED}"
    echo ""
    echo -e "${GREEN}Deployment is healthy and ready for use!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some smoke tests FAILED${NC}"
    echo ""
    echo "Passed: ${PASSED}"
    echo "Failed: ${FAILED}"
    echo ""
    echo -e "${RED}Deployment may have issues. Please investigate.${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check service status: docker compose ps"
    echo "  2. Check logs: docker compose logs -f"
    echo "  3. Verify environment: cat .env"
    echo "  4. Check connectivity: curl -v ${BASE_URL}"
    exit 1
fi
