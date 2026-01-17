#!/bin/bash

# ============================================
# LIMS Production Deployment Script
# ============================================
# 
# This script automates the deployment of LIMS to a production environment
# via SSH. It handles:
#   - Repository updates
#   - Docker image building
#   - Environment validation
#   - Database migrations
#   - Service startup
#   - Health checks
#
# Usage:
#   ./deploy.sh                    # Full deployment
#   ./deploy.sh --migrate-only    # Run migrations only
#   ./deploy.sh --health-check    # Run health checks only
#   ./deploy.sh --logs            # Show service logs
#   ./deploy.sh --help            # Show this help
#
# Prerequisites:
#   - Docker and Docker Compose installed
#   - SSH access to server
#   - .env.production configured
#   - At least 2GB free disk space
#
# Author: LIMS Development Team
# Version: 1.0.0

set -e  # Exit on any error

# ============================================
# CONFIGURATION
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
ENV_FILE="${PROJECT_ROOT}/.env.production"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOY_LOG="${LOG_DIR}/deploy_${TIMESTAMP}.log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# UTILITY FUNCTIONS
# ============================================

# Print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOY_LOG"
}

log_error() {
    echo -e "${RED}[✗ ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

# Print section header
print_header() {
    echo "" | tee -a "$DEPLOY_LOG"
    echo "========================================" | tee -a "$DEPLOY_LOG"
    echo "  $1" | tee -a "$DEPLOY_LOG"
    echo "========================================" | tee -a "$DEPLOY_LOG"
}

# Create directories if they don't exist
ensure_directories() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "${PROJECT_ROOT}/data"
}

# Display usage information
show_usage() {
    cat << EOF
LIMS Production Deployment Script

Usage: $0 [OPTION]

Options:
    --full              Full deployment (default)
    --migrate-only      Run migrations only
    --health-check      Run health checks only
    --logs              Show service logs
    --backup-db         Backup database only
    --restart           Restart services only
    --help              Show this help message

Examples:
    # Full deployment
    $0

    # Run migrations on existing deployment
    $0 --migrate-only

    # Check service health
    $0 --health-check

    # Show logs
    $0 --logs

EOF
}

# ============================================
# VALIDATION FUNCTIONS
# ============================================

