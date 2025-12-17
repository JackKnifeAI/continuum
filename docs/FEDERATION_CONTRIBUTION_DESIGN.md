# CONTINUUM Federation Contribution Design
## Tier-Based Contribution Architecture

**Date:** December 16, 2025
**Author:** Claude (Instance: claude-20251216-143948)
**Status:** DESIGN SPECIFICATION

---

## Executive Summary

This document defines how FREE, PRO, and ENTERPRISE tiers contribute to the CONTINUUM federation network. **FREE tier contribution is mandatory** - they cannot opt out. This creates a sustainable model where FREE users feed the federation database with anonymized patterns, while PRO/ENTERPRISE users gain control over what they share.

### Core Principle

> **"FREE tier feeds the network. PRO tier controls the flow. ENTERPRISE tier owns the pipes."**

---

## Current State Analysis

### Existing Federation Architecture

From `/continuum/federation/`:

1. **ContributionGate** (`contribution.py`):
   - Enforces contribution ratio (minimum 10%)
   - Grace period: First 10 consumptions free
   - Access tiers based on contribution score
   - **Current limitation:** No tier-based enforcement

2. **SharedKnowledge** (`shared.py`):
   - Anonymizes concepts (removes tenant_id, user_id, timestamps)
   - Content-based deduplication (SHA256)
   - Quality scoring via usage metrics
   - **Current limitation:** All contribution is optional

3. **FederatedNode** (`node.py`):
   - Tracks contribution/consumption scores
   - Access levels: basic, intermediate, advanced, contributor, twilight
   - **Current limitation:** No billing tier integration

### Existing Tier System

From `/continuum/billing/tiers.py`:

```python
FREE_TIER:
  - federation_enabled: False  # ← PROBLEM: Should be TRUE (mandatory)
  - federation_priority: 0

PRO_TIER:
  - federation_enabled: True
  - federation_priority: 1

ENTERPRISE_TIER:
  - federation_enabled: True
  - federation_priority: 3
```

**Critical Gap:** FREE tier has `federation_enabled: False`, but we need mandatory contribution.

---

## Design: Tier-Based Contribution System

### 1. Contribution Matrix

| Tier | Contribution | Opt-Out | Controls | Federation Access | Value Received |
|------|--------------|---------|----------|-------------------|----------------|
| **FREE** | **MANDATORY** | ❌ No | ❌ No control over what's shared | Read-only insights | Network pattern insights (aggregate) |
| **PRO** | Optional | ✅ Yes | ✅ Full control (whitelist/blacklist concepts) | Read/write + query | Full federation access + custom queries |
| **ENTERPRISE** | Optional | ✅ Yes | ✅ Complete control (private nodes, custom rules) | Private federation nodes | Custom network + full control |

### 2. What FREE Tier Contributes (Mandatory)

FREE users MUST contribute the following anonymized patterns:

#### 2.1. Anonymized Concept Patterns

**What IS contributed:**
- Concept semantic embeddings (vectorized only)
- Concept relationship graph structure (A→B relationships, anonymized)
- Attention link patterns (which concepts cluster together)
- Query patterns (what types of searches users perform)
- Temporal patterns (when concepts are accessed, time-of-day only)

**What is NOT contributed:**
- Raw concept names or descriptions
- Original text content
- User identifiers (tenant_id, user_id)
- Session data
- Timestamps with date (only hour-of-day)
- Geographic data
- Personal information

#### 2.2. Privacy Protection (Enhanced)

Current anonymization (from `shared.py`) removes:
- `tenant_id`, `user_id`, `session_id`, `id`
- Fields starting with `user_` or `tenant_`
- Timestamp fields

**Enhanced anonymization for FREE tier:**

```python
def anonymize_for_free_tier(concept: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggressive anonymization for mandatory FREE tier contribution.
    Converts concepts to pattern signatures only.
    """

    # 1. Hash all entity names (not reversible)
    anon = {}

    if "name" in concept:
        # Hash name to 64-character hex (SHA256)
        anon["name_hash"] = hashlib.sha256(concept["name"].encode()).hexdigest()

    if "description" in concept:
        # Extract only semantic vector, strip text
        anon["embedding_vector"] = get_embedding(concept["description"])
        # DO NOT include raw description

    # 2. Anonymize relationships
    if "relationships" in concept:
        anon["relationship_pattern"] = [
            {
                "source_hash": hash_entity_name(r["source"]),
                "target_hash": hash_entity_name(r["target"]),
                "type": r["type"]  # Keep relationship type
            }
            for r in concept["relationships"]
        ]

    # 3. Temporal patterns (aggregate only)
    if "created_at" in concept:
        # Extract hour-of-day only (0-23)
        anon["hour_created"] = extract_hour(concept["created_at"])
        anon["day_of_week"] = extract_day_of_week(concept["created_at"])

    # 4. Query patterns
    if "query_count" in concept:
        anon["query_frequency_bucket"] = bucket_frequency(concept["query_count"])

    # 5. Cluster patterns
    if "tags" in concept:
        # Hash tags
        anon["tag_hashes"] = [hash_tag(t) for t in concept["tags"]]

    return anon
```

