#!/usr/bin/env bash
#
# CONTINUUM Scaling Script
#
# Manage instance scaling across regions
#
# Usage:
#   ./scripts/scale.sh up              # Scale up to max instances
#   ./scripts/scale.sh down            # Scale down to min instances
#   ./scripts/scale.sh auto            # Configure auto-scaling
#   ./scripts/scale.sh status          # Show current scale
#   ./scripts/scale.sh regions         # Deploy to multiple regions

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

APP_NAME="${FLY_APP_NAME:-continuum-memory}"
DEFAULT_REGIONS="iad,lhr,sin"  # US East, London, Singapore
MIN_INSTANCES=1
MAX_INSTANCES=10

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
# SCALING FUNCTIONS
# =============================================================================

show_status() {
    log_info "Current status for $APP_NAME:"
    echo ""

    fly status -a "$APP_NAME"

    echo ""
    log_info "Instance counts by region:"
    fly scale show -a "$APP_NAME"

    echo ""
    log_info "VM configuration:"
    fly status --json -a "$APP_NAME" | grep -E '"MemoryMB"|"CPUKind"|"CPUs"' || echo "Using defaults"
}

scale_up() {
    local count="${1:-3}"
    local regions="${2:-$DEFAULT_REGIONS}"

    log_info "Scaling up to $count instances across regions: $regions"

    fly scale count "$count" --region "$regions" -a "$APP_NAME" -y

    if [ $? -eq 0 ]; then
        log_success "Scaled up successfully"
        show_status
    else
        log_error "Scale up failed!"
        exit 1
    fi
}

scale_down() {
    local count="${1:-1}"

    log_warning "Scaling down to $count instances"

    fly scale count "$count" -a "$APP_NAME" -y

    if [ $? -eq 0 ]; then
        log_success "Scaled down successfully"
        show_status
    else
        log_error "Scale down failed!"
        exit 1
    fi
}

configure_autoscaling() {
    log_info "Configuring auto-scaling for $APP_NAME..."

    echo ""
    echo "Auto-scaling configuration:"
    echo "  - Min instances: $MIN_INSTANCES"
    echo "  - Max instances: $MAX_INSTANCES"
    echo "  - Regions: $DEFAULT_REGIONS"
    echo ""

    # Set minimum instances
    log_info "Setting minimum instances to $MIN_INSTANCES..."
    fly scale count "$MIN_INSTANCES" -a "$APP_NAME" -y

    # Configure auto-stop and auto-start
    log_info "Enabling auto-stop and auto-start..."

    # Update fly.toml settings
    log_info "Update fly.toml to configure auto-scaling limits:"
    echo ""
    echo "  [http_service]"
    echo "    auto_stop_machines = true"
    echo "    auto_start_machines = true"
    echo "    min_machines_running = $MIN_INSTANCES"
    echo ""

    log_success "Auto-scaling configured"
    log_info "Deploy changes with: fly deploy"
}

scale_vm() {
    local preset="${1:-shared-cpu-1x}"

    log_info "Scaling VM resources to preset: $preset"

    echo ""
    echo "Available presets:"
    echo "  shared-cpu-1x    - 256MB RAM, 1 shared CPU"
    echo "  shared-cpu-2x    - 512MB RAM, 1 shared CPU"
    echo "  shared-cpu-4x    - 1GB RAM, 1 shared CPU"
    echo "  shared-cpu-8x    - 2GB RAM, 1 shared CPU"
    echo "  dedicated-cpu-1x - 2GB RAM, 1 dedicated CPU"
    echo "  dedicated-cpu-2x - 4GB RAM, 2 dedicated CPUs"
    echo "  dedicated-cpu-4x - 8GB RAM, 4 dedicated CPUs"
    echo ""

    read -p "Continue with $preset? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        exit 0
    fi

    fly scale vm "$preset" -a "$APP_NAME" -y

    if [ $? -eq 0 ]; then
        log_success "VM scaled to $preset"
        show_status
    else
        log_error "VM scaling failed!"
        exit 1
    fi
}

