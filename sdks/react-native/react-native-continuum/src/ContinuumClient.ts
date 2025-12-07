/**
 * CONTINUUM React Native SDK - Main Client
 * Production-grade client with offline support, caching, and error handling
 */

import type {
  ContinuumConfig,
  User,
  Session,
  AuthCredentials,
  Memory,
  CreateMemoryInput,
  UpdateMemoryInput,
  MemoryFilter,
  SearchOptions,
  SearchResult,
  Message,
  LearnResult,
  Concept,
  ConceptFilter,
  SyncResult,
  OfflineOperation,
  ConnectionStatus,
} from './types';

import {
  NetworkError,
  AuthenticationError,
  ValidationError,
  OfflineError,
  QuotaExceededError,
} from './types';

import { StorageManager } from './storage/StorageManager';
import { SyncManager } from './sync/SyncManager';
import { NetworkManager } from './network/NetworkManager';
import { CacheManager } from './cache/CacheManager';
import { Logger } from './utils/Logger';

export class ContinuumClient {
  private config: Required<ContinuumConfig>;
  private storageManager: StorageManager;
  private syncManager: SyncManager;
  private networkManager: NetworkManager;
  private cacheManager: CacheManager;
  private logger: Logger;
  private session: Session | null = null;
  private isInitialized = false;

  constructor(config: ContinuumConfig) {
    // Set defaults
    this.config = {
      apiUrl: config.apiUrl,
      apiKey: config.apiKey || '',
      enableOffline: config.enableOffline ?? true,
      syncInterval: config.syncInterval ?? 300000, // 5 minutes
      maxOfflineStorage: config.maxOfflineStorage ?? 100, // 100MB
      enableBackgroundSync: config.enableBackgroundSync ?? true,
      enablePushNotifications: config.enablePushNotifications ?? false,
      logLevel: config.logLevel ?? 'info',
      customHeaders: config.customHeaders ?? {},
      timeout: config.timeout ?? 30000,
      enableLocalEmbeddings: config.enableLocalEmbeddings ?? true,
      retry: {
        maxAttempts: config.retry?.maxAttempts ?? 3,
        backoff: config.retry?.backoff ?? 'exponential',
        initialDelay: config.retry?.initialDelay ?? 1000,
      },
    };

    this.logger = new Logger(this.config.logLevel);
    this.storageManager = new StorageManager(this.config, this.logger);
    this.networkManager = new NetworkManager(this.config, this.logger);
    this.cacheManager = new CacheManager(this.config, this.logger);
    this.syncManager = new SyncManager(
      this.config,
      this.storageManager,
      this.networkManager,
      this.logger
    );
  }

  // ========================================================================
  // Initialization
  // ========================================================================

  async initialize(): Promise<void> {
    if (this.isInitialized) {
      this.logger.warn('Client already initialized');
      return;
    }

    try {
      this.logger.info('Initializing CONTINUUM client...');

      // Initialize storage
      await this.storageManager.initialize();

      // Restore session if exists
      this.session = await this.storageManager.getSession();

      // Initialize sync manager
      if (this.config.enableOffline) {
        await this.syncManager.initialize();
      }

      // Start background sync if enabled
      if (this.config.enableBackgroundSync && this.session) {
        await this.syncManager.startBackgroundSync();
      }

      this.isInitialized = true;
      this.logger.info('CONTINUUM client initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize client', error);
      throw error;
    }
  }

  private ensureInitialized(): void {
    if (!this.isInitialized) {
      throw new Error('Client not initialized. Call initialize() first.');
    }
  }

  // ========================================================================
  // Authentication
  // ========================================================================

  async signIn(email: string, password: string): Promise<User> {
    this.ensureInitialized();

    try {
      this.logger.info('Signing in user', { email });

      const response = await this.networkManager.post<{ session: Session }>(
        '/auth/signin',
        { email, password }
      );

      this.session = response.session;
      await this.storageManager.saveSession(this.session);

      // Start background sync
      if (this.config.enableBackgroundSync) {
        await this.syncManager.startBackgroundSync();
      }

      this.logger.info('User signed in successfully', { userId: this.session.user.id });
      return this.session.user;
    } catch (error) {
      this.logger.error('Sign in failed', error);
      throw new AuthenticationError('Failed to sign in', error);
    }
  }

  async signOut(): Promise<void> {
    this.ensureInitialized();

    try {
      this.logger.info('Signing out user');

      // Stop background sync
      await this.syncManager.stopBackgroundSync();

      // Call server signout
      if (this.session) {
        await this.networkManager.post('/auth/signout', {});
      }

      // Clear local session
      this.session = null;
      await this.storageManager.clearSession();

      this.logger.info('User signed out successfully');
    } catch (error) {
      this.logger.error('Sign out failed', error);
      throw error;
    }
  }

