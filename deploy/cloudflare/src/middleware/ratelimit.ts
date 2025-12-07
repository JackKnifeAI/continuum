/**
 * CONTINUUM Cloudflare Workers - Rate Limiting Middleware
 */

import { Context, Next } from 'hono';
import type { Env } from '../types';
import { RateLimiter } from '../kv';

/**
 * Rate limiting middleware
 * Enforces tier-based rate limits
 */
export async function rateLimitMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const user = c.get('user');

  if (!user) {
    return c.json({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Authentication required for rate limiting',
      },
    }, 401);
  }

  const rateLimiter = new RateLimiter(c.env.CACHE);
  const result = await rateLimiter.check(user.id, user.tier);

  // Set rate limit headers
  c.header('X-RateLimit-Limit', result.total.toString());
  c.header('X-RateLimit-Remaining', result.remaining.toString());
  c.header('X-RateLimit-Reset', result.reset_at);

  if (!result.allowed) {
    return c.json({
      success: false,
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: `Rate limit exceeded. Try again at ${result.reset_at}`,
        details: {
          limit: result.total,
          reset_at: result.reset_at,
        },
      },
    }, 429);
  }

  await next();
}

/**
 * IP-based rate limiting (for unauthenticated endpoints)
 */
export async function ipRateLimitMiddleware(
  c: Context<{ Bindings: Env }>,
  next: Next,
  options: { limit?: number; window?: number } = {}
) {
  const ip = c.req.header('CF-Connecting-IP') || c.req.header('X-Real-IP') || 'unknown';
  const limit = options.limit || 60; // 60 requests per minute by default
  const window = options.window || 60; // 1 minute

  const rateLimiter = new RateLimiter(c.env.CACHE);

  // Use IP as user ID for rate limiting
  const result = await rateLimiter.check(
    `ip:${ip}`,
    'free' // Use free tier limit structure
  );

  c.header('X-RateLimit-Limit', limit.toString());
  c.header('X-RateLimit-Remaining', result.remaining.toString());
  c.header('X-RateLimit-Reset', result.reset_at);

  if (!result.allowed) {
    return c.json({
      success: false,
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests from this IP address',
        details: {
          limit,
          reset_at: result.reset_at,
        },
      },
    }, 429);
  }

  await next();
}

/**
 * Endpoint-specific rate limiting
 */
export function endpointRateLimit(
  endpoint: string,
  limits: { free: number; paid: number; enterprise: number }
) {
  return async (c: Context<{ Bindings: Env }>, next: Next) => {
    const user = c.get('user');

    if (!user) {
      return c.json({
        success: false,
        error: {
          code: 'UNAUTHORIZED',
          message: 'Authentication required',
        },
      }, 401);
    }

    const limit = limits[user.tier] || limits.free;
    const key = `ratelimit:${endpoint}:${user.id}:${getCurrentWindow()}`;

    const countStr = await c.env.CACHE.get(key);
    const count = countStr ? parseInt(countStr) : 0;
    const remaining = Math.max(0, limit - count - 1);
    const allowed = count < limit;

    c.header('X-RateLimit-Limit', limit.toString());
    c.header('X-RateLimit-Remaining', remaining.toString());
    c.header('X-RateLimit-Reset', getResetTime());

    if (!allowed) {
      return c.json({
        success: false,
        error: {
          code: 'ENDPOINT_RATE_LIMIT_EXCEEDED',
          message: `Rate limit exceeded for ${endpoint}`,
          details: {
            endpoint,
            limit,
            reset_at: getResetTime(),
          },
        },
      }, 429);
    }

    // Increment counter
    await c.env.CACHE.put(
      key,
      (count + 1).toString(),
      { expirationTtl: 60 }
    );

    await next();
  };
}

/**
 * Burst protection middleware
 * Prevents rapid-fire requests
 */
export async function burstProtectionMiddleware(
  c: Context<{ Bindings: Env }>,
  next: Next,
  options: { maxBurst?: number; windowMs?: number } = {}
) {
  const user = c.get('user');
  const identifier = user?.id || c.req.header('CF-Connecting-IP') || 'unknown';
  const maxBurst = options.maxBurst || 10;
  const windowMs = options.windowMs || 1000; // 1 second

  const key = `burst:${identifier}:${Math.floor(Date.now() / windowMs)}`;
  const countStr = await c.env.CACHE.get(key);
  const count = countStr ? parseInt(countStr) : 0;

  if (count >= maxBurst) {
    return c.json({
      success: false,
      error: {
        code: 'BURST_LIMIT_EXCEEDED',
        message: 'Too many requests in a short time period',
        details: {
          max_burst: maxBurst,
          window_ms: windowMs,
        },
      },
    }, 429);
  }

  await c.env.CACHE.put(
    key,
    (count + 1).toString(),
    { expirationTtl: Math.ceil(windowMs / 1000) + 1 }
  );

  await next();
}

/**
 * Helper functions
 */
function getCurrentWindow(): string {
  const now = new Date();
  return `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}-${now.getMinutes()}`;
}

function getResetTime(): string {
  const now = new Date();
  const next = new Date(now.getTime() + 60000);
  next.setSeconds(0);
  next.setMilliseconds(0);
  return next.toISOString();
}

/**
 * Rate limit exemption middleware
 * Bypasses rate limits for specific users/IPs
 */
export function rateLimitExemption(exemptList: string[]) {
  return async (c: Context<{ Bindings: Env }>, next: Next) => {
    const user = c.get('user');
    const ip = c.req.header('CF-Connecting-IP') || 'unknown';

    if (
      (user && exemptList.includes(user.id)) ||
      exemptList.includes(ip)
    ) {
      // Skip rate limiting
      await next();
    } else {
      // Continue to rate limiting
      await rateLimitMiddleware(c, next);
    }
  };
}