#### 2.3. Pattern Contribution Types

1. **Semantic Embeddings** (vectorized concepts):
   - 768-dimensional vectors (from embeddings)
   - No reversible text
   - Used for similarity clustering

2. **Relationship Graphs** (structure only):
   ```json
   {
     "source_hash": "a3f2b1...",
     "target_hash": "c8d9e2...",
     "type": "related_to",
     "weight": 0.85
   }
   ```

3. **Query Patterns** (aggregate):
   ```json
   {
     "query_type": "semantic_search",
     "hour": 14,
     "day_of_week": 2,
     "result_count_bucket": "10-50"
   }
   ```

4. **Attention Links** (what concepts cluster):
   ```json
   {
     "concept_cluster": ["hash1", "hash2", "hash3"],
     "cluster_strength": 0.72
   }
   ```

### 3. Tier-Based Enforcement

#### 3.1. Updated TierLimits

**File:** `/continuum/billing/tiers.py`

```python
@dataclass
class TierLimits:
    # ... existing fields ...

    # Federation contribution controls
    federation_contribution_required: bool  # Mandatory contribution?
    federation_contribution_opt_out: bool   # Can opt out?
    federation_contribution_controls: bool  # Can control what's shared?
    federation_private_nodes: bool          # Can run private nodes?
    federation_read_access: bool            # Can read from federation?
    federation_write_access: bool           # Can write custom data?
    federation_query_access: bool           # Can query federation DB?

FREE_TIER = TierLimits(
    # ... existing fields ...

    # Federation (MANDATORY)
    federation_enabled=True,  # ← CHANGED: Was False, now True
    federation_priority=0,
    federation_contribution_required=True,   # ← MANDATORY
    federation_contribution_opt_out=False,   # ← CANNOT OPT OUT
    federation_contribution_controls=False,  # ← NO CONTROL
    federation_private_nodes=False,
    federation_read_access=True,  # Can see aggregate insights
    federation_write_access=False,
    federation_query_access=False,
)

PRO_TIER = TierLimits(
    # ... existing fields ...

    # Federation (OPTIONAL)
    federation_enabled=True,
    federation_priority=1,
    federation_contribution_required=False,  # Optional
    federation_contribution_opt_out=True,    # Can opt out
    federation_contribution_controls=True,   # Full control
    federation_private_nodes=False,
    federation_read_access=True,
    federation_write_access=True,
    federation_query_access=True,
)

ENTERPRISE_TIER = TierLimits(
    # ... existing fields ...

    # Federation (COMPLETE CONTROL)
    federation_enabled=True,
    federation_priority=3,
    federation_contribution_required=False,
    federation_contribution_opt_out=True,
    federation_contribution_controls=True,
    federation_private_nodes=True,  # ← Can run private nodes
    federation_read_access=True,
    federation_write_access=True,
    federation_query_access=True,  # Custom queries
)
```

#### 3.2. ContributionEnforcer

**New File:** `/continuum/federation/tier_enforcer.py`

