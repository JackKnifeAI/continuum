/**
 * CONTINUUM Cloudflare Workers - Type Definitions
 */

export interface Env {
  // KV Namespaces
  CACHE: KVNamespace;
  SESSIONS: KVNamespace;

  // Durable Objects
  SYNC_SESSIONS: DurableObjectNamespace;

  // Environment Variables
  ENVIRONMENT: string;
  API_VERSION: string;
  LOG_LEVEL: string;

  // Secrets
  JWT_SECRET: string;
  DATABASE_URL?: string;
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
}

export interface JWTPayload {
  sub: string; // user_id
  email?: string;
  tier: 'free' | 'paid' | 'enterprise';
  iat: number;
  exp: number;
}

export interface RateLimitConfig {
  free: number;
  paid: number;
  enterprise: number;
  window: number; // in seconds
}

export interface Memory {
  id: string;
  user_id: string;
  content: string;
  metadata?: Record<string, unknown>;
  embedding?: number[];
  timestamp: string;
  tags?: string[];
}

export interface SearchQuery {
  query: string;
  limit?: number;
  offset?: number;
  filters?: Record<string, unknown>;
  include_embeddings?: boolean;
}

export interface SearchResult {
  memories: Memory[];
  total: number;
  query: string;
  took_ms: number;
}

export interface SyncMessage {
  type: 'memory_created' | 'memory_updated' | 'memory_deleted' | 'search_query' | 'ping' | 'pong';
  payload?: unknown;
  timestamp: string;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  meta?: {
    timestamp: string;
    request_id: string;
    took_ms?: number;
  };
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  services: {
    kv: boolean;
    durable_objects: boolean;
    database?: boolean;
  };
  uptime_ms: number;
}

export interface RateLimitInfo {
  user_id: string;
  tier: 'free' | 'paid' | 'enterprise';
  requests_made: number;
  requests_remaining: number;
  reset_at: string;
  window_start: string;
}