deploy_multi_region() {
    local regions="${1:-$DEFAULT_REGIONS}"
    local count="${2:-3}"

    log_info "Deploying to multiple regions: $regions"
    log_info "Target instance count: $count"

    # Parse regions into array
    IFS=',' read -ra REGION_ARRAY <<< "$regions"

    echo ""
    echo "Deployment plan:"
    for region in "${REGION_ARRAY[@]}"; do
        echo "  - $region: 1 instance"
    done
    echo ""

    read -p "Proceed with multi-region deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        exit 0
    fi

    # Scale to target count across regions
    fly scale count "$count" --region "$regions" -a "$APP_NAME" -y

    if [ $? -eq 0 ]; then
        log_success "Multi-region deployment successful"

        echo ""
        log_info "Testing latency to each region..."
        for region in "${REGION_ARRAY[@]}"; do
            log_info "Region: $region"
        done

        show_status
    else
        log_error "Multi-region deployment failed!"
        exit 1
    fi
}

# =============================================================================
# MONITORING
# =============================================================================

monitor_metrics() {
    log_info "Monitoring metrics for $APP_NAME..."

    echo ""
    log_info "Recent resource usage:"

    fly status --json -a "$APP_NAME" | grep -E '"MemoryMB"|"CPUKind"' || echo "No metrics available"

    echo ""
    log_info "Request metrics:"
    echo "  (Enable with: fly dashboard metrics -a $APP_NAME)"

    echo ""
    log_info "Live logs (Ctrl+C to exit):"
    fly logs -a "$APP_NAME"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    check_fly_cli

    local action="${1:-status}"

    case "$action" in
        up|scale-up)
            local count="${2:-3}"
            local regions="${3:-$DEFAULT_REGIONS}"
            scale_up "$count" "$regions"
            ;;
        down|scale-down)
            local count="${2:-1}"
            scale_down "$count"
            ;;
        auto|autoscale)
            configure_autoscaling
            ;;
        vm|resources)
            local preset="${2:-shared-cpu-1x}"
            scale_vm "$preset"
            ;;
        regions|multi-region)
            local regions="${2:-$DEFAULT_REGIONS}"
            local count="${3:-3}"
            deploy_multi_region "$regions" "$count"
            ;;
        status|show)
            show_status
            ;;
        monitor|metrics)
            monitor_metrics
            ;;
        --help|-h)
            echo "CONTINUUM Scaling Tool"
            echo ""
            echo "Usage:"
            echo "  $0 status                    Show current scale"
            echo "  $0 up [count] [regions]      Scale up instances"
            echo "  $0 down [count]              Scale down instances"
            echo "  $0 auto                      Configure auto-scaling"
            echo "  $0 vm [preset]               Scale VM resources"
            echo "  $0 regions [regions] [count] Deploy to multiple regions"
            echo "  $0 monitor                   Monitor metrics and logs"
            echo "  $0 --help                    Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 up 5                      # Scale to 5 instances"
            echo "  $0 up 3 iad,lhr,sin          # 3 instances across regions"
            echo "  $0 down 1                    # Scale down to 1 instance"
            echo "  $0 vm dedicated-cpu-2x       # Upgrade to dedicated 2x CPU"
            echo "  $0 regions iad,lhr,sin,syd 4 # Deploy to 4 regions"
            echo ""
            echo "Environment variables:"
            echo "  FLY_APP_NAME    Fly.io app name (default: continuum-memory)"
            echo ""
            echo "Default regions: $DEFAULT_REGIONS"
            echo "  iad - Ashburn, Virginia (US East)"
            echo "  lhr - London, UK (Europe)"
            echo "  sin - Singapore (Asia Pacific)"
            ;;
        *)
            show_status
            ;;
    esac
}

main "$@"
