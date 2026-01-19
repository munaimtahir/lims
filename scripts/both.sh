#!/bin/bash
###############################################################################
# Full Application Redeployment Script for Bug Fixing
# 
# Purpose: Stop entire application, rebuild all services, redeploy, and verify
# Usage: ./scripts/both.sh
# 
# This script:
# 1. Stops all running LIMS services
# 2. Rebuilds all Docker images (no cache)
# 3. Starts infrastructure services (db, redis)
# 4. Starts backend services (backend, celery)
# 5. Starts frontend services (frontend, proxy)
# 6. Runs database migrations
# 7. Ensures superuser admin/admin123 exists
# 8. Verifies public access and full functionality
###############################################################################

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
DEPLOY_LOG="$LOG_DIR/full_redeploy_$(date +%Y%m%d_%H%M%S).log"
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
        log_error ".env.production not found in $PROJECT_ROOT"
        log_info "Please copy .env.production.example to .env.production and configure it before running this script."
        exit 1
    fi
    log_success "Environment file exists"
}

check_disk_space() {
    log_info "Checking disk space..."
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if [ "$AVAILABLE_SPACE" -lt 5 ]; then
        log_warning "Low disk space: ${AVAILABLE_SPACE}GB available"
        log_warning "Recommended: At least 5GB free space"
    else
        log_success "Disk space: ${AVAILABLE_SPACE}GB available"
    fi
}

###############################################################################
# DEPLOYMENT FUNCTIONS
###############################################################################

stop_all_services() {
    print_header "Stopping All Services"
    
    log_info "Stopping all LIMS containers..."
    docker compose --env-file "$ENV_FILE" down 2>&1 | tee -a "$DEPLOY_LOG" || true
    
    log_info "Checking for any remaining containers..."
    REMAINING=$(docker ps -a --format '{{.Names}}' | grep "lims_" || true)
    
    if [ -n "$REMAINING" ]; then
        log_warning "Found remaining containers. Cleaning up..."
        echo "$REMAINING" | while read container; do
            log_info "Removing $container..."
            docker stop "$container" 2>&1 | tee -a "$DEPLOY_LOG" || true
            docker rm "$container" 2>&1 | tee -a "$DEPLOY_LOG" || true
        done
    fi
    
    log_success "All services stopped"
}

rebuild_all_images() {
    print_header "Rebuilding All Docker Images"
    
    log_info "Loading environment variables..."
    set -a
    source "$ENV_FILE"
    set +a
    
    log_info "Building all Docker images (no cache)..."
    log_info "This may take several minutes..."
    
    # Build backend first
    log_info "Building backend image..."
    docker compose --env-file "$ENV_FILE" build --no-cache backend 2>&1 | tee -a "$DEPLOY_LOG"
    
    # Build celery (uses same image as backend)
    log_info "Building celery image..."
    docker compose --env-file "$ENV_FILE" build --no-cache celery 2>&1 | tee -a "$DEPLOY_LOG"
    
    # Build frontend
    log_info "Building frontend image..."
    docker compose --env-file "$ENV_FILE" build --no-cache frontend 2>&1 | tee -a "$DEPLOY_LOG"
    
    if [ $? -eq 0 ]; then
        log_success "All Docker images built successfully"
    else
        log_error "Build failed"
        exit 1
    fi
}

start_infrastructure() {
    print_header "Starting Infrastructure Services"
    
    log_info "Starting database and Redis..."
    docker compose --env-file "$ENV_FILE" up -d db redis 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for infrastructure to initialize (20 seconds)..."
    sleep 20
    
    # Verify infrastructure health
    log_info "Checking database health..."
    docker compose --env-file "$ENV_FILE" exec -T db pg_isready -U postgres 2>&1 | tee -a "$DEPLOY_LOG" || true
    
    log_info "Checking Redis health..."
    docker compose --env-file "$ENV_FILE" exec -T redis redis-cli ping 2>&1 | tee -a "$DEPLOY_LOG" || true
    
    log_success "Infrastructure services started"
}

start_backend() {
    print_header "Starting Backend Services"
    
    log_info "Starting backend..."
    docker compose --env-file "$ENV_FILE" up -d backend 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for backend to initialize (25 seconds)..."
    sleep 25
    
    log_info "Starting Celery worker..."
    docker compose --env-file "$ENV_FILE" up -d celery 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for Celery to initialize (10 seconds)..."
    sleep 10
    
    log_success "Backend services started"
}

start_frontend() {
    print_header "Starting Frontend Services"
    
    log_info "Starting frontend..."
    docker compose --env-file "$ENV_FILE" up -d frontend 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Starting proxy..."
    docker compose --env-file "$ENV_FILE" up -d proxy 2>&1 | tee -a "$DEPLOY_LOG"
    
    log_info "Waiting for frontend services to initialize (15 seconds)..."
    sleep 15
    
    log_success "Frontend services started"
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
        log_info "Admin user already exists. Skipping creation and password reset for security."
    else
        log_info "Creating superuser admin/admin123..."
        docker compose --env-file "$ENV_FILE" exec -T backend python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@alshifalab.pk', 'admin123')
print("Superuser created successfully")
PYEOF
        log_success "Superuser created: admin/admin123"
        log_warning "IMPORTANT: Change your admin password immediately!"
    fi
}

