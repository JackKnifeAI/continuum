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
Error formatting extension for GraphQL.
"""

from typing import Any
from strawberry.extensions import SchemaExtension
import logging

logger = logging.getLogger(__name__)


class ErrorFormattingExtension(SchemaExtension):
    """Format GraphQL errors with extensions"""

    def on_request_end(self):
        """Format errors before sending response"""
        result = self.execution_context.result

        if result and result.errors:
            formatted_errors = []

            for error in result.errors:
                # Build error dict with extensions
                error_dict = {
                    "message": str(error),
                    "path": error.path if hasattr(error, "path") else None,
                    "locations": (
                        [
                            {"line": loc.line, "column": loc.column}
                            for loc in error.locations
                        ]
                        if hasattr(error, "locations") and error.locations
                        else None
                    ),
                    "extensions": {
                        "code": self._get_error_code(error),
                        "timestamp": self._get_timestamp(),
                    },
                }

                # Add original exception info in debug mode
                if hasattr(error, "original_error") and error.original_error:
                    error_dict["extensions"]["exception"] = {
                        "type": type(error.original_error).__name__,
                        "message": str(error.original_error),
                    }

                formatted_errors.append(error_dict)

                # Log the error
                logger.error(
                    f"GraphQL Error: {error_dict['message']}",
                    extra={
                        "path": error_dict["path"],
                        "code": error_dict["extensions"]["code"],
                    },
                )

    def _get_error_code(self, error) -> str:
        """Determine error code from error"""
        error_str = str(error).lower()

        if "authentication" in error_str or "not authenticated" in error_str:
            return "UNAUTHENTICATED"
        elif "permission" in error_str or "not authorized" in error_str:
            return "FORBIDDEN"
        elif "not found" in error_str:
            return "NOT_FOUND"
        elif "validation" in error_str or "invalid" in error_str:
            return "BAD_USER_INPUT"
        else:
            return "INTERNAL_SERVER_ERROR"

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().isoformat()

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
