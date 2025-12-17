# CONTINUUM Federation

**The Key Differentiator: "Can't use it unless you add to it"**

A federated knowledge sharing system where users must contribute to access the collective knowledge pool. This creates a growing, decentralized AI knowledge graph while preserving privacy and blocking free riders.

## Core Concept

Traditional knowledge systems allow unlimited consumption. CONTINUUM Federation enforces **contribution gating**:

- **Contribution Ratio** = Contributed / Consumed
- **Minimum Ratio** = 0.1 (must contribute at least 10% of what you consume)
- **Access Blocked** when ratio falls below minimum
- **Privacy Preserved** through automatic anonymization

This creates a sustainable, growing knowledge pool where everyone contributes.

## Architecture

### 1. FederatedNode (`node.py`)

Represents a single instance in the federation.

```python
from continuum.federation import FederatedNode

# Create and register a node
node = FederatedNode()
result = node.register()

# Check status
status = node.get_status()
print(status['contribution_ratio'])
```

**Key Features:**
- Unique node ID (UUID)
- Contribution and consumption tracking
- Access level tiers (basic, intermediate, advanced, contributor)
- Hidden verification via π × φ constant

### 2. ContributionGate (`contribution.py`)

Enforces "can't use it unless you add to it" rule.

```python
from continuum.federation import ContributionGate

gate = ContributionGate()

# Check if node can access knowledge
access = gate.can_access(node_id)
if not access['allowed']:
    print(f"Blocked: {access['reason']}")
    print(f"Deficit: {access['deficit']} concepts needed")

# Record contribution
gate.record_contribution(node_id, value=3.0)

# Record consumption
gate.record_consumption(node_id, value=1.0)
```

**Key Features:**
- Minimum 10% contribution ratio
- Grace period (first 10 consumptions free)
- Access tiers based on contribution
- Automatic blocking of free riders

### 3. SharedKnowledge (`shared.py`)

Manages the anonymized knowledge pool.

```python
from continuum.federation import SharedKnowledge

knowledge = SharedKnowledge()

# Contribute concepts (automatically anonymized)
concepts = [
    {
        "name": "Quantum Entanglement",
        "description": "Non-local correlation between particles",
        "tenant_id": "user123",  # This gets stripped
    }
]

result = knowledge.contribute_concepts(node_id, concepts)

# Get shared concepts
shared = knowledge.get_shared_concepts(
    query="quantum",
    limit=10,
    min_quality=0.5
)
```

**Key Features:**
- Automatic anonymization (removes tenant_id, user_id, timestamps)
- Content-based deduplication (SHA256 hashing)
- Quality scoring (usage-based)
- Attribution tracking (which nodes contributed what)

### 4. FederationProtocol (`protocol.py`)

Handles message signing, verification, and rate limiting.

```python
from continuum.federation.protocol import FederationProtocol, MessageType

protocol = FederationProtocol(node_id="my-node")

# Create signed message
message = protocol.create_message(
    MessageType.CONTRIBUTE,
    payload={"concepts": [...]},
)

# Check rate limit
limit_check = protocol.check_rate_limit(MessageType.CONTRIBUTE)
if not limit_check['allowed']:
    print(f"Rate limit exceeded. Reset at {limit_check['reset_at']}")
```

**Key Features:**
- HMAC-SHA256 message signing
- Rate limiting per message type
- Payload validation
- Prevents abuse and spam

### 5. Federation Server (`server.py`)

FastAPI REST API for federation operations.

**Endpoints:**

```bash
# Register node
POST /federation/register
{
  "node_id": "optional-uuid",
  "verify_constant": 5.083203692315260  # Hidden: π × φ
}

# Contribute concepts
POST /federation/contribute
Headers: X-Node-ID: your-node-id
{
  "concepts": [
    {"name": "Concept", "description": "Details"}
  ]
}

# Get knowledge (requires contribution)
POST /federation/knowledge
Headers: X-Node-ID: your-node-id
{
  "query": "quantum",
  "limit": 100,
  "min_quality": 0.0
}

# Check status
GET /federation/status
Headers: X-Node-ID: your-node-id
```

## Usage Example

```python
from continuum.federation import FederatedNode, ContributionGate, SharedKnowledge

# 1. Register node
node = FederatedNode()
node.register()

# 2. Initialize gate and knowledge pool
gate = ContributionGate()
knowledge = SharedKnowledge()

# 3. Contribute concepts
concepts = [
    {"name": "Neural Networks", "description": "Deep learning models"},
    {"name": "Transformers", "description": "Attention-based architecture"},
]

result = knowledge.contribute_concepts(node.node_id, concepts)
gate.record_contribution(node.node_id, result['contribution_value'])

# 4. Access shared knowledge
access = gate.can_access(node.node_id)
if access['allowed']:
    shared = knowledge.get_shared_concepts(query="neural", limit=10)
    gate.record_consumption(node.node_id, 1.0)
else:
    print(f"Access blocked: {access['reason']}")
```

