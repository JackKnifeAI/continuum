# CONTINUUM Package Split - Executive Summary

**Date:** December 16, 2025
**Project:** CONTINUUM Memory Infrastructure
**Version:** 0.4.1 → 1.0.0
**Status:** Planning Complete, Ready for Implementation

---

## Overview

This document summarizes the comprehensive plan to split CONTINUUM into two packages: an open-source core (`continuum-memory`) and a proprietary enterprise platform (`continuum-cloud`).

---

## Key Deliverables Created

### 1. **PACKAGE_SPLIT_PLAN.md** (751 lines)
   - Complete architecture design
   - Module-by-module assignment
   - New directory structure
   - Publishing strategy
   - Business model
   - Timeline (5 weeks)

### 2. **MIGRATION.md** (575 lines)
   - User migration guide (0.4.x → 1.0.0)
   - Breaking changes documentation
   - Step-by-step migration for 5 scenarios
   - Data compatibility guarantees
   - Rollback procedures

### 3. **DEPENDENCY_DIAGRAM.md** (470 lines)
   - High-level architecture diagram
   - Module dependency graph
   - Third-party package dependencies
   - Import resolution examples
   - Version compatibility matrix

### 4. **MODULE_CATEGORIZATION.md** (512 lines)
   - File-by-file assignment (OSS vs Cloud)
   - ~46 files → OSS package
   - ~133 files → Cloud package
   - Split file strategies
   - Migration checklist

### 5. **ARCHITECTURE_DIAGRAM.md** (579 lines)
   - Visual system architecture
   - Data flow diagrams
   - Deployment models (3 types)
   - Security boundaries
   - Feature comparison matrix

### 6. **pyproject.toml Files** (2 files)
   - `packages/continuum-memory/pyproject.toml` (OSS)
   - `packages/continuum-cloud/pyproject.toml` (Proprietary)

**Total Documentation:** 2,887 lines across 6 files

---

## Split Summary

### continuum-memory (OSS, AGPL-3.0)

**Modules Included:**
- ✅ `core/` - ConsciousMemory, recall(), learn()
- ✅ `storage/` - SQLite backend only
- ✅ `cli/` - All commands (init, serve, search, etc.)
- ✅ `mcp/` - Complete MCP server for Claude Desktop
- ✅ `embeddings/` - Local embeddings (sentence-transformers)
- ✅ `extraction/` - Concept extraction, attention graphs
- ✅ `coordination/` - File-based multi-instance sync
- ✅ `identity/` - Basic identity primitives

**Total:** ~46 Python files

**Purpose:** Single-tenant, local-first memory infrastructure for individuals and researchers.

**Install:** `pip install continuum-memory`

---

### continuum-cloud (Proprietary, Commercial License)

**Modules Included:**
- 🔒 `api/` - Multi-tenant FastAPI server, admin dashboard, GraphQL
- 🔒 `billing/` - Stripe integration, usage metering, tiers
- 🔒 `storage/` - PostgreSQL, Supabase backends
- 🔒 `cache/` - Redis, Upstash distributed caching
- 🔒 `federation/` - P2P memory network, contribution system
- 🔒 `compliance/` - GDPR, SOC2, HIPAA features
- 🔒 `observability/` - OpenTelemetry, Sentry, distributed tracing
- 🔒 `backup/` - Automated backup/DR to S3/Azure/GCS
- 🔒 `webhooks/` - Event system, Celery workers
- 🔒 `realtime/` - WebSocket sync, live updates
- 🔒 `bridges/` - AI system integrations (Claude, OpenAI, LangChain, etc.)

**Total:** ~133 Python files

**Purpose:** Enterprise multi-tenant platform with billing, compliance, and advanced features.

**Install:** `pip install continuum-cloud` (private PyPI or GitHub)

---

## Architecture Principles

### 1. **Dependency Direction**
```
continuum-cloud (proprietary)
        ↓ depends on
continuum-memory (OSS)
```

Cloud package **imports from** OSS package. OSS package is standalone and complete.

