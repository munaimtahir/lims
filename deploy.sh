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
# if [ "$EUID" -ne 0 ]; then
#   error "Please run as root (sudo ./deploy.sh)"
#   exit 1
# fi

# Check Environment
if [ ! -f "$ENV_FILE" ]; then
  error ".env.production not found!"
  exit 1
fi

log "Deploying LIMS Application..."
log "Environment: $ENV_FILE"

# Stop Services
log "Stopping all services..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" down --remove-orphans || true

# Build Images (no cache to ensure latest codebase and new features)
log "Building Images (--no-cache)..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" build --no-cache

# Start Services
log "Starting all services..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up -d
log "Waiting for services to become healthy..."
sleep 30 # Give services some time to start and become healthy

# Optional: run migrations (uncomment if you use scripts/deploy.sh for migrations)
# sleep 15 && docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" exec -T backend python manage.py migrate --noinput

# Verification
log "Looking for active containers..."
docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" ps

success "Deployment Complete! Check the application at your configured domain/port."
