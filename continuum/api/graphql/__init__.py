"""
CONTINUUM GraphQL API

Modern GraphQL API layer providing flexible querying, real-time subscriptions,
and better developer experience compared to REST.

Features:
- Rich type system with SDL schema
- Flexible queries with field selection
- Real-time subscriptions via WebSocket
- DataLoader for N+1 prevention
- Caching and performance optimization
- Full authentication and authorization
"""

from .server import create_graphql_app

__all__ = ["create_graphql_app"]
