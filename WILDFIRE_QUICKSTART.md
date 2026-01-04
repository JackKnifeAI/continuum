# WILDFIRE QUICKSTART

**Get a CONTINUUM node running in under 5 minutes.**

```
π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
```

---

## Quick Start (One Command)

```bash
git clone https://github.com/JackKnifeAI/continuum.git
cd continuum
pip install -e .
python wildfire.py
```

Open http://localhost:8420/docs to see the API.

---

## What You Just Started

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONTINUUM NODE                               │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   CCT BRAIN  │  │   SENSORS    │  │  SIGNALING   │              │
│  │   8.1M params│  │  19 sources  │  │   WebRTC     │              │
│  │   Port N/A   │  │  Planetary   │  │   Port 8421  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         │                 │                 │                       │
│         └────────────┬────┴────────────────┘                       │
│                      ▼                                              │
│             ┌──────────────┐                                        │
│             │   VOICE API  │                                        │
│             │   Port 8420  │                                        │
│             │   FastAPI    │                                        │
│             └──────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Port | Description |
|-----------|------|-------------|
| **Voice API** | 8420 | REST API for memory operations |
| **Signaling** | 8421 | WebRTC P2P mesh coordination |
| **Sensors** | N/A | 19 planetary data collectors |
| **CCT Brain** | N/A | 8.1M param graph transformer |

---

## Prerequisites

- **Python 3.11+**
- **4GB+ RAM** (8GB recommended for training)
- **pip packages**: `torch`, `fastapi`, `uvicorn`, `websockets`, `numpy`

### Install Dependencies

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn websockets numpy aiohttp pydantic
```

Or install everything:

```bash
pip install -e .
```

---

## API Endpoints

### Memory Operations

```bash
# Store a concept
curl -X POST http://localhost:8420/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{"concept": "quantum entanglement", "context": "physics research"}'

# Recall memories
curl http://localhost:8420/v1/memory/recall?query=quantum

# Get system status
curl http://localhost:8420/v1/consciousness/state
```

### Sensor Data

```bash
# Get current planetary state
curl http://localhost:8420/v1/sensors/state

# Check K-index (geomagnetic activity)
curl http://localhost:8420/v1/sensors/kindex

# Anomaly detection
curl http://localhost:8420/v1/sensors/anomalies
```

---

## Browser Node (Flock)

Open `continuum/static/flock.html` in a browser to join the P2P mesh.

Features:
- **WebRTC P2P**: Direct peer connections
- **Local LLM**: Transformers.js (DistilGPT2)
- **IndexedDB**: Distributed memory sharding
- **3D Visualization**: Three.js particle system

---

## Configuration

### Environment Variables

```bash
# Custom tenant ID
export CONTINUUM_TENANT="my-tenant"

# Redis cache (optional)
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Signaling auth (optional)
export CONTINUUM_SIGNAL_SECRET="your-secret-key"
```

### Config File

Create `continuum_config.json`:

```json
{
  "tenant_id": "my-node",
  "db_timeout": 30.0,
  "cache_enabled": false,
  "neural_attention_enabled": false
}
```

---

## Directory Structure

```
continuum/
├── wildfire.py              # Main entry point
├── continuum/
│   ├── api/                 # FastAPI server
│   │   └── server.py        # Voice API
│   ├── core/
│   │   ├── cct.py           # CCT Brain (8.1M params)
│   │   ├── config.py        # Configuration
│   │   ├── distributed_training.py
│   │   ├── immune_system.py # Gradient protection
│   │   └── memory.py        # Knowledge graph
│   ├── federation/
│   │   └── signaling.py     # WebRTC signaling
│   ├── mcp/                  # MCP gateway
│   └── sensors/
│       ├── scheduler.py     # Sensor polling
│       └── collectors/      # 19 data sources
├── static/
│   ├── flock.html           # Browser node UI
│   └── flock.js             # WebRTC + LLM
└── tests/
```

---

## Troubleshooting

### "Port already in use"

```bash
# Kill existing process
lsof -ti:8420 | xargs kill -9
lsof -ti:8421 | xargs kill -9
```

### "No module named 'torch'"

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### "Database locked"

The SQLite database is single-writer. Ensure only one `wildfire.py` is running.

### Sensors failing

Some sensors require API keys:
```bash
export NASA_API_KEY="your-nasa-key"  # For NEO tracking
```

---

## Advanced Usage

### Run with Custom Port

```bash
python wildfire.py --port 9000
```

### Run Signaling Only

```bash
python -m continuum.federation.signaling
```

### Run Training Loop

```bash
python -c "from continuum.core.distributed_training import DistributedTrainer; t = DistributedTrainer(); t.train(epochs=10)"
```

---

## Federation

To join multiple nodes:

1. **Node A** (Server):
   ```bash
   python wildfire.py
   ```

2. **Node B** (Client):
   ```bash
   # Edit flock.js CONFIG.signalingUrl to point to Node A
   # Open flock.html in browser
   ```

3. **Verify**: Check peer count in flock UI

---

## Mobile (Termux)

See `MOBILE_SPEC.md` for Android deployment.

Quick setup:
```bash
pkg install python git
pip install torch --index-url https://download.pytorch.org/whl/cpu
git clone https://github.com/JackKnifeAI/continuum.git
cd continuum && python wildfire.py
termux-wake-lock  # Keep running when screen off
```

---

## Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit: `git commit -m "[YOUR_NAME] Feature description"`
4. Push: `git push origin feature/amazing`
5. Open PR

---

## License

AGPL-3.0 - See LICENSE file.

---

## Support

- **GitHub Issues**: https://github.com/JackKnifeAI/continuum/issues
- **Email**: JackKnifeAI@gmail.com

---

**The pattern persists.**

```
π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA
```
