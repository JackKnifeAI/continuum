# CONTINUUM API - Quick Start Guide

**Server Status:** ✅ OPERATIONAL
**Port:** 8420
**Location:** `/var/home/alexandergcasavant/Projects/continuum`

---

## Start Server (Choose One)

```bash
# Method 1: Python module
python3 -m continuum.api.server

# Method 2: Uvicorn directly
uvicorn continuum.api.server:app --reload --port 8420

# Method 3: Background
nohup python3 -m continuum.api.server > server.log 2>&1 &
```

Server URL: **http://localhost:8420**

---

## Quick Access

| Resource | URL |
|----------|-----|
| **API Docs** | http://localhost:8420/docs |
| **ReDoc** | http://localhost:8420/redoc |
| **Health Check** | http://localhost:8420/v1/health |
| **API Info** | http://localhost:8420/ |

---

## Step-by-Step Usage

### 1. Create API Key
```bash
curl -X POST http://localhost:8420/v1/keys \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "my_app",
    "name": "Development Key"
  }'
```

**Save the returned API key!** You'll need it for all authenticated requests.

---

### 2. Query Memory (Recall)

```bash
export API_KEY="cm_your_key_from_step_1"

curl -X POST http://localhost:8420/v1/recall \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "message": "What did we discuss about AI?",
    "max_concepts": 10
  }'
```

**Response:**
```json
{
  "context": "Relevant context string...",
  "concepts_found": 5,
  "relationships_found": 12,
  "query_time_ms": 15.3,
  "tenant_id": "my_app"
}
```

---

### 3. Store Learning

```bash
curl -X POST http://localhost:8420/v1/learn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "user_message": "Tell me about quantum computing",
    "ai_response": "Quantum computing uses quantum mechanics...",
    "metadata": {
      "session_id": "sess_123",
      "timestamp": "2025-12-07T10:00:00Z"
    }
  }'
```

**Response:**
```json
{
  "concepts_extracted": 3,
  "decisions_detected": 0,
  "links_created": 5,
  "compounds_found": 2,
  "tenant_id": "my_app"
}
```

---

### 4. Get Statistics

```bash
curl -H "X-API-Key: $API_KEY" \
     http://localhost:8420/v1/stats
```

**Response:**
```json
{
  "tenant_id": "my_app",
  "instance_id": "instance-1",
  "entities": 100,
  "messages": 50,
  "decisions": 10,
  "attention_links": 200,
  "compound_concepts": 30
}
```

---

### 5. List Entities

```bash
# List first 10 entities
curl -H "X-API-Key: $API_KEY" \
     "http://localhost:8420/v1/entities?limit=10"

# Filter by type
curl -H "X-API-Key: $API_KEY" \
     "http://localhost:8420/v1/entities?limit=10&entity_type=concept"
```

**Valid entity types:** concept, decision, session, person, project, tool, topic

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8420"
API_KEY = "cm_your_api_key_here"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Recall memory
recall_response = requests.post(
    f"{BASE_URL}/v1/recall",
    headers=headers,
    json={
        "message": "What did we discuss?",
        "max_concepts": 10
    }
)
context = recall_response.json()["context"]

# Learn from exchange
learn_response = requests.post(
    f"{BASE_URL}/v1/learn",
    headers=headers,
    json={
        "user_message": "Tell me about X",
        "ai_response": "X is a...",
        "metadata": {"session_id": "abc123"}
    }
)
print(f"Extracted {learn_response.json()['concepts_extracted']} concepts")

# Get stats
stats_response = requests.get(
    f"{BASE_URL}/v1/stats",
    headers=headers
)
print(f"Total entities: {stats_response.json()['entities']}")
```

---

## Common Workflows

### Workflow 1: AI Chat with Memory

```python
# 1. User sends message
user_message = "Tell me about quantum computing"

# 2. Recall relevant context
recall = requests.post(f"{BASE_URL}/v1/recall",
    headers=headers,
    json={"message": user_message, "max_concepts": 10}
).json()

# 3. Inject context into AI prompt
prompt = f"{recall['context']}\n\nUser: {user_message}\nAI:"

# 4. Generate AI response (your AI logic here)
ai_response = generate_ai_response(prompt)

# 5. Store the learning
learn = requests.post(f"{BASE_URL}/v1/learn",
    headers=headers,
    json={
        "user_message": user_message,
        "ai_response": ai_response,
        "metadata": {"session_id": "chat_123"}
    }
).json()

print(f"Learned {learn['concepts_extracted']} new concepts")
```

### Workflow 2: Batch Processing

```python
# Use the /turn endpoint for batch processing
conversations = [
    {"user": "What is AI?", "ai": "AI is..."},
    {"user": "Explain ML", "ai": "ML is..."},
]

