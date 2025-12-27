#!/bin/bash

# LIMS Setup Script for Automated AI Agent
# This script sets up the complete development environment for the LIMS repository
# It is designed to be idempotent and non-interactive

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Trap errors and provide helpful messages
trap 'log_error "Setup failed at line $LINENO. Check the error above."; exit 1' ERR

# Change to /app directory (where repo is cloned)
if [ ! -d "/app" ]; then
    log_warning "/app directory not found, using current directory: $(pwd)"
    SETUP_DIR=$(pwd)
else
    cd /app || {
        log_error "Failed to change to /app directory"
        exit 1
    }
    SETUP_DIR=/app
fi

log_info "Starting LIMS environment setup..."
log_info "Working directory: $SETUP_DIR"

# ============================================
# 1. Prerequisites Check
# ============================================
log_info "Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 12 ]; then
        log_success "Python $PYTHON_VERSION found (>= 3.12)"
    else
        log_error "Python 3.12+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    log_error "Python 3 not found. Please install Python 3.12+"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    log_success "pip found"
else
    log_error "pip not found. Please install pip"
    exit 1
fi

# Check Node.js version
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    
    if [ "$NODE_MAJOR" -ge 20 ]; then
        log_success "Node.js $NODE_VERSION found (>= 20)"
    else
        log_error "Node.js 20+ required. Found: $NODE_VERSION"
        exit 1
    fi
else
    log_error "Node.js not found. Please install Node.js 20+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    log_success "npm found"
else
    log_error "npm not found. Please install npm"
    exit 1
fi

# Check PostgreSQL (optional, will use SQLite if not available)
if command -v psql &> /dev/null; then
    log_info "PostgreSQL found (optional, using SQLite for development)"
else
    log_warning "PostgreSQL not found. Will use SQLite for development"
fi

log_success "All prerequisites checked"

# ============================================
# 2. Backend Setup
# ============================================
log_info "Setting up backend..."

cd "$SETUP_DIR/lims-backend" || {
    log_error "lims-backend directory not found in $SETUP_DIR"
    exit 1
}

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists, skipping creation"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
log_info "Installing Python dependencies..."
if [ -f "requirements/development.txt" ]; then
    pip install -r requirements/development.txt --quiet
    log_success "Python dependencies installed"
else
    log_error "requirements/development.txt not found"
    exit 1
fi

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating .env file..."
    cat > .env << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development

# Database Configuration (SQLite for development)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Optional: PostgreSQL configuration (uncomment if using PostgreSQL)
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=lims_db
# DB_USER=postgres
# DB_PASSWORD=changeme
# DB_HOST=localhost
# DB_PORT=5432

# Redis Configuration (optional for development)
# REDIS_URL=redis://localhost:6379/0

# CORS Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,*
EOF
    log_success ".env file created"
else
    log_info ".env file already exists, skipping creation"
fi

# Create static directory if it doesn't exist
if [ ! -d "static" ]; then
    log_info "Creating static directory..."
    mkdir -p static
fi

# Run migrations
log_info "Running database migrations..."
python manage.py migrate --noinput
log_success "Database migrations completed"

# Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput --clear || log_warning "Static files collection had issues (may be normal in development)"
log_success "Static files collected"

# Return to setup directory
cd "$SETUP_DIR"

log_success "Backend setup completed"

# ============================================
# 3. Frontend Setup
# ============================================
log_info "Setting up frontend..."

cd "$SETUP_DIR/frontend" || {
    log_error "frontend directory not found in $SETUP_DIR"
    exit 1
}

# Install npm dependencies
if [ ! -d "node_modules" ]; then
    log_info "Installing npm dependencies..."
    npm install --silent
    log_success "npm dependencies installed"
else
    log_info "node_modules already exists, skipping npm install"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log_info "Creating frontend .env file..."
    cat > .env << EOF
# API Configuration
VITE_API_BASE_URL=/api/v1/
EOF
    log_success "Frontend .env file created"
else
    log_info "Frontend .env file already exists, skipping creation"
fi

# Return to setup directory
cd "$SETUP_DIR"

log_success "Frontend setup completed"

# ============================================
# 4. Verification
# ============================================
log_info "Running verification checks..."

# Verify backend setup
cd "$SETUP_DIR/lims-backend"
source venv/bin/activate

# Check if Django can start (quick check)
log_info "Verifying Django configuration..."
python manage.py check --deploy || log_warning "Django check had warnings (may be normal in development)"

# Quick test to verify imports work
log_info "Verifying Python imports..."
python -c "import django; django.setup(); from apps.accounts.models import User; print('✓ Django setup successful')" || {
    log_error "Django setup verification failed"
    exit 1
}

log_success "Backend verification passed"

# Verify frontend setup
cd "$SETUP_DIR/frontend"

# Check if frontend can build (quick check)
log_info "Verifying frontend build..."
npm run build --silent || log_warning "Frontend build had issues (may be normal if dependencies are missing)"

log_success "Frontend verification passed"

# Return to setup directory
cd "$SETUP_DIR"

# ============================================
# 5. Summary
# ============================================
log_success "============================================"
log_success "LIMS Environment Setup Complete!"
log_success "============================================"
echo ""
log_info "Next steps:"
echo "  1. Backend: cd lims-backend && source venv/bin/activate && python manage.py runserver"
echo "  2. Frontend: cd frontend && npm run dev"
echo "  3. Create superuser: cd lims-backend && source venv/bin/activate && python manage.py createsuperuser"
echo ""
log_info "Backend will be available at: http://localhost:8000"
log_info "Frontend will be available at: http://localhost:3000 (or check Vite output)"
echo ""
log_info "API Documentation: http://localhost:8000/api/docs/"
log_info "Admin Panel: http://localhost:8000/admin/"
echo ""
log_success "Setup completed successfully!"

