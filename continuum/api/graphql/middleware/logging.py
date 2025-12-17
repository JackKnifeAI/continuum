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
Logging extension for GraphQL queries.
"""

import logging
import time
from typing import Any
from strawberry.extensions import SchemaExtension

logger = logging.getLogger(__name__)


class LoggingExtension(SchemaExtension):
    """Log GraphQL operations with timing"""

    def on_operation(self):
        """Called when operation starts"""
        self.start_time = time.time()

    def on_request_end(self):
        """Called when request ends"""
        duration = (time.time() - self.start_time) * 1000

        execution_context = self.execution_context

        # Get operation info
        operation_name = execution_context.operation_name
        operation_type = (
            execution_context.graphql_document.definitions[0].operation.value
            if execution_context.graphql_document.definitions
            else "unknown"
        )

        # Log the operation
        logger.info(
            f"GraphQL {operation_type} '{operation_name}' completed in {duration:.2f}ms"
        )

    def on_execute(self):
        """Called before execution"""
        yield

        # Log any errors
        if self.execution_context.errors:
            for error in self.execution_context.errors:
                logger.error(f"GraphQL error: {error}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
