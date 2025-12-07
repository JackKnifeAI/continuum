/**
 * CONTINUUM React Native SDK - Type Definitions
 * Complete TypeScript types for the mobile SDK
 */

// ============================================================================
// Configuration Types
// ============================================================================

export interface ContinuumConfig {
  /** API base URL */
  apiUrl: string;

  /** API key for authentication */
  apiKey?: string;

  /** Enable offline mode with local storage */
  enableOffline?: boolean;

  /** Auto-sync interval in milliseconds (default: 5 minutes) */
  syncInterval?: number;

  /** Maximum offline storage in MB (default: 100MB) */
  maxOfflineStorage?: number;

  /** Enable background sync */
  enableBackgroundSync?: boolean;

  /** Enable push notifications */
  enablePushNotifications?: boolean;

  /** Logging level */
  logLevel?: 'debug' | 'info' | 'warn' | 'error' | 'silent';

  /** Custom headers for API requests */
  customHeaders?: Record<string, string>;

  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;

  /** Enable on-device embeddings */
  enableLocalEmbeddings?: boolean;

  /** Retry configuration */
  retry?: {
    maxAttempts?: number;
    backoff?: 'linear' | 'exponential';
    initialDelay?: number;
  };
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Session {
  accessToken: string;
  refreshToken: string;
  expiresAt: string;
  user: User;
}

export interface AuthCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

// ============================================================================
// Memory Types
// ============================================================================

export type MemoryType = 'episodic' | 'semantic' | 'procedural' | 'working';

export interface Memory {
  id: string;
  userId: string;
  type: MemoryType;
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

export interface CreateMemoryInput {
  type: MemoryType;
  content: string;
  metadata?: Record<string, any>;
  tags?: string[];
  source?: string;
  context?: string;
  importance?: number;
}

export interface UpdateMemoryInput {
  content?: string;
  metadata?: Record<string, any>;
  tags?: string[];
  importance?: number;
}

export interface MemoryFilter {
  type?: MemoryType;
  tags?: string[];
  source?: string;
  startDate?: string;
  endDate?: string;
  minImportance?: number;
  limit?: number;
  offset?: number;
}

export interface SearchOptions {
  type?: MemoryType;
  limit?: number;
  minSimilarity?: number;
  includeEmbeddings?: boolean;
  filters?: MemoryFilter;
}

export interface SearchResult {
  memory: Memory;
  similarity: number;
  highlights?: string[];
}

// ============================================================================
// Learning Types
// ============================================================================

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface LearnResult {
  memoriesCreated: number;
  conceptsExtracted: number;
  entitiesExtracted: number;
  memories: Memory[];
  concepts: Concept[];
  entities: Entity[];
}

export interface RecallContext {
  query?: string;
  limit?: number;
  includeRelated?: boolean;
}

// ============================================================================
// Concept Types
// ============================================================================

export interface Concept {
  id: string;
  name: string;
  description?: string;
  category?: string;
  importance?: number;
  memoryCount?: number;
  relatedConcepts?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ConceptFilter {
  category?: string;
  minImportance?: number;
  limit?: number;
  offset?: number;
}

export interface ConceptRelation {
  fromConceptId: string;
  toConceptId: string;
  relationshipType: string;
  strength?: number;
}

// ============================================================================
// Entity Types
// ============================================================================

export interface Entity {
  id: string;
  name: string;
  type: string;
  metadata?: Record<string, any>;
  memoryIds?: string[];
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Sync Types
// ============================================================================

export interface SyncResult {
  success: boolean;
  memoriesSynced: number;
  conceptsSynced: number;
  conflicts?: SyncConflict[];
  lastSyncTime: string;
  nextSyncTime?: string;
}

export interface SyncConflict {
  id: string;
  type: 'memory' | 'concept' | 'entity';
  localVersion: any;
  remoteVersion: any;
  resolution?: 'local' | 'remote' | 'merge';
}

export interface SyncStatus {
  isSyncing: boolean;
  lastSyncTime?: Date;
  nextSyncTime?: Date;
  pendingOperations: number;
  syncProgress?: number;
}

export interface OfflineOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  resource: 'memory' | 'concept' | 'entity';
  data: any;
  timestamp: string;
  retries: number;
  status: 'pending' | 'syncing' | 'failed';
}

// ============================================================================
// Connection Types
// ============================================================================

export interface ConnectionStatus {
  isConnected: boolean;
  isOnline: boolean;
  type?: 'wifi' | 'cellular' | 'ethernet' | 'none';
  isInternetReachable?: boolean;
}

// ============================================================================
// Error Types
// ============================================================================

export class ContinuumError extends Error {
  code: string;
  statusCode?: number;
  details?: any;

