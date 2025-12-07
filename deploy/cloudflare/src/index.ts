/**
 * CONTINUUM Cloudflare Workers - Main Entry Point
 * Edge API for AI Memory Infrastructure
 */

import { Hono } from 'hono';
import type { Env } from './types';

// Middleware
import { corsMiddleware, developmentCORS, productionCORS } from './middleware/cors';
import { authMiddleware, optionalAuthMiddleware } from './middleware/auth';
import { rateLimitMiddleware, ipRateLimitMiddleware, endpointRateLimit, burstProtectionMiddleware } from './middleware/ratelimit';
import { loggingMiddleware, performanceMiddleware } from './middleware/logging';

// Handlers
import {
  healthHandler,
  readinessHandler,
  livenessHandler,
  versionHandler,
  metricsHandler,
} from './handlers/health';
import {
  listMemoriesHandler,
  getMemoryHandler,
  createMemoryHandler,
  updateMemoryHandler,
  deleteMemoryHandler,
} from './handlers/memories';
import {
  searchHandler,
  semanticSearchHandler,
  suggestHandler,
  searchByTagHandler,
} from './handlers/search';
import {
  syncHandler,
  syncStatusHandler,
  SyncSession,
} from './handlers/sync';

// Initialize Hono app
const app = new Hono<{ Bindings: Env }>();

// Global middleware
app.use('*', loggingMiddleware);
app.use('*', performanceMiddleware);

// Environment-specific CORS
app.use('*', async (c, next) => {
  const cors = c.env.ENVIRONMENT === 'production' ? productionCORS : developmentCORS;
  return cors(c, next);
});

// Public routes (no auth required)
app.get('/health', healthHandler);
app.get('/ready', readinessHandler);
app.get('/live', livenessHandler);
app.get('/version', versionHandler);

// API v1 routes with authentication
const api = new Hono<{ Bindings: Env }>();

// Apply IP rate limiting to all API routes
api.use('*', async (c, next) => {
  return ipRateLimitMiddleware(c, next, { limit: 300, window: 60 });
});

// Apply burst protection
api.use('*', burstProtectionMiddleware);

// Auth middleware for protected routes
api.use('/v1/memories/*', authMiddleware);
api.use('/v1/search/*', authMiddleware);
api.use('/v1/sync/*', authMiddleware);

// Rate limiting for authenticated routes
api.use('/v1/memories/*', rateLimitMiddleware);
api.use('/v1/search/*', rateLimitMiddleware);

// Memories endpoints
api.get('/v1/memories', listMemoriesHandler);
api.get('/v1/memories/:id', getMemoryHandler);
api.post('/v1/memories', createMemoryHandler);
api.patch('/v1/memories/:id', updateMemoryHandler);
api.delete('/v1/memories/:id', deleteMemoryHandler);

// Search endpoints
api.post('/v1/search', searchHandler);
api.post('/v1/search/semantic', async (c, next) => {
  // Semantic search has higher rate limits
  return endpointRateLimit('semantic_search', {
    free: 10,
    paid: 100,
    enterprise: 1000,
  })(c, next);
}, semanticSearchHandler);
api.get('/v1/search/suggest', suggestHandler);
api.get('/v1/search/tags/:tag', searchByTagHandler);

// Sync endpoints (WebSocket)
api.get('/v1/sync', syncHandler);
api.get('/v1/sync/status', syncStatusHandler);

// Metrics endpoint (enterprise only)
api.get('/v1/metrics', metricsHandler);

// Mount API routes
app.route('/api', api);

// 404 handler
app.notFound((c) => {
  return c.json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: 'Endpoint not found',
      details: {
        path: c.req.path,
        method: c.req.method,
      },
    },
  }, 404);
});

// Error handler
app.onError((err, c) => {
  console.error('Unhandled error:', err);

  return c.json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: c.env.ENVIRONMENT === 'production'
        ? 'An internal error occurred'
        : err.message,
      details: c.env.ENVIRONMENT === 'development' ? {
        stack: err.stack,
      } : undefined,
    },
    meta: {
      timestamp: new Date().toISOString(),
      request_id: c.get('requestId') || crypto.randomUUID(),
    },
  }, 500);
});

// Export Durable Object class
export { SyncSession };

// Export default worker
export default app;