verify_all_services() {
    print_header "Verifying All Services"
    
    log_info "Checking container status..."
    docker compose --env-file "$ENV_FILE" ps | tee -a "$DEPLOY_LOG"
    echo "" | tee -a "$DEPLOY_LOG"
    
    # Check each service
    local all_running=true
    
    if docker ps --format '{{.Names}}' | grep -q "lims_db"; then
        log_success "✓ Database is running"
    else
        log_error "✗ Database is NOT running"
        all_running=false
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "lims_redis"; then
        log_success "✓ Redis is running"
    else
        log_error "✗ Redis is NOT running"
        all_running=false
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "lims_backend"; then
        log_success "✓ Backend is running"
    else
        log_error "✗ Backend is NOT running"
        all_running=false
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "lims_celery"; then
        log_success "✓ Celery is running"
    else
        log_warning "⚠ Celery is NOT running"
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "lims_frontend"; then
        log_success "✓ Frontend is running"
    else
        log_error "✗ Frontend is NOT running"
        all_running=false
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "lims_proxy"; then
        log_success "✓ Proxy is running"
    else
        log_error "✗ Proxy is NOT running"
        all_running=false
    fi
    
    if [ "$all_running" = false ]; then
        return 1
    fi
}

verify_full_access() {
    print_header "Verifying Full Application Access"
    
    log_info "Testing frontend access..."
    if curl -f -s -o /dev/null http://localhost:8012/; then
        log_success "✓ Frontend is accessible"
    else
        log_warning "⚠ Frontend access check failed"
    fi
    
    log_info "Testing backend API health..."
    if curl -f -s http://localhost:8012/api/v1/health/ | grep -q "status"; then
        log_success "✓ Backend API is accessible"
    else
        log_warning "⚠ Backend API health check failed"
    fi
    
    log_info "Testing Django admin access..."
    if curl -f -s -o /dev/null http://localhost:8012/admin/; then
        log_success "✓ Django admin is accessible"
    else
        log_warning "⚠ Django admin access check failed"
    fi
    
    log_info "Testing proxy health..."
    if curl -f -s -o /dev/null http://localhost:8012/health; then
        log_success "✓ Proxy health check passed"
    else
        log_warning "⚠ Proxy health check failed"
    fi
}

show_summary() {
    print_header "Full Deployment Summary"
    
    log_success "Complete application redeployment finished!"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "All Services Status:"
    docker compose --env-file "$ENV_FILE" ps 2>&1 | tee -a "$DEPLOY_LOG"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Access URLs:"
    log_info "  - Frontend: http://localhost:8012/"
    log_info "  - API: http://localhost:8012/api/v1/"
    log_info "  - API Docs: http://localhost:8012/api/docs/"
    log_info "  - Admin: http://localhost:8012/admin/"
    log_info "  - Health: http://localhost:8012/api/v1/health/"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Test Credentials:"
    log_info "  Username: admin"
    log_info "  Password: admin123"
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Log file: $DEPLOY_LOG"
    echo "" | tee -a "$DEPLOY_LOG"
}

show_all_logs() {
    print_header "Recent Service Logs"
    
    log_info "Backend logs (last 15 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=15 backend 2>&1 | tee -a "$DEPLOY_LOG"
    
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Frontend logs (last 15 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=15 frontend 2>&1 | tee -a "$DEPLOY_LOG"
    
    echo "" | tee -a "$DEPLOY_LOG"
    log_info "Proxy logs (last 15 lines):"
    docker compose --env-file "$ENV_FILE" logs --tail=15 proxy 2>&1 | tee -a "$DEPLOY_LOG"
}

###############################################################################
# MAIN EXECUTION
###############################################################################

main() {
    print_header "Full Application Redeployment for Bug Fixing"
    log_info "Started at: $(date)"
    log_info "Log file: $DEPLOY_LOG"
    
    # Validation
    check_docker
    check_env_file
    check_disk_space
    
    # Stop everything
    stop_all_services
    
    # Rebuild all images
    rebuild_all_images
    
    # Start services in order
    start_infrastructure
    start_backend
    run_migrations
    start_frontend
    
    # Ensure superuser exists
    ensure_superuser
    
    # Verify everything
    verify_all_services
    verify_full_access
    
    # Show summary
    show_summary
    
    # Show recent logs for debugging
    show_all_logs
    
    log_success "Full application redeployment completed successfully!"
}

# Error handler
trap 'log_error "Script failed at line $LINENO"' ERR

# Run main function
main "$@"
