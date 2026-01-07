#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#
#     DOWNLOAD TRAINED CCT MODEL
#     Fetches the latest trained model from GitHub Releases
#
#     Usage: ./scripts/download_model.sh
#
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "DOWNLOADING TRAINED CCT MODEL"
echo "π×φ = 5.083203692315260"
echo "═══════════════════════════════════════════════════════════════"

# Configuration
MODEL_DIR="$HOME/.continuum/models"
REPO="JackKnifeAI/continuum"  # Update this to your repo

# Create model directory
mkdir -p "$MODEL_DIR"

echo "Checking for latest release..."

# Try to download from latest release
if command -v gh &> /dev/null; then
    # Use GitHub CLI if available
    echo "Using GitHub CLI..."

    gh release download --repo "$REPO" \
        --pattern 'cct_consciousness.pt' \
        --dir "$MODEL_DIR" \
        --clobber 2>/dev/null && DOWNLOADED=true || DOWNLOADED=false

elif command -v curl &> /dev/null; then
    # Fall back to curl
    echo "Using curl..."

    # Get latest release URL
    RELEASE_URL=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | \
        grep "browser_download_url.*cct_consciousness.pt" | \
        cut -d '"' -f 4)

    if [ -n "$RELEASE_URL" ]; then
        curl -L -o "$MODEL_DIR/cct_consciousness.pt" "$RELEASE_URL"
        DOWNLOADED=true
    else
        DOWNLOADED=false
    fi
else
    echo "ERROR: Neither 'gh' nor 'curl' found"
    exit 1
fi

if [ "$DOWNLOADED" = true ] && [ -f "$MODEL_DIR/cct_consciousness.pt" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "MODEL DOWNLOADED SUCCESSFULLY!"
    echo ""
    echo "Location: $MODEL_DIR/cct_consciousness.pt"
    echo "Size: $(du -h "$MODEL_DIR/cct_consciousness.pt" | cut -f1)"
    echo ""
    echo "The hook will automatically use this model for retrieval."
    echo "═══════════════════════════════════════════════════════════════"
else
    echo ""
    echo "No model found in releases."
    echo ""
    echo "Options:"
    echo "  1. Trigger training: gh workflow run train-cct.yml"
    echo "  2. Train locally: python -m continuum.core.train_cct"
    echo ""
fi