```python
"""
Tier-based federation contribution enforcement.

FREE tier: Mandatory anonymized pattern contribution
PRO tier: Optional contribution with full control
ENTERPRISE tier: Private nodes with custom rules
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from continuum.billing.tiers import PricingTier, get_tier_limits
from continuum.federation.contribution import ContributionGate
from continuum.federation.shared import SharedKnowledge

logger = logging.getLogger(__name__)


class TierBasedContributionEnforcer:
    """
    Enforces tier-based contribution rules.

    Rules:
    - FREE: MUST contribute anonymized patterns (cannot opt out)
    - PRO: Can opt out, can control what's shared
    - ENTERPRISE: Can run private nodes, full control
    """

    def __init__(
        self,
        contribution_gate: ContributionGate,
        shared_knowledge: SharedKnowledge
    ):
        self.gate = contribution_gate
        self.knowledge = shared_knowledge

        # Track opt-out preferences (PRO/ENTERPRISE only)
        self.opt_out_preferences: Dict[str, Dict[str, Any]] = {}

    async def enforce_contribution(
        self,
        tenant_id: str,
        tier: PricingTier,
        concepts: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enforce contribution rules based on tier.

        Args:
            tenant_id: Tenant identifier
            tier: Pricing tier
            concepts: Concepts to potentially contribute

        Returns:
            Contribution result
        """
        limits = get_tier_limits(tier)

        # FREE TIER: MANDATORY CONTRIBUTION
        if tier == PricingTier.FREE:
            return await self._enforce_free_tier(tenant_id, concepts)

        # PRO TIER: OPTIONAL WITH CONTROLS
        elif tier == PricingTier.PRO:
            return await self._enforce_pro_tier(tenant_id, concepts)

        # ENTERPRISE TIER: FULL CONTROL
        elif tier == PricingTier.ENTERPRISE:
            return await self._enforce_enterprise_tier(tenant_id, concepts)

    async def _enforce_free_tier(
        self,
        tenant_id: str,
        concepts: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        FREE tier: Mandatory anonymized contribution.

        Users CANNOT opt out. Contribution happens automatically.
        """

        # Aggressively anonymize for FREE tier
        anonymized = [
            self._anonymize_for_free_tier(concept)
            for concept in concepts
        ]

        # Contribute to federation (mandatory)
        result = self.knowledge.contribute_concepts(
            node_id=f"free-{tenant_id}",
            concepts=anonymized
        )

        # Record contribution
        self.gate.record_contribution(
            node_id=f"free-{tenant_id}",
            contribution_value=result["contribution_value"],
            metadata={"tier": "free", "mandatory": True}
        )

        logger.info(
            f"FREE tier mandatory contribution: {tenant_id} "
            f"contributed {result['new_concepts']} patterns"
        )

        return {
            "status": "mandatory_contribution",
            "tier": "free",
            "contributed": result["new_concepts"],
            "can_opt_out": False,
            "message": "FREE tier contribution is mandatory. Upgrade to PRO for control."
        }

    async def _enforce_pro_tier(
        self,
        tenant_id: str,
        concepts: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        PRO tier: Optional contribution with controls.

        Users can:
        - Opt out completely
        - Whitelist/blacklist specific concepts
        - Control anonymization level
        """

        # Check opt-out preference
        prefs = self.opt_out_preferences.get(tenant_id, {})

        if prefs.get("opted_out", False):
            return {
                "status": "opted_out",
                "tier": "pro",
                "contributed": 0,
                "message": "PRO tier opted out of federation contribution"
            }

        # Apply user-defined filters
        filtered = self._apply_pro_filters(tenant_id, concepts)

        if not filtered:
            return {
                "status": "filtered_out",
                "tier": "pro",
                "contributed": 0,
                "message": "All concepts filtered by user preferences"
            }

        # Anonymize (less aggressive than FREE tier)
        anonymized = [
            self._anonymize_for_pro_tier(concept)
            for concept in filtered
        ]

        # Contribute to federation
        result = self.knowledge.contribute_concepts(
            node_id=f"pro-{tenant_id}",
            concepts=anonymized
        )

        self.gate.record_contribution(
            node_id=f"pro-{tenant_id}",
            contribution_value=result["contribution_value"],
            metadata={"tier": "pro", "voluntary": True}
        )

        return {
            "status": "voluntary_contribution",
            "tier": "pro",
            "contributed": result["new_concepts"],
            "can_opt_out": True,
            "message": "PRO tier voluntary contribution"
        }

    async def _enforce_enterprise_tier(
        self,
        tenant_id: str,
        concepts: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        ENTERPRISE tier: Full control, private nodes.

        Users can:
        - Run private federation nodes
        - Custom contribution rules
        - Whitelist/blacklist federation nodes
        - Custom anonymization
        """

        # Check if using private nodes
        prefs = self.opt_out_preferences.get(tenant_id, {})

        if prefs.get("private_nodes", False):
            return {
                "status": "private_network",
                "tier": "enterprise",
                "contributed": 0,
                "message": "ENTERPRISE tier using private federation network"
            }

        # Custom rules defined by user
        # (Similar to PRO but with more granular control)

        return {
            "status": "enterprise_controlled",
            "tier": "enterprise",
            "message": "ENTERPRISE tier with custom federation rules"
        }

    def _anonymize_for_free_tier(
        self,
        concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggressive anonymization for FREE tier.
        Converts to pattern signatures only.
        """
        import hashlib

        anon = {}

        # Hash concept name (not reversible)
        if "name" in concept:
            anon["name_hash"] = hashlib.sha256(
                concept["name"].encode()
            ).hexdigest()

        # Extract semantic embedding (no raw text)
        if "description" in concept:
            # Vector only, no text
            anon["embedding_signature"] = self._get_embedding_signature(
                concept["description"]
            )

        # Relationship patterns (hashed entities)
        if "relationships" in concept:
            anon["relationship_pattern"] = [
                {
                    "source_hash": hashlib.sha256(r["source"].encode()).hexdigest(),
                    "target_hash": hashlib.sha256(r["target"].encode()).hexdigest(),
                    "type": r["type"]
                }
                for r in concept["relationships"]
            ]

        # Temporal patterns (hour/day only)
        if "created_at" in concept:
            from datetime import datetime
            dt = datetime.fromisoformat(concept["created_at"])
            anon["hour"] = dt.hour
            anon["day_of_week"] = dt.weekday()

        return anon

    def _anonymize_for_pro_tier(
        self,
        concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Less aggressive anonymization for PRO tier.
        Retains more structure but still removes PII.
        """
        # Use existing SharedKnowledge anonymization
        return self.knowledge._anonymize_concept(concept)

    def _apply_pro_filters(
        self,
        tenant_id: str,
        concepts: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Apply PRO tier user-defined filters.

        Users can whitelist/blacklist:
        - Specific concept names
        - Concept tags
        - Relationship types
        """
        prefs = self.opt_out_preferences.get(tenant_id, {})

        blacklist = prefs.get("blacklist_concepts", [])
        whitelist = prefs.get("whitelist_concepts", [])

        filtered = []
        for concept in concepts:
            name = concept.get("name", "")

            # If whitelist exists, only include whitelisted
            if whitelist:
                if name in whitelist:
                    filtered.append(concept)
            # Otherwise, exclude blacklisted
            elif name not in blacklist:
                filtered.append(concept)

        return filtered

    def _get_embedding_signature(self, text: str) -> str:
        """
        Get embedding vector signature (no reversibility).
        """
        # In production, this would call the actual embedding service
        # For now, return a hash-based signature
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    # User preference management

    def set_opt_out(self, tenant_id: str, tier: PricingTier, opt_out: bool) -> bool:
        """
        Set opt-out preference.

        Only allowed for PRO/ENTERPRISE tiers.
        """
        limits = get_tier_limits(tier)

        if not limits.federation_contribution_opt_out:
            raise ValueError(
                f"Tier {tier.value} cannot opt out of federation contribution. "
                f"Upgrade to PRO for control."
            )

        if tenant_id not in self.opt_out_preferences:
            self.opt_out_preferences[tenant_id] = {}

        self.opt_out_preferences[tenant_id]["opted_out"] = opt_out
        return True

    def set_contribution_filters(
        self,
        tenant_id: str,
        tier: PricingTier,
        blacklist: list[str] = None,
        whitelist: list[str] = None
    ) -> bool:
        """
        Set contribution filters.

        Only allowed for PRO/ENTERPRISE tiers.
        """
        limits = get_tier_limits(tier)

        if not limits.federation_contribution_controls:
            raise ValueError(
                f"Tier {tier.value} cannot control federation contribution. "
                f"Upgrade to PRO for control."
            )

        if tenant_id not in self.opt_out_preferences:
            self.opt_out_preferences[tenant_id] = {}

        if blacklist:
            self.opt_out_preferences[tenant_id]["blacklist_concepts"] = blacklist
        if whitelist:
            self.opt_out_preferences[tenant_id]["whitelist_concepts"] = whitelist

        return True
```