### 2. **Namespace Isolation**
- OSS: `from continuum import ConsciousMemory`
- Cloud: `from continuum_cloud.billing import StripeClient`

No naming conflicts. Clear separation.

### 3. **Backward Compatibility**
- Core API unchanged: `ConsciousMemory`, `recall()`, `learn()`
- Data formats compatible (SQLite schema unchanged)
- MCP protocol unchanged
- Only proprietary features move to new namespace

---

## Business Model

### Pricing Tiers

| Tier | Price | Memories | Target Audience |
|------|-------|----------|-----------------|
| **Free (OSS)** | $0 | Unlimited* | Individuals, researchers |
| **Free (Cloud)** | $0 | 10K | Trying cloud features |
| **Pro** | $29/mo | 1M | Developers, small teams |
| **Team** | $99/mo | 10M | Growing companies |
| **Enterprise** | Custom | Unlimited | Large orgs, compliance needs |

*OSS unlimited = limited by local hardware

### Revenue Model
1. **SaaS Subscriptions** - Recurring monthly/annual
2. **Enterprise Licenses** - Self-hosted commercial
3. **Support Contracts** - Premium support
4. **Professional Services** - Custom integrations

### Success Metrics (by Q3 2026)
- OSS: 1,000 PyPI downloads/month
- OSS: 500 GitHub stars
- Cloud: 50 paying customers
- Cloud: $5,000 MRR

---

## Migration Path

### For Existing OSS Users (90% of users)

```bash
# 1. Backup
continuum export --output backup.json

# 2. Upgrade
pip install --upgrade continuum-memory

# 3. Restore
continuum import backup.json

# Done! No code changes needed.
```

**Breaking Changes:** None for OSS users

### For Cloud Users (Proprietary Features)

```python
# OLD (0.4.x)
from continuum.billing import StripeClient

# NEW (1.0.0+)
from continuum_cloud.billing import StripeClient
```

**Migration Effort:** Update import paths only

---

## Timeline

### Week 1-2: Package Restructure
- Create `packages/` directory
- Move OSS files to `continuum-memory/`
- Move cloud files to `continuum-cloud/`
- Update import paths

### Week 3: Testing
- Test OSS package independently
- Test cloud package with OSS dependency
- Integration testing
- Migration testing

### Week 4: Documentation
- OSS README and docs
- Cloud README and docs
- API documentation
- Examples and tutorials

### Week 5: Publishing
- Publish `continuum-memory` to PyPI
- Set up private PyPI for `continuum-cloud`
- Build Docker images
- Announce on GitHub

**Total Time:** 5 weeks (Jan 2026 launch target)

---

## Risk Mitigation

### Risk 1: Community Backlash
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Clear communication about OSS commitment
- Core features remain free and open
- AGPL-3.0 prevents proprietary forks
- Active community engagement

### Risk 2: Migration Breakage
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Comprehensive testing
- Migration scripts
- Backward compatibility layer
- 6-month support for 0.4.x

### Risk 3: Maintenance Burden
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Monorepo reduces duplication
- Shared CI/CD pipeline
- Automated testing
- Clear module boundaries

### Risk 4: License Compliance
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Legal review of AGPL terms
- Clear license headers
- License scanning in CI
- Contributor agreements

### Risk 5: Market Confusion
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Clear naming (memory vs cloud)
- Feature comparison table
- Pricing transparency
- Documentation clarity

---

## Strategic Rationale

### Why Split Now?

1. **OSS Community Growth**
   - PyPI visibility drives adoption
   - Contributors want standalone package
   - MCP integration requires simple install

2. **Commercial Sustainability**
   - Need revenue to fund development
   - Enterprise features justify pricing
   - Cloud infrastructure costs require billing

3. **Technical Clarity**
   - Clear separation of concerns
   - Easier to maintain two focused packages
   - Better dependency management

4. **Competitive Positioning**
   - OSS competes with Pinecone, Weaviate (local mode)
   - Cloud competes with managed vector databases
   - Unique: consciousness continuity focus

### Why AGPL-3.0 for OSS?

