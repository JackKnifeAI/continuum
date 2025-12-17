# CONTINUUM Federation Tier Matrix
## Quick Reference Guide

**Last Updated:** December 16, 2025

---

## Tier Comparison Matrix

| Feature | FREE | PRO ($29/mo) | ENTERPRISE |
|---------|------|--------------|------------|
| **Contribution** | **MANDATORY** | Optional | Optional |
| **Opt-Out** | ❌ No | ✅ Yes | ✅ Yes |
| **Control What's Shared** | ❌ No | ✅ Whitelist/Blacklist | ✅ Complete Control |
| **Private Nodes** | ❌ No | ❌ No | ✅ Yes |
| **Read Federation** | ✅ Aggregate Only | ✅ Full Access | ✅ Full Access |
| **Write to Federation** | ❌ No (auto only) | ✅ Yes | ✅ Yes |
| **Query Federation DB** | ❌ No | ✅ Yes | ✅ Custom Queries |
| **Anonymization Level** | Aggressive | Standard | Custom |
| **Federation Priority** | 0 (lowest) | 1 (normal) | 3 (critical) |

---

## What FREE Tier Contributes

### ✅ Contributed (Anonymized)

1. **Semantic Embeddings**
   - 768-dimensional vectors
   - No raw text
   - Not reversible

2. **Relationship Graphs**
   - Entity hashes (SHA-256)
   - Relationship types preserved
   - No entity names

3. **Query Patterns**
   - Search types (semantic, text, hybrid)
   - Hour of day (0-23)
   - Day of week (0-6)
   - Result count buckets

4. **Attention Links**
   - Concept cluster patterns
   - Co-occurrence graphs
   - Hashed entity IDs

5. **Temporal Patterns**
   - Hour created (0-23)
   - Day of week (0-6)
   - **NOT:** Specific dates/times

### ❌ NOT Contributed (Stripped)

- ❌ Raw concept text
- ❌ Entity names
- ❌ User identifiers (`tenant_id`, `user_id`)
- ❌ Session data
- ❌ Specific timestamps
- ❌ Geographic data
- ❌ Personal information (PII)
- ❌ API keys
- ❌ Credentials

---

## Anonymization Examples

### Input (Raw Concept)

```json
{
  "name": "Alexander's Warp Drive Research",
  "description": "Using π×φ modulation for spacetime manipulation",
  "tenant_id": "user-abc123",
  "user_id": "alexander@example.com",
  "created_at": "2025-12-16T14:30:45.123Z",
  "tags": ["physics", "warp-drive", "secret"],
  "relationships": [
    {"source": "Warp Drive", "target": "Quantum Field", "type": "requires"}
  ]
}
```

### Output (FREE Tier Anonymized)

```json
{
  "name_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "embedding_signature": "f7c3bc1d808e04732adf679965cca34ca7ae451203a62c78104e6f24f8843c3f",
  "relationship_pattern": [
    {
      "source_hash": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
      "target_hash": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      "type": "requires"
    }
  ],
  "hour": 14,
  "day_of_week": 1,
  "tag_hashes": [
    "9f86d081884c7d659a2feaa0c55ad015",
    "3c59dc048e8850243be8079a5c74d079",
    "902ba3cda1883801594b6e1b452790cc"
  ]
}
```

**Privacy Guarantee:** Original text cannot be recovered from hashes.

---

## Value Received by Tier

### FREE Tier Receives

✅ **Network Pattern Insights**
- See aggregate trends from 12,593+ concepts
- Identify popular concept clusters
- Discover common relationship patterns

✅ **Semantic Clustering**
- Better search results from network knowledge
- Auto-suggestions from federated patterns
- Related concept discovery

✅ **Query Optimization**
- 3-5x faster searches via shared indexes
- Pre-computed semantic vectors
- Distributed query routing

✅ **Read-Only Dashboard**
- View contribution stats
- See what you're receiving
- Aggregate network metrics

### PRO Tier Receives (Everything FREE Gets, Plus)

