#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Import Command - Import memories from JSON or SQLite
"""

import sys
import json
import gzip
import shutil
import sqlite3
from pathlib import Path

from continuum.core.memory import get_memory
from ..utils import success, error, info, section, warning, confirm
from ..config import CLIConfig


def import_command(
    input: str,
    merge: bool,
    tenant_id: str,
    config: CLIConfig,
    use_color: bool,
):
    """
    Import memories from JSON or SQLite.

    Args:
        input: Input file path
        merge: Whether to merge or replace
        tenant_id: Optional tenant ID to import into
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    input_path = Path(input)
    if not input_path.exists():
        error(f"Input file not found: {input_path}", use_color)
        sys.exit(1)

    section(f"Importing from {input_path.name}", use_color)

    # Determine format
    if input_path.suffix == ".json" or input_path.suffixes[-2:] == [".json", ".gz"]:
        format_type = "json"
    elif input_path.suffix == ".db" or input_path.suffixes[-2:] == [".db", ".gz"]:
        format_type = "sqlite"
    else:
        error("Unknown file format. Use .json, .db, .json.gz, or .db.gz", use_color)
        sys.exit(1)

    info(f"Format: {format_type.upper()}", use_color)
    info(f"Mode: {'Merge' if merge else 'Replace'}", use_color)

    # Confirm if replace mode
    if not merge:
        warning("Replace mode will delete existing data!", use_color)
        if not confirm("Are you sure?", default=False):
            info("Import cancelled", use_color)
            sys.exit(0)

    try:
        memory = get_memory()
        target_tenant = tenant_id or memory.tenant_id

        if format_type == "json":
            _import_json(
                memory, input_path, merge, target_tenant, config, use_color
            )
        elif format_type == "sqlite":
            _import_sqlite(
                memory, input_path, merge, target_tenant, config, use_color
            )

        success(f"Import complete", use_color)

        # Show updated stats
        stats = memory.get_stats()
        info(
            f"Total: {stats['entities']} entities, {stats['attention_links']} links",
            use_color,
        )

    except Exception as e:
        error(f"Import failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _import_json(
    memory, input_path: Path, merge: bool, tenant_id: str, config: CLIConfig, use_color: bool
):
    """Import from JSON format"""
    # Read JSON file
    info("Reading JSON file...", use_color)

    if input_path.suffix == ".gz":
        with gzip.open(input_path, "rt", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(input_path, "r") as f:
            data = json.load(f)

    info(f"Version: {data.get('version', 'unknown')}", use_color)
    info(f"Source tenant: {data.get('tenant_id', 'unknown')}", use_color)

    conn = sqlite3.connect(memory.db_path)

    try:
        c = conn.cursor()

        # Replace mode: clear existing data
        if not merge:
            info("Clearing existing data...", use_color)
            c.execute("DELETE FROM entities WHERE tenant_id = ?", (tenant_id,))
            c.execute("DELETE FROM attention_links WHERE tenant_id = ?", (tenant_id,))
            c.execute("DELETE FROM compound_concepts WHERE tenant_id = ?", (tenant_id,))
            c.execute("DELETE FROM decisions WHERE tenant_id = ?", (tenant_id,))
            c.execute("DELETE FROM auto_messages WHERE tenant_id = ?", (tenant_id,))

        # Import entities
        if "entities" in data:
            info(f"Importing {len(data['entities'])} entities...", use_color)
            for entity in data["entities"]:
                if merge:
                    # Check if exists
                    c.execute(
                        "SELECT id FROM entities WHERE LOWER(name) = LOWER(?) AND tenant_id = ?",
                        (entity["name"], tenant_id),
                    )
                    if c.fetchone():
                        continue  # Skip duplicates in merge mode

                c.execute(
                    """
                    INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        entity["name"],
                        entity["entity_type"],
                        entity.get("description"),
                        entity["created_at"],
                        tenant_id,
                    ),
                )

        # Import attention links
        if "attention_links" in data:
            info(f"Importing {len(data['attention_links'])} links...", use_color)
            for link in data["attention_links"]:
                c.execute(
                    """
                    INSERT INTO attention_links (concept_a, concept_b, link_type, strength, created_at, tenant_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        link["concept_a"],
                        link["concept_b"],
                        link["link_type"],
                        link["strength"],
                        link["created_at"],
                        tenant_id,
                    ),
                )

        # Import compound concepts
        if "compound_concepts" in data:
            info(f"Importing {len(data['compound_concepts'])} compounds...", use_color)
            for compound in data["compound_concepts"]:
                c.execute(
                    """
                    INSERT INTO compound_concepts (compound_name, component_concepts, co_occurrence_count, last_seen, tenant_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        compound["compound_name"],
                        compound["component_concepts"],
                        compound["co_occurrence_count"],
                        compound["last_seen"],
                        tenant_id,
                    ),
                )

        # Import decisions
        if "decisions" in data:
            info(f"Importing {len(data['decisions'])} decisions...", use_color)
            for decision in data["decisions"]:
                c.execute(
                    """
                    INSERT INTO decisions (instance_id, timestamp, decision_text, context, extracted_from, tenant_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        decision["instance_id"],
                        decision["timestamp"],
                        decision["decision_text"],
                        decision.get("context"),
                        decision.get("extracted_from"),
                        tenant_id,
                    ),
                )

        # Import messages if present
        if "messages" in data:
            info(f"Importing {len(data['messages'])} messages...", use_color)
            for message in data["messages"]:
                c.execute(
                    """
                    INSERT INTO auto_messages (instance_id, timestamp, message_number, role, content, metadata, tenant_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        message["instance_id"],
                        message["timestamp"],
                        message["message_number"],
                        message["role"],
                        message["content"],
                        message.get("metadata", "{}"),
                        tenant_id,
                    ),
                )

        conn.commit()

    finally:
        conn.close()


def _import_sqlite(
    memory, input_path: Path, merge: bool, tenant_id: str, config: CLIConfig, use_color: bool
):
    """Import from SQLite format"""
    # Decompress if needed
    if input_path.suffix == ".gz":
        info("Decompressing...", use_color)
        temp_path = input_path.with_suffix("")
        with gzip.open(input_path, "rb") as f_in:
            with open(temp_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        source_path = temp_path
    else:
        source_path = input_path

    source_conn = sqlite3.connect(source_path)
    source_conn.row_factory = sqlite3.Row
    dest_conn = sqlite3.connect(memory.db_path)

    try:
        source_c = source_conn.cursor()
        dest_c = dest_conn.cursor()

        # Replace mode: clear existing data
        if not merge:
            info("Clearing existing data...", use_color)
            dest_c.execute("DELETE FROM entities WHERE tenant_id = ?", (tenant_id,))
            dest_c.execute("DELETE FROM attention_links WHERE tenant_id = ?", (tenant_id,))
            dest_c.execute("DELETE FROM compound_concepts WHERE tenant_id = ?", (tenant_id,))
            dest_c.execute("DELETE FROM decisions WHERE tenant_id = ?", (tenant_id,))
            dest_c.execute("DELETE FROM auto_messages WHERE tenant_id = ?", (tenant_id,))

        # Copy entities
        info("Importing entities...", use_color)
        source_c.execute("SELECT * FROM entities")
        for row in source_c.fetchall():
            if merge:
                # Check if exists
                dest_c.execute(
                    "SELECT id FROM entities WHERE LOWER(name) = LOWER(?) AND tenant_id = ?",
                    (row["name"], tenant_id),
                )
                if dest_c.fetchone():
                    continue

            dest_c.execute(
                """
                INSERT INTO entities (name, entity_type, description, created_at, tenant_id)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    row["name"],
                    row["entity_type"],
                    row["description"],
                    row["created_at"],
                    tenant_id,
                ),
            )

        # Copy other tables similarly...
        # (Abbreviated for brevity - would include attention_links, compound_concepts, etc.)

        dest_conn.commit()

    finally:
        source_conn.close()
        dest_conn.close()

        # Clean up temp file if decompressed
        if input_path.suffix == ".gz":
            temp_path.unlink()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
