#!/bin/bash

# ============================================
# LIMS Health Check & Monitoring Script
# ============================================
#
# Comprehensive health monitoring for production LIMS deployment
# Checks all services and provides detailed status reports
#
# Usage:
#   ./health-check.sh                    # Run all checks
#   ./health-check.sh --quick            # Quick status check
#   ./health-check.sh --detailed         # Detailed report
#   ./health-check.sh --alert-email      # Send alert via email
#   ./health-check.sh --monitor          # Continuous monitoring
#
# Setup for cron jobs:
#   # Run every 5 minutes
#   */5 * * * * /opt/lims/health-check.sh >> /opt/lims/logs/health-check.log 2>&1
#
#   # Run every hour (detailed)
#   0 * * * * /opt/lims/health-check.sh --detailed >> /opt/lims/logs/health-check-detailed.log 2>&1

set -e

# ============================================
# CONFIGURATION
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
LOG_DIR="${PROJECT_ROOT}/logs"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
HEALTH_LOG="${LOG_DIR}/health-check.log"
ALERT_LOG="${LOG_DIR}/health-check-alerts.log"
METRICS_LOG="${LOG_DIR}/health-check-metrics.log"

# Thresholds
DISK_THRESHOLD=90  # percent
MEMORY_THRESHOLD=80  # percent
CPU_THRESHOLD=80  # percent

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure logs directory exists
mkdir -p "$LOG_DIR"

# ============================================
# UTILITY FUNCTIONS
# ============================================

log_message() {
    echo "[${TIMESTAMP}] $1" | tee -a "$HEALTH_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} [${TIMESTAMP}] $1" | tee -a "$HEALTH_LOG"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} [${TIMESTAMP}] $1" | tee -a "$HEALTH_LOG"
    echo "[${TIMESTAMP}] WARNING: $1" >> "$ALERT_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} [${TIMESTAMP}] $1" | tee -a "$HEALTH_LOG"
    echo "[${TIMESTAMP}] ERROR: $1" >> "$ALERT_LOG"
}

print_section() {
    echo "" | tee -a "$HEALTH_LOG"
    echo "========================================" | tee -a "$HEALTH_LOG"
    echo "  $1" | tee -a "$HEALTH_LOG"
    echo "========================================" | tee -a "$HEALTH_LOG"
}

# ============================================
# SERVICE HEALTH CHECKS
# ============================================

check_docker_services() {
    print_section "Docker Services Status"
    
    local all_healthy=true
    
    # Get service status
    local services=$(docker compose ps --services)
    
    for service in $services; do
        local status=$(docker compose ps --filter "name=$service" --format "{{.State}}")
        
        if [[ "$status" == "running" ]]; then
            log_success "$service: Running"
        else
            log_error "$service: $status (Not running)"
            all_healthy=false
        fi
    done
    
    return $([ "$all_healthy" = true ] && echo 0 || echo 1)
}

check_backend_api() {
    print_section "Backend API Status"
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health/)
    
    if [ "$response" = "200" ]; then
        log_success "Backend API: Responding (HTTP $response)"
        return 0
    else
        log_error "Backend API: Not responding (HTTP $response)"
        return 1
    fi
}

