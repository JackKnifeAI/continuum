# Hooks Reference

## useMemories

Fetch and paginate memories.

```typescript
function useMemories(filter?: MemoryFilter): UseMemoriesResult
```

### Example

```typescript
function MemoryList() {
  const { memories, isLoading, error, refetch, loadMore, hasMore } =
    useMemories({
      type: 'episodic',
      limit: 20,
    });

  return (
    <FlatList
      data={memories}
      onEndReached={loadMore}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={refetch} />}
    />
  );
}
```

## useMemory

Fetch a single memory by ID.

```typescript
function useMemory(id: string): UseMemoryResult
```

### Example

```typescript
function MemoryDetail({ id }: { id: string }) {
  const { memory, isLoading, error, refetch } = useMemory(id);

  if (isLoading) return <Loader />;
  if (error) return <Error error={error} />;

  return <MemoryView memory={memory} />;
}
```

## useSearch

Search memories with debouncing.

```typescript
function useSearch(initialQuery = '', debounceMs = 300): UseSearchResult
```

### Example

```typescript
function SearchScreen() {
  const { results, isLoading, search, clear } = useSearch();

  return (
    <>
      <SearchBar onChangeText={search} />
      {isLoading ? (
        <Loader />
      ) : (
        <SearchResults results={results} />
      )}
    </>
  );
}
```

## useCreateMemory

Create memories with mutation state.

```typescript
function useCreateMemory(): UseCreateMemoryMutation
```

### Example

```typescript
function CreateForm() {
  const { createMemory, isLoading, error } = useCreateMemory();

  const handleSubmit = async (content: string) => {
    try {
      await createMemory({
        type: 'episodic',
        content,
        tags: ['user-created'],
      });
      Alert.alert('Success', 'Memory created');
    } catch (err) {
      Alert.alert('Error', error?.message || 'Failed');
    }
  };

  return <Form onSubmit={handleSubmit} loading={isLoading} />;
}
```

## useLearn

Learn from conversations.

```typescript
function useLearn(): UseLearnMutation
```

### Example

```typescript
function ChatScreen() {
  const { learn, isLoading, result } = useLearn();

  const handleLearn = async (messages: Message[]) => {
    const result = await learn(messages);
    console.log(`Created ${result.memoriesCreated} memories`);
  };

  return <Chat onLearn={handleLearn} />;
}
```

## useSession

Manage authentication session.

```typescript
function useSession(): UseSessionResult
```

### Example

```typescript
function AuthGate({ children }: { children: React.ReactNode }) {
  const { session, isLoading, signIn, signOut } = useSession();

  if (isLoading) return <Splash />;

  if (!session) {
    return <LoginScreen onSignIn={signIn} />;
  }

  return <>{children}</>;
}
```

## useUser

Get current user.

```typescript
function useUser(): UseUserResult
```

### Example

```typescript
function ProfileHeader() {
  const { user, isLoading } = useUser();

  if (isLoading) return <Skeleton />;

  return (
    <View>
      <Text>{user?.name}</Text>
      <Text>{user?.email}</Text>
    </View>
  );
}
```

## useSync

Manual sync control.

```typescript
function useSync(): UseSyncMutation
```

### Example

```typescript
function SyncButton() {
  const { sync, isLoading, result } = useSync();

  return (
    <Button
      onPress={sync}
      loading={isLoading}
      title={result ? `Synced ${result.memoriesSynced} items` : 'Sync Now'}
    />
  );
}
```

## useOfflineStatus

Monitor offline status.

```typescript
function useOfflineStatus(): boolean
```

### Example

```typescript
function OfflineIndicator() {
  const isOffline = useOfflineStatus();

  if (!isOffline) return null;

  return <Banner type="warning" text="You're offline" />;
}
```

## useConnectionStatus

Monitor network connection.

```typescript
function useConnectionStatus(): ConnectionStatus
```

### Example

```typescript
function ConnectionBadge() {
  const { isConnected, type } = useConnectionStatus();

  return (
    <Badge
      color={isConnected ? 'green' : 'red'}
      text={isConnected ? type : 'Offline'}
    />
  );
}
```

## useSyncStatus

Monitor sync status.

```typescript
function useSyncStatus(): SyncStatus
```

### Example

```typescript
function SyncIndicator() {
  const { isSyncing, pendingOperations } = useSyncStatus();

  if (isSyncing) return <ActivityIndicator />;

  if (pendingOperations > 0) {
    return <Text>{pendingOperations} pending</Text>;
  }

  return null;
}
```

## useConcepts

Fetch concepts with filtering.

```typescript
function useConcepts(filter?: ConceptFilter): UseConceptsResult
```

### Example

```typescript
function ConceptBrowser() {
  const { concepts, isLoading, refetch } = useConcepts({
    category: 'work',
    minImportance: 0.5,
  });

  return (
    <ConceptCloud
      concepts={concepts}
      onConceptPress={(concept) => console.log(concept)}
    />
  );
}
```
