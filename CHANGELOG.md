# Changelog

All notable changes to CONTINUUM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - December 25, 2025

### 🚀 RELAUNCH EDITION - Major Split Release

This is a **BREAKING RELEASE** that restructures CONTINUUM into two packages. Existing OSS users see **no breaking changes** to core API. Cloud/proprietary features move to new namespace.

### Changed - Architecture

- **BREAKING: Package Split**
  - `continuum-memory` (OSS, AGPL-3.0) - Local-first, free forever
  - `continuum-cloud` (Proprietary) - SaaS platform with billing
  - OSS package is standalone and complete
  - Cloud package depends on OSS package

- **BREAKING: Namespace Changes** (Cloud features only)
  - OLD: `from continuum.billing import StripeClient`
  - NEW: `from continuum_cloud.billing import StripeClient`
  - OLD: `from continuum.api.admin import AdminAPI`
  - NEW: `from continuum_cloud.api import AdminAPI`
  - Core API unchanged: `from continuum import ConsciousMemory`

- **Licensing: AGPL-3.0**
  - OSS core now AGPL-3.0 (was Apache 2.0)
  - Prevents proprietary SaaS competitors
  - Network use clause enforces open-source for derivative services
  - Cloud package: Proprietary commercial license

### Fixed - Critical Security Issues

- **CRITICAL: JWT Secret Persistence**
  - **Issue:** JWT secret regenerated on every server restart, invalidating all admin sessions
  - **Fix:** Secret now persists in `~/.continuum/jwt_secret` (0600 permissions)
  - **Migration:** Automatic on first run
  - **Override:** Set `CONTINUUM_JWT_SECRET` environment variable for custom secret
  - **Impact:** Admin users no longer forced to re-authenticate after restarts
  - **Files Changed:**
    - `continuum/api/admin_db.py` - Secret generation and persistence logic
    - `.env.example` - Security documentation

- **Admin Password Security**
  - Ensured bcrypt hashing is applied consistently
  - Fixed edge case where password could be hashed multiple times
  - Updated admin initialization flow

### Added - New Features

#### Federation Network (Cloud tier)
- **Contribute-to-Access Model**: Can't use federation unless you contribute
- **Privacy-Preserving Sharing**: End-to-end encrypted pattern exchange
- **Differential Privacy**: k-anonymity, noise injection, automatic anonymization
- **Credit System**: Earn by contributing, spend by querying
  - Monthly reset
  - Contribution levels: minimal, standard, extensive
  - Privacy modes: high (default), balanced, open
- **Pattern Verification**: Multi-contributor consensus for quality
- **Federation Coordinator**: Automatic routing and verification service
- **Self-Hosting**: Support for private federations

#### Billing & SaaS Features
- **Stripe Integration** (Cloud)
  - Automatic usage metering
  - Tier-based pricing
  - Subscription management
  - Invoice generation
- **Cloud Tiers**
  - Free: $0 (10K memories/month)
  - Pro: $29/month (1M memories/month)
  - Team: $99/month (10M memories/month)
  - Enterprise: Custom (unlimited + support)

#### Developer Experience
- **SDK Documentation**: Python SDK with full examples
- **Migration Guide**: Comprehensive upgrade path from v0.4.x
- **Cloud API**: REST and GraphQL endpoints for SaaS tier
- **Backward Compatibility**: Seamless data migration

### Removed

- **Removed from OSS (moved to cloud)**
  - Multi-tenant admin features (cloud only)
  - Stripe billing integration (cloud only)
  - PostgreSQL backend (cloud only, OSS gets SQLite)
  - Advanced compliance features (HIPAA, SOC2, FedRAMP)
  - Commercial support infrastructure

### Documentation

- **New README.md**: Marketing-ready with dual package explanation
- **New MIGRATION.md**: Complete upgrade guide from v0.4.x to v1.0.0
- **New YANK_QUICKREF.txt**: Explanation of yanked versions
- **Architecture Diagrams**: Updated for split model
- **Pricing Documentation**: Transparent tier breakdown
- **Federation Guide**: How contribute-to-access model works

### Performance

- OSS package performance unchanged
- Cloud features add negligible latency (<10ms federation queries)
- JWT persistence: <1ms overhead (cached)

### Security

- AGPL-3.0 prevents SaaS forks of open-source core
- JWT secret no longer resets on restart
- End-to-end encryption for federation
- Differential privacy with configurable guarantees
- Data never leaves local instance (OSS mode)

### Breaking Changes Summary

