/**
 * CONTINUUM Cloudflare Workers - Health Check Handler
 */

import { Context } from 'hono';
import type { Env, HealthCheck, APIResponse } from '../types';

const startTime = Date.now();

/**
 * Health check endpoint
 * GET /health
 */
export async function healthHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  const checks = await performHealthChecks(c.env);

  const isHealthy = checks.kv && checks.durable_objects;
  const status: 'healthy' | 'degraded' | 'unhealthy' =
    isHealthy ? 'healthy' : (checks.kv || checks.durable_objects ? 'degraded' : 'unhealthy');

  const health: HealthCheck = {
    status,
    version: c.env.API_VERSION || 'v1',
    timestamp: new Date().toISOString(),
    services: checks,
    uptime_ms: Date.now() - startTime,
  };

  const statusCode = status === 'healthy' ? 200 : (status === 'degraded' ? 200 : 503);

  return c.json({
    success: isHealthy,
    data: health,
    meta: {
      timestamp: new Date().toISOString(),
      request_id: c.get('requestId') || crypto.randomUUID(),
    },
  } as APIResponse<HealthCheck>, statusCode);
}

/**
 * Readiness check endpoint
 * GET /ready
 */
export async function readinessHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  const checks = await performHealthChecks(c.env);
  const isReady = checks.kv && checks.durable_objects;

  return c.json({
    success: isReady,
    data: {
      ready: isReady,
      checks,
    },
  }, isReady ? 200 : 503);
}

/**
 * Liveness check endpoint
 * GET /live
 */
export async function livenessHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  return c.json({
    success: true,
    data: {
      alive: true,
      timestamp: new Date().toISOString(),
    },
  });
}

/**
 * Version endpoint
 * GET /version
 */
export async function versionHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  return c.json({
    success: true,
    data: {
      version: c.env.API_VERSION || 'v1',
      environment: c.env.ENVIRONMENT || 'production',
      build: {
        timestamp: new Date().toISOString(),
      },
    },
  });
}

/**
 * Perform health checks on services
 */
async function performHealthChecks(env: Env): Promise<{
  kv: boolean;
  durable_objects: boolean;
  database?: boolean;
}> {
  const checks = {
    kv: false,
    durable_objects: false,
    database: undefined as boolean | undefined,
  };

  // Check KV
  try {
    const testKey = `health:${Date.now()}`;
    await env.CACHE.put(testKey, 'ok', { expirationTtl: 10 });
    const value = await env.CACHE.get(testKey);
    checks.kv = value === 'ok';
    await env.CACHE.delete(testKey);
  } catch (error) {
    console.error('KV health check failed:', error);
    checks.kv = false;
  }

  // Check Durable Objects
  try {
    // Simple check - just verify the binding exists
    checks.durable_objects = !!env.SYNC_SESSIONS;
  } catch (error) {
    console.error('Durable Objects health check failed:', error);
    checks.durable_objects = false;
  }

  // Check database if configured
  if (env.DATABASE_URL) {
    try {
      // TODO: Implement database health check
      // For now, just mark as undefined
      checks.database = undefined;
    } catch (error) {
      console.error('Database health check failed:', error);
      checks.database = false;
    }
  }

  return checks;
}

/**
 * Metrics endpoint
 * GET /metrics
 */
export async function metricsHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  const user = c.get('user');

  if (!user || user.tier !== 'enterprise') {
    return c.json({
      success: false,
      error: {
        code: 'FORBIDDEN',
        message: 'Metrics endpoint requires enterprise tier',
      },
    }, 403);
  }

  // TODO: Implement metrics collection
  // For now, return basic metrics
  const metrics = {
    uptime_ms: Date.now() - startTime,
    timestamp: new Date().toISOString(),
    // Add more metrics as needed
  };

  return c.json({
    success: true,
    data: metrics,
  });
}
