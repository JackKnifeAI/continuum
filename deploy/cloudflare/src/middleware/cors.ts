/**
 * CONTINUUM Cloudflare Workers - CORS Middleware
 */

import { Context, Next } from 'hono';
import type { Env } from '../types';

export interface CORSOptions {
  origin?: string | string[] | ((origin: string) => boolean);
  methods?: string[];
  allowedHeaders?: string[];
  exposedHeaders?: string[];
  credentials?: boolean;
  maxAge?: number;
}

const defaultOptions: CORSOptions = {
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID', 'X-API-Key'],
  exposedHeaders: ['X-Request-ID', 'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'],
  credentials: true,
  maxAge: 86400, // 24 hours
};

/**
 * CORS Middleware
 */
export function corsMiddleware(options: CORSOptions = {}) {
  const opts = { ...defaultOptions, ...options };

  return async (c: Context<{ Bindings: Env }>, next: Next) => {
    const origin = c.req.header('Origin');

    // Handle preflight requests
    if (c.req.method === 'OPTIONS') {
      return handlePreflight(c, origin, opts);
    }

    // Set CORS headers for actual requests
    setCORSHeaders(c, origin, opts);

    await next();
  };
}

/**
 * Handle preflight OPTIONS requests
 */
function handlePreflight(
  c: Context,
  origin: string | undefined,
  options: CORSOptions
): Response {
  const headers = new Headers();

  // Set allowed origin
  const allowedOrigin = getAllowedOrigin(origin, options.origin);
  if (allowedOrigin) {
    headers.set('Access-Control-Allow-Origin', allowedOrigin);
  }

  // Set allowed methods
  if (options.methods) {
    headers.set('Access-Control-Allow-Methods', options.methods.join(', '));
  }

  // Set allowed headers
  if (options.allowedHeaders) {
    headers.set('Access-Control-Allow-Headers', options.allowedHeaders.join(', '));
  }

  // Set credentials
  if (options.credentials) {
    headers.set('Access-Control-Allow-Credentials', 'true');
  }

  // Set max age
  if (options.maxAge) {
    headers.set('Access-Control-Max-Age', options.maxAge.toString());
  }

  return new Response(null, {
    status: 204,
    headers,
  });
}

/**
 * Set CORS headers on response
 */
function setCORSHeaders(
  c: Context,
  origin: string | undefined,
  options: CORSOptions
): void {
  // Set allowed origin
  const allowedOrigin = getAllowedOrigin(origin, options.origin);
  if (allowedOrigin) {
    c.header('Access-Control-Allow-Origin', allowedOrigin);
  }

  // Set exposed headers
  if (options.exposedHeaders) {
    c.header('Access-Control-Expose-Headers', options.exposedHeaders.join(', '));
  }

  // Set credentials
  if (options.credentials) {
    c.header('Access-Control-Allow-Credentials', 'true');
  }

  // Vary header for caching
  c.header('Vary', 'Origin');
}

/**
 * Determine allowed origin
 */
function getAllowedOrigin(
  requestOrigin: string | undefined,
  allowedOrigin: string | string[] | ((origin: string) => boolean) | undefined
): string | null {
  if (!requestOrigin) {
    return null;
  }

  // Allow all origins
  if (allowedOrigin === '*') {
    return '*';
  }

  // String array
  if (Array.isArray(allowedOrigin)) {
    return allowedOrigin.includes(requestOrigin) ? requestOrigin : null;
  }

  // Function
  if (typeof allowedOrigin === 'function') {
    return allowedOrigin(requestOrigin) ? requestOrigin : null;
  }

  // String
  if (typeof allowedOrigin === 'string') {
    return allowedOrigin === requestOrigin ? requestOrigin : null;
  }

  return null;
}

/**
 * Production CORS configuration
 * Only allow specific domains
 */
export const productionCORS = corsMiddleware({
  origin: [
    'https://continuum.ai',
    'https://app.continuum.ai',
    'https://dashboard.continuum.ai',
  ],
  credentials: true,
});

/**
 * Development CORS configuration
 * Allow localhost and development domains
 */
export const developmentCORS = corsMiddleware({
  origin: (origin: string) => {
    return (
      origin.startsWith('http://localhost') ||
      origin.startsWith('https://localhost') ||
      origin.endsWith('.continuum.ai') ||
      origin.endsWith('.vercel.app') ||
      origin.endsWith('.netlify.app')
    );
  },
  credentials: true,
});

/**
 * Permissive CORS for testing
 */
export const testingCORS = corsMiddleware({
  origin: '*',
  credentials: false,
});
