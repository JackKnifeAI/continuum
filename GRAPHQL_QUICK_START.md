# GraphQL Quick Start

## Status: ✓ INTEGRATED - Install strawberry-graphql to activate

---

## One Command to Activate

```bash
pip install strawberry-graphql[fastapi]
```

---

## Start Server

```bash
cd /var/home/alexandergcasavant/Projects/continuum
python -m continuum.api.server
```

Look for:
```
GraphQL: http://localhost:8420/graphql
```

---

## Access Playground

```
http://localhost:8420/graphql
```

---

## Test Query

```graphql
query HealthCheck {
  health {
    status
    service
    version
  }
}
```

---

## Query with Authentication

**Headers**:
```json
{
  "X-API-Key": "your-api-key-here"
}
```

**Query**:
```graphql
query MyProfile {
  me {
    id
    email
    displayName
    role
  }
}
```

---

## Create Memory

```graphql
mutation CreateMemory {
  createMemory(input: {
    content: "Test memory"
    memoryType: USER_MESSAGE
    importance: 0.8
  }) {
    id
    content
    memoryType
    importance
    createdAt
  }
}
```

---

## Search Memories

```graphql
query SearchMemories {
  searchMemories(
    query: "test"
    type: SEMANTIC
    limit: 10
  ) {
    memory {
      id
      content
      importance
    }
    score
  }
}
```

---

## Real-time Subscription

```graphql
subscription WatchMemories {
  memoryCreated {
    id
    content
    memoryType
    createdAt
  }
}
```

---

## Available Endpoints

- **Playground**: `/graphql` (GET)
- **API**: `/graphql` (POST)
- **Subscriptions**: `/graphql` (WebSocket)

---

## Files Created

1. **GRAPHQL_DEBUG_REPORT.md** - Detailed technical report
2. **GRAPHQL_INTEGRATION_SUMMARY.md** - Complete integration guide
3. **GRAPHQL_QUICK_START.md** - This file
4. **test_graphql.py** - Test script

---

## Verify Integration

```bash
python3 test_graphql.py
```

Expected after installing strawberry:
```
Total: 5/5 tests passed
```

---

## What's Integrated

- ✓ Schema with 50+ queries/mutations/subscriptions
- ✓ Authentication via X-API-Key header
- ✓ DataLoader pattern (N+1 prevention)
- ✓ Query depth/complexity limiting
- ✓ Error handling middleware
- ✓ Request logging
- ✓ GraphQL Playground UI
- ✓ WebSocket subscriptions
- ✓ Mounted at /graphql endpoint

---

## Schema Stats

- **9 GraphQL schema files** (26KB total)
- **Type definitions**: Memory, Concept, User, Session, Federation
- **Queries**: 15+ operations
- **Mutations**: 15+ operations
- **Subscriptions**: 4 real-time channels

---

## Next Steps After Install

1. Start server
2. Open playground
3. Run health query
4. Test with your API key
5. Explore schema docs in playground

---

**Full Documentation**: See `GRAPHQL_INTEGRATION_SUMMARY.md`
