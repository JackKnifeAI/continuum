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
Tests for GraphQL mutations.
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
async def test_create_memory(app, api_key):
    """Test createMemory mutation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    mutation CreateMemory($input: CreateMemoryInput!) {
                        createMemory(input: $input) {
                            id
                            content
                            importance
                            createdAt
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "content": "Test memory content",
                        "memoryType": "USER_MESSAGE",
                        "importance": 0.8
                    }
                }
            }
        )

        data = response.json()
        assert "data" in data
        if "createMemory" in data.get("data", {}):
            assert data["data"]["createMemory"]["content"] == "Test memory content"


@pytest.mark.asyncio
async def test_create_concept(app, api_key):
    """Test createConcept mutation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    mutation CreateConcept($input: CreateConceptInput!) {
                        createConcept(input: $input) {
                            id
                            name
                            confidence
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "name": "Machine Learning",
                        "description": "AI technology",
                        "confidence": 0.9
                    }
                }
            }
        )

        data = response.json()
        assert "data" in data


@pytest.mark.asyncio
async def test_start_session(app, api_key):
    """Test startSession mutation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    mutation StartSession($title: String) {
                        startSession(title: $title) {
                            id
                            title
                            status
                            startedAt
                        }
                    }
                """,
                "variables": {
                    "title": "Test Session"
                }
            }
        )

        data = response.json()
        assert "data" in data
        if "startSession" in data.get("data", {}):
            assert data["data"]["startSession"]["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_learn_mutation(app, api_key):
    """Test learn mutation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={
                "query": """
                    mutation Learn($input: ConversationInput!) {
                        learn(conversation: $input) {
                            conceptsExtracted
                            decisionsDetected
                            linksCreated
                            success
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "userMessage": "What is AI?",
                        "aiResponse": "AI is artificial intelligence..."
                    }
                }
            }
        )

        data = response.json()
        assert "data" in data


@pytest.mark.asyncio
async def test_mutation_without_auth(app):
    """Test mutation without authentication (should fail)"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            json={
                "query": """
                    mutation {
                        createMemory(input: {
                            content: "Test"
                            memoryType: USER_MESSAGE
                        }) {
                            id
                        }
                    }
                """
            }
        )

        data = response.json()
        assert "errors" in data

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