  constructor(message: string, code: string, statusCode?: number, details?: any) {
    super(message);
    this.name = 'ContinuumError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export class NetworkError extends ContinuumError {
  constructor(message: string = 'Network request failed', details?: any) {
    super(message, 'NETWORK_ERROR', 0, details);
    this.name = 'NetworkError';
  }
}

export class AuthenticationError extends ContinuumError {
  constructor(message: string = 'Authentication failed', details?: any) {
    super(message, 'AUTH_ERROR', 401, details);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends ContinuumError {
  constructor(message: string = 'Validation failed', details?: any) {
    super(message, 'VALIDATION_ERROR', 400, details);
    this.name = 'ValidationError';
  }
}

export class SyncConflictError extends ContinuumError {
  conflicts: SyncConflict[];

  constructor(message: string = 'Sync conflict detected', conflicts: SyncConflict[] = []) {
    super(message, 'SYNC_CONFLICT', 409, { conflicts });
    this.name = 'SyncConflictError';
    this.conflicts = conflicts;
  }
}

export class OfflineError extends ContinuumError {
  constructor(message: string = 'Operation requires network connection') {
    super(message, 'OFFLINE_ERROR', 0);
    this.name = 'OfflineError';
  }
}

export class QuotaExceededError extends ContinuumError {
  constructor(message: string = 'Storage quota exceeded', details?: any) {
    super(message, 'QUOTA_EXCEEDED', 507, details);
    this.name = 'QuotaExceededError';
  }
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UseMemoriesResult {
  memories: Memory[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  loadMore: () => Promise<void>;
  hasMore: boolean;
}

export interface UseMemoryResult {
  memory: Memory | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export interface UseSearchResult {
  results: SearchResult[];
  isLoading: boolean;
  error: Error | null;
  search: (query: string, options?: SearchOptions) => Promise<void>;
  clear: () => void;
}

export interface UseConceptsResult {
  concepts: Concept[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export interface UseSessionResult {
  session: Session | null;
  isLoading: boolean;
  error: Error | null;
  signIn: (credentials: AuthCredentials) => Promise<void>;
  signOut: () => Promise<void>;
}

export interface UseUserResult {
  user: User | null;
  isLoading: boolean;
  error: Error | null;
}

export interface UseCreateMemoryMutation {
  createMemory: (input: CreateMemoryInput) => Promise<Memory>;
  isLoading: boolean;
  error: Error | null;
  reset: () => void;
}

export interface UseLearnMutation {
  learn: (conversation: Message[]) => Promise<LearnResult>;
  isLoading: boolean;
  error: Error | null;
  result: LearnResult | null;
  reset: () => void;
}

export interface UseSyncMutation {
  sync: () => Promise<SyncResult>;
  isLoading: boolean;
  error: Error | null;
  result: SyncResult | null;
}

// ============================================================================
// Component Props Types
// ============================================================================

export interface MemoryCardProps {
  memory: Memory;
  onPress?: (memory: Memory) => void;
  onLongPress?: (memory: Memory) => void;
  showMetadata?: boolean;
  compact?: boolean;
}

export interface MemoryListProps {
  filter?: MemoryFilter;
  onMemoryPress?: (memory: Memory) => void;
  emptyComponent?: React.ReactNode;
  headerComponent?: React.ReactNode;
  footerComponent?: React.ReactNode;
}

export interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  debounceMs?: number;
  autoFocus?: boolean;
}

export interface ConceptTagProps {
  concept: Concept;
  onPress?: (concept: Concept) => void;
  size?: 'small' | 'medium' | 'large';
}

export interface ContinuumProviderProps {
  client: any; // ContinuumClient type
  children: React.ReactNode;
}

// ============================================================================
// Native Module Types
// ============================================================================

export interface NativeEmbeddingResult {
  embedding: number[];
  dimensions: number;
  processingTime: number;
}

export interface NativeSecureStorage {
  set(key: string, value: string): Promise<void>;
  get(key: string): Promise<string | null>;
  remove(key: string): Promise<void>;
  clear(): Promise<void>;
}

export interface NativeBackgroundSync {
  configure(options: BackgroundSyncOptions): Promise<void>;
  start(): Promise<void>;
  stop(): Promise<void>;
  getStatus(): Promise<BackgroundSyncStatus>;
}

export interface BackgroundSyncOptions {
  minimumInterval: number; // seconds
  requiresNetworkConnectivity: boolean;
  requiresCharging?: boolean;
  requiresDeviceIdle?: boolean;
}

export interface BackgroundSyncStatus {
  isEnabled: boolean;
  lastSyncTime?: string;
  nextScheduledSync?: string;
}

// ============================================================================
// Storage Types
// ============================================================================

export interface StorageAdapter {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
  clear(): Promise<void>;
  getAllKeys(): Promise<string[]>;
  multiGet(keys: string[]): Promise<[string, string | null][]>;
  multiSet(keyValuePairs: [string, string][]): Promise<void>;
}

export interface CacheOptions {
  ttl?: number; // seconds
  priority?: 'low' | 'normal' | 'high';
  persist?: boolean;
}

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
  priority: 'low' | 'normal' | 'high';
}
