# CONTINUUM GraphQL Schema Documentation

Complete schema reference for CONTINUUM GraphQL API.

## Table of Contents

1. [Scalars](#scalars)
2. [Enums](#enums)
3. [Interfaces](#interfaces)
4. [Types](#types)
5. [Queries](#queries)
6. [Mutations](#mutations)
7. [Subscriptions](#subscriptions)
8. [Input Types](#input-types)

---

## Scalars

### DateTime
ISO-8601 datetime string (e.g., `2025-12-06T10:00:00Z`)

### JSON
Arbitrary JSON data stored as object

### Vector
Vector embedding represented as array of floats `[0.1, 0.2, ...]`

### Cursor
Opaque cursor string for pagination

---

## Enums

### MemoryType
Type of memory entry:
- `USER_MESSAGE` - User-generated content
- `AI_RESPONSE` - AI-generated content
- `SYSTEM_EVENT` - System event
- `DECISION` - Decision made
- `CONCEPT` - Concept definition

### SearchType
Search algorithm to use:
- `SEMANTIC` - Embedding-based semantic search
- `KEYWORD` - Text-based keyword search
- `HYBRID` - Combined semantic + keyword

### ConceptRelationship
Relationship between concepts:
- `RELATED_TO` - General relationship
- `PART_OF` - Hierarchical relationship
- `CAUSED_BY` - Causal relationship
- `SIMILAR_TO` - Similarity relationship
- `CONTRADICTS` - Contradictory relationship
- `CUSTOM` - Custom relationship

### SessionStatus
Status of conversation session:
- `ACTIVE` - Currently active
- `PAUSED` - Temporarily paused
- `ENDED` - Completed
- `ARCHIVED` - Archived for storage

### UserRole
User permission level:
- `USER` - Regular user
- `ADMIN` - Administrator
- `READONLY` - Read-only access

### PeerStatus
Federation peer status:
- `ONLINE` - Peer is reachable
- `OFFLINE` - Peer is offline
- `SYNCING` - Currently syncing
- `UNREACHABLE` - Cannot reach peer
- `BLOCKED` - Peer is blocked

---

## Interfaces

### Node
Common interface for all entities:
```graphql
interface Node {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

---

## Types

### Memory
A stored memory item:
```graphql
type Memory implements Node {
  id: ID!
  content: String!
  memoryType: MemoryType!
  importance: Float!
  embedding: Vector
  accessCount: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
  lastAccessedAt: DateTime
  tenantId: String!
  metadata: JSON

  # Relationships
  concepts(limit: Int = 10): [Concept!]!
  relatedMemories(limit: Int = 10, threshold: Float = 0.7): [Memory!]!
  session: Session
}
```

**Fields:**
- `id` - Unique identifier
- `content` - Memory text content
- `memoryType` - Type of memory (user/AI/system/etc)
- `importance` - Importance score (0.0-1.0)
- `embedding` - Vector representation for semantic search
- `accessCount` - Number of times accessed
- `tenantId` - Tenant/namespace identifier
- `metadata` - Additional arbitrary data

### Concept
Entity in knowledge graph:
```graphql
type Concept implements Node {
  id: ID!
  name: String!
  description: String
  confidence: Float!
  conceptType: String
  createdAt: DateTime!
  updatedAt: DateTime!
  tenantId: String!
  metadata: JSON

  # Relationships
  memories(pagination: PaginationInput): MemoryConnection!
  relatedConcepts(depth: Int = 1, relationship: ConceptRelationship): [ConceptEdge!]!
}
```

### ConceptEdge
Relationship between concepts:
```graphql
type ConceptEdge {
  from: Concept!
  to: Concept!
  relationship: ConceptRelationship!
  label: String
  strength: Float!
  metadata: JSON
  createdAt: DateTime!
}
```

### ConceptGraph
Graph structure of concepts:
```graphql
type ConceptGraph {
  root: Concept!
  nodes: [Concept!]!
  edges: [ConceptEdge!]!
  depth: Int!
  nodeCount: Int!
  edgeCount: Int!
}
```

### User
User account:
```graphql
type User implements Node {
  id: ID!
  username: String!
  email: String!
  displayName: String
  role: UserRole!
  profile: UserProfile
  settings: UserSettings
  memoryCount: Int!
  conceptCount: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
  lastLoginAt: DateTime

  # Relationships
  sessions(pagination: PaginationInput): SessionConnection!
}
```

### Session
Conversation session:
```graphql
type Session implements Node {
  id: ID!
  title: String
  summary: String
  status: SessionStatus!
  messageCount: Int!
  startedAt: DateTime!
  endedAt: DateTime
  createdAt: DateTime!
  updatedAt: DateTime!
  tenantId: String!
  metadata: JSON

  # Relationships
  user: User!
  memories(pagination: PaginationInput): MemoryConnection!
  concepts(limit: Int = 20): [Concept!]!
}
```

### SearchResult
Search result with relevance:
```graphql
type SearchResult {
  memory: Memory!
  score: Float!
  matchedFields: [String!]!
  highlights: [String!]
}
```

### FederationPeer
Federated network peer:
```graphql
type FederationPeer {
  id: ID!
  url: String!
  name: String
  status: PeerStatus!
  lastSync: DateTime
  sharedMemories: Int!
  trustScore: Float!
  metadata: JSON
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### HealthStatus
System health:
```graphql
type HealthStatus {
  status: String!
  service: String!
  version: String!
  timestamp: DateTime!
  database: Boolean!
  cache: Boolean!
}
```

### SystemStats
System statistics:
```graphql
type SystemStats {
  totalMemories: Int!
  totalConcepts: Int!
  totalUsers: Int!
  totalSessions: Int!
  apiRequests24h: Int!
  avgQueryTimeMs: Float!
}
```

---

## Queries

### Health & System

#### health
```graphql
health: HealthStatus!
```
No authentication required. Returns service health.

#### stats
```graphql
stats: SystemStats!
```
Requires authentication. Returns system statistics.

### Memory Queries

#### memory
```graphql
memory(id: ID!): Memory
```
Get single memory by ID.

#### memories
```graphql
memories(
  filter: MemoryFilter
  pagination: PaginationInput
): MemoryConnection!
```
List memories with filtering and pagination.

#### searchMemories
```graphql
searchMemories(
  query: String!
  type: SearchType = SEMANTIC
  limit: Int = 10
  threshold: Float = 0.7
): [SearchResult!]!
```
Search memories using semantic or keyword search.

### Concept Queries

#### concept
```graphql
concept(id: ID!): Concept
```
Get single concept by ID.

#### concepts
```graphql
concepts(
  filter: ConceptFilter
  pagination: PaginationInput
): ConceptConnection!
```
List concepts with filtering.

#### conceptGraph
```graphql
conceptGraph(
  rootId: ID!
  depth: Int = 2
  relationship: ConceptRelationship
): ConceptGraph
```
Get concept graph starting from root.

### User Queries

#### me
```graphql
me: User!
```
Get current authenticated user.

#### user (admin only)
```graphql
user(id: ID!): User
```
Get user by ID.

#### users (admin only)
```graphql
users(
  filter: UserFilter
  pagination: PaginationInput
): UserConnection!
```
List all users.

### Session Queries

#### session
```graphql
session(id: ID!): Session
```
Get session by ID.

#### sessions
```graphql
sessions(
  limit: Int = 10
  status: SessionStatus
): [Session!]!
```
List sessions for current user.

#### currentSession
```graphql
currentSession: Session
```
Get current active session.

---

## Mutations

### Memory Mutations

#### createMemory
```graphql
createMemory(input: CreateMemoryInput!): Memory!
```

#### updateMemory
```graphql
updateMemory(id: ID!, input: UpdateMemoryInput!): Memory!
```

#### deleteMemory
```graphql
deleteMemory(id: ID!): Boolean!
```

#### mergeMemories
```graphql
mergeMemories(sourceIds: [ID!]!, targetId: ID!): Memory!
```

### Concept Mutations

#### createConcept
```graphql
createConcept(input: CreateConceptInput!): Concept!
```

#### linkConcepts
```graphql
linkConcepts(
  sourceId: ID!
  targetId: ID!
  relationship: ConceptRelationship!
  label: String
  strength: Float = 0.8
): ConceptEdge!
```

#### unlinkConcepts
```graphql
unlinkConcepts(sourceId: ID!, targetId: ID!): Boolean!
```

### Session Mutations

#### startSession
```graphql
startSession(title: String, metadata: JSON): Session!
```

#### endSession
```graphql
endSession(id: ID!, summary: String): Session!
```

### Learning Mutations

#### learn
```graphql
learn(conversation: ConversationInput!): LearnResult!
```

### Federation Mutations

#### syncMemories
```graphql
syncMemories(peerUrl: String!, memoryIds: [ID!]): SyncResult!
```

### User Mutations

#### updateProfile
```graphql
updateProfile(input: UpdateProfileInput!): User!
```

#### updateSettings
```graphql
updateSettings(input: SettingsInput!): Settings!
```

---

## Subscriptions

### memoryCreated
```graphql
memoryCreated(
  memoryType: MemoryType
  sessionId: ID
): Memory!
```
Subscribe to new memories.

### conceptDiscovered
```graphql
conceptDiscovered(conceptType: String): Concept!
```
Subscribe to new concepts.

### federationSync
```graphql
federationSync(peerId: ID): SyncEvent!
```
Subscribe to federation sync events.

### sessionActivity
```graphql
sessionActivity(sessionId: ID): SessionEvent!
```
Subscribe to session activity.

---

## Input Types

### PaginationInput
```graphql
input PaginationInput {
  first: Int = 20
  after: Cursor
  last: Int
  before: Cursor
}
```

### MemoryFilter
```graphql
input MemoryFilter {
  memoryType: MemoryType
  minImportance: Float
  concepts: [String!]
  sessionId: ID
  createdAfter: DateTime
  createdBefore: DateTime
  search: String
}
```

### CreateMemoryInput
```graphql
input CreateMemoryInput {
  content: String!
  memoryType: MemoryType!
  importance: Float = 0.5
  sessionId: ID
  metadata: JSON
}
```

### UpdateMemoryInput
```graphql
input UpdateMemoryInput {
  content: String
  importance: Float
  metadata: JSON
}
```

### ConceptFilter
```graphql
input ConceptFilter {
  conceptType: String
  minConfidence: Float
  search: String
  createdAfter: DateTime
  createdBefore: DateTime
}
```

### CreateConceptInput
```graphql
input CreateConceptInput {
  name: String!
  description: String
  confidence: Float = 0.8
  conceptType: String
  metadata: JSON
}
```

### ConversationInput
```graphql
input ConversationInput {
  userMessage: String!
  aiResponse: String!
  sessionId: ID
  metadata: JSON
}
```

### UpdateProfileInput
```graphql
input UpdateProfileInput {
  displayName: String
  avatar: String
  bio: String
  timezone: String
  language: String
}
```

### SettingsInput
```graphql
input SettingsInput {
  realtimeSync: Boolean
  autoSaveInterval: Int
  defaultSearchType: SearchType
  maxResultsPerQuery: Int
  embeddingProvider: String
  custom: JSON
}
```

---

## Connection Types

All paginated results use Relay-style connections:

```graphql
type MemoryConnection {
  edges: [MemoryEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type MemoryEdge {
  cursor: Cursor!
  node: Memory!
  score: Float  # For search results
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: Cursor
  endCursor: Cursor
}
```

Same pattern for `ConceptConnection`, `UserConnection`, `SessionConnection`.
