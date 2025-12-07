# CONTINUUM GraphQL API

Modern GraphQL API layer for CONTINUUM providing flexible querying, real-time subscriptions, and better developer experience.

## Features

- **Rich Type System**: Complete GraphQL schema with SDL definitions
- **Flexible Queries**: Field selection, filtering, and pagination
- **Real-time Subscriptions**: WebSocket support for live updates
- **DataLoader Integration**: Automatic N+1 query prevention
- **Authentication**: API key-based authentication
- **Performance**: Query depth limiting, complexity analysis, caching
- **Developer Experience**: GraphiQL playground, error formatting, logging

## Quick Start

### Running the Server

```python
from continuum.api.graphql import create_standalone_app
import uvicorn

app = create_standalone_app(debug=True)
uvicorn.run(app, host="0.0.0.0", port=8000)
```

Or run directly:

```bash
python -m continuum.api.graphql.server
```

### Integrating with Existing FastAPI App

```python
from fastapi import FastAPI
from continuum.api.graphql import create_graphql_app

app = FastAPI()
graphql_app = create_graphql_app()
app.include_router(graphql_app, prefix="/graphql")
```

## Authentication

All queries and mutations (except `health`) require authentication via API key:

```http
POST /graphql
X-API-Key: cm_your_api_key_here
Content-Type: application/json

{
  "query": "query { me { username } }"
}
```

## Example Queries

### Get Current User

```graphql
query GetCurrentUser {
  me {
    id
    username
    email
    displayName
    memoryCount
    conceptCount
  }
}
```

### Search Memories

```graphql
query SearchMemories {
  searchMemories(
    query: "machine learning"
    type: SEMANTIC
    limit: 10
    threshold: 0.7
  ) {
    memory {
      id
      content
      importance
      createdAt
    }
    score
    highlights
  }
}
```

### Get Memory with Related Data

```graphql
query GetMemory {
  memory(id: "123") {
    id
    content
    importance
    concepts(limit: 5) {
      id
      name
      confidence
    }
    relatedMemories(limit: 5, threshold: 0.8) {
      id
      content
      importance
    }
    session {
      id
      title
      status
    }
  }
}
```

### Explore Concept Graph

```graphql
query ConceptGraph {
  conceptGraph(rootId: "456", depth: 2) {
    root {
      id
      name
      description
    }
    nodes {
      id
      name
      confidence
    }
    edges {
      from { name }
      to { name }
      relationship
      strength
    }
    nodeCount
    edgeCount
  }
}
```

### List Memories with Pagination

```graphql
query ListMemories {
  memories(
    filter: {
      memoryType: USER_MESSAGE
      minImportance: 0.7
      createdAfter: "2025-01-01T00:00:00Z"
    }
    pagination: {
      first: 20
      after: "cursor_here"
    }
  ) {
    edges {
      cursor
      node {
        id
        content
        importance
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    totalCount
  }
}
```

## Example Mutations

### Create Memory

```graphql
mutation CreateMemory {
  createMemory(
    input: {
      content: "Important discussion about AI safety"
      memoryType: USER_MESSAGE
      importance: 0.9
      metadata: { tags: ["ai", "safety"] }
    }
  ) {
    id
    content
    createdAt
  }
}
```

### Learn from Conversation

```graphql
mutation Learn {
  learn(
    conversation: {
      userMessage: "What is quantum computing?"
      aiResponse: "Quantum computing uses quantum mechanics..."
      sessionId: "session_123"
    }
  ) {
    conceptsExtracted
    decisionsDetected
    linksCreated
    concepts {
      id
      name
      confidence
    }
    success
  }
}
```

### Link Concepts

```graphql
mutation LinkConcepts {
  linkConcepts(
    sourceId: "123"
    targetId: "456"
    relationship: RELATED_TO
    strength: 0.85
  ) {
    from { name }
    to { name }
    relationship
    strength
  }
}
```

### Start Session

```graphql
mutation StartSession {
  startSession(
    title: "Research Session"
    metadata: { project: "continuum" }
  ) {
    id
    title
    status
    startedAt
  }
}
```

## Example Subscriptions

### Subscribe to New Memories

```graphql
subscription OnMemoryCreated {
  memoryCreated(memoryType: USER_MESSAGE) {
    id
    content
    createdAt
  }
}
```