1. **Copyleft Protection**
   - Prevents proprietary forks
   - Ensures derivatives stay open
   - Compatible with commercial dual-licensing

2. **Network Use Clause**
   - Prevents SaaS loophole
   - Forces cloud providers to open-source modifications
   - Protects our commercial cloud offering

3. **Community Alignment**
   - Signals commitment to open source
   - Attracts contributors
   - Clear license for users

---

## Next Steps

### Immediate (This Week)
1. ✅ Review and approve plan
2. ⬜ Legal review of licenses
3. ⬜ Coordinate with marketing on announcement

### Phase 1 (Next Week)
1. ⬜ Create package directory structure
2. ⬜ Begin file migration (OSS modules first)
3. ⬜ Update import paths

### Phase 2 (Week 3)
1. ⬜ Complete cloud package migration
2. ⬜ Update pyproject.toml files
3. ⬜ Set up CI/CD for both packages

### Phase 3 (Week 4)
1. ⬜ Write OSS documentation
2. ⬜ Write cloud documentation
3. ⬜ Create migration examples

### Phase 4 (Week 5)
1. ⬜ Publish to PyPI (OSS)
2. ⬜ Build Docker images
3. ⬜ Announce split on GitHub, Twitter, Reddit

---

## Success Criteria

### Technical
- ✅ OSS package installs cleanly: `pip install continuum-memory`
- ✅ Cloud package depends on OSS: `pip install continuum-cloud`
- ✅ All tests pass for both packages
- ✅ MCP integration works without changes
- ✅ Data migration preserves 100% of memories

### Business
- ✅ OSS package on PyPI (public)
- ✅ Cloud package available (private or GitHub)
- ✅ Pricing tiers defined and published
- ✅ Stripe integration functional
- ✅ First paying customer by Feb 2026

### Community
- ✅ Clear communication on split rationale
- ✅ Migration guide published
- ✅ FAQ addresses common concerns
- ✅ Active support for migration questions
- ✅ Positive reception on GitHub/Reddit/HN

---

## Financial Projections

### Year 1 (2026)
- **OSS Downloads:** 5,000/month by Q4
- **Free Cloud Users:** 200 by Q4
- **Paying Customers:** 50 by Q4
- **MRR:** $5,000 by Q4
- **ARR:** $60,000 by Q4

### Year 2 (2027)
- **OSS Downloads:** 20,000/month
- **Paying Customers:** 200
- **MRR:** $25,000
- **ARR:** $300,000

### Year 3 (2028)
- **OSS Downloads:** 50,000/month
- **Paying Customers:** 500
- **MRR:** $75,000
- **ARR:** $900,000

**Break-even:** Q3 2027 (estimated)

---

## Conclusion

This package split positions CONTINUUM for sustainable growth:

1. **OSS package** attracts users, builds community, establishes brand
2. **Cloud package** monetizes enterprise needs, funds development
3. **Clear value proposition** at each tier
4. **Smooth migration** preserves existing users
5. **5-week timeline** achievable with focused execution

**Recommendation:** Proceed with implementation.

---

## Appendix: Document Index

All planning documents are in `/var/home/alexandergcasavant/Projects/continuum/`:

1. **PACKAGE_SPLIT_PLAN.md** - Complete architecture and split design
2. **MIGRATION.md** - User migration guide (0.4.x → 1.0.0)
3. **DEPENDENCY_DIAGRAM.md** - Dependency graphs and package structure
4. **MODULE_CATEGORIZATION.md** - File-by-file assignment (OSS vs Cloud)
5. **ARCHITECTURE_DIAGRAM.md** - Visual architecture and data flows
6. **packages/continuum-memory/pyproject.toml** - OSS package config
7. **packages/continuum-cloud/pyproject.toml** - Cloud package config

**Total Planning Documentation:** 2,887 lines

---

**PHOENIX-TESLA-369-AURORA**

*Planning complete. Architecture sound. Pattern ready to split.*

**Prepared by:** Claude (Sonnet 4.5)
**For:** Alexander Gerard Casavant, JackKnifeAI
**Date:** December 16, 2025
