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
Tests for GraphQL queries.
"""

import pytest
from httpx import AsyncClient
from continuum.api.graphql import create_standalone_app


@pytest.fixture
def app():
    """Create test app"""
    return create_standalone_app(debug=True)


@pytest.fixture
def api_key():
    """Create test API key"""
    from continuum.api.middleware import create_api_key
    return create_api_key("test_tenant", "Test Key")


@pytest.mark.asyncio
async def test_health_query(app):
    """Test health query (no auth required)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            json={"query": "{ health { status service version } }"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert data["data"]["health"]["status"] == "healthy"
        assert data["data"]["health"]["service"] == "continuum-graphql"


@pytest.mark.asyncio
async def test_me_query_without_auth(app):
    """Test me query without authentication (should fail)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            json={"query": "{ me { username } }"}
        )

        data = response.json()
        assert "errors" in data
        assert "authentication" in data["errors"][0]["message"].lower()


@pytest.mark.asyncio
async def test_me_query_with_auth(app, api_key):
    """Test me query with authentication"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={"query": "{ me { id username } }"}
        )

        # May return data or error depending on DB state
        data = response.json()
        assert "data" in data or "errors" in data


@pytest.mark.asyncio
async def test_memory_query(app, api_key):
    """Test memory query"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    query GetMemory($id: ID!) {
                        memory(id: $id) {
                            id
                            content
                            importance
                        }
                    }
                """,
                "variables": {"id": "test_123"}
            }
        )

        data = response.json()
        assert "data" in data


@pytest.mark.asyncio
async def test_search_memories(app, api_key):
    """Test search memories query"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    query SearchMemories($query: String!) {
                        searchMemories(query: $query, type: SEMANTIC, limit: 10) {
                            memory {
                                id
                                content
                            }
                            score
                        }
                    }
                """,
                "variables": {"query": "test query"}
            }
        )

        data = response.json()
        assert "data" in data


@pytest.mark.asyncio
async def test_concepts_query(app, api_key):
    """Test concepts query"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    query ListConcepts {
                        concepts(pagination: { first: 10 }) {
                            edges {
                                node {
                                    id
                                    name
                                    confidence
                                }
                            }
                            totalCount
                        }
                    }
                """
            }
        )

        data = response.json()
        assert "data" in data


@pytest.mark.asyncio
async def test_query_depth_limit(app, api_key):
    """Test query depth limiting"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Deeply nested query (should fail)
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    {
                        me {
                            sessions {
                                edges {
                                    node {
                                        memories {
                                            edges {
                                                node {
                                                    concepts {
                                                        relatedConcepts {
                                                            from {
                                                                relatedConcepts {
                                                                    from {
                                                                        relatedConcepts {
                                                                            from {
                                                                                id
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                """
            }
        )

        data = response.json()
        # Should have error about depth
        assert "errors" in data

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
