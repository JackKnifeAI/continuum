# CONTINUUM - Cloudflare Workers Edge API

Global edge deployment of the CONTINUUM AI Memory Infrastructure API using Cloudflare Workers.

## Features

- **Global Edge Network**: Deploy to 300+ cities worldwide for ultra-low latency
- **JWT Authentication**: Secure token-based authentication
- **Tier-based Rate Limiting**: 100 req/min (free), 1000 req/min (paid), 10K req/min (enterprise)
- **KV Caching**: Fast distributed caching with Cloudflare KV
- **WebSocket Sync**: Real-time synchronization using Durable Objects
- **CORS Support**: Configurable cross-origin resource sharing
- **TypeScript**: Full type safety with TypeScript
- **Request Logging**: Structured logging with request IDs
- **Health Checks**: /health, /ready, /live endpoints for monitoring

## Architecture

```
┌─────────────────┐
│  Global CDN     │
│  (Cloudflare)   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Worker  │  (Your API code)
    └────┬────┘
         │
    ┌────┴────────────────────┐
    │                         │
┌───▼──────┐         ┌────▼────────┐
│ KV Store │         │   Durable   │
│ (Cache)  │         │   Objects   │
└──────────┘         │ (WebSocket) │
                     └─────────────┘
```

## Prerequisites

- Node.js 18+ and npm
- Cloudflare account (free tier works)
- Wrangler CLI: `npm install -g wrangler`
- Authenticated with Cloudflare: `wrangler login`

## Quick Start

### 1. Install Dependencies

```bash
cd deploy/cloudflare
npm install
```

### 2. Create KV Namespaces

```bash
# Create production KV namespaces
wrangler kv:namespace create CACHE
wrangler kv:namespace create SESSIONS

# Create preview KV namespaces (for development)
wrangler kv:namespace create CACHE --preview
wrangler kv:namespace create SESSIONS --preview
```

Copy the namespace IDs from the output and update `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "YOUR_CACHE_KV_ID"
preview_id = "YOUR_CACHE_PREVIEW_KV_ID"

[[kv_namespaces]]
binding = "SESSIONS"
id = "YOUR_SESSION_KV_ID"
preview_id = "YOUR_SESSION_PREVIEW_KV_ID"
```

### 3. Set Secrets

```bash
# Generate a secure JWT secret
openssl rand -base64 32

# Set the secret in Cloudflare
wrangler secret put JWT_SECRET

# Optional: Set database URL
wrangler secret put DATABASE_URL

# Optional: Set Supabase credentials
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_ANON_KEY
```

### 4. Configure Development Environment

```bash
# Copy example env file
cp .dev.vars.example .dev.vars

# Edit .dev.vars with your local secrets
nano .dev.vars
```

### 5. Local Development

```bash
# Start local development server
npm run dev

# The API will be available at http://localhost:8787
```

### 6. Deploy

```bash
# Deploy to development environment
npm run deploy:dev

# Deploy to staging
npm run deploy:staging

# Deploy to production
npm run deploy:prod
```

## API Endpoints

### Health & Status

- `GET /health` - Health check with service status
- `GET /ready` - Readiness probe
- `GET /live` - Liveness probe
- `GET /version` - API version info

### Memories (Authentication Required)

- `GET /api/v1/memories` - List memories
  - Query params: `limit`, `offset`, `tags`
- `GET /api/v1/memories/:id` - Get memory by ID
- `POST /api/v1/memories` - Create memory
- `PATCH /api/v1/memories/:id` - Update memory
- `DELETE /api/v1/memories/:id` - Delete memory

### Search (Authentication Required)

- `POST /api/v1/search` - Full-text search
- `POST /api/v1/search/semantic` - Semantic search (paid tier)
- `GET /api/v1/search/suggest?q=query` - Search suggestions
- `GET /api/v1/search/tags/:tag` - Search by tag

### Sync (Authentication Required)

- `GET /api/v1/sync` - WebSocket connection for real-time sync
- `GET /api/v1/sync/status` - Sync status

### Metrics (Enterprise Only)

- `GET /api/v1/metrics` - API metrics

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://your-worker.workers.dev/api/v1/memories
```

### JWT Payload Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "tier": "free|paid|enterprise",
  "iat": 1234567890,
  "exp": 1234567890
}
```

## Rate Limiting

Rate limits are enforced per user based on their tier:

| Tier       | Requests/Minute | Semantic Search |
|------------|-----------------|-----------------|
| Free       | 100             | Not available   |
| Paid       | 1,000           | 10/min          |
| Enterprise | 10,000          | 1,000/min       |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: When the limit resets (ISO 8601)

## WebSocket Sync

Connect to real-time sync via WebSocket:

```javascript
const ws = new WebSocket('wss://your-worker.workers.dev/api/v1/sync', {
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN'
  }
});

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Sync message:', message);
};

// Send messages
ws.send(JSON.stringify({
  type: 'memory_created',
  payload: { /* ... */ },
  timestamp: new Date().toISOString()
}));
```

### Message Types

- `ping` / `pong` - Heartbeat
- `memory_created` - New memory added
- `memory_updated` - Memory modified
- `memory_deleted` - Memory removed
- `search_query` - Search performed

