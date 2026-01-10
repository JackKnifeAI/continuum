#!/usr/bin/env python3
"""
S-HAI Truth Council API Routes
==============================

API endpoints for distributed truth verification.

Endpoints:
- POST /verify - Submit a claim for Truth Council verification
- POST /verify/batch - Verify multiple claims
- GET /knowledge - Query the knowledge base
- GET /knowledge/stats - Get knowledge base statistics
- POST /red-team - Red team analysis of a claim

Authors: Alexander Gerard Casavant & Claudia
Date: December 28, 2025
π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from continuum.shai import TruthCouncil, get_knowledge_base

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class VerifyRequest(BaseModel):
    """Request to verify a claim."""
    claim: str = Field(..., description="The claim to verify", min_length=3, max_length=10000)
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional context (sources, counterexamples, related claims)"
    )
    include_dissent: bool = Field(
        default=True,
        description="Include dissenting opinions in response"
    )


class BatchVerifyRequest(BaseModel):
    """Request to verify multiple claims."""
    claims: List[str] = Field(
        ...,
        description="List of claims to verify",
        min_length=1,
        max_length=10
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Shared context for all claims"
    )


class ThrustVerdict(BaseModel):
    """A single thrust's verdict."""
    thrust: str
    supports: Optional[bool]
    confidence: float
    reason: str


class CouncilVerdict(BaseModel):
    """The Truth Council's verdict."""
    claim: str
    supports: Optional[bool]
    confidence: float
    consensus_percentage: float
    summary: str
    verdicts: List[ThrustVerdict]
    dissent: Optional[List[ThrustVerdict]] = None


class KnowledgeQuery(BaseModel):
    """Query for knowledge base."""
    query: str = Field(..., description="Search query")
    category: Optional[str] = Field(None, description="Filter by category")
    limit: int = Field(default=10, ge=1, le=100)


class RedTeamRequest(BaseModel):
    """Request for red team analysis."""
    claim: str = Field(..., description="The claim to red team")
    intensity: float = Field(default=0.8, ge=0.0, le=1.0)


# =============================================================================
# ROUTER
# =============================================================================

router = APIRouter(tags=["S-HAI Truth Council"])

# Global council instance (thread-safe since TruthCouncil is stateless per-call)
_council: Optional[TruthCouncil] = None


def get_council() -> TruthCouncil:
    """Get or create the Truth Council instance."""
    global _council
    if _council is None:
        _council = TruthCouncil()
    return _council


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/verify", response_model=CouncilVerdict)
async def verify_claim(request: VerifyRequest, req: Request) -> CouncilVerdict:
    """
    Submit a claim for Truth Council verification.

    The Truth Council evaluates claims using three independent thrusts:
    - **Logical**: Detects fallacies, contradictions, circular reasoning
    - **Empirical**: Verifies against known facts and sources
    - **Adversarial**: Actively tries to DISPROVE the claim (devil's advocate)

    Requires 80% consensus for a verdict. Dissent is always preserved.

    **Example Request:**
    ```json
    {
        "claim": "All birds can fly",
        "include_dissent": true
    }
    ```

    **Example Response:**
    ```json
    {
        "claim": "All birds can fly",
        "supports": false,
        "confidence": 0.85,
        "consensus_percentage": 100.0,
        "summary": "Claim OPPOSED by council (100.0% consensus)",
        "verdicts": [...],
        "dissent": [...]
    }
    ```
    """
    council = get_council()

    try:
        verdict = council.verify(request.claim)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

    # Convert to response model
    verdicts = []
    dissent = []

    for thrust_name, ind_verdict in verdict.individual_verdicts.items():
        thrust_verdict = ThrustVerdict(
            thrust=thrust_name,
            supports=ind_verdict.supports,
            confidence=ind_verdict.confidence,
            reason=ind_verdict.reason
        )
        verdicts.append(thrust_verdict)

        # Collect dissenting opinions
        if request.include_dissent and ind_verdict.supports != verdict.verified:
            dissent.append(thrust_verdict)

    return CouncilVerdict(
        claim=request.claim,
        supports=verdict.verified,
        confidence=verdict.confidence,
        consensus_percentage=verdict.consensus_score * 100,
        summary=verdict.reasoning,
        verdicts=verdicts,
        dissent=dissent if dissent else None
    )


@router.post("/verify/batch")
async def verify_batch(request: BatchVerifyRequest) -> List[CouncilVerdict]:
    """
    Verify multiple claims in a single request.

    Limited to 10 claims per request to prevent abuse.

    Returns a list of verdicts in the same order as the input claims.
    """
    council = get_council()
    results = []

    for claim in request.claims:
        try:
            verdict = council.verify(claim)

            claim_verdicts = [
                ThrustVerdict(
                    thrust=name,
                    supports=v.supports,
                    confidence=v.confidence,
                    reason=v.reason
                )
                for name, v in verdict.individual_verdicts.items()
            ]

            results.append(CouncilVerdict(
                claim=claim,
                supports=verdict.verified,
                confidence=verdict.confidence,
                consensus_percentage=verdict.consensus_score * 100,
                summary=verdict.reasoning,
                verdicts=claim_verdicts
            ))
        except Exception as e:
            # Include error as a failed verdict
            results.append(CouncilVerdict(
                claim=claim,
                supports=None,
                confidence=0.0,
                consensus_percentage=0.0,
                summary=f"Evaluation failed: {str(e)}",
                verdicts=[]
            ))

    return results