### Subscribe to Concept Discovery

```graphql
subscription OnConceptDiscovered {
  conceptDiscovered(conceptType: "technology") {
    id
    name
    description
    confidence
  }
}
```

### Subscribe to Session Activity

```graphql
subscription OnSessionActivity {
  sessionActivity(sessionId: "session_123") {
    type
    session {
      id
      title
      messageCount
    }
    timestamp
  }
}
```

## Schema Types

### Core Types

- `Memory`: Stored conversational memory
- `Concept`: Entity in knowledge graph
- `User`: User account
- `Session`: Conversation session
- `FederationPeer`: Federated network peer

### Enums

- `MemoryType`: USER_MESSAGE, AI_RESPONSE, SYSTEM_EVENT, DECISION, CONCEPT
- `SearchType`: SEMANTIC, KEYWORD, HYBRID
- `ConceptRelationship`: RELATED_TO, PART_OF, CAUSED_BY, SIMILAR_TO, CONTRADICTS
- `SessionStatus`: ACTIVE, PAUSED, ENDED, ARCHIVED
- `UserRole`: USER, ADMIN, READONLY

### Scalars

- `DateTime`: ISO-8601 datetime string
- `JSON`: Arbitrary JSON data
- `Vector`: Vector embedding (array of floats)
- `Cursor`: Opaque pagination cursor

## Performance

### DataLoader Batching

All relationships use DataLoaders to prevent N+1 queries:

```graphql
query {
  memories(pagination: { first: 100 }) {
    edges {
      node {
        concepts {  # Batched with DataLoader
          name
        }
      }
    }
  }
}
```

### Query Limits

- **Max Depth**: 10 (configurable)
- **Max Complexity**: 1000 (configurable)
- **Max Results**: 100 per query

### Caching

- DataLoader per-request caching
- Redis caching (optional)
- HTTP caching headers

## Error Handling

Errors include structured extensions:

```json
{
  "errors": [
    {
      "message": "Authentication required",
      "path": ["me"],
      "locations": [{ "line": 2, "column": 3 }],
      "extensions": {
        "code": "UNAUTHENTICATED",
        "timestamp": "2025-12-06T10:00:00Z"
      }
    }
  ]
}
```

Error codes:
- `UNAUTHENTICATED`: Not authenticated
- `FORBIDDEN`: Not authorized
- `NOT_FOUND`: Resource not found
- `BAD_USER_INPUT`: Invalid input
- `QUERY_TOO_DEEP`: Query depth exceeded
- `QUERY_TOO_COMPLEX`: Query complexity exceeded
- `INTERNAL_SERVER_ERROR`: Server error

## GraphQL Playground

Access GraphiQL at `http://localhost:8000/graphql` for interactive exploration.

## File Structure

```
continuum/api/graphql/
├── __init__.py                 # Public exports
├── server.py                   # FastAPI server setup
├── schema.py                   # Main schema (Query/Mutation/Subscription)
├── types.py                    # Strawberry type definitions
├── schema/                     # SDL schema files
│   ├── common.graphql
│   ├── types/
│   │   ├── memory.graphql
│   │   ├── concept.graphql
│   │   ├── user.graphql
│   │   ├── session.graphql
│   │   └── federation.graphql
│   └── operations/
│       ├── queries.graphql
│       ├── mutations.graphql
│       └── subscriptions.graphql
├── resolvers/                  # Resolver functions
│   ├── memory_resolvers.py
│   ├── concept_resolvers.py
│   ├── query_resolvers.py
│   └── mutation_resolvers.py
├── dataloaders/                # DataLoader implementations
│   ├── memory_loader.py
│   ├── concept_loader.py
│   └── user_loader.py
├── auth/                       # Authentication & permissions
│   ├── context.py
│   └── permissions.py
├── middleware/                 # GraphQL middleware
│   ├── logging.py
│   ├── error_handling.py
│   └── complexity.py
└── tests/                      # Tests
    ├── test_queries.py
    └── test_mutations.py
```

## Development

### Running Tests

```bash
pytest continuum/api/graphql/tests/
```

### Generating Schema SDL

```bash
python -m continuum.api.graphql.codegen.generate_schema
```

### Type Generation

```bash
python -m continuum.api.graphql.codegen.generate_types
```

## License

See main CONTINUUM license.
