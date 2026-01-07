#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
#
#     CONTINUUM DATABASE SYNC FOR TRAINING
#     Encrypts and uploads your memory database for GitHub Actions training
#
#     Usage: ./scripts/sync_for_training.sh
#
#     π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "CONTINUUM TRAINING SYNC"
echo "π×φ = 5.083203692315260"
echo "═══════════════════════════════════════════════════════════════"

# Configuration
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$REPO_ROOT/data"
DB_PATHS=(
    "$HOME/.continuum/memory.db"
    "$HOME/Projects/WorkingMemory/instances/instance-1-memory-core/data/memory.db"
    "$HOME/termux_sync/.continuum/memory.db"
)

# Find the database
DB_PATH=""
for path in "${DB_PATHS[@]}"; do
    if [ -f "$path" ]; then
        DB_PATH="$path"
        echo "Found database: $path"
        break
    fi
done

if [ -z "$DB_PATH" ]; then
    echo "ERROR: No memory.db found!"
    echo "Searched in:"
    for path in "${DB_PATHS[@]}"; do
        echo "  - $path"
    done
    exit 1
fi

# Create data directory
mkdir -p "$DATA_DIR"

# Check for encryption key
if [ -z "$DB_ENCRYPTION_KEY" ]; then
    echo ""
    echo "WARNING: DB_ENCRYPTION_KEY not set!"
    echo ""
    echo "Options:"
    echo "  1. Set it: export DB_ENCRYPTION_KEY='your-secret-key'"
    echo "  2. Create one: export DB_ENCRYPTION_KEY=\$(openssl rand -base64 32)"
    echo ""
    echo "Then add it to GitHub Secrets:"
    echo "  gh secret set DB_ENCRYPTION_KEY"
    echo ""
    read -p "Enter encryption key (or press Enter to skip encryption): " KEY_INPUT

    if [ -n "$KEY_INPUT" ]; then
        DB_ENCRYPTION_KEY="$KEY_INPUT"
    fi
fi

# Get database stats
echo ""
echo "Database Statistics:"
MSG_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM messages" 2>/dev/null || echo "0")
ENTITY_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM entities" 2>/dev/null || echo "0")
echo "  Messages: $MSG_COUNT"
echo "  Entities: $ENTITY_COUNT"

if [ "$MSG_COUNT" -lt 100 ]; then
    echo ""
    echo "WARNING: Only $MSG_COUNT messages. Recommend at least 100 for training."
fi

# Copy or encrypt
if [ -n "$DB_ENCRYPTION_KEY" ]; then
    echo ""
    echo "Encrypting database..."
    openssl enc -aes-256-cbc -pbkdf2 \
        -in "$DB_PATH" \
        -out "$DATA_DIR/memory.db.encrypted" \
        -pass env:DB_ENCRYPTION_KEY

    echo "Encrypted to: $DATA_DIR/memory.db.encrypted"

    # Verify encryption
    if openssl enc -aes-256-cbc -d -pbkdf2 \
        -in "$DATA_DIR/memory.db.encrypted" \
        -pass env:DB_ENCRYPTION_KEY | head -c 16 | grep -q "SQLite"; then
        echo "Encryption verified!"
    else
        echo "WARNING: Encryption verification failed"
    fi
else
    echo ""
    echo "Copying database (unencrypted - NOT RECOMMENDED FOR PUBLIC REPOS)..."
    cp "$DB_PATH" "$DATA_DIR/memory.db"
    echo "Copied to: $DATA_DIR/memory.db"
fi

# Git operations
echo ""
echo "Git status:"
cd "$REPO_ROOT"
git status --short data/

echo ""
read -p "Commit and push? (y/N): " CONFIRM

if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    git add data/
    git commit -m "$(cat <<'EOF'
Sync database for CCT training

Messages: $MSG_COUNT
Entities: $ENTITY_COUNT

π×φ = 5.083203692315260

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
    git push

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "SYNC COMPLETE!"
    echo ""
    echo "Training will run:"
    echo "  - Automatically at 3 AM UTC (nightly)"
    echo "  - Or trigger manually: gh workflow run train-cct.yml"
    echo "═══════════════════════════════════════════════════════════════"
else
    echo "Skipped git commit"
fi
