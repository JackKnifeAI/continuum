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
Export Command - Export memories to JSON or SQLite
"""

import sys
import json
import gzip
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

from continuum.core.memory import get_memory
from ..utils import success, error, info, section, format_size
from ..config import CLIConfig


def export_command(
    output: str,
    format: str,
    include_messages: bool,
    compress: bool,
    config: CLIConfig,
    use_color: bool,
):
    """
    Export memories to JSON or SQLite.

    Args:
        output: Output file path
        format: Export format (json or sqlite)
        include_messages: Whether to include message history
        compress: Whether to compress output
        config: CLI configuration
        use_color: Whether to use colored output
    """
    if not config.db_path or not config.db_path.exists():
        error("CONTINUUM not initialized. Run 'continuum init' first.", use_color)
        sys.exit(1)

    output_path = Path(output)

    section(f"Exporting to {format.upper()}", use_color)
    info(f"Output: {output_path}", use_color)

    try:
        memory = get_memory()

        if format == "json":
            _export_json(
                memory, output_path, include_messages, compress, config, use_color
            )
        elif format == "sqlite":
            _export_sqlite(
                memory, output_path, include_messages, compress, config, use_color
            )
        else:
            error(f"Unknown format: {format}", use_color)
            sys.exit(1)

        # Show file size
        if output_path.exists():
            size = output_path.stat().st_size
            info(f"File size: {format_size(size)}", use_color)

        success(f"Export complete: {output_path}", use_color)

    except Exception as e:
        error(f"Export failed: {e}", use_color)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _export_json(
    memory, output_path: Path, include_messages: bool, compress: bool, config: CLIConfig, use_color: bool
):
    """Export to JSON format"""
    conn = sqlite3.connect(memory.db_path)
    conn.row_factory = sqlite3.Row

    try:
        c = conn.cursor()

        # Build export data
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "tenant_id": memory.tenant_id,
            "entities": [],
            "attention_links": [],
            "compound_concepts": [],
            "decisions": [],
        }

        # Export entities
        info("Exporting entities...", use_color)
        c.execute(
            "SELECT * FROM entities WHERE tenant_id = ?", (memory.tenant_id,)
        )
        export_data["entities"] = [dict(row) for row in c.fetchall()]

        # Export attention links
        info("Exporting attention links...", use_color)
        c.execute(
            "SELECT * FROM attention_links WHERE tenant_id = ?", (memory.tenant_id,)
        )
        export_data["attention_links"] = [dict(row) for row in c.fetchall()]

        # Export compound concepts
        info("Exporting compound concepts...", use_color)
        c.execute(
            "SELECT * FROM compound_concepts WHERE tenant_id = ?", (memory.tenant_id,)
        )
        export_data["compound_concepts"] = [dict(row) for row in c.fetchall()]

        # Export decisions
        info("Exporting decisions...", use_color)
        c.execute(
            "SELECT * FROM decisions WHERE tenant_id = ?", (memory.tenant_id,)
        )
        export_data["decisions"] = [dict(row) for row in c.fetchall()]

        # Export messages if requested
        if include_messages:
            info("Exporting messages...", use_color)
            c.execute(
                "SELECT * FROM auto_messages WHERE tenant_id = ? ORDER BY timestamp",
                (memory.tenant_id,),
            )
            export_data["messages"] = [dict(row) for row in c.fetchall()]

        # Write to file
        json_str = json.dumps(export_data, indent=2, default=str)

        if compress:
            output_path = output_path.with_suffix(output_path.suffix + ".gz")
            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                f.write(json_str)
        else:
            with open(output_path, "w") as f:
                f.write(json_str)

        info(
            f"Exported {len(export_data['entities'])} entities, "
            f"{len(export_data['attention_links'])} links",
            use_color,
        )

    finally:
        conn.close()


def _export_sqlite(
    memory, output_path: Path, include_messages: bool, compress: bool, config: CLIConfig, use_color: bool
):
    """Export to SQLite format"""
    if output_path.exists():
        error(f"Output file already exists: {output_path}", use_color)
        sys.exit(1)

    # Copy database
    info("Copying database...", use_color)
    shutil.copy2(memory.db_path, output_path)

    # If not including messages, remove them
    if not include_messages:
        info("Removing messages...", use_color)
        conn = sqlite3.connect(output_path)
        try:
            c = conn.cursor()
            c.execute("DELETE FROM auto_messages WHERE tenant_id = ?", (memory.tenant_id,))
            conn.commit()

            # Vacuum to reclaim space
            c.execute("VACUUM")
        finally:
            conn.close()

    # Compress if requested
    if compress:
        info("Compressing...", use_color)
        compressed_path = output_path.with_suffix(output_path.suffix + ".gz")
        with open(output_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        output_path.unlink()  # Remove uncompressed file
        output_path = compressed_path

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
