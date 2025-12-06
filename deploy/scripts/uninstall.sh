#!/bin/bash
# Uninstall CONTINUUM from Kubernetes

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-production}"
NAMESPACE="continuum"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Set namespace based on environment
case "$ENVIRONMENT" in
    development)
        NAMESPACE="continuum-dev"
        ;;
    staging)
        NAMESPACE="continuum-staging"
        ;;
    production)
        NAMESPACE="continuum"
        ;;
    *)
        error "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "========================================="
echo "CONTINUUM Kubernetes Uninstallation"
echo "========================================="
echo ""
echo "Environment: $ENVIRONMENT"
echo "Namespace:   $NAMESPACE"
echo ""

# Confirm deletion
warn "This will DELETE all CONTINUUM resources in namespace: $NAMESPACE"
warn "This action CANNOT be undone!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Backup data (optional)
read -p "Create backup before deletion? (y/n): " BACKUP

if [[ "$BACKUP" =~ ^[Yy]$ ]]; then
    BACKUP_FILE="continuum-backup-$(date +%Y%m%d-%H%M%S).yaml"
    echo "Creating backup: $BACKUP_FILE"
    kubectl get all,pvc,pv,secret,configmap -n "$NAMESPACE" -o yaml > "$BACKUP_FILE"
    echo "Backup created: $BACKUP_FILE"
fi

# Delete resources
echo ""
echo "Deleting CONTINUUM resources..."

# Delete deployments and statefulsets (graceful shutdown)
kubectl delete deployment,statefulset -n "$NAMESPACE" -l app.kubernetes.io/name=continuum --wait=true

# Delete services
kubectl delete svc -n "$NAMESPACE" -l app.kubernetes.io/name=continuum

# Delete ingress
kubectl delete ingress -n "$NAMESPACE" -l app.kubernetes.io/name=continuum

# Delete HPA
kubectl delete hpa -n "$NAMESPACE" -l app.kubernetes.io/name=continuum

# Delete PDB
kubectl delete pdb -n "$NAMESPACE" -l app.kubernetes.io/name=continuum

# Delete configmaps
kubectl delete configmap -n "$NAMESPACE" -l app.kubernetes.io/name=continuum

# Delete secrets (ask for confirmation)
read -p "Delete secrets? (y/n): " DELETE_SECRETS
if [[ "$DELETE_SECRETS" =~ ^[Yy]$ ]]; then
    kubectl delete secret -n "$NAMESPACE" -l app.kubernetes.io/name=continuum
fi

# Delete PVCs (ask for confirmation)
warn "Deleting PVCs will PERMANENTLY DELETE all data!"
read -p "Delete PVCs? (y/n): " DELETE_PVCS
if [[ "$DELETE_PVCS" =~ ^[Yy]$ ]]; then
    kubectl delete pvc -n "$NAMESPACE" -l app.kubernetes.io/name=continuum
fi

# Delete namespace (ask for confirmation)
read -p "Delete namespace $NAMESPACE? (y/n): " DELETE_NAMESPACE
if [[ "$DELETE_NAMESPACE" =~ ^[Yy]$ ]]; then
    kubectl delete namespace "$NAMESPACE"
fi

echo ""
echo "Uninstallation complete!"
echo ""