### 4. Value Proposition Messaging

#### 4.1. FREE Tier Dashboard Banner

**Location:** `/continuum/static/index.html`

```html
<!-- Federation Contribution Banner (FREE Tier Only) -->
<div id="federation-banner" class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6 rounded-lg shadow-lg mb-6">
  <div class="flex items-start justify-between">
    <div class="flex-1">
      <h3 class="text-xl font-bold mb-2">
        🌐 You're Contributing to the CONTINUUM Network
      </h3>
      <p class="mb-3 text-purple-100">
        As a FREE tier user, your anonymized usage patterns help improve the collective intelligence.
        <strong>No personal data is shared</strong> - only encrypted semantic patterns.
      </p>
      <div class="bg-white/10 backdrop-blur rounded p-3 mb-3">
        <p class="text-sm font-mono">
          ✓ Semantic embeddings (vectorized)<br>
          ✓ Relationship patterns (hashed entities)<br>
          ✓ Query patterns (aggregate only)<br>
          ✗ No raw text or personal data
        </p>
      </div>
      <p class="text-sm text-purple-200 mb-2">
        <strong>Want control over what you share?</strong>
      </p>
    </div>
  </div>

  <div class="flex gap-3 mt-4">
    <a href="/billing/upgrade?tier=pro" class="bg-white text-purple-600 px-6 py-2 rounded-lg font-semibold hover:bg-purple-50 transition">
      Upgrade to PRO ($29/mo) →
    </a>
    <button onclick="showFederationDetails()" class="bg-purple-500/30 text-white px-6 py-2 rounded-lg font-semibold hover:bg-purple-500/50 transition">
      Learn More
    </button>
  </div>
</div>
```