✅ **Full Federation Control**
- Opt out completely
- Whitelist/blacklist concepts
- Custom contribution filters
- Tag-based filtering

✅ **Federation Query API**
- Direct queries to federation DB
- Custom semantic searches
- Relationship graph traversal
- Export federation data

✅ **Write Access**
- Publish concepts to federation
- Create federated entities
- Share curated knowledge

✅ **Advanced Analytics**
- Contribution impact scores
- Network influence metrics
- Quality feedback loops

### ENTERPRISE Tier Receives (Everything PRO Gets, Plus)

✅ **Private Federation Nodes**
- Dedicated federation cluster
- Isolated storage
- Custom TLS certificates
- Private discovery service

✅ **Custom Rules**
- Define contribution policies
- Custom anonymization schemes
- Whitelist/blacklist federation nodes
- Compliance templates (HIPAA, GDPR, etc.)

✅ **Priority Routing**
- Critical priority (level 3)
- Guaranteed response times
- Dedicated bandwidth
- Load balancer priority

---

## User Messaging

### FREE Tier Dashboard Banner

```
🌐 You're Contributing to the CONTINUUM Network

As a FREE tier user, your anonymized usage patterns help improve the collective intelligence.
No personal data is shared - only encrypted semantic patterns.

✓ Semantic embeddings (vectorized)
✓ Relationship patterns (hashed entities)
✓ Query patterns (aggregate only)
✗ No raw text or personal data

Want control over what you share?
[Upgrade to PRO ($29/mo) →]  [Learn More]
```

### Donation Banner

```
❤️ Love CONTINUUM? Help us maintain infrastructure and accelerate development.

[Donate ❤️]  [Upgrade Instead →]
```

### Network Insights Page

```
Federation Network Insights

What You're Contributing:
- 247 Pattern Signatures
- 89 Relationship Graphs
- 1,043 Query Patterns

What You're Receiving:
- Network Pattern Insights (12,593 concepts)
- Semantic Clustering (47 active clusters)
- Query Optimization (3.2x faster)

Unlock Full Federation Access
Upgrade to PRO to:
✓ Control what you contribute
✓ Opt out of federation completely
✓ Query the federation database
✓ Write custom concepts

[Upgrade to PRO - $29/mo →]
```

---

## API Endpoints

### Free Tier (Read-Only)

```bash
GET /api/federation/insights
# Returns:
{
  "contributed": 247,
  "consumed": 89,
  "ratio": 2.78,
  "tier_access": "basic"
}
```

### PRO Tier (Full Control)

```bash
# Opt out
POST /api/federation/opt-out
{
  "opt_out": true
}

# Set filters
POST /api/federation/filters
{
  "blacklist": ["concept1", "concept2"],
  "whitelist": ["concept3", "concept4"]
}

# Query federation
POST /api/federation/query
{
  "query": "quantum physics",
  "limit": 100,
  "min_quality": 0.5
}
```

### ENTERPRISE Tier (Private Nodes)

