/**
 * CONTINUUM Cloudflare Workers - Validation Utilities
 */

import { z } from 'zod';

/**
 * UUID validation
 */
export const uuidSchema = z.string().uuid();

/**
 * Validate UUID
 */
export function isValidUUID(value: string): boolean {
  return uuidSchema.safeParse(value).success;
}

/**
 * Email validation
 */
export const emailSchema = z.string().email();

/**
 * Validate email
 */
export function isValidEmail(value: string): boolean {
  return emailSchema.safeParse(value).success;
}

/**
 * Tier validation
 */
export const tierSchema = z.enum(['free', 'paid', 'enterprise']);

/**
 * Pagination schema
 */
export const paginationSchema = z.object({
  limit: z.number().min(1).max(100).default(20),
  offset: z.number().min(0).default(0),
});

/**
 * Date range schema
 */
export const dateRangeSchema = z.object({
  start: z.string().datetime().optional(),
  end: z.string().datetime().optional(),
});

/**
 * Validate pagination params
 */
export function validatePagination(params: {
  limit?: string | number;
  offset?: string | number;
}): { limit: number; offset: number } {
  return paginationSchema.parse({
    limit: typeof params.limit === 'string' ? parseInt(params.limit) : params.limit,
    offset: typeof params.offset === 'string' ? parseInt(params.offset) : params.offset,
  });
}

/**
 * Sanitize string input
 */
export function sanitizeString(input: string, maxLength: number = 1000): string {
  return input.trim().slice(0, maxLength);
}

/**
 * Validate JWT token format
 */
export function isValidJWTFormat(token: string): boolean {
  const parts = token.split('.');
  return parts.length === 3 && parts.every(part => part.length > 0);
}