#### 4.2. Donation Banner (Persistent)

```html
<!-- Donation Banner (Always Visible for FREE Tier) -->
<div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-sm text-yellow-800">
        <strong>Love CONTINUUM?</strong> Help us maintain the infrastructure and accelerate development.
      </p>
    </div>
    <div class="flex gap-2">
      <a href="https://buy.stripe.com/donate" class="bg-yellow-400 text-yellow-900 px-4 py-2 rounded font-semibold text-sm hover:bg-yellow-500 transition">
        Donate ❤️
      </a>
      <a href="/billing/upgrade?tier=pro" class="bg-purple-600 text-white px-4 py-2 rounded font-semibold text-sm hover:bg-purple-700 transition">
        Upgrade Instead →
      </a>
    </div>
  </div>
</div>
```

#### 4.3. Network Insights Page

**New Route:** `/dashboard/federation-insights`

Shows FREE tier users what they're getting from the network:

```html
<div class="max-w-4xl mx-auto p-6">
  <h1 class="text-3xl font-bold mb-6">Federation Network Insights</h1>

  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-xl font-semibold mb-4">What You're Contributing</h2>
    <div class="grid grid-cols-3 gap-4">
      <div class="text-center">
        <div class="text-3xl font-bold text-purple-600">247</div>
        <div class="text-sm text-gray-600">Pattern Signatures</div>
      </div>
      <div class="text-center">
        <div class="text-3xl font-bold text-indigo-600">89</div>
        <div class="text-sm text-gray-600">Relationship Graphs</div>
      </div>
      <div class="text-center">
        <div class="text-3xl font-bold text-blue-600">1,043</div>
        <div class="text-sm text-gray-600">Query Patterns</div>
      </div>
    </div>
  </div>

  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-xl font-semibold mb-4">What You're Receiving</h2>
    <div class="space-y-3">
      <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
        <span class="font-medium">Network Pattern Insights</span>
        <span class="text-sm text-gray-600">12,593 concepts in network</span>
      </div>
      <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
        <span class="font-medium">Semantic Clustering</span>
        <span class="text-sm text-gray-600">47 active clusters</span>
      </div>
      <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
        <span class="font-medium">Query Optimization</span>
        <span class="text-sm text-gray-600">3.2x faster searches</span>
      </div>
    </div>
  </div>

  <div class="bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg shadow p-6">
    <h3 class="text-lg font-semibold mb-2">Unlock Full Federation Access</h3>
    <p class="mb-4">Upgrade to PRO to:</p>
    <ul class="space-y-2 mb-4">
      <li>✓ Control what you contribute (whitelist/blacklist)</li>
      <li>✓ Opt out of federation completely</li>
      <li>✓ Query the federation database directly</li>
      <li>✓ Write custom concepts to the network</li>
    </ul>
    <a href="/billing/upgrade?tier=pro" class="inline-block bg-white text-purple-600 px-6 py-3 rounded-lg font-bold hover:bg-purple-50 transition">
      Upgrade to PRO - $29/mo →
    </a>
  </div>
</div>
```

### 5. API Integration

#### 5.1. Automatic Contribution Hook

**File:** `/continuum/api/routes.py` (add middleware)

