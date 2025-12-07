/**
 * CONTINUUM Cloudflare Workers - JWT Authentication Middleware
 */

import { Context, Next } from 'hono';
import * as jose from 'jose';
import type { Env, JWTPayload } from '../types';

/**
 * JWT Authentication Middleware
 * Validates JWT tokens and attaches user context to request
 */
export async function authMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const authHeader = c.req.header('Authorization');

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return c.json({
      success: false,
      error: {
        code: 'UNAUTHORIZED',
        message: 'Missing or invalid authorization header',
      },
    }, 401);
  }

  const token = authHeader.substring(7); // Remove 'Bearer ' prefix

  try {
    const secret = new TextEncoder().encode(c.env.JWT_SECRET);

    // Verify JWT
    const { payload } = await jose.jwtVerify(token, secret, {
      algorithms: ['HS256'],
    });

    // Validate payload structure
    if (!payload.sub || typeof payload.sub !== 'string') {
      throw new Error('Invalid token payload: missing subject');
    }

    // Attach user context to request
    c.set('user', {
      id: payload.sub,
      email: payload.email as string | undefined,
      tier: (payload.tier as 'free' | 'paid' | 'enterprise') || 'free',
    });

    await next();
  } catch (error) {
    console.error('JWT verification failed:', error);

    return c.json({
      success: false,
      error: {
        code: 'INVALID_TOKEN',
        message: error instanceof Error ? error.message : 'Token verification failed',
      },
    }, 401);
  }
}

/**
 * Optional authentication middleware
 * Allows requests to proceed even without valid token
 */
export async function optionalAuthMiddleware(c: Context<{ Bindings: Env }>, next: Next) {
  const authHeader = c.req.header('Authorization');

  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);

    try {
      const secret = new TextEncoder().encode(c.env.JWT_SECRET);
      const { payload } = await jose.jwtVerify(token, secret, {
        algorithms: ['HS256'],
      });

      if (payload.sub && typeof payload.sub === 'string') {
        c.set('user', {
          id: payload.sub,
          email: payload.email as string | undefined,
          tier: (payload.tier as 'free' | 'paid' | 'enterprise') || 'free',
        });
      }
    } catch (error) {
      // Log error but continue
      console.warn('Optional auth failed:', error);
    }
  }

  await next();
}

/**
 * Generate JWT token
 */
export async function generateToken(
  userId: string,
  email: string,
  tier: 'free' | 'paid' | 'enterprise',
  secret: string,
  expiresIn: string = '7d'
): Promise<string> {
  const secretKey = new TextEncoder().encode(secret);

  const token = await new jose.SignJWT({
    email,
    tier,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setSubject(userId)
    .setIssuedAt()
    .setExpirationTime(expiresIn)
    .sign(secretKey);

  return token;
}

/**
 * Verify and decode token without middleware
 */
export async function verifyToken(
  token: string,
  secret: string
): Promise<JWTPayload | null> {
  try {
    const secretKey = new TextEncoder().encode(secret);
    const { payload } = await jose.jwtVerify(token, secretKey, {
      algorithms: ['HS256'],
    });

    return {
      sub: payload.sub as string,
      email: payload.email as string | undefined,
      tier: (payload.tier as 'free' | 'paid' | 'enterprise') || 'free',
      iat: payload.iat as number,
      exp: payload.exp as number,
    };
  } catch (error) {
    console.error('Token verification failed:', error);
    return null;
  }
}

/**
 * Refresh token
 */
export async function refreshToken(
  oldToken: string,
  secret: string
): Promise<string | null> {
  const payload = await verifyToken(oldToken, secret);

  if (!payload) {
    return null;
  }

  return generateToken(
    payload.sub,
    payload.email || '',
    payload.tier,
    secret,
    '7d'
  );
}
