# GraphQL API Examples

Real-world usage examples for CONTINUUM GraphQL API.

## Setup

First, create an API key:

```python
from continuum.api.middleware import create_api_key

api_key = create_api_key("my_tenant", "My API Key")
# Save this key securely - cm_xxxxxxxxxx
```

## Python Client Example

```python
import httpx
import json

class ContinuumGraphQLClient:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    async def query(self, query: str, variables: dict = None):
        """Execute a GraphQL query"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url,
                json={"query": query, "variables": variables},
                headers=self.headers
            )
            return response.json()

# Usage
client = ContinuumGraphQLClient(
    url="http://localhost:8000/graphql",
    api_key="cm_your_key_here"
)

# Query memories
result = await client.query("""
    query SearchMemories($query: String!) {
        searchMemories(query: $query, type: SEMANTIC, limit: 10) {
            memory {
                id
                content
                importance
            }
            score
        }
    }
""", variables={"query": "machine learning"})

print(result)
```

## Use Case: Chat Application

### 1. Start a Session

```graphql
mutation StartChatSession {
  startSession(title: "User Chat Session") {
    id
    title
    status
    startedAt
  }
}
```

### 2. Before Generating Response: Query Context

```graphql
query GetContext($message: String!) {
  searchMemories(query: $message, type: HYBRID, limit: 5) {
    memory {
      content
      importance
      concepts {
        name
        description
      }
    }
    score
  }
}
```

Variables:
```json
{
  "message": "Tell me about our previous discussion on AI"
}
```

### 3. After Response: Learn from Exchange

```graphql
mutation LearnFromChat($input: ConversationInput!) {
  learn(conversation: $input) {
    conceptsExtracted
    decisionsDetected
    concepts {
      name
      confidence
      description
    }
    success
  }
}
```

Variables:
```json
{
  "input": {
    "userMessage": "Tell me about our previous discussion on AI",
    "aiResponse": "We previously discussed AI safety, machine learning fundamentals...",
    "sessionId": "session_123",
    "metadata": {
      "source": "chat",
      "model": "claude-opus-4"
    }
  }
}
```

### 4. End Session

```graphql
mutation EndChatSession($sessionId: ID!, $summary: String) {
  endSession(id: $sessionId, summary: $summary) {
    id
    status
    summary
    messageCount
    endedAt
  }
}
```

## Use Case: Knowledge Graph Explorer

### 1. Find Root Concept

```graphql
query FindConcept($search: String!) {
  concepts(
    filter: { search: $search }
    pagination: { first: 1 }
  ) {
    edges {
      node {
        id
        name
        description
        confidence
      }
    }
  }
}
```

### 2. Explore Graph from Root

```graphql
query ExploreGraph($rootId: ID!, $depth: Int!) {
  conceptGraph(rootId: $rootId, depth: $depth) {
    root {
      id
      name
      description
    }
    nodes {
      id
      name
      conceptType
      confidence
      memories(pagination: { first: 3 }) {
        edges {
          node {
            content
            createdAt
          }
        }
      }
    }
    edges {
      from { id name }
      to { id name }
      relationship
      label
      strength
    }
    nodeCount
    edgeCount
  }
}
```

### 3. Link New Concept

```graphql
mutation LinkNewConcept(
  $sourceId: ID!
  $targetId: ID!
  $relationship: ConceptRelationship!
  $label: String
  $strength: Float
) {
  linkConcepts(
    sourceId: $sourceId
    targetId: $targetId
    relationship: $relationship
    label: $label
    strength: $strength
  ) {
    from { name }
    to { name }
    relationship
    strength
    createdAt
  }
}
```

Variables:
```json
{
  "sourceId": "123",
  "targetId": "456",
  "relationship": "RELATED_TO",
  "label": "shares principles with",
  "strength": 0.85
}
```

## Use Case: Real-time Updates

### Subscribe to Activity

```graphql
subscription WatchActivity {
  sessionActivity(sessionId: "session_123") {
    type
    session {
      id
      title
      messageCount
    }
    timestamp
    metadata
  }
}
```

### Subscribe to Discoveries

```graphql
subscription WatchDiscoveries {
  conceptDiscovered(conceptType: "technology") {
    id
    name
    description
    confidence
    createdAt
  }
}
```

## Use Case: Memory Management

### List All User Memories

```graphql
query ListMyMemories($cursor: Cursor) {
  me {
    id
    username
    sessions(pagination: { first: 10 }) {
      edges {
        node {
          id
          title
          memories(pagination: { first: 50, after: $cursor }) {
            edges {
              cursor
              node {
                id
                content
                memoryType
                importance
                createdAt
                concepts(limit: 3) {
                  name
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
          }
        }
      }
    }
  }
}
```