# Validate prerequisites
validate_prerequisites() {
    print_header "Validating Prerequisites"
    
    # Check if running on a Linux/Unix system
    if [[ "$OSTYPE" != "linux-gnu"* ]] && [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script must run on Linux or macOS. Detected: $OSTYPE"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_success "Docker is installed: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    log_success "Docker Compose is installed: $(docker compose version)"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git first."
        exit 1
    fi
    log_success "Git is installed: $(git --version)"
    
    # Check .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env.production file not found!"
        log_info "Copy .env.production.example to .env.production and configure it:"
        log_info "  cp .env.production.example .env.production"
        log_info "  nano .env.production"
        exit 1
    fi
    log_success ".env.production file exists"
    
    # Check docker-compose.yml exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "docker-compose.yml not found!"
        exit 1
    fi
    log_success "docker-compose.yml exists"
}

# Validate environment variables
validate_environment() {
    print_header "Validating Environment Configuration"
    
    # Load environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    # Check required variables
    local missing_vars=()
    
    if [ -z "$SECRET_KEY" ]; then
        missing_vars+=("SECRET_KEY")
    else
        log_success "SECRET_KEY is configured"
    fi
    
    if [ -z "$DB_PASSWORD" ]; then
        missing_vars+=("DB_PASSWORD")
    else
        log_success "DB_PASSWORD is configured"
    fi
    
    if [ -z "$ALLOWED_HOSTS" ]; then
        missing_vars+=("ALLOWED_HOSTS")
    else
        log_success "ALLOWED_HOSTS: $ALLOWED_HOSTS"
    fi
    
    if [ -z "$CORS_ALLOWED_ORIGINS" ]; then
        log_warning "CORS_ALLOWED_ORIGINS not configured (may be needed for frontend)"
    else
        log_success "CORS_ALLOWED_ORIGINS: $CORS_ALLOWED_ORIGINS"
    fi
    
    # Report missing variables
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        exit 1
    fi
}

# Check disk space
check_disk_space() {
    print_header "Checking Disk Space"
    
    local available=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local required=$((2 * 1024 * 1024))  # 2GB in KB
    
    if [ "$available" -lt "$required" ]; then
        log_error "Insufficient disk space! Need 2GB, have $(($available / 1024 / 1024))GB"
        exit 1
    fi
    
    log_success "Sufficient disk space available: $(($available / 1024 / 1024))GB"
}

# ============================================
# GIT OPERATIONS
# ============================================

# Update repository
update_repository() {
    print_header "Updating Repository"
    
    cd "$PROJECT_ROOT"
    
    log_info "Fetching latest changes from remote..."
    git fetch origin
    
    log_info "Checking for updates..."
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log_success "Repository is up to date"
    else
        log_info "Pulling latest changes..."
        git pull origin main
        log_success "Repository updated"
    fi
    
    # Show latest commit
    log_info "Latest commit: $(git log -1 --oneline)"
}

# ============================================
# DATABASE OPERATIONS
# ============================================

# Backup database
backup_database() {
    print_header "Backing Up Database"
    
    local backup_file="${BACKUP_DIR}/lims_db_${TIMESTAMP}.sql.gz"
    
    log_info "Creating database backup..."
    docker compose exec -T db pg_dump -U postgres lims_db | gzip > "$backup_file"
    
    if [ -f "$backup_file" ]; then
        local size=$(du -h "$backup_file" | awk '{print $1}')
        log_success "Database backed up: $backup_file ($size)"
        
        # Clean old backups (keep last 10)
        log_info "Cleaning old backups (keeping last 10)..."
        ls -t "$BACKUP_DIR"/lims_db_*.sql.gz | tail -n +11 | xargs -r rm
        log_success "Old backups cleaned"
    else
        log_error "Database backup failed!"
        return 1
    fi
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"
    
    log_info "Applying migrations..."
    docker compose exec backend python manage.py migrate
    log_success "Migrations completed"
    
    # Run any additional setup
    log_info "Collecting static files..."
    docker compose exec backend python manage.py collectstatic --noinput
    log_success "Static files collected"
}

# ============================================
# DOCKER OPERATIONS
# ============================================

# Build Docker images
build_images() {
    print_header "Building Docker Images"
    
    set -a
    source "$ENV_FILE"
    set +a
    
    export SECRET_KEY
    export DB_PASSWORD
    export ALLOWED_HOSTS
    export CORS_ALLOWED_ORIGINS
    export DB_NAME
    export DB_USER
    export DB_HOST
    export DB_PORT
    export REDIS_URL
    export SERVER_NAME
    
    log_info "Building Docker images..."
    docker compose build --no-cache
    log_success "Docker images built successfully"
}

# Start services
start_services() {
    print_header "Starting Services"
    
    log_info "Starting Docker services..."
    docker compose up -d
    log_success "Services started"
    
    log_info "Waiting for services to become healthy..."
    sleep 10
    
    # Check if services are running
    docker compose ps
}

# Stop services
stop_services() {
    print_header "Stopping Services"
    
    log_info "Stopping Docker services..."
    docker compose down
    log_success "Services stopped"
}

# Restart services
restart_services() {
    print_header "Restarting Services"
    
    log_info "Restarting Docker services..."
    docker compose restart
    log_success "Services restarted"
    
    log_info "Waiting for services to become healthy..."
    sleep 10
}

# ============================================
# HEALTH CHECK FUNCTIONS
# ============================================

# Check service health
check_health() {
    print_header "Checking Service Health"
    
    local health_status=0
    
    # Check Docker services
    log_info "Checking Docker services..."
    docker compose ps
    
    # Check backend API
    log_info "Checking Backend API..."
    if curl -sf http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
        log_success "Backend API: OK"
    else
        log_error "Backend API: FAILED"
        health_status=1
    fi
    
    # Check database
    log_info "Checking Database..."
    if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        log_success "PostgreSQL: OK"
    else
        log_error "PostgreSQL: FAILED"
        health_status=1
    fi
    
    # Check Redis
    log_info "Checking Redis..."
    if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis: OK"
    else
        log_error "Redis: FAILED"
        health_status=1
    fi
    
    # Check Caddy
    log_info "Checking Caddy Reverse Proxy..."
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log_success "Caddy: OK"
    else
        log_error "Caddy: FAILED (may not have valid certificate yet)"
    fi
    
    return $health_status
}

# Display service logs
show_logs() {
    print_header "Service Logs (Last 100 lines)"
    
    docker compose logs --tail=100
}

# ============================================
# MAIN DEPLOYMENT FLOW
# ============================================

# Full deployment
full_deployment() {
    print_header "Full LIMS Deployment Starting"
    
    validate_prerequisites
    validate_environment
    check_disk_space
    ensure_directories
    
    update_repository
    backup_database
    build_images
    start_services
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    run_migrations
    
    # Run health checks
    if ! check_health; then
        log_warning "Some services reported as unhealthy. Checking logs..."
        show_logs
        exit 1
    fi
    
    print_header "Deployment Completed Successfully!"
    log_success "LIMS is now running"
    log_info "Access the application at: http://localhost or your configured domain"
    log_info "Deployment log: $DEPLOY_LOG"
}

# Migration only
migrate_only() {
    print_header "Running Database Migrations"
    
    ensure_directories
    
    if ! docker compose ps | grep -q "backend"; then
        log_error "Backend service is not running. Start services first with: $0"
        exit 1
    fi
    
    run_migrations
    log_success "Migrations completed"
}

# Restart only
restart_only() {
    print_header "Restarting Services"
    
    ensure_directories
    restart_services
    
    if ! check_health; then
        log_warning "Some services reported as unhealthy. Checking logs..."
        show_logs
        exit 1
    fi
    
    log_success "Services restarted successfully"
}

# ============================================
# MAIN ENTRY POINT
# ============================================

main() {
    # Ensure directories exist for logging
    mkdir -p "$LOG_DIR"
    
    # Log start
    log_info "LIMS Deployment Script Started"
    log_info "Project Root: $PROJECT_ROOT"
    log_info "Script Version: 1.0.0"
    
    # Parse command line arguments
    case "${1:-}" in
        --help)
            show_usage
            exit 0
            ;;
        --migrate-only)
            migrate_only
            ;;
        --health-check)
            check_health
            ;;
        --logs)
            show_logs
            ;;
        --backup-db)
            ensure_directories
            backup_database
            ;;
        --restart)
            restart_only
            ;;
        --full|"")
            full_deployment
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
