#!/bin/bash
###############################################################################
# Frontend Redeployment Script for Bug Fixing
# 
# Purpose: Stop frontend services, rebuild, redeploy, and verify functionality
# Usage: ./scripts/frontend.sh
# 
# This script:
# 1. Stops running frontend-related services
# 2. Rebuilds frontend Docker image (no cache)
# 3. Restarts frontend and proxy services
# 4. Ensures superuser admin/admin123 exists
# 5. Verifies public access and functionality
###############################################################################

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/home/munaim/srv/apps/lims"
LOG_DIR="$PROJECT_ROOT/logs"
DEPLOY_LOG="$LOG_DIR/frontend_redeploy_$(date +%Y%m%d_%H%M%S).log"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

###############################################################################
# LOGGING FUNCTIONS
###############################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$DEPLOY_LOG"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

print_header() {
    echo "" | tee -a "$DEPLOY_LOG"
    echo "============================================" | tee -a "$DEPLOY_LOG"
    echo "$1" | tee -a "$DEPLOY_LOG"
    echo "============================================" | tee -a "$DEPLOY_LOG"
}

###############################################################################
# VALIDATION FUNCTIONS
###############################################################################

check_docker() {
    log_info "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker service."
        exit 1
    fi
    
    log_success "Docker is available and running"
}

check_env_file() {
    log_info "Checking environment file..."
    if [ ! -f "$ENV_FILE" ]; then
        log_warning ".env.production not found. Creating default environment file..."
        cat > "$ENV_FILE" << 'EOF'
# Django Settings
SECRET_KEY=change-me-in-production
DB_NAME=lims_db
DB_USER=postgres
DB_PASSWORD=changeme
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=portal.alshifalab.pk,localhost,127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://portal.alshifalab.pk
CSRF_TRUSTED_ORIGINS=https://portal.alshifalab.pk

# Frontend
VITE_API_BASE_URL=/api/v1/
REACT_APP_API_BASE_URL=/api/v1/

# Server
SERVER_NAME=portal.alshifalab.pk

# Logging
LOG_LEVEL=INFO
EOF
        chmod 600 "$ENV_FILE"
        log_warning "Please update $ENV_FILE with proper values before production use"
    fi
    log_success "Environment file exists"
}

###############################################################################
# FRONTEND DEPLOYMENT FUNCTIONS
###############################################################################

stop_frontend_services() {
    print_header "Stopping Frontend Services"
    
    log_info "Checking for running frontend services..."
    
    # Stop and remove frontend container if running
    if docker ps -a --format '{{.Names}}' | grep -q "lims_frontend"; then
        log_info "Stopping lims_frontend container..."
        docker stop lims_frontend 2>&1 | tee -a "$DEPLOY_LOG" || true
        docker rm lims_frontend 2>&1 | tee -a "$DEPLOY_LOG" || true
        log_success "Frontend container stopped"
    else
        log_info "Frontend container not running"
    fi
    
    # Stop and remove proxy container if running
    if docker ps -a --format '{{.Names}}' | grep -q "lims_proxy"; then
        log_info "Stopping lims_proxy container..."
        docker stop lims_proxy 2>&1 | tee -a "$DEPLOY_LOG" || true
        docker rm lims_proxy 2>&1 | tee -a "$DEPLOY_LOG" || true
        log_success "Proxy container stopped"
    else
        log_info "Proxy container not running"
    fi
    
    log_success "All frontend services stopped"
}

rebuild_frontend() {
    print_header "Rebuilding Frontend"
    
    log_info "Loading environment variables..."
    set -a
    source "$ENV_FILE"
    set +a
    
    log_info "Building frontend Docker image (no cache)..."
    docker compose --env-file "$ENV_FILE" build --no-cache frontend 2>&1 | tee -a "$DEPLOY_LOG"
    
    if [ $? -eq 0 ]; then
        log_success "Frontend image built successfully"
    else
        log_error "Frontend build failed"
        exit 1
    fi
}

start_frontend_services() {
    print_header "Starting Frontend Services"
    
    log_info "Starting frontend container..."
    docker compose --env-file "$ENV_FILE" up -d frontend 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Starting proxy container..."
    docker compose --env-file "$ENV_FILE" up -d proxy 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for services to initialize (15 seconds)..."
    sleep 15
    
    log_success "Frontend services started"
}

###############################################################################
# VERIFICATION FUNCTIONS
###############################################################################

