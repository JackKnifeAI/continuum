/**
 * Cache Manager - In-memory cache with TTL support
 */

import type { CacheEntry, CacheOptions, ContinuumConfig } from '../types';
import type { Logger } from '../utils/Logger';

export class CacheManager {
  private cache: Map<string, CacheEntry<any>>;
  private config: Required<ContinuumConfig>;
  private logger: Logger;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(config: Required<ContinuumConfig>, logger: Logger) {
    this.cache = new Map();
    this.config = config;
    this.logger = logger;
    this.startCleanup();
  }

  async get<T>(key: string): Promise<T | null> {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    const now = Date.now();
    if (now - entry.timestamp > entry.ttl * 1000) {
      this.cache.delete(key);
      this.logger.debug('Cache entry expired', { key });
      return null;
    }

    this.logger.debug('Cache hit', { key });
    return entry.data as T;
  }

  async set<T>(key: string, data: T, options?: CacheOptions): Promise<void> {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: options?.ttl || 3600, // Default 1 hour
      priority: options?.priority || 'normal',
    };

    this.cache.set(key, entry);
    this.logger.debug('Cache set', { key, ttl: entry.ttl });

    // Evict if cache is too large
    await this.evictIfNeeded();
  }

  async invalidate(key: string): Promise<void> {
    this.cache.delete(key);
    this.logger.debug('Cache invalidated', { key });
  }

  async invalidatePattern(pattern: string): Promise<void> {
    const regex = new RegExp(pattern);
    let count = 0;

    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
        count++;
      }
    }

    this.logger.debug('Cache pattern invalidated', { pattern, count });
  }

  async clear(): Promise<void> {
    this.cache.clear();
    this.logger.info('Cache cleared');
  }

  private async evictIfNeeded(): Promise<void> {
    const maxEntries = 1000; // Configurable

    if (this.cache.size <= maxEntries) {
      return;
    }

    // Evict low priority entries first
    const entries = Array.from(this.cache.entries()).sort((a, b) => {
      const priorityOrder = { low: 0, normal: 1, high: 2 };
      return (
        priorityOrder[a[1].priority] - priorityOrder[b[1].priority] ||
        a[1].timestamp - b[1].timestamp
      );
    });

    // Remove oldest 10%
    const toRemove = Math.floor(maxEntries * 0.1);
    for (let i = 0; i < toRemove; i++) {
      this.cache.delete(entries[i][0]);
    }

    this.logger.debug('Cache evicted entries', { count: toRemove });
  }

  private startCleanup(): void {
    // Cleanup expired entries every 5 minutes
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 300000);
  }

  private cleanup(): void {
    const now = Date.now();
    let removed = 0;

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl * 1000) {
        this.cache.delete(key);
        removed++;
      }
    }

    if (removed > 0) {
      this.logger.debug('Cache cleanup', { removed });
    }
  }

  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    this.cache.clear();
  }
}
