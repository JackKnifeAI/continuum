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
Database Layer Instrumentation
===============================

SQLAlchemy and raw SQL query tracing.

Features:
- Query tracing with SQL statements in attributes
- Connection pool metrics
- Transaction boundary tracking
- Slow query detection and warnings
- Query parameter sanitization
"""

import time
from typing import Any, Optional, Dict
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind

from .tracer import get_tracer, get_current_span
from .metrics import record_histogram, increment_counter, set_gauge


# Module-level tracer
tracer = get_tracer(__name__)


@contextmanager
def trace_query(
    query: str,
    operation: str = "SELECT",
    table: Optional[str] = None,
    tenant_id: Optional[str] = None,
    capture_sql: bool = True,
):
    """
    Context manager for tracing database queries.

    Args:
        query: SQL query string
        operation: SQL operation type (SELECT, INSERT, UPDATE, DELETE)
        table: Primary table name
        tenant_id: Tenant identifier
        capture_sql: Whether to capture full SQL in span attributes

    Example:
        ```python
        with trace_query("SELECT * FROM entities WHERE id = ?", "SELECT", "entities"):
            cursor.execute(query, (entity_id,))
            result = cursor.fetchall()
        ```
    """
    span_name = f"db.{operation.lower()}"
    if table:
        span_name = f"{span_name}.{table}"

    with tracer.start_as_current_span(span_name, kind=SpanKind.CLIENT) as span:
        # Set database attributes
        span.set_attribute("db.system", "sqlite")  # or detect from connection
        span.set_attribute("db.operation", operation)

        if table:
            span.set_attribute("db.sql.table", table)

        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        # Capture SQL statement if enabled
        if capture_sql:
            # Sanitize query (remove sensitive data if needed)
            sanitized_query = _sanitize_query(query)
            span.set_attribute("db.statement", sanitized_query)

        # Record start time
        start_time = time.time()

        try:
            yield span

            # Record success
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))

            # Record query duration metric
            record_histogram(
                "continuum_db_query_duration_seconds",
                duration,
                {
                    "operation": operation.lower(),
                    "table": table or "unknown",
                    "tenant_id": tenant_id or "unknown",
                }
            )

            # Warn on slow queries
            if duration > 1.0:  # 1 second threshold
                span.add_event(
                    "slow_query",
                    {
                        "duration_seconds": duration,
                        "threshold_seconds": 1.0,
                    }
                )
                increment_counter(
                    "continuum_db_slow_queries_total",
                    {
                        "operation": operation.lower(),
                        "table": table or "unknown",
                    }
                )

        except Exception as e:
            # Record error
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

            # Record error metric
            increment_counter(
                "continuum_db_errors_total",
                {
                    "operation": operation.lower(),
                    "table": table or "unknown",
                    "error_type": type(e).__name__,
                }
            )

            raise


@contextmanager
def trace_transaction(tenant_id: Optional[str] = None):
    """
    Context manager for tracing database transactions.

    Example:
        ```python
        with trace_transaction(tenant_id="user_123"):
            # Multiple queries in a transaction
            cursor.execute("INSERT ...")
            cursor.execute("UPDATE ...")
            conn.commit()
        ```
    """
    with tracer.start_as_current_span("db.transaction", kind=SpanKind.CLIENT) as span:
        if tenant_id:
            span.set_attribute("tenant.id", tenant_id)

        span.set_attribute("db.system", "sqlite")

        start_time = time.time()

        try:
            yield span

            # Transaction succeeded
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))
            span.set_attribute("db.transaction.committed", True)

            # Record metric
            record_histogram(
                "continuum_db_transaction_duration_seconds",
                duration,
                {"tenant_id": tenant_id or "unknown"}
            )

        except Exception as e:
            # Transaction failed
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("db.transaction.committed", False)
            span.record_exception(e)

            # Record error metric
            increment_counter(
                "continuum_db_transaction_errors_total",
                {"tenant_id": tenant_id or "unknown"}
            )

            raise


def trace_connection_pool(
    pool_size: int,
    active_connections: int,
    idle_connections: int,
):
    """
    Record connection pool metrics.

    Args:
        pool_size: Total pool size
        active_connections: Number of active connections
        idle_connections: Number of idle connections

    Example:
        ```python
        # Called periodically by connection pool manager
        trace_connection_pool(
            pool_size=10,
            active_connections=3,
            idle_connections=7,
        )
        ```
    """
    set_gauge("continuum_db_pool_size", pool_size)
    set_gauge("continuum_db_pool_active", active_connections)
    set_gauge("continuum_db_pool_idle", idle_connections)


def enrich_span_with_query_plan(plan: str, span: Optional[trace.Span] = None):
    """
    Add query execution plan to span.

    Args:
        plan: Query execution plan (from EXPLAIN)
        span: Optional span to enrich (uses current span if not provided)
    """
    if span is None:
        span = get_current_span()

    span.set_attribute("db.query_plan", plan)


def enrich_span_with_row_count(row_count: int, span: Optional[trace.Span] = None):
    """
    Add row count to span.

    Args:
        row_count: Number of rows affected/returned
        span: Optional span to enrich
    """
    if span is None:
        span = get_current_span()

    span.set_attribute("db.row_count", row_count)


def _sanitize_query(query: str) -> str:
    """
    Sanitize SQL query to remove sensitive data.

    Replaces parameter values with placeholders.

    Args:
        query: Raw SQL query

    Returns:
        Sanitized query
    """
    import re

    # Replace string literals with placeholder
    query = re.sub(r"'[^']*'", "'?'", query)

    # Replace numeric literals (but not in identifiers)
    query = re.sub(r'\b\d+\b', '?', query)

    return query


class SQLAlchemyInstrumentation:
    """
    Instrumentation for SQLAlchemy ORM.

    Hooks into SQLAlchemy events to trace queries automatically.
    """

    def __init__(self, engine):
        """
        Initialize SQLAlchemy instrumentation.

        Args:
            engine: SQLAlchemy engine instance

        Example:
            ```python
            from sqlalchemy import create_engine
            from continuum.observability.database_instrumentation import SQLAlchemyInstrumentation

            engine = create_engine("sqlite:///memory.db")
            instrumentation = SQLAlchemyInstrumentation(engine)
            ```
        """
        from sqlalchemy import event

        self.engine = engine

        # Hook into before_cursor_execute
        event.listen(
            engine,
            "before_cursor_execute",
            self._before_cursor_execute,
        )

        # Hook into after_cursor_execute
        event.listen(
            engine,
            "after_cursor_execute",
            self._after_cursor_execute,
        )

    def _before_cursor_execute(
        self,
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        """Called before query execution"""
        # Extract operation and table
        operation = self._extract_operation(statement)
        table = self._extract_table(statement)

        # Create span
        span_name = f"db.{operation.lower()}"
        if table:
            span_name = f"{span_name}.{table}"

        span = tracer.start_span(span_name, kind=SpanKind.CLIENT)

        # Set attributes
        span.set_attribute("db.system", "sqlite")
        span.set_attribute("db.operation", operation)

        if table:
            span.set_attribute("db.sql.table", table)

        # Sanitize and store statement
        sanitized = _sanitize_query(statement)
        span.set_attribute("db.statement", sanitized)

        # Store span in context for after_execute
        context._otel_span = span
        context._otel_start_time = time.time()

    def _after_cursor_execute(
        self,
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        """Called after query execution"""
        if not hasattr(context, "_otel_span"):
            return

        span = context._otel_span
        start_time = context._otel_start_time

        try:
            # Record duration
            duration = time.time() - start_time

            # Set row count if available
            if cursor.rowcount >= 0:
                span.set_attribute("db.row_count", cursor.rowcount)

            # Set success status
            span.set_status(Status(StatusCode.OK))

        finally:
            # End span
            span.end()

            # Clean up context
            delattr(context, "_otel_span")
            delattr(context, "_otel_start_time")

    def _extract_operation(self, statement: str) -> str:
        """Extract SQL operation from statement"""
        statement_upper = statement.strip().upper()

        if statement_upper.startswith("SELECT"):
            return "SELECT"
        elif statement_upper.startswith("INSERT"):
            return "INSERT"
        elif statement_upper.startswith("UPDATE"):
            return "UPDATE"
        elif statement_upper.startswith("DELETE"):
            return "DELETE"
        elif statement_upper.startswith("CREATE"):
            return "CREATE"
        elif statement_upper.startswith("DROP"):
            return "DROP"
        elif statement_upper.startswith("ALTER"):
            return "ALTER"
        else:
            return "UNKNOWN"

    def _extract_table(self, statement: str) -> Optional[str]:
        """Extract primary table name from statement"""
        import re

        # Try to extract table name after FROM, INTO, UPDATE
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        for pattern in patterns:
            match = re.search(pattern, statement, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