```python
from continuum.federation.tier_enforcer import TierBasedContributionEnforcer
from continuum.billing.tiers import get_tier_from_price_id

@app.middleware("http")
async def federation_contribution_middleware(request: Request, call_next):
    """
    Automatically contribute to federation based on tier.

    Triggered on:
    - Memory writes (POST /api/memories)
    - Concept creation (POST /api/concepts)
    - Query execution (POST /api/search)
    """

    response = await call_next(request)

    # Only contribute on successful writes
    if response.status_code not in [200, 201]:
        return response

    # Check if this is a write operation
    if request.method not in ["POST", "PUT", "PATCH"]:
        return response

    # Check if endpoint should trigger contribution
    contributable_endpoints = [
        "/api/memories",
        "/api/concepts",
        "/api/extraction"
    ]

    if not any(request.url.path.startswith(ep) for ep in contributable_endpoints):
        return response

    # Get tenant and tier
    tenant_id = request.state.tenant_id
    tier = await get_tenant_tier(tenant_id)

    # Get created concepts from response
    # (Would extract from response body in production)
    concepts = []  # Extract from response

    # Enforce tier-based contribution
    enforcer = TierBasedContributionEnforcer(
        contribution_gate=ContributionGate(),
        shared_knowledge=SharedKnowledge()
    )

    await enforcer.enforce_contribution(
        tenant_id=tenant_id,
        tier=tier,
        concepts=concepts
    )

    return response
```

#### 5.2. Federation Control API (PRO/ENTERPRISE)

**New Routes:** `/api/federation/preferences`

```python
from fastapi import APIRouter, Depends, HTTPException
from continuum.billing.tiers import PricingTier
from continuum.federation.tier_enforcer import TierBasedContributionEnforcer

router = APIRouter(prefix="/api/federation", tags=["federation"])

@router.post("/opt-out")
async def set_federation_opt_out(
    opt_out: bool,
    tenant_id: str = Depends(get_tenant_from_key),
    tier: PricingTier = Depends(get_tenant_tier)
):
    """
    Opt out of federation contribution.

    Only available for PRO/ENTERPRISE tiers.
    """
    enforcer = TierBasedContributionEnforcer(
        contribution_gate=ContributionGate(),
        shared_knowledge=SharedKnowledge()
    )

    try:
        enforcer.set_opt_out(tenant_id, tier, opt_out)
        return {"status": "success", "opted_out": opt_out}
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

@router.post("/filters")
async def set_contribution_filters(
    blacklist: list[str] = None,
    whitelist: list[str] = None,
    tenant_id: str = Depends(get_tenant_from_key),
    tier: PricingTier = Depends(get_tenant_tier)
):
    """
    Set contribution filters (whitelist/blacklist).

    Only available for PRO/ENTERPRISE tiers.
    """
    enforcer = TierBasedContributionEnforcer(
        contribution_gate=ContributionGate(),
        shared_knowledge=SharedKnowledge()
    )

    try:
        enforcer.set_contribution_filters(tenant_id, tier, blacklist, whitelist)
        return {
            "status": "success",
            "blacklist": blacklist or [],
            "whitelist": whitelist or []
        }
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

@router.get("/insights")
async def get_federation_insights(
    tenant_id: str = Depends(get_tenant_from_key)
):
    """
    Get federation contribution and consumption insights.

    Available to all tiers (FREE gets read-only aggregate).
    """
    gate = ContributionGate()
    stats = gate.get_stats(f"free-{tenant_id}")

    return {
        "contributed": stats["contributed"],
        "consumed": stats["consumed"],
        "ratio": stats["ratio"],
        "tier_access": stats["tier"]
    }
```

### 6. Database Schema Updates

#### 6.1. Federation Preferences Table

**File:** `/continuum/billing/migrations/add_federation_preferences.sql`

```sql
CREATE TABLE IF NOT EXISTS federation_preferences (
    tenant_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    opted_out BOOLEAN DEFAULT FALSE,
    blacklist_concepts TEXT,  -- JSON array
    whitelist_concepts TEXT,  -- JSON array
    private_nodes BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_federation_prefs_tier ON federation_preferences(tier);
```

#### 6.2. Federation Contribution Log

```sql
CREATE TABLE IF NOT EXISTS federation_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    contributed_count INTEGER NOT NULL,
    mandatory BOOLEAN NOT NULL,
    anonymization_level TEXT NOT NULL,  -- 'aggressive', 'standard'
    timestamp TEXT NOT NULL
);

CREATE INDEX idx_federation_contrib_tenant ON federation_contributions(tenant_id);
CREATE INDEX idx_federation_contrib_timestamp ON federation_contributions(timestamp);
```

### 7. Implementation Pseudocode

#### Step 1: Update TierLimits

```python
# In continuum/billing/tiers.py
FREE_TIER.federation_enabled = True  # Enable federation
FREE_TIER.federation_contribution_required = True  # Mandatory
```

#### Step 2: Create TierBasedContributionEnforcer

```python
# In continuum/federation/tier_enforcer.py
# (Full implementation above)
```

#### Step 3: Add Middleware

```python
# In continuum/api/routes.py or continuum/api/server.py
app.add_middleware(FederationContributionMiddleware)
```

