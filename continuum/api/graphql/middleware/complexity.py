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
Query complexity and depth limiting extension.
"""

from typing import Any
from strawberry.extensions import SchemaExtension
from graphql import GraphQLError


class ComplexityExtension(SchemaExtension):
    """Limit query depth and complexity to prevent abuse"""

    def __init__(self, max_depth: int = 10, max_complexity: int = 1000):
        super().__init__()
        self.max_depth = max_depth
        self.max_complexity = max_complexity

    def on_validate(self):
        """Validate query depth and complexity before execution"""
        execution_context = self.execution_context

        # Calculate query depth
        depth = self._calculate_depth(execution_context.graphql_document)

        if depth > self.max_depth:
            raise GraphQLError(
                f"Query depth {depth} exceeds maximum depth {self.max_depth}",
                extensions={"code": "QUERY_TOO_DEEP", "max_depth": self.max_depth},
            )

        # Calculate query complexity
        complexity = self._calculate_complexity(execution_context.graphql_document)

        if complexity > self.max_complexity:
            raise GraphQLError(
                f"Query complexity {complexity} exceeds maximum {self.max_complexity}",
                extensions={
                    "code": "QUERY_TOO_COMPLEX",
                    "max_complexity": self.max_complexity,
                },
            )

    def _calculate_depth(self, document, current_depth: int = 0) -> int:
        """Calculate maximum depth of query"""
        if not document or not hasattr(document, "definitions"):
            return current_depth

        max_depth = current_depth

        for definition in document.definitions:
            if hasattr(definition, "selection_set") and definition.selection_set:
                depth = self._calculate_selection_depth(
                    definition.selection_set, current_depth + 1
                )
                max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_selection_depth(self, selection_set, current_depth: int) -> int:
        """Recursively calculate depth of selection set"""
        if not selection_set or not hasattr(selection_set, "selections"):
            return current_depth

        max_depth = current_depth

        for selection in selection_set.selections:
            if hasattr(selection, "selection_set") and selection.selection_set:
                depth = self._calculate_selection_depth(
                    selection.selection_set, current_depth + 1
                )
                max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_complexity(self, document) -> int:
        """Calculate query complexity (simplified)"""
        if not document or not hasattr(document, "definitions"):
            return 0

        total_complexity = 0

        for definition in document.definitions:
            if hasattr(definition, "selection_set") and definition.selection_set:
                total_complexity += self._calculate_selection_complexity(
                    definition.selection_set
                )

        return total_complexity

    def _calculate_selection_complexity(self, selection_set) -> int:
        """Recursively calculate complexity of selection set"""
        if not selection_set or not hasattr(selection_set, "selections"):
            return 0

        complexity = 0

        for selection in selection_set.selections:
            # Each field adds 1 to complexity
            complexity += 1

            # Nested selections add their complexity
            if hasattr(selection, "selection_set") and selection.selection_set:
                complexity += self._calculate_selection_complexity(
                    selection.selection_set
                )

        return complexity

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