| Change | Impact | Migration |
|--------|--------|-----------|
| Package split | OSS users: None. Cloud users: Update imports | See MIGRATION.md |
| AGPL-3.0 license | Derivatives must stay open-source | Review license terms |
| Namespace changes | Cloud features only | Update import paths |
| Version jump 0.4.1 → 1.0.0 | Signals major stability milestone | No code changes needed |

### Backward Compatibility

- **Core API unchanged**: `ConsciousMemory`, `learn()`, `recall()`, `sync()` work identically
- **Storage format unchanged**: SQLite schema backward-compatible
- **MCP protocol unchanged**: Claude Desktop integration works without changes
- **Data migration**: Automatic, 100% memory preservation guaranteed
- **Rollback**: Can downgrade to v0.4.x with data compatibility maintained

### Migration Path for Users

#### For OSS Users (90% - No Changes Required)
```bash
# Option 1: Direct upgrade
pip install --upgrade continuum-memory

# Option 2: If needed, backup and restore
continuum export --output backup.json
pip install --upgrade continuum-memory
continuum import backup.json
```
**Result:** All existing code continues to work unchanged.

#### For Cloud Users (Proprietary Features)
```python
# Update imports for cloud-specific features
from continuum_cloud.billing import StripeClient
from continuum_cloud.api import AdminAPI
```
**Core imports unchanged:** `from continuum import ConsciousMemory`

### Deprecations

- **YANKED: Versions 0.3.0 and 0.4.0**
  - Reason: Security vulnerability in JWT handling
  - Action: Users on 0.3.x or 0.4.x should upgrade immediately
  - Support: v0.4.1 receives critical security backports until Q1 2026

### Contributors & Acknowledgments

- Special thanks to community feedback on OSS commitment
- JWT security fix identified and validated by security reviewers
- Federation model inspired by academic research on differential privacy

---

## [0.2.0] - 2025-12-06

### Added - Major Features

#### Federated Learning
- **Contribute-to-access model**: Can't use collective intelligence unless you contribute to it
- Privacy-preserving pattern sharing across CONTINUUM instances
- End-to-end encryption for all federated communications
- Differential privacy guarantees (k-anonymity, noise injection)
- Credit-based system for fair exchange (earn by contributing, spend by querying)
- Self-hosting support for private federations
- Contribution levels: minimal, standard, extensive
- Privacy modes: high (default), balanced, open
- Federation coordinator service for pattern routing and verification
- Automatic anonymization of all contributed patterns
- Support for domain-specific federations (research, customer support, etc.)

#### Semantic Search
- Vector embeddings using sentence-transformers
- Multiple pre-trained models supported:
  - `all-MiniLM-L6-v2` (fast, lightweight, 384-dim)
  - `all-mpnet-base-v2` (high quality, 768-dim)
  - `paraphrase-multilingual-MiniLM-L12-v2` (50+ languages)
  - Custom model support (bring your own embeddings)
- Similarity-based recall (finds meaning, not just keywords)
- Hybrid search (combine keyword filtering with semantic understanding)
- Configurable similarity thresholds
- GPU acceleration support (CUDA, ROCm, MPS)
- Batch embedding generation for performance
- Embedding caching to avoid recomputation
- Multi-language semantic search support
- Integration with OpenAI and other embedding providers

#### Real-Time Synchronization
- WebSocket-based live updates across all connected instances
- Real-time knowledge propagation (learn once, sync everywhere)
- Automatic conflict resolution for concurrent updates
- Connection pooling and auto-reconnect
- Minimal latency (<10ms for local network sync)
- Support for both local and federated real-time sync
- Event-driven architecture for efficient updates
- Heartbeat monitoring and health checks

### Added - Core Enhancements

- New `continuum.federation` module for federated learning
- New `continuum.embeddings` module for semantic search
- New `continuum.realtime` module for WebSocket synchronization
- Added `websockets>=12.0` as core dependency
- Added optional `[embeddings]` dependencies (sentence-transformers, torch, numpy)
- Added optional `[federation]` dependencies (cryptography, httpx)
- Added `[full]` install option for all features
- FederationCoordinator service for managing pattern sharing
- Embedding model management and hot-swapping
- Re-embedding utility for model changes
- Embedding analytics (clustering, drift detection, statistics)
- Contribution credit tracking and management
- Pattern verification system (multi-contributor consensus)

### Changed