check_database() {
    print_section "Database Status"
    
    if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        # Get database size
        local db_size=$(docker compose exec -T db psql -U postgres -t -c "
            SELECT pg_size_pretty(pg_database.datsize)
            FROM pg_database
            WHERE datname = 'lims_db';
        " 2>/dev/null | xargs)
        
        # Get connection count
        local connections=$(docker compose exec -T db psql -U postgres -t -c "
            SELECT count(*)
            FROM pg_stat_activity
            WHERE datname = 'lims_db';
        " 2>/dev/null | xargs)
        
        log_success "PostgreSQL: Connected"
        log_message "  Database Size: $db_size"
        log_message "  Active Connections: $connections"
        return 0
    else
        log_error "PostgreSQL: Not responding"
        return 1
    fi
}

check_redis() {
    print_section "Redis Status"
    
    if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        # Get Redis memory usage
        local memory=$(docker compose exec -T redis redis-cli info memory 2>/dev/null | grep used_memory_human)
        
        # Get number of keys
        local keys=$(docker compose exec -T redis redis-cli DBSIZE 2>/dev/null | grep -o '[0-9]*')
        
        log_success "Redis: Connected"
        log_message "  $memory"
        log_message "  Keys in database: $keys"
        return 0
    else
        log_error "Redis: Not responding"
        return 1
    fi
}

check_frontend() {
    print_section "Frontend Status"
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8012/index.html)
    
    if [ "$response" = "200" ]; then
        log_success "Frontend: Accessible (HTTP $response)"
        return 0
    else
        log_error "Frontend: Not accessible (HTTP $response)"
        return 1
    fi
}

check_caddy() {
    print_section "Caddy Reverse Proxy Status"
    
    if docker compose exec -T proxy caddy version > /dev/null 2>&1; then
        log_success "Caddy: Running"
        
        # Check if health endpoint responds
        if curl -sf http://localhost:8012/health > /dev/null 2>&1; then
            log_success "Health endpoint: Responding"
            return 0
        else
            log_warning "Health endpoint: Not responding (HTTPS cert may not be ready yet)"
            return 0
        fi
    else
        log_error "Caddy: Not running"
        return 1
    fi
}

# ============================================
# SYSTEM RESOURCE CHECKS
# ============================================

check_disk_space() {
    print_section "Disk Space Usage"
    
    local root_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    local app_usage=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
    local app_size=$(du -sh "$PROJECT_ROOT" | awk '{print $1}')
    
    echo "Root Filesystem: ${root_usage}%" | tee -a "$HEALTH_LOG"
    echo "App Directory: ${app_usage}% (${app_size})" | tee -a "$HEALTH_LOG"
    
    if [ "$root_usage" -gt "$DISK_THRESHOLD" ]; then
        log_warning "Disk usage above ${DISK_THRESHOLD}% threshold: ${root_usage}%"
        return 1
    else
        log_success "Disk usage normal: ${root_usage}%"
        return 0
    fi
}

check_memory_usage() {
    print_section "Memory Usage"
    
    local total_memory=$(free -h | awk 'NR==2 {print $2}')
    local used_memory=$(free -h | awk 'NR==2 {print $3}')
    local memory_percent=$(free | awk 'NR==2 {printf("%.0f", $3/$2 * 100)}')
    
    echo "Total: $total_memory | Used: $used_memory | Usage: ${memory_percent}%" | tee -a "$HEALTH_LOG"
    
    if [ "$memory_percent" -gt "$MEMORY_THRESHOLD" ]; then
        log_warning "Memory usage above ${MEMORY_THRESHOLD}% threshold: ${memory_percent}%"
        return 1
    else
        log_success "Memory usage normal: ${memory_percent}%"
        return 0
    fi
}

check_docker_resources() {
    print_section "Docker Container Resource Usage"
    
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tee -a "$HEALTH_LOG"
}

# ============================================
# LOG AND BACKUP CHECKS
# ============================================

check_logs() {
    print_section "Log Files Status"
    
    # Check log directory size
    local log_size=$(du -sh "$LOG_DIR" 2>/dev/null | awk '{print $1}')
    log_message "Total logs size: $log_size"
    
    # Check for recent errors in logs
    if [ -f "${PROJECT_ROOT}/logs/django.log" ]; then
        local error_count=$(grep -c "ERROR" "${PROJECT_ROOT}/logs/django.log" 2>/dev/null || echo "0")
        if [ "$error_count" -gt "0" ]; then
            log_warning "Found $error_count ERROR entries in Django logs"
            log_message "Last 5 errors:"
            grep "ERROR" "${PROJECT_ROOT}/logs/django.log" | tail -5 | tee -a "$HEALTH_LOG"
        fi
    fi
    
    # Check security logs
    if [ -f "${PROJECT_ROOT}/logs/security.log" ]; then
        local security_count=$(wc -l < "${PROJECT_ROOT}/logs/security.log" 2>/dev/null || echo "0")
        if [ "$security_count" -gt "0" ]; then
            log_warning "Found $security_count entries in security log"
        fi
    fi
}

check_backups() {
    print_section "Database Backups Status"
    
    local backup_count=$(find "${PROJECT_ROOT}/backups" -name "lims_db_*.sql.gz" -type f 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt 0 ]; then
        log_success "Found $backup_count database backups"
        
        # Show latest backup
        local latest_backup=$(ls -t "${PROJECT_ROOT}/backups"/lims_db_*.sql.gz 2>/dev/null | head -1)
        if [ -n "$latest_backup" ]; then
            local backup_size=$(du -h "$latest_backup" | awk '{print $1}')
            local backup_date=$(stat -f%Sm -t%Y-%m-%d "$latest_backup" 2>/dev/null || stat --format=%y "$latest_backup" 2>/dev/null | awk '{print $1}')
            log_message "Latest backup: $(basename "$latest_backup") (${backup_size}) - ${backup_date}"
        fi
    else
        log_warning "No database backups found!"
    fi
}

# ============================================
# DETAILED ANALYSIS
# ============================================

run_detailed_checks() {
    print_section "Running Detailed Health Analysis"
    
    # Container health status
    log_message ""
    log_message "Container Health Status:"
    docker compose ps --format "table {{.Names}}\t{{.State}}\t{{.Health}}" | tee -a "$HEALTH_LOG"
    
    # Network connectivity
    log_message ""
    log_message "Network Connectivity:"
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        log_success "Internet connectivity: OK"
    else
        log_warning "Internet connectivity: No external access"
    fi
    
    # Port availability
    log_message ""
    log_message "Port Availability:"
    for port in 80 443 8012 8000 5432 6379; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            log_success "Port $port: In use"
        fi
    done
}

# ============================================
# ALERT FUNCTIONS
# ============================================

send_email_alert() {
    local subject="[LIMS Alert] Health Check Issues - $(date '+%Y-%m-%d %H:%M:%S')"
    local body=$(cat "$ALERT_LOG" 2>/dev/null | tail -20)
    
    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "${ALERT_EMAIL:-admin@example.com}"
        log_message "Alert email sent to ${ALERT_EMAIL:-admin@example.com}"
    else
        log_warning "Mail command not found. Install mailutils to enable email alerts."
    fi
}

# ============================================
# MONITORING MODE
# ============================================

continuous_monitoring() {
    print_section "Starting Continuous Monitoring (Press Ctrl+C to exit)"
    
    while true; do
        clear
        echo "LIMS Health Monitor - $(date)"
        echo "========================================"
        
        # Quick status checks
        check_docker_services || true
        check_backend_api || true
        check_database || true
        check_redis || true
        
        # System resources
        echo ""
        echo "System Resources:"
        free -h | head -2
        echo ""
        df -h / | tail -1
        
        echo ""
        echo "Next update in 30 seconds... (Ctrl+C to exit)"
        sleep 30
    done
}

# ============================================
# MAIN EXECUTION
# ============================================

main() {
    log_message "========== LIMS Health Check Started =========="
    
    local overall_status=0
    
    # Parse command line arguments
    case "${1:-}" in
        --quick)
            check_docker_services || overall_status=1
            check_backend_api || overall_status=1
            check_database || overall_status=1
            check_redis || overall_status=1
            ;;
        --detailed)
            check_docker_services || overall_status=1
            check_backend_api || overall_status=1
            check_database || overall_status=1
            check_redis || overall_status=1
            check_frontend || overall_status=1
            check_caddy || overall_status=1
            check_disk_space || overall_status=1
            check_memory_usage || overall_status=1
            check_docker_resources || overall_status=1
            check_logs || overall_status=1
            check_backups || overall_status=1
            run_detailed_checks || overall_status=1
            ;;
        --alert-email)
            check_docker_services || overall_status=1
            check_backend_api || overall_status=1
            check_database || overall_status=1
            check_redis || overall_status=1
            check_disk_space || overall_status=1
            check_memory_usage || overall_status=1
            
            if [ $overall_status -ne 0 ] && [ -n "$ALERT_EMAIL" ]; then
                send_email_alert
            fi
            ;;
        --monitor)
            continuous_monitoring
            ;;
        *)
            # Default: Run all standard checks
            check_docker_services || overall_status=1
            check_backend_api || overall_status=1
            check_database || overall_status=1
            check_redis || overall_status=1
            check_frontend || overall_status=1
            check_caddy || overall_status=1
            check_disk_space || overall_status=1
            check_memory_usage || overall_status=1
            check_logs || overall_status=1
            check_backups || overall_status=1
            ;;
    esac
    
    # Print summary
    print_section "Health Check Complete"
    if [ $overall_status -eq 0 ]; then
        log_success "All checks passed!"
    else
        log_error "Some checks failed. Review log for details: $HEALTH_LOG"
    fi
    
    log_message "========== Health Check Completed =========="
    
    return $overall_status
}

# Run main function
main "$@"
