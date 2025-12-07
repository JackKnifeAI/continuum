# @continuum/react-native

Official React Native SDK for CONTINUUM - AI memory and knowledge graph integration for mobile apps.

## Features

- **Memory Management** - Create, search, and organize memories
- **Semantic Search** - Vector-based search with similarity scoring
- **Concept Extraction** - Automatic concept and entity extraction
- **Offline-First** - Full offline support with background sync
- **Type-Safe** - Complete TypeScript definitions
- **Native Performance** - Native modules for embeddings and secure storage
- **React Hooks** - Comprehensive hooks for React Native
- **UI Components** - Pre-built components for common patterns

## Installation

```bash
npm install @continuum/react-native
# or
yarn add @continuum/react-native
```

### iOS

```bash
cd ios && pod install
```

### Android

No additional steps required.

## Quick Start

### 1. Initialize the client

```typescript
import { ContinuumClient, ContinuumProvider } from '@continuum/react-native';

const client = new ContinuumClient({
  apiUrl: 'https://api.continuum.ai',
  apiKey: 'your-api-key',
  enableOffline: true,
  enableBackgroundSync: true,
});

function App() {
  return (
    <ContinuumProvider client={client}>
      <YourApp />
    </ContinuumProvider>
  );
}
```

### 2. Use hooks in your components

```typescript
import { useMemories, useCreateMemory } from '@continuum/react-native';

function MemoriesScreen() {
  const { memories, isLoading } = useMemories({ type: 'episodic' });
  const { createMemory } = useCreateMemory();

  const handleCreate = async () => {
    await createMemory({
      type: 'episodic',
      content: 'Just had a great meeting with the team!',
      tags: ['work', 'meeting'],
    });
  };

  // ... render UI
}
```

### 3. Use pre-built components

```typescript
import { MemoryList, SearchBar, OfflineBanner } from '@continuum/react-native';

function MemoriesScreen() {
  return (
    <>
      <OfflineBanner />
      <SearchBar onSearch={(query) => console.log(query)} />
      <MemoryList
        filter={{ type: 'episodic' }}
        onMemoryPress={(memory) => navigation.navigate('Detail', { memory })}
      />
    </>
  );
}
```

## API Reference

### Client

```typescript
const client = new ContinuumClient(config);

// Authentication
await client.signIn(email, password);
await client.signOut();

// Memory operations
const memory = await client.createMemory(input);
const memories = await client.getMemories(filter);
const results = await client.searchMemories(query);

// Learning
const result = await client.learn(conversation);
const memories = await client.recall(context);

// Sync
await client.sync();
const status = await client.getSyncStatus();
```

### Hooks

- `useMemories(filter)` - Fetch and paginate memories
- `useMemory(id)` - Fetch single memory
- `useSearch(query)` - Search with debouncing
- `useConcepts(filter)` - Fetch concepts
- `useSession()` - Manage authentication
- `useUser()` - Get current user
- `useCreateMemory()` - Create memories
- `useLearn()` - Learn from conversations
- `useSync()` - Manual sync
- `useOfflineStatus()` - Monitor offline status
- `useConnectionStatus()` - Monitor connection
- `useSyncStatus()` - Monitor sync status

### Components

- `<ContinuumProvider>` - Context provider
- `<MemoryCard>` - Single memory display
- `<MemoryList>` - Scrollable memory list
- `<MemoryDetail>` - Full memory view
- `<CreateMemoryForm>` - Memory creation form
- `<SearchBar>` - Search input
- `<SearchResults>` - Search results list
- `<ConceptTag>` - Concept badge
- `<ConceptCloud>` - Tag cloud
- `<SyncStatusBadge>` - Sync indicator
- `<OfflineBanner>` - Offline warning
- `<ConnectionIndicator>` - Network status

## Configuration

```typescript
interface ContinuumConfig {
  apiUrl: string;
  apiKey?: string;
  enableOffline?: boolean; // default: true
  syncInterval?: number; // default: 300000 (5 min)
  maxOfflineStorage?: number; // default: 100 (MB)
  enableBackgroundSync?: boolean; // default: true
  enablePushNotifications?: boolean; // default: false
  logLevel?: 'debug' | 'info' | 'warn' | 'error' | 'silent';
  timeout?: number; // default: 30000
  enableLocalEmbeddings?: boolean; // default: true
  retry?: {
    maxAttempts?: number; // default: 3
    backoff?: 'linear' | 'exponential'; // default: 'exponential'
    initialDelay?: number; // default: 1000
  };
}
```

## Offline Support

The SDK is offline-first by default:

- All operations work offline
- Changes are queued for sync
- Automatic sync when online
- Background sync support
- Conflict resolution

```typescript
// Enable offline mode
await client.enableOfflineMode();

// Check offline queue
const queue = await client.getOfflineQueue();

// Manual sync
await client.sync();
```

## Native Modules

### Secure Storage

```typescript
import { SecureStorage } from '@continuum/react-native';

await SecureStorage.set('key', 'value');
const value = await SecureStorage.get('key');
await SecureStorage.remove('key');
await SecureStorage.clear();
```

### Embedding Generation

```typescript
import { EmbeddingGenerator } from '@continuum/react-native';

const result = await EmbeddingGenerator.generate('Hello world');
// { embedding: number[], dimensions: 384, processingTime: 45.2 }
```

## Examples

See the [example](./example) directory for a complete example app.

## License

MIT

## Support

- Documentation: https://docs.continuum.ai
- Issues: https://github.com/continuum-ai/react-native-continuum/issues
- Discord: https://discord.gg/continuum