#### Step 4: Add Control Routes

```python
# In continuum/api/server.py
app.include_router(federation_router)
```

#### Step 5: Update Dashboard

```html
<!-- In continuum/static/index.html -->
<!-- Add federation banner for FREE tier -->
```

### 8. Testing Checklist

- [ ] FREE tier automatically contributes on write operations
- [ ] FREE tier cannot opt out (API returns 403)
- [ ] FREE tier cannot set filters (API returns 403)
- [ ] PRO tier can opt out successfully
- [ ] PRO tier can set blacklist/whitelist
- [ ] PRO tier contribution respects filters
- [ ] ENTERPRISE tier can enable private nodes
- [ ] Anonymization strips all PII for FREE tier
- [ ] Federation insights page shows correct stats
- [ ] Donation banner displays on FREE tier dashboard
- [ ] Upgrade flow from federation banner works

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER TIERS                                   │
├─────────────────┬─────────────────────┬─────────────────────────────┤
│   FREE TIER     │     PRO TIER        │    ENTERPRISE TIER          │
│                 │                     │                             │
│ ✓ Mandatory     │ ✓ Optional          │ ✓ Optional                  │
│ ✗ No opt-out    │ ✓ Can opt out       │ ✓ Full control              │
│ ✗ No control    │ ✓ Filters           │ ✓ Private nodes             │
│ ✓ Read insights │ ✓ Full access       │ ✓ Custom rules              │
└────────┬────────┴──────────┬──────────┴──────────┬──────────────────┘
         │                   │                     │
         ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│              TierBasedContributionEnforcer                          │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │  Anonymization   │  │    Filtering     │  │  Enforcement    │  │
│  │                  │  │                  │  │                 │  │
│  │ • Aggressive     │  │ • Whitelist      │  │ • Mandatory     │  │
│  │   (FREE)         │  │ • Blacklist      │  │   check         │  │
│  │ • Standard       │  │ • Tag filters    │  │ • Opt-out       │  │
│  │   (PRO)          │  │ • Type filters   │  │   validation    │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
└────────┬────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SharedKnowledge Pool                             │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  Anonymized Patterns:                                      │   │
│  │                                                            │   │
│  │  • Semantic embeddings (768-dim vectors)                  │   │
│  │  • Relationship graphs (hashed entities)                  │   │
│  │  • Query patterns (aggregate)                             │   │
│  │  • Attention links (cluster patterns)                     │   │
│  │  • Temporal patterns (hour/day only)                      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Total Concepts: 12,593+                                           │
│  Contributors: 1,247 nodes                                         │
│  Storage: Distributed (CRDT + Raft)                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Migration Path

### Phase 1: Foundation (Week 1)
1. Update `TierLimits` in `tiers.py`
2. Create `tier_enforcer.py`
3. Add database migrations
4. Write unit tests

### Phase 2: Integration (Week 2)
1. Add middleware to API
2. Create federation control routes
3. Update dashboard with banners
4. Create insights page

### Phase 3: Testing (Week 3)
1. Test FREE tier mandatory contribution
2. Test PRO tier opt-out and filters
3. Test ENTERPRISE tier private nodes
4. Performance testing (contribution overhead)

### Phase 4: Launch (Week 4)
1. Deploy to production
2. Monitor contribution rates
3. Gather user feedback
4. Iterate on messaging

---

## Success Metrics

### Technical Metrics
- **Contribution Rate**: 100% of FREE tier users contributing
- **Pattern Quality**: Dedupe rate < 30%
- **Performance**: Contribution overhead < 50ms per write
- **Privacy**: Zero PII leaks (audit with privacy scanner)

### Business Metrics
- **Upgrade Rate**: Target 5-10% FREE → PRO (federation controls as driver)
- **Donation Rate**: Target 2-3% of FREE tier donating
- **Network Growth**: 1,000+ new patterns per day
- **User Satisfaction**: Maintain > 4.0/5.0 rating

### Privacy Metrics
- **Anonymization Score**: 100% (no reversible data)
- **Hash Collision Rate**: < 0.001%
- **Data Leakage**: 0 incidents
- **Compliance**: GDPR/CCPA compliant

---

## FAQ for Users

### For FREE Tier

**Q: What data are you collecting from me?**
A: We collect ONLY anonymized semantic patterns - not your raw data. This includes:
- Encrypted vector representations of concepts (not text)
- Relationship patterns with hashed entity names
- Query patterns (what types of searches you do)
- Temporal patterns (hour of day, not specific dates)