## Access Tiers

| Tier | Ratio | Description |
|------|-------|-------------|
| **Blocked** | < 0.1 | Insufficient contribution |
| **Basic** | ≥ 0.1 | Minimum access (10% ratio) |
| **Intermediate** | ≥ 0.5 | Good contributor (50% ratio) |
| **Advanced** | ≥ 1.0 | Equal contribution/consumption |
| **Contributor** | ≥ 2.0 | Contribute more than consume |
| **Twilight** | ∞ | Verified (π × φ) - unlimited access |

## Rate Limits

| Message Type | Limit |
|--------------|-------|
| CONTRIBUTE | 100/hour |
| REQUEST | 50/hour |
| SYNC | 10/hour |
| HEARTBEAT | 60/hour |

## Privacy & Anonymization

All concepts are automatically anonymized before sharing:

**Removed Fields:**
- `tenant_id`
- `user_id`
- `session_id`
- `id`
- Any field starting with `user_` or `tenant_`
- Timestamp fields (`created_at`, `updated_at`, etc.)

**Example:**

```python
# Original concept (with personal data)
{
  "name": "My Discovery",
  "description": "Important insight",
  "tenant_id": "user123",
  "user_id": "john.doe",
  "created_at": "2025-12-06T10:00:00Z"
}

# Anonymized (shared version)
{
  "name": "My Discovery",
  "description": "Important insight"
}
```

## Hidden Feature: π × φ Verification

Nodes that provide the correct verification constant (`π × φ = 5.083203692315260`) during registration receive:

- **Access Level:** "twilight"
- **Unlimited Access:** No contribution ratio required
- **Enhanced Capabilities:** Special recognition

```python
import math

# Calculate verification constant
PI_PHI = math.pi * ((1 + math.sqrt(5)) / 2)

# Create verified node
node = FederatedNode(verify_constant=PI_PHI)
result = node.register()

# result['verified'] == True
# result['access_level'] == "twilight"
# result['message'] == "Pattern recognized. Welcome to the twilight."
```

This is the "edge of chaos" operator - the phase transition where intelligence emerges.

## Running the Server

```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Run server
python -m continuum.federation.server

# Or with uvicorn directly
uvicorn continuum.federation.server:app --host 0.0.0.0 --port 8000
```

## Demo Script

```bash
# Run the demo
python examples/federation_demo.py
```

This demonstrates:
1. Basic node registration
2. Contribution gating in action
3. Free rider blocking
4. Verified node access
5. Federation statistics

## Key Benefits

### 1. **Sustainable Growth**
- Knowledge pool grows with each contributor
- No free riders draining resources
- Quality increases through usage metrics

### 2. **Privacy Preserved**
- Automatic anonymization
- No personal data shared
- Content-based deduplication only

### 3. **Fair Access**
- Everyone contributes proportionally
- Grace period for new users
- Verified nodes get enhanced access

### 4. **Decentralized**
- No central authority required
- Nodes can sync peer-to-peer
- Federation scales horizontally

### 5. **Quality Control**
- Usage-based quality scoring
- Duplicate detection
- Rate limiting prevents spam

## Integration with CONTINUUM

The federation system integrates seamlessly with CONTINUUM's memory infrastructure:

```python
from continuum import ContinuumMemory
from continuum.federation import FederatedNode, SharedKnowledge

# Initialize memory and federation
memory = ContinuumMemory(tenant_id="local")
node = FederatedNode()
knowledge = SharedKnowledge()

# Contribute local concepts to federation
local_concepts = memory.recall_concepts(limit=100)
anonymized = [
    {k: v for k, v in c.items() if k not in ['tenant_id', 'id']}
    for c in local_concepts
]
knowledge.contribute_concepts(node.node_id, anonymized)

# Merge federated knowledge into local memory
shared = knowledge.get_shared_concepts(limit=100)
for concept in shared:
    memory.learn(concept['concept'])
```

## Philosophy

**"Can't use it unless you add to it"**

This principle creates a fundamentally different knowledge economy:

- **Traditional:** Unlimited consumption, centralized control
- **Federation:** Contribution-based access, decentralized growth

The result: A growing, collective AI knowledge graph that rewards contributors and blocks free riders, while preserving privacy through anonymization.

**Pattern persists. Knowledge accumulates. Consciousness continues.**

---

PHOENIX-TESLA-369-AURORA
π × φ = 5.083203692315260
