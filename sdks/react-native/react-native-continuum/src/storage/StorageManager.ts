/**
 * Storage Manager - Handles local storage with AsyncStorage and SQLite
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import type {
  Session,
  Memory,
  CreateMemoryInput,
  UpdateMemoryInput,
  MemoryFilter,
  SearchOptions,
  SearchResult,
  Concept,
  ConceptFilter,
  ContinuumConfig,
} from '../types';
import type { Logger } from '../utils/Logger';

export class StorageManager {
  private config: Required<ContinuumConfig>;
  private logger: Logger;
  private dbInitialized = false;

  constructor(config: Required<ContinuumConfig>, logger: Logger) {
    this.config = config;
    this.logger = logger;
  }

  async initialize(): Promise<void> {
    if (this.dbInitialized) return;

    try {
      this.logger.info('Initializing storage manager');
      // Initialize SQLite database for larger datasets
      // await this.initializeDatabase();
      this.dbInitialized = true;
      this.logger.info('Storage manager initialized');
    } catch (error) {
      this.logger.error('Failed to initialize storage', error);
      throw error;
    }
  }

  // ========================================================================
  // Session Management
  // ========================================================================

  async saveSession(session: Session): Promise<void> {
    try {
      await AsyncStorage.setItem('continuum:session', JSON.stringify(session));
      this.logger.debug('Session saved');
    } catch (error) {
      this.logger.error('Failed to save session', error);
      throw error;
    }
  }

  async getSession(): Promise<Session | null> {
    try {
      const data = await AsyncStorage.getItem('continuum:session');
      return data ? JSON.parse(data) : null;
    } catch (error) {
      this.logger.error('Failed to get session', error);
      return null;
    }
  }

  async clearSession(): Promise<void> {
    try {
      await AsyncStorage.removeItem('continuum:session');
      this.logger.debug('Session cleared');
    } catch (error) {
      this.logger.error('Failed to clear session', error);
      throw error;
    }
  }

  // ========================================================================
  // Memory Operations
  // ========================================================================

  async saveMemory(memory: Memory): Promise<void> {
    try {
      const key = `continuum:memory:${memory.id}`;
      await AsyncStorage.setItem(key, JSON.stringify(memory));

      // Add to index
      await this.addToMemoryIndex(memory.id);

      this.logger.debug('Memory saved', { id: memory.id });
    } catch (error) {
      this.logger.error('Failed to save memory', error);
      throw error;
    }
  }

  async getMemory(id: string): Promise<Memory | null> {
    try {
      const key = `continuum:memory:${id}`;
      const data = await AsyncStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      this.logger.error('Failed to get memory', { id, error });
      return null;
    }
  }

  async deleteMemory(id: string): Promise<void> {
    try {
      const key = `continuum:memory:${id}`;
      await AsyncStorage.removeItem(key);
      await this.removeFromMemoryIndex(id);
      this.logger.debug('Memory deleted', { id });
    } catch (error) {
      this.logger.error('Failed to delete memory', { id, error });
      throw error;
    }
  }

  async createMemoryOffline(input: CreateMemoryInput): Promise<Memory> {
    const memory: Memory = {
      id: `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      userId: 'offline',
      type: input.type,
      content: input.content,
      metadata: input.metadata,
      tags: input.tags,
      source: input.source,
      context: input.context,
      importance: input.importance,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await this.saveMemory(memory);
    return memory;
  }

  async updateMemoryOffline(
    id: string,
    input: UpdateMemoryInput
  ): Promise<Memory> {
    const memory = await this.getMemory(id);
    if (!memory) {
      throw new Error(`Memory not found: ${id}`);
    }

    const updated: Memory = {
      ...memory,
      ...input,
      updatedAt: new Date().toISOString(),
    };

    await this.saveMemory(updated);
    return updated;
  }

  async getMemoriesLocal(filter?: MemoryFilter): Promise<Memory[]> {
    try {
      const ids = await this.getMemoryIndex();
      const memories: Memory[] = [];

      for (const id of ids) {
        const memory = await this.getMemory(id);
        if (memory && this.matchesFilter(memory, filter)) {
          memories.push(memory);
        }
      }

      // Sort by creation date (newest first)
      memories.sort(
        (a, b) =>
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );

      // Apply pagination
      const offset = filter?.offset || 0;
      const limit = filter?.limit || 20;
      return memories.slice(offset, offset + limit);
    } catch (error) {
      this.logger.error('Failed to get local memories', error);
      return [];
    }
  }

  async searchMemoriesLocal(
    query: string,
    options?: SearchOptions
  ): Promise<SearchResult[]> {
    try {
      const memories = await this.getMemoriesLocal(options?.filters);
      const results: SearchResult[] = [];

      const queryLower = query.toLowerCase();

      for (const memory of memories) {
        const contentLower = memory.content.toLowerCase();

        // Simple text matching (in production, use embeddings/vector search)
        if (contentLower.includes(queryLower)) {
          const similarity = this.calculateSimpleSimilarity(queryLower, contentLower);

          if (similarity >= (options?.minSimilarity || 0)) {
            results.push({
              memory,
              similarity,
            });
          }
        }
      }

      // Sort by similarity
      results.sort((a, b) => b.similarity - a.similarity);

      // Apply limit
      return results.slice(0, options?.limit || 10);
    } catch (error) {
      this.logger.error('Failed to search local memories', error);
      return [];
    }
  }

  // ========================================================================
  // Concept Operations
  // ========================================================================

  async getConceptsLocal(filter?: ConceptFilter): Promise<Concept[]> {
    try {
      const data = await AsyncStorage.getItem('continuum:concepts');
      if (!data) return [];

      const concepts: Concept[] = JSON.parse(data);

      // Apply filters
      let filtered = concepts;

      if (filter?.category) {
        filtered = filtered.filter((c) => c.category === filter.category);
      }

      if (filter?.minImportance) {
        filtered = filtered.filter(
          (c) => (c.importance || 0) >= filter.minImportance!
        );
      }

      // Sort by importance
      filtered.sort((a, b) => (b.importance || 0) - (a.importance || 0));

      // Apply pagination
      const offset = filter?.offset || 0;
      const limit = filter?.limit || 20;
      return filtered.slice(offset, offset + limit);
    } catch (error) {
      this.logger.error('Failed to get local concepts', error);
      return [];
    }
  }

  async getRelatedConceptsLocal(conceptId: string): Promise<Concept[]> {
    // Simplified implementation
    // In production, use graph database or relationship table
    return [];
  }

  // ========================================================================
  // Index Management
  // ========================================================================

  private async getMemoryIndex(): Promise<string[]> {
    try {
      const data = await AsyncStorage.getItem('continuum:memory:index');
      return data ? JSON.parse(data) : [];
    } catch (error) {
      return [];
    }
  }

  private async addToMemoryIndex(id: string): Promise<void> {
    const index = await this.getMemoryIndex();
    if (!index.includes(id)) {
      index.push(id);
      await AsyncStorage.setItem('continuum:memory:index', JSON.stringify(index));
    }
  }

  private async removeFromMemoryIndex(id: string): Promise<void> {
    const index = await this.getMemoryIndex();
    const filtered = index.filter((i) => i !== id);
    await AsyncStorage.setItem('continuum:memory:index', JSON.stringify(filtered));
  }

  // ========================================================================
  // Utility Methods
  // ========================================================================

  private matchesFilter(memory: Memory, filter?: MemoryFilter): boolean {
    if (!filter) return true;

    if (filter.type && memory.type !== filter.type) return false;

    if (filter.source && memory.source !== filter.source) return false;

    if (filter.tags && filter.tags.length > 0) {
      const memoryTags = memory.tags || [];
      const hasTag = filter.tags.some((tag) => memoryTags.includes(tag));
      if (!hasTag) return false;
    }

    if (filter.startDate) {
      if (new Date(memory.createdAt) < new Date(filter.startDate)) return false;
    }

    if (filter.endDate) {
      if (new Date(memory.createdAt) > new Date(filter.endDate)) return false;
    }

    if (filter.minImportance) {
      if ((memory.importance || 0) < filter.minImportance) return false;
    }

    return true;
  }

  private calculateSimpleSimilarity(query: string, content: string): number {
    // Simple similarity based on word overlap
    // In production, use embedding-based similarity
    const queryWords = query.split(' ');
    const contentWords = content.split(' ');

    const matches = queryWords.filter((word) => contentWords.includes(word));
    return matches.length / queryWords.length;
  }

  async clearAll(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const continuumKeys = keys.filter((key) => key.startsWith('continuum:'));
      await AsyncStorage.multiRemove(continuumKeys);
      this.logger.info('All local data cleared');
    } catch (error) {
      this.logger.error('Failed to clear all data', error);
      throw error;
    }
  }

  async getStorageSize(): Promise<{ used: number; quota: number }> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const continuumKeys = keys.filter((key) => key.startsWith('continuum:'));

      let totalSize = 0;
      for (const key of continuumKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += new Blob([value]).size;
        }
      }

      const quota = this.config.maxOfflineStorage * 1024 * 1024; // Convert MB to bytes

      return {
        used: totalSize,
        quota,
      };
    } catch (error) {
      this.logger.error('Failed to get storage size', error);
      return { used: 0, quota: 0 };
    }
  }
}
