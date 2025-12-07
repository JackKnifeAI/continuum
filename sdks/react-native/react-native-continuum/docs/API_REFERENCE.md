# API Reference

## ContinuumClient

Main client class for interacting with CONTINUUM.

### Constructor

```typescript
new ContinuumClient(config: ContinuumConfig)
```

### Methods

#### Authentication

##### `signIn(email: string, password: string): Promise<User>`

Sign in a user.

```typescript
const user = await client.signIn('user@example.com', 'password');
```

##### `signOut(): Promise<void>`

Sign out the current user.

```typescript
await client.signOut();
```

##### `getSession(): Promise<Session | null>`

Get the current session.

```typescript
const session = await client.getSession();
```

#### Memory Operations

##### `createMemory(input: CreateMemoryInput): Promise<Memory>`

Create a new memory.

```typescript
const memory = await client.createMemory({
  type: 'episodic',
  content: 'Met with the team today',
  tags: ['work', 'meeting'],
});
```

##### `getMemory(id: string): Promise<Memory>`

Fetch a memory by ID.

```typescript
const memory = await client.getMemory('mem_123');
```

##### `getMemories(filter?: MemoryFilter): Promise<Memory[]>`

Fetch multiple memories with optional filtering.

```typescript
const memories = await client.getMemories({
  type: 'episodic',
  limit: 20,
  tags: ['work'],
});
```

##### `searchMemories(query: string, options?: SearchOptions): Promise<SearchResult[]>`

Search memories semantically.

```typescript
const results = await client.searchMemories('team meeting', {
  limit: 10,
  minSimilarity: 0.7,
});
```

##### `updateMemory(id: string, input: UpdateMemoryInput): Promise<Memory>`

Update a memory.

```typescript
const updated = await client.updateMemory('mem_123', {
  content: 'Updated content',
  tags: ['work', 'meeting', 'important'],
});
```

##### `deleteMemory(id: string): Promise<void>`

Delete a memory.

```typescript
await client.deleteMemory('mem_123');
```

#### Learning

##### `learn(conversation: Message[]): Promise<LearnResult>`

Learn from a conversation.

```typescript
const result = await client.learn([
  { role: 'user', content: 'What did we discuss yesterday?' },
  { role: 'assistant', content: 'We discussed the new project timeline' },
]);
```

##### `recall(context: string): Promise<Memory[]>`

Recall relevant memories for a context.

```typescript
const memories = await client.recall('project timeline');
```

#### Concepts

##### `getConcepts(filter?: ConceptFilter): Promise<Concept[]>`

Fetch concepts.

```typescript
const concepts = await client.getConcepts({
  category: 'work',
  minImportance: 0.5,
});
```

##### `getRelatedConcepts(conceptId: string): Promise<Concept[]>`

Get related concepts.

```typescript
const related = await client.getRelatedConcepts('concept_123');
```

#### Sync

##### `sync(): Promise<SyncResult>`

Manually trigger sync.

```typescript
const result = await client.sync();
console.log(`Synced ${result.memoriesSynced} memories`);
```

##### `getLastSyncTime(): Promise<Date | null>`

Get last sync timestamp.

```typescript
const lastSync = await client.getLastSyncTime();
```

##### `getSyncStatus(): Promise<SyncStatus>`

Get current sync status.

```typescript
const status = await client.getSyncStatus();
console.log(`${status.pendingOperations} operations pending`);
```

#### Offline Support

##### `enableOfflineMode(): Promise<void>`

Enable offline mode.

```typescript
await client.enableOfflineMode();
```

##### `getOfflineQueue(): Promise<OfflineOperation[]>`

Get queued offline operations.

```typescript
const queue = await client.getOfflineQueue();
```

#### Utilities

##### `clearCache(): Promise<void>`

Clear in-memory cache.

```typescript
await client.clearCache();
```

##### `clearAllData(): Promise<void>`

Clear all local data.

```typescript
await client.clearAllData();
```

##### `getStorageSize(): Promise<{ used: number; quota: number }>`

Get storage usage.

```typescript
const { used, quota } = await client.getStorageSize();
console.log(`Using ${used / 1024 / 1024}MB of ${quota / 1024 / 1024}MB`);
```

## Types

### ContinuumConfig

```typescript
interface ContinuumConfig {
  apiUrl: string;
  apiKey?: string;
  enableOffline?: boolean;
  syncInterval?: number;
  maxOfflineStorage?: number;
  enableBackgroundSync?: boolean;
  enablePushNotifications?: boolean;
  logLevel?: 'debug' | 'info' | 'warn' | 'error' | 'silent';
  customHeaders?: Record<string, string>;
  timeout?: number;
  enableLocalEmbeddings?: boolean;
  retry?: {
    maxAttempts?: number;
    backoff?: 'linear' | 'exponential';
    initialDelay?: number;
  };
}
```

### Memory

```typescript
interface Memory {
  id: string;
  userId: string;
  type: 'episodic' | 'semantic' | 'procedural' | 'working';
  content: string;
  metadata?: Record<string, any>;
  embedding?: number[];
  concepts?: string[];
  entities?: Entity[];
  importance?: number;
  accessCount?: number;
  lastAccessedAt?: string;
  createdAt: string;
  updatedAt: string;
  tags?: string[];
  source?: string;
  context?: string;
}
```

### CreateMemoryInput

```typescript
interface CreateMemoryInput {
  type: MemoryType;
  content: string;
  metadata?: Record<string, any>;
  tags?: string[];
  source?: string;
  context?: string;
  importance?: number;
}
```

### SearchOptions

```typescript
interface SearchOptions {
  type?: MemoryType;
  limit?: number;
  minSimilarity?: number;
  includeEmbeddings?: boolean;
  filters?: MemoryFilter;
}
```

### SearchResult

```typescript
interface SearchResult {
  memory: Memory;
  similarity: number;
  highlights?: string[];
}
```

For complete type definitions, see [types.ts](../src/types.ts).
