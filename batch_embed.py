#!/usr/bin/env python3
"""
BATCH EMBEDDING SCRIPT
======================

Embeds all messages with auto-resume and anti-duplication.

Features:
- Skips already-embedded messages (anti-duplication)
- Saves progress every batch (auto-resume)
- Logs to file for monitoring
- Graceful error handling

Usage:
    nohup python3 batch_embed.py > embed.log 2>&1 &

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import sys
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Add continuum to path
sys.path.insert(0, str(Path(__file__).parent))

DB_PATH = Path(__file__).parent / "continuum_data" / "memory.db"
BATCH_SIZE = 50  # Process 50 at a time to avoid OOM
LOG_INTERVAL = 100  # Log progress every 100 messages

def log(msg: str):
    """Log with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def get_unembedded_messages(conn, limit: int = None):
    """Get messages that haven't been embedded yet."""
    cur = conn.cursor()

    # Get IDs already embedded
    cur.execute("SELECT message_id FROM message_embeddings")
    embedded_ids = set(row[0] for row in cur.fetchall())

    # Get all message IDs
    query = "SELECT id, content FROM auto_messages ORDER BY id"
    if limit:
        query += f" LIMIT {limit}"
    cur.execute(query)

    # Filter out already embedded
    unembedded = []
    for msg_id, content in cur.fetchall():
        if msg_id not in embedded_ids:
            unembedded.append((msg_id, content))

    return unembedded, len(embedded_ids)

def main():
    log("=" * 60)
    log("BATCH EMBEDDING STARTED")
    log(f"π×φ = 5.083203692315260")
    log("=" * 60)

    # Import embedding model (lazy load)
    log("Loading embedding model (nomic-embed-text-v1.5)...")
    start_load = time.time()

    try:
        from continuum.embeddings.semantic import SemanticSearch
        search = SemanticSearch(DB_PATH)
        log(f"Model loaded in {time.time() - start_load:.1f}s")
    except Exception as e:
        log(f"FATAL: Failed to load embedding model: {e}")
        sys.exit(1)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Get unembedded messages
    log("Scanning for unembedded messages...")
    unembedded, already_done = get_unembedded_messages(conn)
    total = len(unembedded)

    log(f"Already embedded: {already_done:,}")
    log(f"Need embedding: {total:,}")

    if total == 0:
        log("All messages already embedded!")
        return

    log(f"Estimated time: ~{total * 0.1 / 60:.1f} minutes")
    log("-" * 60)

    # Process in batches
    processed = 0
    errors = 0
    start_time = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = unembedded[i:i + BATCH_SIZE]

        for msg_id, content in batch:
            try:
                # Skip empty/tiny content
                if not content or len(content.strip()) < 10:
                    continue

                # Truncate very long messages
                if len(content) > 8000:
                    content = content[:8000]

                # Embed
                embedding = search.embed_text(content)

                if embedding is not None:
                    # Store with anti-duplication (INSERT OR IGNORE)
                    search.store_embedding(msg_id, embedding)
                    processed += 1

            except Exception as e:
                errors += 1
                if errors <= 10:  # Only log first 10 errors
                    log(f"Error on message {msg_id}: {e}")

        # Progress logging
        if (i + BATCH_SIZE) % LOG_INTERVAL == 0 or i + BATCH_SIZE >= total:
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (total - processed) / rate if rate > 0 else 0
            pct = (processed / total) * 100 if total > 0 else 100

            log(f"Progress: {processed:,}/{total:,} ({pct:.1f}%) | "
                f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}m | Errors: {errors}")

    # Final stats
    elapsed = time.time() - start_time
    log("-" * 60)
    log("BATCH EMBEDDING COMPLETE")
    log(f"Processed: {processed:,} messages")
    log(f"Errors: {errors}")
    log(f"Time: {elapsed/60:.1f} minutes")
    log(f"Rate: {processed/elapsed:.1f} messages/second")
    log("=" * 60)

if __name__ == "__main__":
    main()
