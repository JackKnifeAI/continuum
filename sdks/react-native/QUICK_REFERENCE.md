# CONTINUUM React Native SDK - Quick Reference

## Installation

```bash
npm install @continuum/react-native
cd ios && pod install  # iOS only
```

## Setup

```typescript
import { ContinuumClient, ContinuumProvider } from '@continuum/react-native';

const client = new ContinuumClient({
  apiUrl: 'https://api.continuum.ai',
  apiKey: 'your-key',
});

<ContinuumProvider client={client}>
  <App />
</ContinuumProvider>
```

## Hooks Cheat Sheet

```typescript
// Fetch data
const { memories, isLoading, refetch, loadMore } = useMemories({ type: 'episodic' });
const { memory } = useMemory('id');
const { results, search } = useSearch();
const { concepts } = useConcepts();

// Auth
const { session, signIn, signOut } = useSession();
const { user } = useUser();

// Mutations
const { createMemory } = useCreateMemory();
const { learn } = useLearn();
const { sync } = useSync();

// Status
const isOffline = useOfflineStatus();
const { isConnected, type } = useConnectionStatus();
const { isSyncing, pendingOperations } = useSyncStatus();
```

## Components Quick Use

```typescript
// Memory display
<MemoryCard memory={memory} onPress={handlePress} />
<MemoryList filter={{ type: 'episodic' }} onMemoryPress={handlePress} />
<MemoryDetail memoryId="id" />
<CreateMemoryForm onSubmit={handleSubmit} />

// Search
<SearchBar onSearch={handleSearch} />
<SearchResults query={query} />
<SearchSuggestions onSelect={handleSelect} />

// Concepts
<ConceptTag concept={concept} />
<ConceptCloud concepts={concepts} />

// Status
<OfflineBanner />
<SyncStatusBadge />
<ConnectionIndicator />
```

## Client API Quick Use

```typescript
// Auth
await client.signIn(email, password);
await client.signOut();

// Memories
const memory = await client.createMemory({ type: 'episodic', content: '...' });
const memories = await client.getMemories({ type: 'episodic', limit: 20 });
const results = await client.searchMemories('query', { limit: 10 });

// Learning
const result = await client.learn([
  { role: 'user', content: 'What did we discuss?' },
  { role: 'assistant', content: 'We talked about...' }
]);

// Sync
await client.sync();
const queue = await client.getOfflineQueue();
```

## Native Modules

```typescript
import { SecureStorage, EmbeddingGenerator } from '@continuum/react-native';

// Secure storage
await SecureStorage.set('key', 'value');
const value = await SecureStorage.get('key');

// Embeddings
const result = await EmbeddingGenerator.generate('text');
// { embedding: number[], dimensions: 384, processingTime: 45 }
```

## API Surface Summary

- **Client Methods**: 22
- **React Hooks**: 13
- **Components**: 14
- **Native Methods**: 6 per platform
- **TypeScript Types**: 50+

## Platform Support

- **iOS**: 13.0+
- **Android**: 21+ (Android 5.0)
- **Offline**: Full support
- **Background Sync**: iOS + Android
- **Secure Storage**: Keychain + EncryptedSharedPreferences

## Key Features

✅ Offline-first architecture
✅ Background sync
✅ Secure storage
✅ Local embeddings
✅ TypeScript types
✅ React hooks
✅ Pre-built components
✅ Native performance

## Documentation

- `/docs/API_REFERENCE.md` - Full API docs
- `/docs/HOOKS.md` - Hooks guide
- `/README.md` - Quick start
- `/example/App.tsx` - Example app

## Package Location

```
/var/home/alexandergcasavant/Projects/continuum/sdks/react-native/react-native-continuum/
```