ensure_superuser() {
    print_header "Ensuring Superuser Exists"
    
    log_info "Checking if backend is running..."
    if ! docker ps --format '{{.Names}}' | grep -q "lims_backend"; then
        log_warning "Backend not running. Starting backend services..."
        docker compose --env-file "$ENV_FILE" up -d db redis backend
        log_info "Waiting for backend to initialize (20 seconds)..."
        sleep 20
    fi
    
    log_info "Checking for admin user..."
    USER_EXISTS=$(docker compose --env-file "$ENV_FILE" exec -T backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
exists = User.objects.filter(username='admin').exists()
print('EXISTS' if exists else 'NOTEXISTS')
PYEOF
)
    
    if echo "$USER_EXISTS" | grep -q "EXISTS"; then
        log_info "Admin user already exists. Resetting password to 'admin123'..."
        docker compose --env-file "$ENV_FILE" exec -T backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
admin = User.objects.get(username='admin')
admin.set_password('admin123')
admin.is_superuser = True
admin.is_staff = True
admin.save()
print("Password reset successfully")
PYEOF
        log_success "Admin password reset to 'admin123'"
    else
        log_info "Creating superuser admin/admin123..."
        docker compose --env-file "$ENV_FILE" exec -T backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@alshifalab.pk', 'admin123')
print("Superuser created successfully")
PYEOF
        log_success "Superuser created: admin/admin123"
    fi
}

verify_services() {
    print_header "Verifying Services"
    
    log_info "Checking container status..."
    docker compose --env-file "$ENV_FILE" ps | tee -a "$DEPLOY_LOG"
    
    # Check if frontend is running
    if docker ps --format '{{.Names}}' | grep -q "lims_frontend"; then
        log_success "✓ Frontend container is running"
    else
        log_error "✗ Frontend container is NOT running"
        return 1
    fi
    
    # Check if proxy is running
    if docker ps --format '{{.Names}}' | grep -q "lims_proxy"; then
        log_success "✓ Proxy container is running"
    else
        log_error "✗ Proxy container is NOT running"
        return 1
    fi
    
    # Check if backend is running
    if docker ps --format '{{.Names}}' | grep -q "lims_backend"; then
        log_success "✓ Backend container is running"
    else
        log_warning "⚠ Backend container is NOT running (may affect API calls)"
    fi
}

verify_access() {
    print_header "Verifying Public Access"
    
    log_info "Testing proxy health endpoint..."
    if curl -f -s -o /dev/null http://localhost:8013/health; then
        log_success "✓ Proxy health check passed"
    else
        log_warning "⚠ Proxy health check failed (may need warmup time)"
    fi
    
    log_info "Testing frontend access..."
    if curl -f -s -o /dev/null http://localhost:8013/; then
        log_success "✓ Frontend is accessible"
    else
        log_warning "⚠ Frontend access check failed"
    fi
    
    log_info "Testing backend API health..."
    if curl -f -s http://localhost:8013/api/v1/health/ | grep -q "status"; then
        log_success "✓ Backend API is accessible"
    else
        log_warning "⚠ Backend API health check failed"
    fi
}

show_summary() {
    print_header "Deployment Summary"
    
    log_info "Frontend redeployment completed!"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Access URLs:"
    log_info "  - Frontend: http://localhost:8013/"
    log_info "  - API: http://localhost:8013/api/v1/"
    log_info "  - Admin: http://localhost:8013/admin/"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Test Credentials:"
    log_info "  Username: admin"
    log_info "  Password: admin123"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Log file: $DEPLOY_LOG"
    echo "" | tee -a "$DEPLOY_LOG"
}

show_logs() {
    print_header "Recent Service Logs"
    
    log_info "Frontend logs (last 20 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=20 frontend 2>&1 | tee -a "$DEPLOY_LOG"
    
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Proxy logs (last 20 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=20 proxy 2>&1 | tee -a "$DEPLOY_LOG"
}

###############################################################################
# MAIN EXECUTION
###############################################################################

main() {
    print_header "Frontend Redeployment for Bug Fixing"
    log_info "Started at: $(date)"
    log_info "Log file: $DEPLOY_LOG"
    
    # Validation
    check_docker
    check_env_file
    
    # Stop services
    stop_frontend_services
    
    # Rebuild and deploy
    rebuild_frontend
    start_frontend_services
    
    # Ensure superuser exists
    ensure_superuser
    
    # Verify deployment
    verify_services
    verify_access
    
    # Show summary
    show_summary
    
    # Show recent logs for debugging
    show_logs
    
    log_success "Frontend redeployment completed successfully!"
}

# Error handler
trap 'log_error "Script failed at line $LINENO"' ERR

# Run main function
main "$@"
