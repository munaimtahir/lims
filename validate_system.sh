#!/bin/bash

# LIMS System Validation Script
# This script validates that all components of the LIMS are properly configured

set -e  # Exit on error

echo "🔬 LIMS System Validation"
echo "========================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking Backend..."
echo "   -------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    check_pass "Python installed: $PYTHON_VERSION"
else
    check_fail "Python 3 not found"
fi

# Check backend directory structure
if [ -d "lims-backend" ]; then
    check_pass "Backend directory exists"
else
    check_fail "Backend directory not found"
fi

# Check backend files
if [ -f "lims-backend/manage.py" ]; then
    check_pass "Django project configured"
else
    check_fail "manage.py not found"
fi

# Check backend apps
APPS=("accounts" "patients" "orders" "samples" "results" "reports" "billing" "audit" "dashboard" "laboratory")
for app in "${APPS[@]}"; do
    if [ -d "lims-backend/apps/$app" ]; then
        check_pass "App '$app' exists"
    else
        check_warn "App '$app' not found"
    fi
done

# Check requirements files
if [ -f "lims-backend/requirements/base.txt" ]; then
    check_pass "Requirements files exist"
else
    check_fail "Requirements files not found"
fi

echo ""
echo "2. Checking Frontend..."
echo "   --------------------"

# Check Node version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js installed: $NODE_VERSION"
else
    check_warn "Node.js not found (optional for backend-only setup)"
fi

# Check frontend directory
if [ -d "frontend" ]; then
    check_pass "Frontend directory exists"
else
    check_fail "Frontend directory not found"
fi

# Check frontend files
if [ -f "frontend/package.json" ]; then
    check_pass "Frontend package.json exists"
else
    check_fail "Frontend package.json not found"
fi

if [ -f "frontend/vite.config.ts" ]; then
    check_pass "Vite configuration exists"
else
    check_fail "Vite configuration not found"
fi

echo ""
echo "3. Checking Docker Configuration..."
echo "   ---------------------------------"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    check_pass "Docker installed: $DOCKER_VERSION"
else
    check_warn "Docker not found (required for containerized deployment)"
fi

# Check docker-compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
    check_pass "Docker Compose available"
else
    check_warn "Docker Compose not found (required for containerized deployment)"
fi

# Check Docker files
if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_fail "docker-compose.yml not found"
fi

if [ -f "lims-backend/Dockerfile" ]; then
    check_pass "Backend Dockerfile exists"
else
    check_fail "Backend Dockerfile not found"
fi

if [ -f "frontend/Dockerfile" ]; then
    check_pass "Frontend Dockerfile exists"
else
    check_fail "Frontend Dockerfile not found"
fi

if [ -f "Caddyfile" ]; then
    check_pass "Caddyfile exists"
else
    check_fail "Caddyfile not found"
fi

echo ""
echo "4. Checking Configuration..."
echo "   --------------------------"

# Check environment files
if [ -f ".env.example" ]; then
    check_pass "Root .env.example exists"
else
    check_warn ".env.example not found (create from template)"
fi

if [ -f "lims-backend/.env.example" ]; then
    check_pass "Backend .env.example exists"
else
    check_warn "Backend .env.example not found"
fi

if [ -f "frontend/.env.example" ]; then
    check_pass "Frontend .env.example exists"
else
    check_warn "Frontend .env.example not found"
fi

echo ""
echo "5. Checking Documentation..."
echo "   --------------------------"

DOCS=("README.md" "ARCHITECTURE.md" "API_DESIGN.md" "DATA_MODEL.md" "DEPLOYMENT.md" "VISION.md" "WORKFLOW.md")
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc exists"
    else
        check_warn "$doc not found"
    fi
done

echo ""
echo "6. Checking Migrations..."
echo "   -----------------------"

MIGRATION_DIRS=$(find lims-backend/apps -name "migrations" -type d 2>/dev/null | wc -l)
if [ "$MIGRATION_DIRS" -gt 0 ]; then
    check_pass "Found $MIGRATION_DIRS app migrations"
else
    check_fail "No migrations found"
fi

echo ""
echo "7. Checking Test Suite..."
echo "   -----------------------"

TEST_DIRS=$(find lims-backend/apps -name "tests" -type d 2>/dev/null | wc -l)
if [ "$TEST_DIRS" -gt 0 ]; then
    check_pass "Found $TEST_DIRS test directories"
else
    check_warn "No test directories found"
fi

echo ""
echo "========================="
echo "✨ Validation Complete!"
echo "========================="
echo ""
echo "Next Steps:"
echo "----------"
echo "1. For development setup:"
echo "   - Backend: cd lims-backend && pip install -r requirements/development.txt"
echo "   - Frontend: cd frontend && npm install"
echo ""
echo "2. For Docker deployment:"
echo "   - Copy .env.example to .env and configure"
echo "   - Run: docker-compose up --build"
echo ""
echo "3. Read the full setup instructions in README.md"
echo ""
