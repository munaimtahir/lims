#!/bin/bash
###############################################################################
# Backend Redeployment Script for Bug Fixing
# 
# Purpose: Stop backend services, rebuild, redeploy, and verify functionality
# Usage: ./scripts/backend.sh
# 
# This script:
# 1. Stops running backend-related services (backend, celery)
# 2. Rebuilds backend Docker image (no cache)
# 3. Runs database migrations
# 4. Restarts backend and celery services
# 5. Ensures superuser admin/admin123 exists
# 6. Verifies public access and functionality
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
DEPLOY_LOG="$LOG_DIR/backend_redeploy_$(date +%Y%m%d_%H%M%S).log"
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
# BACKEND DEPLOYMENT FUNCTIONS
###############################################################################

ensure_infrastructure() {
    print_header "Ensuring Infrastructure Services"
    
    log_info "Checking if database is running..."
    if ! docker ps --format '{{.Names}}' | grep -q "lims_db"; then
        log_info "Starting database..."
        docker compose --env-file "$ENV_FILE" up -d db
        log_info "Waiting for database to initialize (15 seconds)..."
        sleep 15
    else
        log_success "Database is already running"
    fi
    
    log_info "Checking if Redis is running..."
    if ! docker ps --format '{{.Names}}' | grep -q "lims_redis"; then
        log_info "Starting Redis..."
        docker compose --env-file "$ENV_FILE" up -d redis
        log_info "Waiting for Redis to initialize (5 seconds)..."
        sleep 5
    else
        log_success "Redis is already running"
    fi
}

stop_backend_services() {
    print_header "Stopping Backend Services"
    
    log_info "Checking for running backend services..."
    
    # Stop and remove backend container if running
    if docker ps -a --format '{{.Names}}' | grep -q "lims_backend"; then
        log_info "Stopping lims_backend container..."
        docker stop lims_backend 2>&1 | tee -a "$DEPLOY_LOG" || true
        docker rm lims_backend 2>&1 | tee -a "$DEPLOY_LOG" || true
        log_success "Backend container stopped"
    else
        log_info "Backend container not running"
    fi
    
    # Stop and remove celery container if running
    if docker ps -a --format '{{.Names}}' | grep -q "lims_celery"; then
        log_info "Stopping lims_celery container..."
        docker stop lims_celery 2>&1 | tee -a "$DEPLOY_LOG" || true
        docker rm lims_celery 2>&1 | tee -a "$DEPLOY_LOG" || true
        log_success "Celery container stopped"
    else
        log_info "Celery container not running"
    fi
    
    log_success "All backend services stopped"
}

rebuild_backend() {
    print_header "Rebuilding Backend"
    
    log_info "Loading environment variables..."
    set -a
    source "$ENV_FILE"
    set +a
    
    log_info "Building backend Docker image (no cache)..."
    docker compose --env-file "$ENV_FILE" build --no-cache backend 2>&1 | tee -a "$DEPLOY_LOG"
    
    if [ $? -eq 0 ]; then
        log_success "Backend image built successfully"
    else
        log_error "Backend build failed"
        exit 1
    fi
    
    log_info "Building Celery Docker image (no cache)..."
    docker compose --env-file "$ENV_FILE" build --no-cache celery 2>&1 | tee -a "$DEPLOY_LOG"
    
    if [ $? -eq 0 ]; then
        log_success "Celery image built successfully"
    else
        log_error "Celery build failed"
        exit 1
    fi
}

start_backend_services() {
    print_header "Starting Backend Services"
    
    log_info "Starting backend container..."
    docker compose --env-file "$ENV_FILE" up -d backend 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for backend to initialize (20 seconds)..."
    sleep 20
    
    log_info "Starting celery worker..."
    docker compose --env-file "$ENV_FILE" up -d celery 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for celery to initialize (10 seconds)..."
    sleep 10
    
    log_success "Backend services started"
}

