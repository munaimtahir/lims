#!/bin/bash
set -e

# Configuration
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
ENV_FILE="$PROJECT_ROOT/.env.production"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
DEPLOY_LOG="$LOG_DIR/deploy_$(date +%Y%m%d_%H%M%S).log"

# Setup logging
exec > >(tee -a "$DEPLOY_LOG") 2>&1

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check Root
if [ "$EUID" -ne 0 ]; then
  error "Please run as root (sudo ./deploy.sh)"
  exit 1
fi

# Check Environment
if [ ! -f "$ENV_FILE" ]; then
  error ".env.production not found!"
  exit 1
fi

log "Deploying LIMS Application..."
log "Environment: $ENV_FILE"

# Stop Services
log "Stopping all services..."
docker compose --env-file "$ENV_FILE" down --remove-orphans || true

# Clean previous builds and irrelevant containers/images
log "Cleaning build cache and dangling resources..."
docker builder prune -f || true
docker image prune -f || true

# Build Images
log "Building Backend (No Cache)..."
docker compose --env-file "$ENV_FILE" build --no-cache backend

log "Building Celery (Using Backend Cache)..."
docker compose --env-file "$ENV_FILE" build celery

log "Building Frontend (No Cache)..."
docker compose --env-file "$ENV_FILE" build --no-cache frontend

# Start Services
log "Starting Infrastructure (DB, Redis)..."
docker compose --env-file "$ENV_FILE" up -d db redis
log "Waiting 15s for DB..."
sleep 15

log "Starting Backend..."
docker compose --env-file "$ENV_FILE" up -d backend
log "Waiting 15s for Backend..."
sleep 15

log "Starting Celery..."
docker compose --env-file "$ENV_FILE" up -d celery
log "Waiting 5s for Celery..."
sleep 5

log "Starting Frontend & Proxy..."
docker compose --env-file "$ENV_FILE" up -d frontend proxy
log "Waiting 10s..."
sleep 10

# Verification
log "Looking for active containers..."
docker compose --env-file "$ENV_FILE" ps

success "Deployment Complete! Check the application at your configured domain/port."
