#!/bin/bash
# Build Docker image for CONTINUUM

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$DEPLOY_DIR")"

# Default values
IMAGE_NAME="${IMAGE_NAME:-continuum}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"
PLATFORM="${PLATFORM:-linux/amd64}"
BUILD_CONTEXT="${BUILD_CONTEXT:-$PROJECT_DIR}"
DOCKERFILE="${DOCKERFILE:-$DEPLOY_DIR/Dockerfile}"
PUSH="${PUSH:-false}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Full image name with registry
if [[ -n "$REGISTRY" ]]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
fi

echo "========================================="
echo "Building CONTINUUM Docker Image"
echo "========================================="
echo ""
echo "Image:      $FULL_IMAGE_NAME"
echo "Platform:   $PLATFORM"
echo "Context:    $BUILD_CONTEXT"
echo "Dockerfile: $DOCKERFILE"
echo "Push:       $PUSH"
echo ""

# Build image
info "Building image..."
docker build \
    --platform "$PLATFORM" \
    --file "$DOCKERFILE" \
    --tag "$FULL_IMAGE_NAME" \
    --build-arg VERSION="$IMAGE_TAG" \
    "$BUILD_CONTEXT"

info "Image built successfully: $FULL_IMAGE_NAME"

# Show image size
IMAGE_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "{{.Size}}")
info "Image size: $IMAGE_SIZE"

# Push if requested
if [[ "$PUSH" == "true" ]]; then
    if [[ -z "$REGISTRY" ]]; then
        warn "REGISTRY not set. Cannot push image."
        exit 1
    fi

    info "Pushing image to registry..."
    docker push "$FULL_IMAGE_NAME"
    info "Image pushed successfully!"
fi

# Security scan (if trivy is installed)
if command -v trivy &> /dev/null; then
    info "Running security scan with trivy..."
    trivy image "$FULL_IMAGE_NAME"
fi

echo ""
info "Build complete!"
echo ""
echo "Next steps:"
echo "  1. Test image: docker run --rm -p 8420:8420 $FULL_IMAGE_NAME"
echo "  2. Push to registry: PUSH=true REGISTRY=your-registry ./build-image.sh"
echo "  3. Update Kubernetes manifests with new image tag"
echo ""