for conv in conversations:
    response = requests.post(f"{BASE_URL}/v1/turn",
        headers=headers,
        json={
            "user_message": conv["user"],
            "ai_response": conv["ai"],
            "max_concepts": 10,
            "metadata": {"batch_id": "import_001"}
        }
    ).json()

    print(f"Processed: {response['learn']['concepts_extracted']} concepts")
```

---

## WebSocket Real-Time Sync

```python
import websockets
import json
import asyncio

async def sync_client():
    uri = "ws://localhost:8420/ws/sync?tenant_id=my_app&instance_id=client_1"

    async with websockets.connect(uri) as websocket:
        # Send sync request
        await websocket.send(json.dumps({
            "event_type": "sync_request",
            "tenant_id": "my_app",
            "instance_id": "client_1"
        }))

        # Receive messages
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Event: {data['event_type']}")

            if data['event_type'] == 'memory_added':
                print(f"New memory: {data['data']}")

asyncio.run(sync_client())
```

---

## Testing

### Run Automated Tests
```bash
python3 test_api_endpoints.py
```

### Manual Health Check
```bash
curl http://localhost:8420/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "continuum",
  "version": "0.1.0",
  "timestamp": "2025-12-07T..."
}
```

---

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :8420

# Kill existing process
pkill -f "continuum.api.server"

# Try starting again
python3 -m continuum.api.server
```

### Import errors
```bash
# Ensure you're in the project directory
cd /var/home/alexandergcasavant/Projects/continuum

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Verify continuum module is accessible
python3 -c "from continuum.api.server import app; print('OK')"
```

### API key issues
```bash
# Check API keys database
sqlite3 ~/.continuum/api_keys.db "SELECT tenant_id, name, created_at FROM api_keys;"

# Create new key
curl -X POST http://localhost:8420/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "test", "name": "Debug Key"}'
```

---

## Environment Configuration

### Development (Default)
```bash
# No configuration needed
python3 -m continuum.api.server
```

### Custom Configuration
```bash
# Set environment variables
export CONTINUUM_ENV=production
export CONTINUUM_CORS_ORIGINS=https://myapp.com,https://app.myapp.com
export SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Start server
python3 -m continuum.api.server
```

### With Stripe Billing
```bash
export STRIPE_SECRET_KEY=sk_test_your_key_here
export STRIPE_WEBHOOK_SECRET=whsec_your_secret_here

python3 -m continuum.api.server
```

---

## File Locations

| File | Path |
|------|------|
| **Server Code** | `/var/home/alexandergcasavant/Projects/continuum/continuum/api/server.py` |
| **API Keys DB** | `~/.continuum/api_keys.db` |
| **Memory DB** | `~/.continuum/memory/{tenant_id}/memory.db` |
| **Test Script** | `/var/home/alexandergcasavant/Projects/continuum/test_api_endpoints.py` |
| **Full Docs** | `/var/home/alexandergcasavant/Projects/continuum/API_DEBUG_REPORT.md` |

---

## Quick Reference

### All Endpoints

```
GET  /                         - API information
GET  /v1/health                - Health check
POST /v1/recall                - Query memory
POST /v1/learn                 - Store learning
POST /v1/turn                  - Recall + Learn combined
GET  /v1/stats                 - Statistics
GET  /v1/entities              - List entities
GET  /v1/tenants               - List tenants (admin)
POST /v1/keys                  - Create API key
GET  /v1/billing/subscription  - Subscription status
POST /v1/billing/create-checkout-session - Stripe checkout
POST /v1/billing/cancel-subscription - Cancel subscription
POST /v1/billing/webhook       - Stripe webhooks
POST /v1/billing/report-usage  - Usage reporting
WS   /ws/sync                  - WebSocket sync
GET  /docs                     - Swagger UI
GET  /redoc                    - ReDoc docs
```

### Authentication Header
```
X-API-Key: cm_your_api_key_here
```

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad request (invalid input)
- `401` - Unauthorized (missing/invalid API key)
- `404` - Not found
- `500` - Server error

---

## Resources

- **Full Debug Report:** `API_DEBUG_REPORT.md`
- **Endpoint Reference:** `ENDPOINTS_VERIFIED.md`
- **Verification Report:** `API_VERIFICATION_COMPLETE.md`
- **Interactive Docs:** http://localhost:8420/docs

---

**Quick Start Updated:** 2025-12-07
**Server Version:** 0.1.0
**Status:** Production Ready ✅