run_migrations() {
    print_header "Running Database Migrations"
    
    log_info "Applying database migrations..."
    docker compose --env-file "$ENV_FILE" exec -T backend python manage.py migrate --noinput 2>&1 | tee -a "$DEPLOY_LOG"
    
    if [ $? -eq 0 ]; then
        log_success "Migrations applied successfully"
    else
        log_warning "Migration warnings occurred (check log for details)"
    fi
    
    log_info "Collecting static files..."
    docker compose --env-file "$ENV_FILE" exec -T backend python manage.py collectstatic --noinput 2>&1 | tee -a "$DEPLOY_LOG"
    
    if [ $? -eq 0 ]; then
        log_success "Static files collected"
    else
        log_warning "Static files collection had warnings"
    fi
}

###############################################################################
# VERIFICATION FUNCTIONS
###############################################################################

ensure_superuser() {
    print_header "Ensuring Superuser Exists"
    
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
    
    # Check if backend is running
    if docker ps --format '{{.Names}}' | grep -q "lims_backend"; then
        log_success "✓ Backend container is running"
    else
        log_error "✗ Backend container is NOT running"
        return 1
    fi
    
    # Check if celery is running
    if docker ps --format '{{.Names}}' | grep -q "lims_celery"; then
        log_success "✓ Celery container is running"
    else
        log_warning "⚠ Celery container is NOT running"
    fi
    
    # Check if database is running
    if docker ps --format '{{.Names}}' | grep -q "lims_db"; then
        log_success "✓ Database container is running"
    else
        log_error "✗ Database container is NOT running"
        return 1
    fi
    
    # Check if redis is running
    if docker ps --format '{{.Names}}' | grep -q "lims_redis"; then
        log_success "✓ Redis container is running"
    else
        log_warning "⚠ Redis container is NOT running"
    fi
}

verify_access() {
    print_header "Verifying Public Access"
    
    log_info "Testing backend health endpoint..."
    if docker compose --env-file "$ENV_FILE" exec -T backend curl -f -s http://localhost:8000/api/v1/health/ | grep -q "status"; then
        log_success "✓ Backend health check passed (internal)"
    else
        log_warning "⚠ Backend internal health check failed"
    fi
    
    # Check if proxy is running for external access
    if docker ps --format '{{.Names}}' | grep -q "lims_proxy"; then
        log_info "Testing external API access through proxy..."
        if curl -f -s http://localhost:8013/api/v1/health/ | grep -q "status"; then
            log_success "✓ Backend API is publicly accessible"
        else
            log_warning "⚠ External API access check failed"
        fi
    else
        log_info "Proxy not running. Starting proxy for public access..."
        docker compose --env-file "$ENV_FILE" up -d proxy
        sleep 10
        log_success "Proxy started"
    fi
    
    log_info "Testing Django admin access..."
    if curl -f -s -o /dev/null http://localhost:8013/admin/; then
        log_success "✓ Django admin is accessible"
    else
        log_warning "⚠ Django admin access check failed"
    fi
}

show_summary() {
    print_header "Deployment Summary"
    
    log_info "Backend redeployment completed!"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Access URLs:"
    log_info "  - API: http://localhost:8013/api/v1/"
    log_info "  - API Docs: http://localhost:8013/api/docs/"
    log_info "  - Admin: http://localhost:8013/admin/"
    log_info "  - Health: http://localhost:8013/api/v1/health/"
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
    
    log_info "Backend logs (last 20 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=20 backend 2>&1 | tee -a "$DEPLOY_LOG"
    
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Celery logs (last 20 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=20 celery 2>&1 | tee -a "$DEPLOY_LOG"
}

###############################################################################
# MAIN EXECUTION
###############################################################################

main() {
    print_header "Backend Redeployment for Bug Fixing"
    log_info "Started at: $(date)"
    log_info "Log file: $DEPLOY_LOG"
    
    # Validation
    check_docker
    check_env_file
    
    # Ensure infrastructure is running
    ensure_infrastructure
    
    # Stop services
    stop_backend_services
    
    # Rebuild and deploy
    rebuild_backend
    start_backend_services
    
    # Run migrations
    run_migrations
    
    # Ensure superuser exists
    ensure_superuser
    
    # Verify deployment
    verify_services
    verify_access
    
    # Show summary
    show_summary
    
    # Show recent logs for debugging
    show_logs
    
    log_success "Backend redeployment completed successfully!"
}

# Error handler
trap 'log_error "Script failed at line $LINENO"' ERR

# Run main function
main "$@"