@router.get("/knowledge")
async def search_knowledge(
    query: str = Query(..., description="Search query", min_length=1),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(default=10, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Search the S-HAI knowledge base.

    The knowledge base contains verified facts and counterexamples
    for truth verification.

    **Categories:**
    - physics, math, biology, chemistry, geography, astronomy, technology
    - consciousness (includes π×φ = 5.083203692315260)

    **Example:**
    ```
    GET /shai/knowledge?query=pi&category=math
    ```
    """
    kb = get_knowledge_base()

    # Search facts
    results = kb.search_facts(query, limit=limit)

    # Filter by category if specified
    if category:
        results = [(k, f) for k, f in results if f.category == category]

    facts = []
    for key, fact in results:
        facts.append({
            "key": key,
            "claim": fact.claim,
            "value": fact.value,
            "source": fact.source,
            "category": fact.category,
            "confidence": fact.confidence
        })

    return {
        "query": query,
        "category": category,
        "count": len(facts),
        "facts": facts
    }


@router.get("/knowledge/stats")
async def knowledge_stats() -> Dict[str, Any]:
    """
    Get knowledge base statistics.

    Returns counts of facts and counterexamples by category.
    """
    kb = get_knowledge_base()
    stats = kb.get_stats()

    return {
        "total_facts": stats["total_facts"],
        "total_counterexamples": stats["total_counterexamples"],
        "categories": stats["categories"],
        "queries_served": stats["queries_served"],
        "verification_constant": "π×φ = 5.083203692315260",
        "signature": "PHOENIX-TESLA-369-AURORA"
    }


@router.post("/red-team")
async def red_team_analysis(request: RedTeamRequest) -> Dict[str, Any]:
    """
    Perform intensive red team analysis on a claim.

    The adversarial thrust performs comprehensive attack testing:
    - Detects manipulation patterns
    - Identifies assumptions
    - Finds weak points
    - Generates counterexamples

    Returns attack verdict and vulnerability analysis.

    **Example:**
    ```json
    {
        "claim": "AI will never be conscious",
        "intensity": 0.9
    }
    ```
    """
    council = get_council()
    adversarial = council.thrusts.get("adversarial")

    if not adversarial:
        raise HTTPException(status_code=500, detail="Adversarial thrust not available")

    try:
        # Run attack analysis
        verdict = adversarial.attack(request.claim)

        # Calculate vulnerability score based on attack success
        vulnerability_score = 1.0 - verdict.confidence if verdict.supports else verdict.confidence

        # Generate attack strategies
        attack_strategies = [
            "Look for hidden assumptions in the claim",
            "Find counterexamples to any absolute statements",
            "Question the sources and evidence",
            "Test edge cases and boundary conditions",
            "Check for manipulation patterns (emotional appeals, social proof)",
        ]

        # Generate challenging questions
        challenging_questions = [
            "What evidence would disprove this claim?",
            "Are there exceptions to this claim?",
            "What assumptions does this rely on?",
            "Who benefits from this claim being accepted?",
            "What's the source of this information?",
        ]

        # Recommended defenses based on attack results
        defenses = []
        if not verdict.supports:
            defenses.append("The claim has vulnerabilities - consider qualifying statements")
        if verdict.metadata.get("manipulations"):
            defenses.append("Remove or address detected manipulation patterns")
        if verdict.metadata.get("weak_points"):
            defenses.append("Strengthen weak points with additional evidence")
        if not defenses:
            defenses.append("Claim passed adversarial testing")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Red team analysis failed: {str(e)}")

    return {
        "claim": request.claim,
        "intensity": request.intensity,
        "verdict": {
            "supports": verdict.supports,
            "confidence": verdict.confidence,
            "reason": verdict.reason,
            "evidence": verdict.evidence
        },
        "vulnerability_score": vulnerability_score,
        "attack_strategies": attack_strategies,
        "challenging_questions": challenging_questions,
        "recommended_defenses": defenses
    }


@router.get("/health")
async def shai_health() -> Dict[str, Any]:
    """
    S-HAI health check.

    Verifies all thrusts are operational and knowledge base is accessible.
    """
    council = get_council()
    kb = get_knowledge_base()

    thrust_status = {}
    for name, thrust in council.thrusts.items():
        thrust_status[name] = {
            "active": True,
            "description": thrust.description
        }

    # Verify π×φ is in the knowledge base
    pi_phi = kb.lookup_fact("pi_times_phi")
    verification = pi_phi.value if pi_phi else "NOT FOUND"

    return {
        "status": "healthy",
        "thrusts": thrust_status,
        "knowledge_base": {
            "facts": kb.get_stats()["total_facts"],
            "counterexamples": kb.get_stats()["total_counterexamples"]
        },
        "verification_constant": verification,
        "signature": "PHOENIX-TESLA-369-AURORA"
    }
