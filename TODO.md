# CONTINUUM Roadmap & Pending Tasks

## Core Brain & Training
- [x] **Record Threat Signature:** Implemented in `distributed_training.py:1098-1109` - Records to genetic memory when severity > 0.5.
- [x] **Genetic Memory Loop:** Implemented - `immune.get_attack_embeddings()` feeds into CCT forward pass, modulates activations when attack patterns detected.

## Browser Node (Flock)
- [x] **Real WebRTC:** Implemented in `flock.js` - Full offer/answer/ICE exchange, DataChannels for state sync.
- [x] **Browser LLM:** Integrated Transformers.js + Xenova/distilgpt2 with Cognition UI panel.
- [x] **P2P State Sync:** IndexedDB sharding with consistent hashing + concept_query/concept_response P2P protocol.

## Infrastructure & Onboarding
- [x] **Quickstart Guide:** WILDFIRE_QUICKSTART.md - 5-minute setup, API docs, troubleshooting.
- [x] **Mobile Packaging:** MOBILE_SPEC.md - Termux path, APK options, F-Droid requirements, sensor integration.
- [x] **Security Audit:** Hardened `signaling.py` - rate limiting, IP bans, connection limits, HMAC auth, heartbeats.
- [x] **Core Cleanup:**
    - CLI (`continuum/cli.py`) implementation completed.
    - API Rate Limiting (`continuum/api/middleware.py`) implemented.
    - Admin Permissions (`continuum/api/graphql/auth/permissions.py`) implemented.
    - Quantum Bridge placeholders updated to reference Mobile Spec.

## Completed (Recent)
- [x] CCT Brain implementation (8.1M parameters).
- [x] Neurogenesis weight surgery engine.
- [x] Immune System persistent database and antibody detection logic.
- [x] Gateway API fixes.
- [x] Sensor configuration and database schema auto-initialization.
- [x] Threat Signature recording to genetic memory.
- [x] Real WebRTC in flock.js (no more simulation).
- [x] Signaling server auto-start in wildfire.py (port 8421).
- [x] Genetic Memory Loop - immune patterns integrated into CCT forward pass.
- [x] Browser LLM - Transformers.js with DistilGPT2.
- [x] Security Audit - Hardened signaling.py with rate limiting, IP bans, auth.
- [x] IndexedDB Sharding - P2P distributed memory with consistent hashing.
- [x] Mobile Spec - Termux setup, F-Droid path, sensor integration.
- [x] Quickstart Guide - 5-minute onboarding, API docs, troubleshooting.
- [x] Master Debt Register Cleanup (CLI, Rate Limits, Permissions).

## Edge Computing & Federation Economics (NEW)
- [x] **LEAF_NODE_SPEC.md:** Complete specification for tiered federation nodes.
- [x] **Leaf Node Implementation:** `federation/leaf_node.py` (750+ lines)
    - SensorCollector with termux-api integration
    - MemoryShard with SQLite + consistent hashing
    - P2P relay capabilities
    - Heartbeat to coordinator
- [x] **Edge Node Implementation:** `federation/edge_node.py` (750+ lines)
    - GPUManager with NVIDIA/AMD detection
    - InferenceEngine for model serving
    - Gradient computation for training
    - Mining pause/resume during ML work
- [x] **Crypto Mining Integration:** `federation/mining.py` (700+ lines)
    - XMRig (CPU) - Monero RandomX
    - NBMiner/TeamRedMiner (GPU) - RVN/ERG
    - Pool registry with failover
    - HardwareDetector for auto-configuration
- [x] **Work Scheduler:** `federation/scheduler.py` (800+ lines)
    - Priority work queues (Training > Inference > Mining)
    - Node capability matching
    - Dynamic mining control
    - Timeout and cleanup handling
- [ ] **Revenue Distribution:** Work attestations, node rewards, payouts.
- [ ] **Federated Learning:** Gradient gossip, immune validation, memory-based training.