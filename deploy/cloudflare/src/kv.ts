/**
 * CONTINUUM Cloudflare Workers - KV Storage Utilities
 */

import type { Env } from './types';

export class KVCache {
  private kv: KVNamespace;
  private defaultTTL: number = 3600; // 1 hour

  constructor(kv: KVNamespace) {
    this.kv = kv;
  }

  /**
   * Get value from cache
   */
  async get<T = unknown>(key: string): Promise<T | null> {
    try {
      const value = await this.kv.get(key, { type: 'json' });
      return value as T | null;
    } catch (error) {
      console.error(`KV get error for key ${key}:`, error);
      return null;
    }
  }

  /**
   * Set value in cache with optional TTL
   */
  async set<T = unknown>(
    key: string,
    value: T,
    ttl?: number
  ): Promise<void> {
    try {
      await this.kv.put(
        key,
        JSON.stringify(value),
        ttl ? { expirationTtl: ttl } : { expirationTtl: this.defaultTTL }
      );
    } catch (error) {
      console.error(`KV set error for key ${key}:`, error);
      throw error;
    }
  }

  /**
   * Delete value from cache
   */
  async delete(key: string): Promise<void> {
    try {
      await this.kv.delete(key);
    } catch (error) {
      console.error(`KV delete error for key ${key}:`, error);
      throw error;
    }
  }

  /**
   * Check if key exists
   */
  async exists(key: string): Promise<boolean> {
    const value = await this.kv.get(key);
    return value !== null;
  }

  /**
   * List keys with prefix
   */
  async listKeys(prefix: string, limit: number = 100): Promise<string[]> {
    try {
      const list = await this.kv.list({ prefix, limit });
      return list.keys.map(k => k.name);
    } catch (error) {
      console.error(`KV list error for prefix ${prefix}:`, error);
      return [];
    }
  }

  /**
   * Batch delete keys with prefix
   */
  async deletePrefix(prefix: string): Promise<number> {
    const keys = await this.listKeys(prefix, 1000);
    await Promise.all(keys.map(key => this.delete(key)));
    return keys.length;
  }
}

export class SessionStore {
  private kv: KVNamespace;
  private sessionTTL: number = 86400; // 24 hours

  constructor(kv: KVNamespace) {
    this.kv = kv;
  }

  /**
   * Create or update session
   */
  async set(
    sessionId: string,
    userId: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    const session = {
      id: sessionId,
      user_id: userId,
      created_at: new Date().toISOString(),
      metadata: metadata || {},
    };

    await this.kv.put(
      `session:${sessionId}`,
      JSON.stringify(session),
      { expirationTtl: this.sessionTTL }
    );
  }

  /**
   * Get session
   */
  async get(sessionId: string): Promise<{
    id: string;
    user_id: string;
    created_at: string;
    metadata: Record<string, unknown>;
  } | null> {
    const value = await this.kv.get(`session:${sessionId}`, { type: 'json' });
    return value as any;
  }

  /**
   * Delete session
   */
  async delete(sessionId: string): Promise<void> {
    await this.kv.delete(`session:${sessionId}`);
  }

  /**
   * Extend session TTL
   */
  async extend(sessionId: string): Promise<void> {
    const session = await this.get(sessionId);
    if (session) {
      await this.kv.put(
        `session:${sessionId}`,
        JSON.stringify(session),
        { expirationTtl: this.sessionTTL }
      );
    }
  }

  /**
   * List user sessions
   */
  async listUserSessions(userId: string): Promise<string[]> {
    // Note: This is expensive and should be used sparingly
    // Consider using a different pattern for production
    const list = await this.kv.list({ prefix: 'session:' });
    const sessions: string[] = [];

    for (const key of list.keys) {
      const session = await this.kv.get(key.name, { type: 'json' }) as any;
      if (session?.user_id === userId) {
        sessions.push(session.id);
      }
    }

    return sessions;
  }
}

/**
 * Rate limiting using KV storage
 */
export class RateLimiter {
  private kv: KVNamespace;
  private limits: Map<string, number> = new Map([
    ['free', 100],
    ['paid', 1000],
    ['enterprise', 10000],
  ]);
  private window: number = 60; // 1 minute in seconds

  constructor(kv: KVNamespace) {
    this.kv = kv;
  }

  /**
   * Check if request is within rate limit
   */
  async check(
    userId: string,
    tier: 'free' | 'paid' | 'enterprise'
  ): Promise<{
    allowed: boolean;
    remaining: number;
    reset_at: string;
    total: number;
  }> {
    const limit = this.limits.get(tier) || 100;
    const key = `ratelimit:${userId}:${this.getCurrentWindow()}`;

    // Get current count
    const countStr = await this.kv.get(key);
    const count = countStr ? parseInt(countStr) : 0;

    const allowed = count < limit;
    const remaining = Math.max(0, limit - count - 1);

    if (allowed) {
      // Increment counter
      await this.kv.put(
        key,
        (count + 1).toString(),
        { expirationTtl: this.window }
      );
    }

    return {
      allowed,
      remaining,
      reset_at: this.getResetTime(),
      total: limit,
    };
  }

  /**
   * Get current time window (minute-based)
   */
  private getCurrentWindow(): string {
    const now = new Date();
    return `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}-${now.getMinutes()}`;
  }

  /**
   * Get reset time (start of next minute)
   */
  private getResetTime(): string {
    const now = new Date();
    const next = new Date(now.getTime() + this.window * 1000);
    next.setSeconds(0);
    next.setMilliseconds(0);
    return next.toISOString();
  }

  /**
   * Reset rate limit for user
   */
  async reset(userId: string): Promise<void> {
    const key = `ratelimit:${userId}:${this.getCurrentWindow()}`;
    await this.kv.delete(key);
  }

  /**
   * Get current usage
   */
  async getUsage(
    userId: string,
    tier: 'free' | 'paid' | 'enterprise'
  ): Promise<{
    used: number;
    limit: number;
    remaining: number;
    reset_at: string;
  }> {
    const limit = this.limits.get(tier) || 100;
    const key = `ratelimit:${userId}:${this.getCurrentWindow()}`;
    const countStr = await this.kv.get(key);
    const used = countStr ? parseInt(countStr) : 0;

    return {
      used,
      limit,
      remaining: Math.max(0, limit - used),
      reset_at: this.getResetTime(),
    };
  }
}

/**
 * Helper to create KV instances from environment
 */
export function createKVInstances(env: Env) {
  return {
    cache: new KVCache(env.CACHE),
    sessions: new SessionStore(env.SESSIONS),
    rateLimiter: new RateLimiter(env.CACHE), // Reuse CACHE KV for rate limiting
  };
}
