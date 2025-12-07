/**
 * CONTINUUM Cloudflare Workers - Sync API Handlers
 * WebSocket-based real-time synchronization
 */

import { Context } from 'hono';
import type { Env, SyncMessage } from '../types';
import { createLogger } from '../middleware/logging';

/**
 * WebSocket upgrade handler
 * GET /api/v1/sync
 */
export async function syncHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  const user = c.get('user');

  if (!user) {
    return c.json({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'Authentication required' },
    }, 401);
  }

  // Check if this is a WebSocket upgrade request
  const upgradeHeader = c.req.header('Upgrade');
  if (upgradeHeader !== 'websocket') {
    return c.json({
      success: false,
      error: {
        code: 'BAD_REQUEST',
        message: 'Expected WebSocket upgrade request',
      },
    }, 400);
  }

  try {
    // Get or create Durable Object for this user's sync session
    const id = c.env.SYNC_SESSIONS.idFromName(user.id);
    const stub = c.env.SYNC_SESSIONS.get(id);

    // Forward the request to the Durable Object
    return stub.fetch(c.req.raw);
  } catch (error) {
    console.error('Sync handler error:', error);
    return c.json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to establish sync connection',
      },
    }, 500);
  }
}

/**
 * Get sync status
 * GET /api/v1/sync/status
 */
export async function syncStatusHandler(c: Context<{ Bindings: Env }>): Promise<Response> {
  const logger = createLogger(c);
  const user = c.get('user');

  if (!user) {
    return c.json({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'Authentication required' },
    }, 401);
  }

  try {
    // TODO: Get active connections count from Durable Object
    const status = {
      user_id: user.id,
      connected: false,
      connections: 0,
      last_sync: null,
    };

    return c.json({
      success: true,
      data: status,
      meta: {
        timestamp: new Date().toISOString(),
        request_id: c.get('requestId'),
      },
    });
  } catch (error) {
    logger.error('Failed to get sync status', error);
    return c.json({
      success: false,
      error: {
        code: 'INTERNAL_ERROR',
        message: 'Failed to retrieve sync status',
      },
    }, 500);
  }
}

/**
 * Durable Object class for WebSocket sessions
 * Handles real-time synchronization between clients
 */
export class SyncSession {
  private state: DurableObjectState;
  private env: Env;
  private sessions: Map<string, WebSocket>;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.env = env;
    this.sessions = new Map();
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // Handle WebSocket upgrade
    if (request.headers.get('Upgrade') === 'websocket') {
      const pair = new WebSocketPair();
      const [client, server] = Object.values(pair);

      // Accept the WebSocket connection
      await this.handleSession(server, request);

      return new Response(null, {
        status: 101,
        webSocket: client,
      });
    }

    // Handle HTTP requests to the Durable Object
    if (url.pathname === '/status') {
      return new Response(JSON.stringify({
        active_sessions: this.sessions.size,
        timestamp: new Date().toISOString(),
      }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    return new Response('Not found', { status: 404 });
  }

  async handleSession(webSocket: WebSocket, request: Request): Promise<void> {
    const sessionId = crypto.randomUUID();
    this.sessions.set(sessionId, webSocket);

    // Accept the WebSocket
    webSocket.accept();

    // Send welcome message
    const welcomeMessage: SyncMessage = {
      type: 'ping',
      timestamp: new Date().toISOString(),
      payload: {
        session_id: sessionId,
        message: 'Connected to CONTINUUM sync',
      },
    };
    webSocket.send(JSON.stringify(welcomeMessage));

    // Set up message handler
    webSocket.addEventListener('message', async (event) => {
      try {
        const message: SyncMessage = JSON.parse(event.data as string);
        await this.handleMessage(sessionId, message);
      } catch (error) {
        console.error('Error handling message:', error);
        webSocket.send(JSON.stringify({
          type: 'error',
          payload: {
            code: 'INVALID_MESSAGE',
            message: 'Failed to process message',
          },
          timestamp: new Date().toISOString(),
        }));
      }
    });

    // Set up close handler
    webSocket.addEventListener('close', () => {
      this.sessions.delete(sessionId);
      console.log(`Session ${sessionId} closed. Active sessions: ${this.sessions.size}`);
    });

    // Set up error handler
    webSocket.addEventListener('error', (error) => {
      console.error(`WebSocket error for session ${sessionId}:`, error);
      this.sessions.delete(sessionId);
    });
  }

  async handleMessage(sessionId: string, message: SyncMessage): Promise<void> {
    const webSocket = this.sessions.get(sessionId);
    if (!webSocket) return;

    switch (message.type) {
      case 'ping':
        // Respond with pong
        webSocket.send(JSON.stringify({
          type: 'pong',
          timestamp: new Date().toISOString(),
        }));
        break;

      case 'memory_created':
      case 'memory_updated':
      case 'memory_deleted':
        // Broadcast to all other sessions
        await this.broadcast(sessionId, message);
        break;

      case 'search_query':
        // Handle search query (could trigger notifications to other clients)
        // For now, just acknowledge
        webSocket.send(JSON.stringify({
          type: 'pong',
          payload: { received: message.type },
          timestamp: new Date().toISOString(),
        }));
        break;

      default:
        webSocket.send(JSON.stringify({
          type: 'error',
          payload: {
            code: 'UNKNOWN_MESSAGE_TYPE',
            message: `Unknown message type: ${message.type}`,
          },
          timestamp: new Date().toISOString(),
        }));
    }
  }

  async broadcast(excludeSessionId: string, message: SyncMessage): Promise<void> {
    const messageStr = JSON.stringify(message);

    for (const [sessionId, webSocket] of this.sessions.entries()) {
      if (sessionId !== excludeSessionId) {
        try {
          webSocket.send(messageStr);
        } catch (error) {
          console.error(`Failed to send to session ${sessionId}:`, error);
          this.sessions.delete(sessionId);
        }
      }
    }
  }

  async alarm(): Promise<void> {
    // Periodic cleanup or heartbeat
    console.log(`Alarm triggered. Active sessions: ${this.sessions.size}`);

    // Send ping to all sessions to check connectivity
    const pingMessage: SyncMessage = {
      type: 'ping',
      timestamp: new Date().toISOString(),
    };

    await this.broadcast('', pingMessage);

    // Schedule next alarm (every 30 seconds)
    await this.state.storage.setAlarm(Date.now() + 30000);
  }
}