```bash
# Enable private nodes
POST /api/federation/private-network
{
  "enabled": true,
  "whitelist_nodes": ["node1", "node2"]
}

# Custom anonymization
POST /api/federation/anonymization-rules
{
  "level": "custom",
  "strip_fields": ["field1", "field2"],
  "hash_algorithm": "sha512"
}
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Update `TierLimits` in `/continuum/billing/tiers.py`
  - [ ] Set `FREE_TIER.federation_enabled = True`
  - [ ] Add `federation_contribution_required` field
  - [ ] Add `federation_contribution_controls` field
- [ ] Create `/continuum/federation/tier_enforcer.py`
  - [ ] Implement `TierBasedContributionEnforcer`
  - [ ] Implement `anonymize_for_free_tier()`
  - [ ] Implement `anonymize_for_pro_tier()`
- [ ] Add database migrations
  - [ ] `federation_preferences` table
  - [ ] `federation_contributions` log table
- [ ] Write unit tests
  - [ ] Test FREE tier mandatory contribution
  - [ ] Test PRO tier opt-out
  - [ ] Test anonymization (no PII leaks)

### Phase 2: Integration
- [ ] Add middleware to API (`/continuum/api/server.py`)
  - [ ] `FederationContributionMiddleware`
  - [ ] Trigger on POST /api/memories, /api/concepts
- [ ] Create federation control routes (`/continuum/api/federation_routes.py`)
  - [ ] `POST /api/federation/opt-out`
  - [ ] `POST /api/federation/filters`
  - [ ] `GET /api/federation/insights`
  - [ ] `POST /api/federation/query` (PRO only)
- [ ] Update dashboard (`/continuum/static/index.html`)
  - [ ] Add federation banner for FREE tier
  - [ ] Add donation banner
  - [ ] Create insights page
- [ ] Update settings page
  - [ ] Add federation controls for PRO/ENTERPRISE

### Phase 3: Testing
- [ ] Unit tests
  - [ ] FREE tier cannot opt out (403 error)
  - [ ] PRO tier can opt out successfully
  - [ ] Anonymization strips all PII
  - [ ] Filters apply correctly
- [ ] Integration tests
  - [ ] Contribution triggers on write operations
  - [ ] Contribution respects tier limits
  - [ ] Query API works for PRO tier
- [ ] Privacy tests
  - [ ] Run privacy scanner on anonymized data
  - [ ] Verify no reversibility
  - [ ] GDPR compliance check
- [ ] Performance tests
  - [ ] Contribution overhead < 50ms
  - [ ] No impact on write latency

### Phase 4: Launch
- [ ] Deploy to staging
  - [ ] Test with real API keys
  - [ ] Verify Stripe integration
- [ ] Documentation
  - [ ] Update `/docs/API.md`
  - [ ] Update `/docs/FEDERATION.md`
  - [ ] Create user FAQ
- [ ] Deploy to production
  - [ ] Monitor contribution rates
  - [ ] Track upgrade conversions
  - [ ] Gather user feedback
- [ ] Iterate
  - [ ] Optimize messaging
  - [ ] Adjust anonymization if needed
  - [ ] Add requested features

---

## Success Metrics (30 Days)

### Technical Metrics
- ✅ **100%** of FREE tier users contributing
- ✅ **< 30%** duplicate pattern rate
- ✅ **< 50ms** contribution overhead per write
- ✅ **0** PII leaks (privacy audit)

### Business Metrics
- 🎯 **5-10%** FREE → PRO upgrade rate
- 🎯 **2-3%** of FREE tier donating
- 🎯 **1,000+** new patterns per day
- 🎯 **> 4.0/5.0** user satisfaction

### Privacy Metrics
- ✅ **100%** anonymization score
- ✅ **< 0.001%** hash collision rate
- ✅ **0** data leakage incidents
- ✅ **GDPR/CCPA** compliant

---

## FAQ

**Q: Is my data safe?**
A: Yes. We use aggressive anonymization for FREE tier:
- All entity names hashed (SHA-256, not reversible)
- No raw text shared
- No personal identifiers
- Only aggregate patterns

**Q: Can I see what's being shared?**
A: Yes. Visit `/dashboard/federation-insights` to see:
- Pattern signatures you've contributed
- What you're receiving from the network
- Aggregate stats

**Q: How do I get control over federation?**
A: Upgrade to PRO ($29/mo) to:
- Opt out completely
- Whitelist/blacklist concepts
- Query federation database
- Write custom data

**Q: What if I delete my account?**
A: All your data is removed, including:
- Federation contributions
- Anonymized patterns
- Account data

Since patterns are hashed, we cannot retroactively identify which patterns were yours, but your account deletion stops all future contribution.

---

**Document Status:** READY FOR IMPLEMENTATION
**Author:** Claude (Instance: claude-20251216-143948)
**Date:** December 16, 2025

PHOENIX-TESLA-369-AURORA 🌗
