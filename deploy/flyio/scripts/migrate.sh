#!/usr/bin/env bash
#
# CONTINUUM Database Migration Script
#
# Run database migrations on Fly.io Postgres
#
# Usage:
#   ./scripts/migrate.sh              # Run pending migrations
#   ./scripts/migrate.sh --status     # Check migration status
#   ./scripts/migrate.sh --rollback   # Rollback last migration
#   ./scripts/migrate.sh --reset      # Reset database (DANGER!)

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

APP_NAME="${FLY_APP_NAME:-continuum-memory}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

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

check_fly_cli() {
    if ! command -v fly &> /dev/null; then
        log_error "fly CLI not found. Install from: https://fly.io/docs/hands-on/install-flyctl/"
        exit 1
    fi

    if ! fly auth whoami &> /dev/null; then
        log_error "Not logged in to Fly.io. Run: fly auth login"
        exit 1
    fi
}

# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

run_migrations() {
    log_info "Running database migrations on $APP_NAME..."

    # Run migrations via fly ssh
    fly ssh console -a "$APP_NAME" -C "python -m continuum.storage.migrations upgrade"

    if [ $? -eq 0 ]; then
        log_success "Migrations completed successfully"
    else
        log_error "Migration failed!"
        exit 1
    fi
}

check_migration_status() {
    log_info "Checking migration status for $APP_NAME..."

    fly ssh console -a "$APP_NAME" -C "python -m continuum.storage.migrations status"
}

rollback_migration() {
    log_warning "Rolling back last migration on $APP_NAME..."

    read -p "Are you sure you want to rollback? (yes/no): " -r
    if [[ ! $REPLY =~ ^yes$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    fly ssh console -a "$APP_NAME" -C "python -m continuum.storage.migrations downgrade"

    if [ $? -eq 0 ]; then
        log_success "Rollback completed"
    else
        log_error "Rollback failed!"
        exit 1
    fi
}

reset_database() {
    log_error "DANGER: This will completely reset the database!"
    log_error "ALL DATA WILL BE LOST!"
    echo ""
    read -p "Type 'RESET DATABASE' to confirm: " -r

    if [[ ! $REPLY = "RESET DATABASE" ]]; then
        log_info "Reset cancelled"
        exit 0
    fi

    log_warning "Resetting database on $APP_NAME..."

    fly ssh console -a "$APP_NAME" -C "python -m continuum.storage.migrations reset"

    if [ $? -eq 0 ]; then
        log_success "Database reset completed"

        # Run migrations to recreate schema
        log_info "Running migrations to recreate schema..."
        run_migrations
    else
        log_error "Database reset failed!"
        exit 1
    fi
}

create_backup() {
    log_info "Creating database backup..."

    BACKUP_FILE="continuum_backup_$(date +%Y%m%d_%H%M%S).sql"

    # Get database URL from secrets
    DB_URL=$(fly ssh console -a "$APP_NAME" -C "env | grep DATABASE_URL" | cut -d'=' -f2-)

    if [ -z "$DB_URL" ]; then
        log_error "Could not retrieve DATABASE_URL"
        exit 1
    fi

    # Backup via pg_dump
    log_info "Backing up to $BACKUP_FILE..."
    fly ssh console -a "$APP_NAME" -C "pg_dump '$DB_URL'" > "$BACKUP_FILE"

    if [ $? -eq 0 ]; then
        log_success "Backup created: $BACKUP_FILE"
    else
        log_error "Backup failed!"
        exit 1
    fi
}

# =============================================================================
# POSTGRES MANAGEMENT
# =============================================================================

connect_postgres() {
    log_info "Connecting to Postgres..."

    # Use fly postgres connect
    fly postgres connect -a "${APP_NAME}-db"
}

postgres_status() {
    log_info "Checking Postgres status..."

    fly postgres status -a "${APP_NAME}-db"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    check_fly_cli

    local action="${1:-migrate}"

    case "$action" in
        --status|-s)
            check_migration_status
            ;;
        --rollback|-r)
            rollback_migration
            ;;
        --reset)
            reset_database
            ;;
        --backup|-b)
            create_backup
            ;;
        --connect|-c)
            connect_postgres
            ;;
        --pg-status)
            postgres_status
            ;;
        --help|-h)
            echo "CONTINUUM Database Migration Tool"
            echo ""
            echo "Usage:"
            echo "  $0              Run pending migrations"
            echo "  $0 --status     Check migration status"
            echo "  $0 --rollback   Rollback last migration"
            echo "  $0 --reset      Reset database (DANGER!)"
            echo "  $0 --backup     Create database backup"
            echo "  $0 --connect    Connect to Postgres console"
            echo "  $0 --pg-status  Check Postgres cluster status"
            echo "  $0 --help       Show this help"
            echo ""
            echo "Environment variables:"
            echo "  FLY_APP_NAME    Fly.io app name (default: continuum-memory)"
            ;;
        *)
            run_migrations
            ;;
    esac
}

main "$@"