## CORS Configuration

CORS is automatically configured based on environment:

**Production**: Only specific domains allowed
```typescript
origin: [
  'https://continuum.ai',
  'https://app.continuum.ai',
  'https://dashboard.continuum.ai',
]
```

**Development**: Localhost and preview domains
```typescript
origin: (origin) => {
  return origin.startsWith('http://localhost') ||
         origin.endsWith('.continuum.ai') ||
         origin.endsWith('.vercel.app');
}
```

## Caching Strategy

- **Memories List**: 5 minutes
- **Individual Memory**: 1 hour
- **Search Results**: 5 minutes
- **Tag Searches**: 10 minutes
- **Suggestions**: 1 hour

Cache is automatically invalidated on:
- Memory creation
- Memory updates
- Memory deletion

## Error Handling

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* optional additional context */ }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00.000Z",
    "request_id": "uuid-here"
  }
}
```

### Common Error Codes

- `UNAUTHORIZED` - Missing or invalid authentication
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Invalid request data
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INTERNAL_ERROR` - Server error

## Monitoring

### Cloudflare Dashboard

- Workers Analytics: Real-time request metrics
- Logs: `wrangler tail` for live logs
- Alarms: Configure alerts for errors/latency

### Log Streaming

```bash
# Stream live logs
wrangler tail

# Filter by status
wrangler tail --status error

# Filter by method
wrangler tail --method POST
```

### Custom Metrics

Request timing headers are included:

```
Server-Timing: db;dur=10, cache;dur=5, processing;dur=15, total;dur=30
```

## Development

### Project Structure

```
src/
├── index.ts              # Main entry point & routing
├── types.ts              # TypeScript type definitions
├── kv.ts                 # KV storage utilities
├── middleware/
│   ├── auth.ts          # JWT authentication
│   ├── cors.ts          # CORS configuration
│   ├── ratelimit.ts     # Rate limiting
│   └── logging.ts       # Request logging
└── handlers/
    ├── health.ts        # Health check endpoints
    ├── memories.ts      # Memory CRUD operations
    ├── search.ts        # Search endpoints
    └── sync.ts          # WebSocket sync + Durable Object
```

### Adding New Endpoints

1. Create handler in `src/handlers/`
2. Add route in `src/index.ts`
3. Apply appropriate middleware
4. Update this README

### Testing Locally

```bash
# Run development server
npm run dev

# Test health endpoint
curl http://localhost:8787/health

# Test with authentication (after generating token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8787/api/v1/memories
```

## Environment Variables

Set via `wrangler secret put` for production or `.dev.vars` for local:

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | Secret key for JWT signing/verification |
| `DATABASE_URL` | No | External database connection string |
| `SUPABASE_URL` | No | Supabase project URL |
| `SUPABASE_ANON_KEY` | No | Supabase anonymous key |
| `ENVIRONMENT` | No | Environment name (auto-set by wrangler) |
| `API_VERSION` | No | API version (default: v1) |
| `LOG_LEVEL` | No | Logging level (debug/info/warn/error) |

## Custom Domains

Add custom domain in `wrangler.toml`:

```toml
[[routes]]
pattern = "api.continuum.ai/*"
zone_name = "continuum.ai"
```

Then deploy:

```bash
wrangler deploy
```

## Performance

- **Cold Start**: ~5ms (V8 isolates, not containers)
- **Execution Time**: Typically < 50ms
- **Global Latency**: < 50ms to nearest POP
- **Throughput**: 10M+ requests/day on free tier

## Cost Estimation

Cloudflare Workers free tier includes:
- 100,000 requests/day
- 10ms CPU time/request
- KV: 100,000 reads/day, 1,000 writes/day

Paid ($5/month):
- 10M requests/month
- 50ms CPU time/request
- KV: 10M reads/month, 1M writes/month

## Troubleshooting

### Issue: "Durable Object binding not found"

Make sure `wrangler.toml` includes:

```toml
[[durable_objects.bindings]]
name = "SYNC_SESSIONS"
class_name = "SyncSession"
script_name = "continuum-api"
```

### Issue: "KV namespace not found"

Create KV namespaces and update IDs in `wrangler.toml`:

```bash
wrangler kv:namespace create CACHE
wrangler kv:namespace create SESSIONS
```

### Issue: "JWT_SECRET not set"

Set the secret:

```bash
wrangler secret put JWT_SECRET
```

### Issue: CORS errors

Check `ENVIRONMENT` variable matches your deployment and update allowed origins in `src/middleware/cors.ts`.

## Security

- All secrets stored in Cloudflare's encrypted secret storage
- JWT tokens signed with HS256 algorithm
- Rate limiting on all endpoints
- Burst protection (max 10 requests/second)
- IP-based rate limiting for unauthenticated endpoints
- CORS configured for specific origins in production

## License

MIT License - See main CONTINUUM repository

## Support

- Documentation: https://docs.continuum.ai
- Issues: https://github.com/continuum/continuum/issues
- Discord: https://discord.gg/continuum

---

Built with Cloudflare Workers, Hono, and TypeScript for global edge deployment.