  async getSession(): Promise<Session | null> {
    this.ensureInitialized();
    return this.session;
  }

  async refreshSession(): Promise<Session> {
    this.ensureInitialized();

    if (!this.session) {
      throw new AuthenticationError('No session to refresh');
    }

    try {
      const response = await this.networkManager.post<{ session: Session }>(
        '/auth/refresh',
        { refreshToken: this.session.refreshToken }
      );

      this.session = response.session;
      await this.storageManager.saveSession(this.session);

      return this.session;
    } catch (error) {
      this.logger.error('Session refresh failed', error);
      throw new AuthenticationError('Failed to refresh session', error);
    }
  }

  // ========================================================================
  // Memory Operations
  // ========================================================================

  async createMemory(input: CreateMemoryInput): Promise<Memory> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Creating memory', { type: input.type });

      // Validate input
      if (!input.content || input.content.trim().length === 0) {
        throw new ValidationError('Memory content cannot be empty');
      }

      // Try online first
      if (await this.networkManager.isOnline()) {
        const memory = await this.networkManager.post<Memory>('/memories', input);
        await this.storageManager.saveMemory(memory);
        this.cacheManager.invalidate(`memory:${memory.id}`);
        return memory;
      }

      // Offline mode
      if (!this.config.enableOffline) {
        throw new OfflineError();
      }

      // Create offline and queue for sync
      const memory = await this.storageManager.createMemoryOffline(input);
      await this.syncManager.queueOperation({
        type: 'create',
        resource: 'memory',
        data: input,
        localId: memory.id,
      });