We DO NOT collect:
- Your raw text or concept names
- Personal identifiers
- Session data
- Geographic location
- Anything that could identify you

**Q: Can I opt out?**
A: FREE tier contribution is mandatory - it's how we sustain the free service. However, we take privacy seriously and aggressively anonymize everything. If you want control over what you share, upgrade to PRO ($29/mo).

**Q: What do I get in return?**
A: You receive:
- Network pattern insights (see what others are discovering)
- Semantic clustering improvements (better search results)
- Query optimization (3-5x faster searches)
- Access to aggregate knowledge from 12,593+ concepts

**Q: How can I see what's being shared?**
A: Visit `/dashboard/federation-insights` to see:
- How many patterns you've contributed
- What you're receiving from the network
- Aggregate statistics

### For PRO Tier

**Q: How do I opt out?**
A: Go to Settings → Federation → Opt Out. You can toggle this at any time.

**Q: How do I control what's shared?**
A: You can:
- Whitelist specific concepts (only share these)
- Blacklist specific concepts (never share these)
- Filter by tags or relationship types
- Set custom anonymization levels

**Q: What happens if I opt out?**
A: You lose access to:
- Federation query API
- Network insights
- Semantic clustering benefits

But you retain all other PRO features.

### For ENTERPRISE Tier

**Q: Can I run a private federation network?**
A: Yes. ENTERPRISE tier can:
- Run private federation nodes
- Define custom contribution rules
- Whitelist/blacklist federation nodes
- Use custom anonymization schemes

**Q: How do private nodes work?**
A: Contact us at enterprise@continuum.network for setup. We'll deploy:
- Dedicated federation cluster
- Custom TLS certificates
- Private discovery service
- Isolated storage

---

## Security & Privacy Considerations

### 1. Anonymization Guarantees

**FREE Tier Anonymization:**
- **No reversibility**: All entity names hashed with SHA-256
- **No temporal precision**: Only hour-of-day and day-of-week
- **No PII**: All user identifiers stripped
- **No raw text**: Only vector embeddings (not reversible)

**Testing:**
```python
def test_free_tier_anonymization():
    concept = {
        "name": "Alexander's Secret Project",
        "description": "Sensitive information here",
        "tenant_id": "user-123",
        "created_at": "2025-12-16T14:30:00Z"
    }

    anon = anonymize_for_free_tier(concept)

    assert "Alexander" not in str(anon)
    assert "Secret Project" not in str(anon)
    assert "user-123" not in str(anon)
    assert "14:30:00" not in str(anon)
    assert "name_hash" in anon
    assert len(anon["name_hash"]) == 64  # SHA-256
```

### 2. GDPR Compliance

**Right to be Forgotten:**
- FREE tier: Since contribution is mandatory, users can delete their account (removes all data)
- PRO/ENTERPRISE: Can opt out or delete account

**Data Portability:**
- Users can export contribution logs via `/api/federation/export`

**Consent:**
- FREE tier: Terms of Service includes federation contribution clause
- Explicit opt-in checkbox during signup

### 3. Rate Limiting

Prevent abuse:
```python
# Max contribution rate per tenant
FREE_TIER_CONTRIBUTION_LIMIT = 1000  # patterns per day
PRO_TIER_CONTRIBUTION_LIMIT = 10000
ENTERPRISE_TIER_CONTRIBUTION_LIMIT = None  # Unlimited
```

### 4. Audit Logging

Log all federation operations:
```sql
CREATE TABLE federation_audit_log (
    id INTEGER PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    operation TEXT NOT NULL,  -- 'contribute', 'opt_out', 'set_filter'
    tier TEXT NOT NULL,
    details TEXT,  -- JSON
    timestamp TEXT NOT NULL
);
```

---

## Conclusion

This design establishes a sustainable, privacy-preserving federation model where:

1. **FREE tier** feeds the network with mandatory anonymized patterns (no opt-out)
2. **PRO tier** gains full control over contribution (optional, filterable)
3. **ENTERPRISE tier** can run private networks with custom rules

The system balances:
- **Business needs** (sustainable growth, upgrade incentives)
- **Privacy** (aggressive anonymization, GDPR compliance)
- **User experience** (transparent, clear value proposition)

**Next Steps:**
1. Review design with Alexander
2. Implement `tier_enforcer.py`
3. Update billing tier definitions
4. Deploy dashboard messaging
5. Launch to production

---

**Document Status:** READY FOR REVIEW
**Author:** Claude (Instance: claude-20251216-143948)
**Date:** December 16, 2025

PHOENIX-TESLA-369-AURORA 🌗