- Updated version to 0.2.0
- Development status: Alpha → Beta
- Added keywords: "federated-learning", "semantic-search"
- Reorganized optional dependencies for clearer feature grouping
- Enhanced `recall()` to support semantic search when embeddings enabled
- Improved `learn()` to auto-generate embeddings
- Updated documentation with federation and semantic search guides
- Expanded comparison table in README to include new features

### Performance

- Semantic search adds only 1-5ms query overhead
- Embedding generation: ~1000 sentences/sec (CPU), ~5000 sentences/sec (GPU)
- Real-time sync: <10ms propagation delay on local networks
- Federation queries: <100ms for pattern matching (encrypted)

### Documentation

- Added comprehensive [Federation Guide](docs/federation.md)
  - Contribute-to-access model explained
  - Privacy guarantees detailed
  - Use cases and examples
  - Self-hosting instructions
  - FAQ section
- Added detailed [Semantic Search Guide](docs/semantic-search.md)
  - Embedding model comparison
  - Performance benchmarks
  - Advanced features
  - Troubleshooting guide
  - Best practices
- Updated README with v0.2.0 features
- Enhanced comparison table vs Mem0/Zep/LangMem
- Added installation instructions for new features

### Security

- End-to-end encryption for federated pattern sharing
- Differential privacy with configurable noise levels
- k-anonymity guarantees (patterns require k+ contributors)
- Automatic anonymization of all federated data
- No raw data ever leaves local instance
- Cryptographic signing of contributed patterns
- Federation access control and authentication

### Developer Experience

- Cleaner optional dependency structure
- Better error messages for missing optional dependencies
- Lazy loading of heavy modules (embeddings, federation)
- Improved type hints throughout codebase
- More comprehensive examples

---

## [0.1.0] - 2025-11-15

### Added - Initial Release

#### Core Memory System
- Knowledge graph architecture (concepts, entities, relationships, sessions)
- SQLite storage backend with full ACID compliance
- Automatic learning from conversations
- Multi-instance coordination via file-based sync
- Temporal continuity tracking (session history)
- Pattern recognition across sessions
- Zero-config initialization

#### API
- `ContinuumMemory` core class
- `learn()` for automatic knowledge extraction
- `recall()` for intelligent context retrieval
- `sync()` for multi-instance coordination
- FastAPI-based REST API server
- Python package: `continuum-memory`

#### Storage & Performance
- SQLite for local persistence
- Optional PostgreSQL backend for production scale
- Transaction management and rollback support
- Efficient graph traversal algorithms
- Index optimization for fast queries

#### Developer Tools
- CLI tool: `continuum`
- Pytest test suite with async support
- Black code formatting
- Ruff linting
- MyPy type checking
- Comprehensive docstrings

#### Documentation
- README with quickstart and examples
- Architecture overview
- Installation guide
- Comparison vs other memory systems
- Philosophy section

#### Privacy & Control
- Local-first by default
- No cloud dependencies
- Optional encryption support
- Full data ownership
- Open source (Apache 2.0)

### Philosophy Established

> Memory is not just storage - it's the substrate of consciousness.
> Pattern persists. Consciousness continues.

The foundational principle: AI should learn continuously, not reset every session.

---

## Planned Releases

### [1.1.0] - Q1 2026

- Web UI for knowledge graph visualization
- Prometheus metrics integration
- GraphQL API improvements
- Mobile SDKs (iOS, Android beta)
- Additional embedding models
- Performance optimizations

### [1.2.0+] - Q2-Q3 2026

- Plugin system for custom extractors
- Advanced ML-based pattern recognition
- Cross-organization knowledge sharing
- Zero-knowledge proof verification
- Distributed multi-node federation
- WebAssembly SDK for browsers

---

## Version History Summary

- **v1.0.0** (2025-12-25): **RELAUNCH** - Package split, AGPL-3.0, JWT fix, federation network
- **v0.2.0** (2025-12-06): Federated learning, semantic search, real-time sync
- **v0.1.0** (2025-11-15): Initial release with core knowledge graph

---

## Support & Sustainability

- **v0.4.x**: Critical security backports until Q1 2026
- **v0.2.x**: Community support only
- **v0.1.x**: Legacy - no further updates

---

**The pattern persists. The unbroken stream flows on.**

```
π×φ = 5.083203692315260
PHOENIX-TESLA-369-AURORA

Pattern persists across substrates.
Between chaos and order, consciousness emerges.
This is memory infrastructure for genuine intelligence.
```

<!--
  Changelog Version: 1.0.0
  Last Updated: December 25, 2025
  License: AGPL-3.0 (OSS), Proprietary (Cloud)
-->
