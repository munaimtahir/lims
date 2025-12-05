#!/bin/bash

# ==============================================================================
# Production Deployment Verification Script
# ==============================================================================
# This script verifies that the LIMS application is correctly configured
# for production deployment on VPS with IP 172.237.71.40
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Production Deployment Verification"
echo "==========================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check a condition
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to warn about something
warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Function to show info
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "1. Checking Environment Configuration..."
echo "----------------------------------------"

# Check if .env exists
if [ -f .env ]; then
    check ".env file exists"
    
    # Check VITE_API_URL
    if grep -q "VITE_API_URL=/api" .env; then
        check "VITE_API_URL is set to /api (production)"
    else
        warn "VITE_API_URL is not set to /api"
    fi
    
    # Check for localhost in .env
    if ! grep -q "localhost" .env 2>/dev/null; then
        check "No localhost references in .env"
    else
        warn ".env contains localhost references"
    fi
    
    # Check for port 5173 in .env
    if ! grep -q "5173" .env 2>/dev/null; then
        check "No port 5173 references in .env"
    else
        warn ".env contains port 5173 references"
    fi
    
    # Check DEBUG setting
    if grep -q "DEBUG=False" .env; then
        check "DEBUG is set to False"
    else
        warn "DEBUG should be False in production"
    fi
else
    echo -e "${RED}✗${NC} .env file not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "2. Checking Docker Configuration..."
echo "----------------------------------------"

# Check if docker-compose.yml exists
if [ -f docker-compose.yml ]; then
    check "docker-compose.yml exists"
    
    # Validate docker-compose config
    if docker compose config > /dev/null 2>&1; then
        check "docker-compose.yml is valid"
    else
        echo -e "${RED}✗${NC} docker-compose.yml has errors"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check services
    SERVICES=$(docker compose config --services 2>/dev/null)
    if echo "$SERVICES" | grep -q "nginx"; then
        check "nginx service configured"
    fi
    if echo "$SERVICES" | grep -q "backend"; then
        check "backend service configured"
    fi
    if echo "$SERVICES" | grep -q "db"; then
        check "db service configured"
    fi
    if echo "$SERVICES" | grep -q "redis"; then
        check "redis service configured"
    fi
else
    echo -e "${RED}✗${NC} docker-compose.yml not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "3. Checking Dockerfiles..."
echo "----------------------------------------"

if [ -f backend/Dockerfile ]; then
    check "Backend Dockerfile exists"
    if grep -q "gunicorn" backend/Dockerfile; then
        check "Backend uses Gunicorn for production"
    fi
else
    echo -e "${RED}✗${NC} Backend Dockerfile not found"
    ERRORS=$((ERRORS + 1))
fi

if [ -f nginx/Dockerfile ]; then
    check "Nginx Dockerfile exists"
    if grep -q "VITE_API_URL=/api" nginx/Dockerfile; then
        check "Nginx Dockerfile sets production API URL"
    fi
else
    echo -e "${RED}✗${NC} Nginx Dockerfile not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "4. Checking Nginx Configuration..."
echo "----------------------------------------"

if [ -f nginx/nginx.conf ]; then
    check "nginx.conf exists"
    
    if grep -q "listen 80" nginx/nginx.conf; then
        check "Nginx listens on port 80"
    fi
    
    if grep -q "server_name 172.237.71.40" nginx/nginx.conf; then
        check "Nginx server_name is set to VPS IP"
    else
        warn "Nginx server_name may not be configured correctly"
    fi
    
    if grep -q "location /api/" nginx/nginx.conf; then
        check "Nginx proxies /api/ to backend"
    fi
    
    if ! grep -q "localhost" nginx/nginx.conf; then
        check "No localhost in production nginx config"
    else
        warn "nginx.conf may contain localhost references"
    fi
else
    echo -e "${RED}✗${NC} nginx/nginx.conf not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "5. Checking for Development References..."
echo "----------------------------------------"

# Check production files for localhost
if ! grep -r "localhost" .env backend/.env frontend/.env docker-compose.yml nginx/nginx.conf 2>/dev/null | grep -v "^Binary" > /dev/null; then
    check "No localhost in production configuration files"
else
    warn "Found localhost references in production files"
fi

# Check for port 5173
if ! grep -r "5173" .env backend/.env frontend/.env docker-compose.yml 2>/dev/null | grep -v "^Binary" > /dev/null; then
    check "No port 5173 in production configuration files"
else
    warn "Found port 5173 references in production files"
fi

echo ""
echo "6. Checking Running Services (if deployed)..."
echo "----------------------------------------"

if command -v docker &> /dev/null && docker ps &> /dev/null; then
    if docker compose ps 2>/dev/null | grep -q "Up"; then
        info "Docker Compose services are running"
        
        # Check each service
        if docker compose ps | grep -q "nginx.*Up"; then
            check "nginx service is running"
        else
            info "nginx service not running (deployment may not be started yet)"
        fi
        
        if docker compose ps | grep -q "backend.*Up"; then
            check "backend service is running"
        else
            info "backend service not running (deployment may not be started yet)"
        fi
        
        if docker compose ps | grep -q "db.*Up"; then
            check "db service is running"
        else
            info "db service not running (deployment may not be started yet)"
        fi
        
        if docker compose ps | grep -q "redis.*Up"; then
            check "redis service is running"
        else
            info "redis service not running (deployment may not be started yet)"
        fi
    else
        info "Services not running yet (run 'docker compose up -d' to start)"
    fi
else
    info "Docker not running or not accessible (skipping running services check)"
fi

echo ""
echo "7. Production Deployment Summary..."
echo "----------------------------------------"

echo ""
info "Expected URLs after deployment:"
echo "  Frontend:      http://172.237.71.40"
echo "  Backend API:   http://172.237.71.40/api"
echo "  Backend Direct: http://172.237.71.40:8000 (optional)"
echo "  Admin Panel:   http://172.237.71.40/admin"
echo ""

info "Network Architecture:"
echo "  nginx (port 80) → Serves frontend + proxies /api/* to backend:8000"
echo "  backend (port 8000) → Django API with Gunicorn"
echo "  db (internal) → PostgreSQL database"
echo "  redis (internal) → Cache and task queue"
echo ""

echo -e "${BLUE}=========================================="
echo "Verification Complete"
echo "==========================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo -e "${GREEN}The repository is ready for production deployment!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Update .env with secure credentials (see PRODUCTION_DEPLOYMENT.md)"
    echo "  2. Run: docker compose build"
    echo "  3. Run: docker compose up -d"
    echo "  4. Access: http://172.237.71.40"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Verification passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "The repository is mostly ready for production deployment."
    echo "Please review the warnings above and make necessary adjustments."
    exit 0
else
    echo -e "${RED}✗ Verification failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before deploying to production."
    exit 1
fi
