/**
 * CONTINUUM Cloudflare Workers - Error Utilities
 */

export class APIError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode: number = 500,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class ValidationError extends APIError {
  constructor(message: string, details?: unknown) {
    super('VALIDATION_ERROR', message, 400, details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication required') {
    super('UNAUTHORIZED', message, 401);
    this.name = 'AuthenticationError';
  }
}

export class ForbiddenError extends APIError {
  constructor(message: string = 'Access denied') {
    super('FORBIDDEN', message, 403);
    this.name = 'ForbiddenError';
  }
}

export class NotFoundError extends APIError {
  constructor(message: string = 'Resource not found') {
    super('NOT_FOUND', message, 404);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends APIError {
  constructor(resetAt: string, limit: number) {
    super(
      'RATE_LIMIT_EXCEEDED',
      `Rate limit exceeded. Resets at ${resetAt}`,
      429,
      { reset_at: resetAt, limit }
    );
    this.name = 'RateLimitError';
  }
}

export class InternalError extends APIError {
  constructor(message: string = 'Internal server error', details?: unknown) {
    super('INTERNAL_ERROR', message, 500, details);
    this.name = 'InternalError';
  }
}
