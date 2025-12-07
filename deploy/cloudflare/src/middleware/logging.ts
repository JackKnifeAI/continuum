/**
 * CONTINUUM Cloudflare Workers - Logging Middleware
 */

import { Context, Next } from 'hono';
import type { Env } from '../types';

export interface LogEntry {
  timestamp: string;
  request_id: string;
  method: string;
  path: string;
  status: number;
  duration_ms: number;
  user_id?: string;
  ip?: string;
  user_agent?: string;
  error?: string;
}

/**
 * Request logging middleware
 */
export async function loggingMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const startTime = Date.now();
  const requestId = crypto.randomUUID();

  // Attach request ID to context
  c.set('requestId', requestId);

  // Add request ID to response headers
  c.header('X-Request-ID', requestId);

  try {
    await next();
  } finally {
    const duration = Date.now() - startTime;
    const user = c.get('user');

    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      request_id: requestId,
      method: c.req.method,
      path: c.req.path,
      status: c.res.status,
      duration_ms: duration,
      user_id: user?.id,
      ip: c.req.header('CF-Connecting-IP') || c.req.header('X-Real-IP'),
      user_agent: c.req.header('User-Agent'),
    };

    // Log based on environment and status
    if (c.env.LOG_LEVEL === 'debug' || c.res.status >= 400) {
      console.log(JSON.stringify(logEntry));
    }

    // For errors, log more details
    if (c.res.status >= 500) {
      console.error(`[ERROR] ${requestId}: ${c.req.method} ${c.req.path} - ${c.res.status}`);
    }
  }
}

/**
 * Performance monitoring middleware
 */
export async function performanceMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const metrics = {
    request_start: Date.now(),
    db_time: 0,
    cache_time: 0,
    processing_time: 0,
  };

  c.set('metrics', metrics);

  await next();

  const totalTime = Date.now() - metrics.request_start;

  // Add performance headers
  c.header('Server-Timing', [
    `db;dur=${metrics.db_time}`,
    `cache;dur=${metrics.cache_time}`,
    `processing;dur=${metrics.processing_time}`,
    `total;dur=${totalTime}`,
  ].join(', '));
}

/**
 * Error logging helper
 */
export function logError(
  error: Error,
  context: {
    requestId: string;
    userId?: string;
    path: string;
    method: string;
  }
): void {
  console.error({
    timestamp: new Date().toISOString(),
    level: 'error',
    request_id: context.requestId,
    user_id: context.userId,
    path: context.path,
    method: context.method,
    error: {
      name: error.name,
      message: error.message,
      stack: error.stack,
    },
  });
}

/**
 * Structured logging helper
 */
export class Logger {
  private context: {
    requestId?: string;
    userId?: string;
    environment?: string;
  };

  constructor(context: { requestId?: string; userId?: string; environment?: string } = {}) {
    this.context = context;
  }

  private log(level: 'debug' | 'info' | 'warn' | 'error', message: string, data?: unknown) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...this.context,
      ...(data && { data }),
    };

    console.log(JSON.stringify(logEntry));
  }

  debug(message: string, data?: unknown) {
    this.log('debug', message, data);
  }

  info(message: string, data?: unknown) {
    this.log('info', message, data);
  }

  warn(message: string, data?: unknown) {
    this.log('warn', message, data);
  }

  error(message: string, error?: Error | unknown) {
    const errorData = error instanceof Error
      ? {
          name: error.name,
          message: error.message,
          stack: error.stack,
        }
      : error;

    this.log('error', message, errorData);
  }
}

/**
 * Create logger from context
 */
export function createLogger(c: Context<{ Bindings: Env }>): Logger {
  const user = c.get('user');
  return new Logger({
    requestId: c.get('requestId'),
    userId: user?.id,
    environment: c.env.ENVIRONMENT,
  });
}
