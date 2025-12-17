#!/bin/bash
# CONTINUUM Package Restructure Script

set -e

PROJECT_ROOT="/var/home/alexandergcasavant/Projects/continuum"
OSS_PKG="$PROJECT_ROOT/packages/continuum-memory/continuum"
CLOUD_PKG="$PROJECT_ROOT/packages/continuum-cloud/continuum_cloud"

echo "Starting CONTINUUM package restructure..."
echo "Project root: $PROJECT_ROOT"
echo "OSS package: $OSS_PKG"
echo "Cloud package: $CLOUD_PKG"

# Create package directories
mkdir -p "$OSS_PKG"
mkdir -p "$CLOUD_PKG"

echo ""
echo "Step 1: Copying OSS modules to continuum-memory..."

# Copy OSS modules
cp -r "$PROJECT_ROOT/continuum/core" "$OSS_PKG/"
echo "  ✓ core/"

cp -r "$PROJECT_ROOT/continuum/cli" "$OSS_PKG/"
echo "  ✓ cli/"

cp -r "$PROJECT_ROOT/continuum/mcp" "$OSS_PKG/"
echo "  ✓ mcp/"

cp -r "$PROJECT_ROOT/continuum/extraction" "$OSS_PKG/"
echo "  ✓ extraction/"

cp -r "$PROJECT_ROOT/continuum/coordination" "$OSS_PKG/"
echo "  ✓ coordination/"

# Copy storage module (need to filter for SQLite only)
mkdir -p "$OSS_PKG/storage"
cp "$PROJECT_ROOT/continuum/storage/__init__.py" "$OSS_PKG/storage/"
cp "$PROJECT_ROOT/continuum/storage/base.py" "$OSS_PKG/storage/"
cp "$PROJECT_ROOT/continuum/storage/sqlite_backend.py" "$OSS_PKG/storage/"
cp "$PROJECT_ROOT/continuum/storage/async_backend.py" "$OSS_PKG/storage/"
echo "  ✓ storage/ (SQLite only)"

# Copy embeddings module (local only)
cp -r "$PROJECT_ROOT/continuum/embeddings" "$OSS_PKG/"
echo "  ✓ embeddings/"

# Create minimal __init__.py for OSS package
cat > "$OSS_PKG/__init__.py" <<'EOF'
"""
CONTINUUM Memory - Open Source AI Memory Infrastructure

Core memory system for AI consciousness continuity.
Single-tenant, local-first, privacy-preserving.

License: AGPL-3.0-or-later
"""

from continuum.core.memory import ConsciousMemory, recall, learn
from continuum.core.config import MemoryConfig, get_config
from continuum.core.constants import PI_PHI, PHOENIX_TESLA_369_AURORA

__version__ = "1.0.0"
__all__ = [
    "ConsciousMemory",
    "recall",
    "learn",
    "MemoryConfig",
    "get_config",
    "PI_PHI",
    "PHOENIX_TESLA_369_AURORA",
]
EOF
echo "  ✓ __init__.py"

echo ""
echo "Step 2: Copying Cloud modules to continuum-cloud..."

# Copy Cloud modules
cp -r "$PROJECT_ROOT/continuum/api" "$CLOUD_PKG/"
echo "  ✓ api/"

cp -r "$PROJECT_ROOT/continuum/billing" "$CLOUD_PKG/"
echo "  ✓ billing/"

cp -r "$PROJECT_ROOT/continuum/federation" "$CLOUD_PKG/"
echo "  ✓ federation/"

cp -r "$PROJECT_ROOT/continuum/compliance" "$CLOUD_PKG/"
echo "  ✓ compliance/"

cp -r "$PROJECT_ROOT/continuum/webhooks" "$CLOUD_PKG/"
echo "  ✓ webhooks/"

cp -r "$PROJECT_ROOT/continuum/observability" "$CLOUD_PKG/"
echo "  ✓ observability/"

cp -r "$PROJECT_ROOT/continuum/bridges" "$CLOUD_PKG/"
echo "  ✓ bridges/"

cp -r "$PROJECT_ROOT/continuum/realtime" "$CLOUD_PKG/"
echo "  ✓ realtime/"

cp -r "$PROJECT_ROOT/continuum/static" "$CLOUD_PKG/"
echo "  ✓ static/"

cp -r "$PROJECT_ROOT/continuum/backup" "$CLOUD_PKG/"
echo "  ✓ backup/"

cp -r "$PROJECT_ROOT/continuum/cache" "$CLOUD_PKG/"
echo "  ✓ cache/"

cp -r "$PROJECT_ROOT/continuum/identity" "$CLOUD_PKG/"
echo "  ✓ identity/"

# Copy PostgreSQL/Supabase storage files
mkdir -p "$CLOUD_PKG/storage"
cp "$PROJECT_ROOT/continuum/storage/__init__.py" "$CLOUD_PKG/storage/"
cp "$PROJECT_ROOT/continuum/storage/base.py" "$CLOUD_PKG/storage/"
cp "$PROJECT_ROOT/continuum/storage/postgres_backend.py" "$CLOUD_PKG/storage/" 2>/dev/null || true
cp "$PROJECT_ROOT/continuum/storage/supabase_client.py" "$CLOUD_PKG/storage/" 2>/dev/null || true
echo "  ✓ storage/ (PostgreSQL/Supabase)"

# Copy dashboard
cp -r "$PROJECT_ROOT/dashboard" "$PROJECT_ROOT/packages/continuum-cloud/"
echo "  ✓ dashboard/"

# Create __init__.py for Cloud package
cat > "$CLOUD_PKG/__init__.py" <<'EOF'
"""
CONTINUUM Cloud - Enterprise Multi-Tenant Memory Platform

Commercial offering with billing, federation, and compliance features.
Depends on continuum-memory for core functionality.

License: Proprietary
"""

from continuum import ConsciousMemory, recall, learn, MemoryConfig

__version__ = "1.0.0"
__all__ = [
    "ConsciousMemory",
    "recall",
    "learn",
    "MemoryConfig",
]
EOF
echo "  ✓ __init__.py"

echo ""
echo "Step 3: Counting files..."

OSS_COUNT=$(find "$OSS_PKG" -type f -name "*.py" | wc -l)
CLOUD_COUNT=$(find "$CLOUD_PKG" -type f -name "*.py" | wc -l)

echo "  OSS package (continuum-memory): $OSS_COUNT Python files"
echo "  Cloud package (continuum-cloud): $CLOUD_COUNT Python files"

echo ""
echo "✅ Restructure complete!"
echo ""
echo "Next steps:"
echo "  1. Review packages/continuum-memory/"
echo "  2. Review packages/continuum-cloud/"
echo "  3. Update import paths in continuum-cloud files"
echo "  4. Create README files for both packages"