      this.logger.info('Memory created offline', { id: memory.id });
      return memory;
    } catch (error) {
      this.logger.error('Failed to create memory', error);
      throw error;
    }
  }

  async getMemory(id: string): Promise<Memory> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    const cacheKey = `memory:${id}`;

    try {
      // Check cache first
      const cached = await this.cacheManager.get<Memory>(cacheKey);
      if (cached) {
        this.logger.debug('Memory cache hit', { id });
        return cached;
      }

      // Try local storage
      const local = await this.storageManager.getMemory(id);
      if (local) {
        await this.cacheManager.set(cacheKey, local);
        return local;
      }

      // Fetch from server
      if (await this.networkManager.isOnline()) {
        const memory = await this.networkManager.get<Memory>(`/memories/${id}`);
        await this.storageManager.saveMemory(memory);
        await this.cacheManager.set(cacheKey, memory);
        return memory;
      }

      throw new Error(`Memory not found: ${id}`);
    } catch (error) {
      this.logger.error('Failed to get memory', { id, error });
      throw error;
    }
  }

  async searchMemories(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Searching memories', { query, options });

      // Try online search first
      if (await this.networkManager.isOnline()) {
        const results = await this.networkManager.post<SearchResult[]>(
          '/memories/search',
          { query, ...options }
        );
        return results;
      }

      // Offline search
      if (!this.config.enableOffline) {
        throw new OfflineError();
      }

      return await this.storageManager.searchMemoriesLocal(query, options);
    } catch (error) {
      this.logger.error('Failed to search memories', error);
      throw error;
    }
  }

  async updateMemory(id: string, input: UpdateMemoryInput): Promise<Memory> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Updating memory', { id });

      if (await this.networkManager.isOnline()) {
        const memory = await this.networkManager.patch<Memory>(`/memories/${id}`, input);
        await this.storageManager.saveMemory(memory);
        this.cacheManager.invalidate(`memory:${id}`);
        return memory;
      }

      // Offline mode
      if (!this.config.enableOffline) {
        throw new OfflineError();
      }

      const memory = await this.storageManager.updateMemoryOffline(id, input);
      await this.syncManager.queueOperation({
        type: 'update',
        resource: 'memory',
        data: { id, ...input },
        localId: id,
      });

      return memory;
    } catch (error) {
      this.logger.error('Failed to update memory', { id, error });
      throw error;
    }
  }

  async deleteMemory(id: string): Promise<void> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Deleting memory', { id });

      if (await this.networkManager.isOnline()) {
        await this.networkManager.delete(`/memories/${id}`);
        await this.storageManager.deleteMemory(id);
        this.cacheManager.invalidate(`memory:${id}`);
        return;
      }

      // Offline mode
      if (!this.config.enableOffline) {
        throw new OfflineError();
      }

      await this.storageManager.deleteMemory(id);
      await this.syncManager.queueOperation({
        type: 'delete',
        resource: 'memory',
        data: { id },
        localId: id,
      });
    } catch (error) {
      this.logger.error('Failed to delete memory', { id, error });
      throw error;
    }
  }

  async getMemories(filter?: MemoryFilter): Promise<Memory[]> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Getting memories', { filter });

      // Try online first
      if (await this.networkManager.isOnline()) {
        const memories = await this.networkManager.post<Memory[]>('/memories/query', filter);
        // Cache results
        for (const memory of memories) {
          await this.storageManager.saveMemory(memory);
        }
        return memories;
      }

      // Offline mode
      return await this.storageManager.getMemoriesLocal(filter);
    } catch (error) {
      this.logger.error('Failed to get memories', error);
      throw error;
    }
  }

  // ========================================================================
  // Learning Operations
  // ========================================================================

  async learn(conversation: Message[]): Promise<LearnResult> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Learning from conversation', { messageCount: conversation.length });

      if (conversation.length === 0) {
        throw new ValidationError('Conversation cannot be empty');
      }

      // Require online for learning
      if (!(await this.networkManager.isOnline())) {
        throw new OfflineError('Learning requires network connection');
      }

      const result = await this.networkManager.post<LearnResult>('/learn', {
        messages: conversation,
      });

      // Cache extracted data locally
      for (const memory of result.memories) {
        await this.storageManager.saveMemory(memory);
      }

      this.logger.info('Learning complete', {
        memories: result.memoriesCreated,
        concepts: result.conceptsExtracted,
      });

      return result;
    } catch (error) {
      this.logger.error('Failed to learn from conversation', error);
      throw error;
    }
  }

  async recall(context: string): Promise<Memory[]> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.debug('Recalling memories', { context });

      if (await this.networkManager.isOnline()) {
        return await this.networkManager.post<Memory[]>('/recall', { context });
      }

      // Offline recall
      return await this.storageManager.searchMemoriesLocal(context);
    } catch (error) {
      this.logger.error('Failed to recall memories', error);
      throw error;
    }
  }

  // ========================================================================
  // Concept Operations
  // ========================================================================

  async getConcepts(filter?: ConceptFilter): Promise<Concept[]> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      if (await this.networkManager.isOnline()) {
        return await this.networkManager.post<Concept[]>('/concepts/query', filter);
      }

      return await this.storageManager.getConceptsLocal(filter);
    } catch (error) {
      this.logger.error('Failed to get concepts', error);
      throw error;
    }
  }

  async getRelatedConcepts(conceptId: string): Promise<Concept[]> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      if (await this.networkManager.isOnline()) {
        return await this.networkManager.get<Concept[]>(`/concepts/${conceptId}/related`);
      }

      return await this.storageManager.getRelatedConceptsLocal(conceptId);
    } catch (error) {
      this.logger.error('Failed to get related concepts', { conceptId, error });
      throw error;
    }
  }

  // ========================================================================
  // Sync Operations
  // ========================================================================

  async sync(): Promise<SyncResult> {
    this.ensureInitialized();
    this.ensureAuthenticated();

    try {
      this.logger.info('Starting manual sync');
      return await this.syncManager.sync();
    } catch (error) {
      this.logger.error('Sync failed', error);
      throw error;
    }
  }

  async getLastSyncTime(): Promise<Date | null> {
    this.ensureInitialized();
    return await this.syncManager.getLastSyncTime();
  }

  async getSyncStatus(): Promise<{
    isSyncing: boolean;
    lastSyncTime?: Date;
    pendingOperations: number;
  }> {
    this.ensureInitialized();
    return await this.syncManager.getStatus();
  }

  // ========================================================================
  // Offline Support
  // ========================================================================

  async enableOfflineMode(): Promise<void> {
    this.ensureInitialized();
    this.config.enableOffline = true;
    await this.syncManager.initialize();
    this.logger.info('Offline mode enabled');
  }

  async disableOfflineMode(): Promise<void> {
    this.ensureInitialized();
    this.config.enableOffline = false;
    await this.syncManager.stopBackgroundSync();
    this.logger.info('Offline mode disabled');
  }

  async getOfflineQueue(): Promise<OfflineOperation[]> {
    this.ensureInitialized();
    return await this.syncManager.getQueue();
  }

  async getConnectionStatus(): Promise<ConnectionStatus> {
    return await this.networkManager.getConnectionStatus();
  }

  // ========================================================================
  // Utility Methods
  // ========================================================================

  private ensureAuthenticated(): void {
    if (!this.session) {
      throw new AuthenticationError('Not authenticated');
    }
  }

  async clearCache(): Promise<void> {
    this.ensureInitialized();
    await this.cacheManager.clear();
    this.logger.info('Cache cleared');
  }

  async clearAllData(): Promise<void> {
    this.ensureInitialized();
    await this.storageManager.clearAll();
    await this.cacheManager.clear();
    this.session = null;
    this.logger.info('All local data cleared');
  }

  async getStorageSize(): Promise<{ used: number; quota: number }> {
    this.ensureInitialized();
    return await this.storageManager.getStorageSize();
  }

  getConfig(): Readonly<Required<ContinuumConfig>> {
    return { ...this.config };
  }
}
