# CONTINUUM Cloudflare Workers - Quick Start Guide

Get your edge API running in under 5 minutes.

## Prerequisites

```bash
# Install Node.js 18+ (if not already installed)
node --version  # Should be >= 18.0.0

# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

## 1. Automated Setup

```bash
cd deploy/cloudflare

# Run setup script (creates KV namespaces, generates secrets)
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## 2. Update Configuration

After setup script runs, update `wrangler.toml` with the KV namespace IDs:

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "abc123..."  # From setup output
preview_id = "xyz789..."

[[kv_namespaces]]
binding = "SESSIONS"
id = "def456..."  # From setup output
preview_id = "uvw101..."
```

## 3. Set Production Secrets

```bash
# JWT secret (use the one from setup.sh output)
echo "YOUR_GENERATED_SECRET" | wrangler secret put JWT_SECRET

# Optional: Database URL
# echo "postgresql://..." | wrangler secret put DATABASE_URL

# Optional: Supabase
# echo "https://xyz.supabase.co" | wrangler secret put SUPABASE_URL
# echo "anon_key" | wrangler secret put SUPABASE_ANON_KEY
```

## 4. Test Locally

```bash
# Start development server
npm run dev

# In another terminal, test the API
curl http://localhost:8787/health
```

## 5. Deploy to Production

```bash
# Deploy to production
npm run deploy:prod

# Your API is now live at:
# https://continuum-api-prod.YOUR_ACCOUNT.workers.dev
```

## 6. Test Production Deployment

```bash
# Set your worker URL
export API_URL="https://continuum-api-prod.YOUR_ACCOUNT.workers.dev"

# Health check
curl $API_URL/health

# Version info
curl $API_URL/version
```

## Generate JWT Token (for testing)

```bash
# Install jose CLI (if needed)
npm install -g jose-cli

# Generate token
# Note: Replace USER_ID and YOUR_SECRET with actual values
node -e "
const jose = require('jose');
const secret = new TextEncoder().encode('YOUR_JWT_SECRET');

(async () => {
  const token = await new jose.SignJWT({ email: 'test@example.com', tier: 'paid' })
    .setProtectedHeader({ alg: 'HS256' })
    .setSubject('user123')
    .setIssuedAt()
    .setExpirationTime('7d')
    .sign(secret);
  console.log('JWT Token:', token);
})();
"
```

Or use the example client:

```typescript
import { generateToken } from './src/middleware/auth';

const token = await generateToken(
  'user123',           // user ID
  'test@example.com',  // email
  'paid',              // tier
  'YOUR_JWT_SECRET',   // secret
  '7d'                 // expires in 7 days
);

console.log('Token:', token);
```

## Test Authenticated Endpoints

```bash
export TOKEN="your-jwt-token-here"

# List memories
curl -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/memories?limit=10"

# Create memory
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "My first memory",
    "tags": ["test"],
    "metadata": {"source": "quickstart"}
  }' \
  "$API_URL/api/v1/memories"

# Search
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "first", "limit": 5}' \
  "$API_URL/api/v1/search"
```

## Use TypeScript Client

```typescript
import { ContinuumClient } from './examples/client';

const client = new ContinuumClient({
  apiUrl: 'https://continuum-api-prod.YOUR_ACCOUNT.workers.dev',
  token: 'your-jwt-token',
});

// Health check
const health = await client.healthCheck();
console.log('Status:', health.status);

// Create memory
const memory = await client.createMemory({
  content: 'Testing CONTINUUM API',
  tags: ['test'],
});
console.log('Created:', memory);

// List memories
const { memories } = await client.listMemories({ limit: 10 });
console.log('Total memories:', memories.length);

// Search
const results = await client.search({ query: 'test', limit: 5 });
console.log('Found:', results.total, 'results');
```

## WebSocket Real-time Sync

```javascript
const ws = new WebSocket(
  'wss://continuum-api-prod.YOUR_ACCOUNT.workers.dev/api/v1/sync',
  {
    headers: {
      'Authorization': 'Bearer YOUR_TOKEN'
    }
  }
);

ws.onopen = () => {
  console.log('Connected to sync');
  ws.send(JSON.stringify({
    type: 'ping',
    timestamp: new Date().toISOString()
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

## Common Commands

```bash
# Development
npm run dev              # Start local server
npm run build            # Build TypeScript
npm run type-check       # Check types
npm run lint             # Lint code
npm run format           # Format code

# Deployment
npm run deploy:dev       # Deploy to development
npm run deploy:staging   # Deploy to staging
npm run deploy:prod      # Deploy to production

# Logs
npm run tail             # Stream live logs
wrangler tail --status error  # Only errors

# KV Management
npm run kv:create        # Create KV namespaces
npm run kv:list          # List KV namespaces
wrangler kv:key list --namespace-id=YOUR_ID  # List keys

# Secrets
npm run secret:put       # Interactive secret setting
wrangler secret list     # List secrets (not values)
wrangler secret delete SECRET_NAME  # Delete secret
```

## Monitoring

### View Metrics in Cloudflare Dashboard
1. Go to Workers & Pages
2. Click your worker
3. View Analytics tab for:
   - Request volume
   - Success/error rates
   - CPU time usage
   - Invocation duration

### Live Log Streaming
```bash
# All logs
wrangler tail

# Errors only
wrangler tail --status error

# Specific method
wrangler tail --method POST

# Format as JSON
wrangler tail --format json
```

## Troubleshooting

### "namespace not found"
```bash
# Create namespaces
wrangler kv:namespace create CACHE
wrangler kv:namespace create SESSIONS
# Update wrangler.toml with IDs
```

### "JWT_SECRET not set"
```bash
# Generate and set secret
openssl rand -base64 32 | wrangler secret put JWT_SECRET
```

### "Unauthorized" errors
```bash
# Check token is valid
# Token must be in format: Bearer YOUR_JWT_TOKEN
# Verify JWT_SECRET matches between generation and verification
```

### CORS errors
```bash
# Check ENVIRONMENT variable
# Update allowed origins in src/middleware/cors.ts
# Redeploy after changes
```

## Next Steps

1. **Custom Domain**: Add your domain in Cloudflare dashboard
2. **Database**: Connect to Supabase or PostgreSQL
3. **Analytics**: Set up monitoring and alerts
4. **CI/CD**: Automate deployment with GitHub Actions
5. **Testing**: Add tests with Vitest

## Support

- **Documentation**: See full README.md
- **Examples**: Check examples/ directory
- **Issues**: Report at GitHub
- **Logs**: Use `wrangler tail` for debugging

---

**You're ready to build!** The edge API is deployed and responding globally with < 50ms latency.