### Filter Memories by Importance

```graphql
query ImportantMemories {
  memories(
    filter: {
      minImportance: 0.8
      memoryType: DECISION
    }
    pagination: { first: 20 }
  ) {
    edges {
      node {
        id
        content
        importance
        concepts {
          name
          conceptType
        }
        createdAt
      }
    }
  }
}
```

### Merge Duplicate Memories

```graphql
mutation MergeDuplicates($sourceIds: [ID!]!, $targetId: ID!) {
  mergeMemories(sourceIds: $sourceIds, targetId: $targetId) {
    id
    content
    importance
    concepts {
      name
    }
  }
}
```

## Use Case: Analytics Dashboard

### System Statistics

```graphql
query DashboardStats {
  stats {
    totalMemories
    totalConcepts
    totalUsers
    totalSessions
    apiRequests24h
    avgQueryTimeMs
  }

  me {
    memoryCount
    conceptCount
    sessions(limit: 5) {
      id
      title
      status
      messageCount
      startedAt
    }
  }
}
```

### Recent Activity

```graphql
query RecentActivity {
  memories(
    filter: {
      createdAfter: "2025-12-06T00:00:00Z"
    }
    pagination: { first: 20 }
  ) {
    edges {
      node {
        id
        content
        memoryType
        createdAt
        session {
          title
        }
      }
    }
    totalCount
  }
}
```

## Use Case: Federation

### List Federation Peers

```graphql
query FederationOverview {
  federationStatus {
    enabled
    totalPeers
    onlinePeers
    syncedMemories
    pendingSync
    lastSync
  }

  federationPeers {
    id
    url
    name
    status
    sharedMemories
    trustScore
    lastSync
  }
}
```

### Sync with Peer

```graphql
mutation SyncWithPeer($peerUrl: String!, $memoryIds: [ID!]) {
  syncMemories(peerUrl: $peerUrl, memoryIds: $memoryIds) {
    success
    memoriesSynced
    conceptsSynced
    durationMs
    error
    timestamp
  }
}
```

## Error Handling

```python
async def safe_query(client, query, variables=None):
    """Execute query with error handling"""
    result = await client.query(query, variables)

    if "errors" in result:
        for error in result["errors"]:
            code = error.get("extensions", {}).get("code")

            if code == "UNAUTHENTICATED":
                # Refresh API key
                print("Authentication failed")
            elif code == "QUERY_TOO_COMPLEX":
                # Simplify query
                print("Query too complex, simplifying...")
            else:
                print(f"Error: {error['message']}")

        return None

    return result["data"]
```

## Batch Operations

```python
async def batch_create_memories(client, memories):
    """Create multiple memories efficiently"""
    query = """
        mutation CreateMemory($input: CreateMemoryInput!) {
            createMemory(input: $input) {
                id
            }
        }
    """

    tasks = [
        client.query(query, {"input": memory})
        for memory in memories
    ]

    results = await asyncio.gather(*tasks)
    return results
```

## Pagination Helper

```python
async def fetch_all_memories(client, filter=None):
    """Fetch all memories using pagination"""
    all_memories = []
    cursor = None

    while True:
        result = await client.query("""
            query GetMemories($filter: MemoryFilter, $cursor: Cursor) {
                memories(
                    filter: $filter
                    pagination: { first: 100, after: $cursor }
                ) {
                    edges {
                        cursor
                        node { id content }
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        """, {"filter": filter, "cursor": cursor})

        data = result.get("data", {}).get("memories", {})
        edges = data.get("edges", [])
        page_info = data.get("pageInfo", {})

        all_memories.extend([edge["node"] for edge in edges])

        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")

    return all_memories
```

## Testing Queries

```python
import pytest
from continuum.api.graphql import create_standalone_app
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_query():
    app = create_standalone_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            json={"query": "{ health { status service } }"}
        )

        data = response.json()
        assert "data" in data
        assert data["data"]["health"]["status"] == "healthy"

@pytest.mark.asyncio
async def test_authenticated_query():
    app = create_standalone_app()

    # Create API key first
    from continuum.api.middleware import create_api_key
    api_key = create_api_key("test_tenant", "Test Key")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/graphql",
            headers={"X-API-Key": api_key},
            json={"query": "{ me { username } }"}
        )

        data = response.json()
        assert "data" in data or "errors" in data
```
