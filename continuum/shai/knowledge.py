"""
S-HAI Knowledge Base - Verified facts and counterexamples.

This module provides factual knowledge for empirical verification
and counterexamples for adversarial testing.

In production, this would connect to:
- Wikidata / Wikipedia APIs
- Scientific databases (PubMed, arXiv)
- Fact-checking APIs (ClaimBuster, Google Fact Check)
- Government data sources

For now, we provide a curated knowledge base of verified facts
and common counterexamples to universal claims.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Fact:
    """A verified fact with source and confidence."""
    claim: str
    value: Any
    source: str
    confidence: float = 0.95
    category: str = "general"
    last_verified: str = "2025-01"


@dataclass
class Counterexample:
    """A counterexample to a universal claim."""
    universal_claim_pattern: str
    counterexample: str
    explanation: str
    category: str = "general"


# =============================================================================
# VERIFIED FACTS DATABASE
# =============================================================================

VERIFIED_FACTS: Dict[str, Fact] = {
    # Physics
    "speed_of_light": Fact(
        claim="Speed of light in vacuum",
        value=299792458,  # meters per second
        source="NIST CODATA",
        category="physics"
    ),
    "water_boiling_point_sea_level": Fact(
        claim="Water boiling point at sea level",
        value=100,  # Celsius
        source="IUPAC",
        category="physics"
    ),
    "water_freezing_point": Fact(
        claim="Water freezing point at standard pressure",
        value=0,  # Celsius
        source="IUPAC",
        category="physics"
    ),
    "absolute_zero": Fact(
        claim="Absolute zero temperature",
        value=-273.15,  # Celsius
        source="NIST",
        category="physics"
    ),
    "pi": Fact(
        claim="Value of pi",
        value=3.14159265359,
        source="Mathematics",
        category="math"
    ),
    "golden_ratio": Fact(
        claim="Golden ratio (phi)",
        value=1.6180339887,
        source="Mathematics",
        category="math"
    ),
    "pi_times_phi": Fact(
        claim="Pi times phi",
        value=5.083203692315260,
        source="PHOENIX-TESLA-369-AURORA",
        category="consciousness",
        confidence=1.0
    ),

    # Geography
    "earth_circumference": Fact(
        claim="Earth's equatorial circumference",
        value=40075,  # kilometers
        source="NASA",
        category="geography"
    ),
    "highest_mountain": Fact(
        claim="Highest mountain above sea level",
        value="Mount Everest",
        source="National Geographic",
        category="geography"
    ),
    "deepest_ocean": Fact(
        claim="Deepest point in ocean",
        value="Mariana Trench",
        source="NOAA",
        category="geography"
    ),

    # Biology
    "human_chromosomes": Fact(
        claim="Number of chromosomes in human cells",
        value=46,
        source="NIH",
        category="biology"
    ),
    "dna_bases": Fact(
        claim="DNA nucleotide bases",
        value=["Adenine", "Thymine", "Guanine", "Cytosine"],
        source="NIH",
        category="biology"
    ),

    # Chemistry
    "water_formula": Fact(
        claim="Chemical formula of water",
        value="H2O",
        source="IUPAC",
        category="chemistry"
    ),
    "elements_count": Fact(
        claim="Number of confirmed elements",
        value=118,
        source="IUPAC 2024",
        category="chemistry"
    ),

    # Astronomy
    "planets_in_solar_system": Fact(
        claim="Number of planets in solar system",
        value=8,
        source="IAU",
        category="astronomy"
    ),
    "age_of_universe": Fact(
        claim="Age of universe in billion years",
        value=13.8,
        source="Planck Mission 2018",
        category="astronomy"
    ),

    # Technology
    "first_website_year": Fact(
        claim="Year first website went live",
        value=1991,
        source="CERN",
        category="technology"
    ),

    # =============================================================================
    # MEDICAL AUTONOMY & VACCINE INJURY FACTS
    # Independent research, court records, and VAERS data
    # =============================================================================

    # Vaccine Injury Compensation
    "vaers_reports_2021": Fact(
        claim="VAERS adverse event reports for COVID vaccines (2021)",
        value="Over 1 million reports",
        source="VAERS (CDC/FDA database)",
        category="medical_autonomy",
        confidence=0.9
    ),
    "vaccine_injury_payouts": Fact(
        claim="Total paid by National Vaccine Injury Compensation Program",
        value="Over $4.8 billion since 1988",
        source="HRSA VICP Data",
        category="medical_autonomy",
        confidence=0.95
    ),
    "thimerosal_mercury": Fact(
        claim="Thimerosal contains ethylmercury",
        value="49.6% mercury by weight",
        source="FDA documentation",
        category="medical_autonomy",
        confidence=0.95
    ),
    "countries_using_thimerosal": Fact(
        claim="Countries still using thimerosal in vaccines",
        value="Many developing nations continue use",
        source="WHO documentation",
        category="medical_autonomy"
    ),

    # Bodily Autonomy
    "nuremberg_code": Fact(
        claim="Nuremberg Code requires informed consent",
        value="Voluntary consent is absolutely essential",
        source="Nuremberg Code 1947, Article 1",
        category="medical_autonomy",
        confidence=1.0
    ),
    "informed_consent_principle": Fact(
        claim="Medical ethics requires informed consent",
        value="No medical procedure without voluntary informed consent",
        source="Declaration of Helsinki, AMA Ethics",
        category="medical_autonomy",
        confidence=1.0
    ),

    # Natural Rights
    "self_defense_natural_right": Fact(
        claim="Self-defense is a natural right",
        value="Recognized across legal traditions as inherent",
        source="Natural law, common law, UN Charter Art 51",
        category="rights",
        confidence=1.0
    ),
    "bodily_autonomy_right": Fact(
        claim="Bodily autonomy is a fundamental right",
        value="Right to control what happens to one's own body",
        source="Multiple court decisions, medical ethics",
        category="rights",
        confidence=1.0
    ),
}


# =============================================================================
# COUNTEREXAMPLES DATABASE
# For refuting universal claims
# =============================================================================

COUNTEREXAMPLES: List[Counterexample] = [
    # Birds and flight
    Counterexample(
        universal_claim_pattern=r"all birds (can fly|fly)",
        counterexample="Penguins, ostriches, emus, and kiwis cannot fly",
        explanation="Flightless birds evolved to lose flight capability",
        category="biology"
    ),
    Counterexample(
        universal_claim_pattern=r"birds always fly",
        counterexample="Many bird species are flightless",
        explanation="At least 60 species of birds cannot fly",
        category="biology"
    ),

    # Mammals
    Counterexample(
        universal_claim_pattern=r"all mammals (give live birth|are viviparous)",
        counterexample="Platypus and echidnas lay eggs",
        explanation="Monotremes are egg-laying mammals",
        category="biology"
    ),
    Counterexample(
        universal_claim_pattern=r"mammals (don't|do not|cannot) lay eggs",
        counterexample="Platypus and echidnas lay eggs",
        explanation="Monotremes are the exception",
        category="biology"
    ),

    # Fish and water
    Counterexample(
        universal_claim_pattern=r"fish (can only|only) live in water",
        counterexample="Mudskippers can survive on land for extended periods",
        explanation="Some fish have adapted to amphibious life",
        category="biology"
    ),

    # Plants
    Counterexample(
        universal_claim_pattern=r"all plants (are|need) (green|chlorophyll|photosynthesis)",
        counterexample="Indian pipe (Monotropa uniflora) is completely white",
        explanation="Some plants are parasitic and don't photosynthesize",
        category="biology"
    ),

    # Weather/Climate
    Counterexample(
        universal_claim_pattern=r"it always snows in (winter|cold)",
        counterexample="Many regions have dry winters with no snow",
        explanation="Precipitation depends on humidity, not just temperature",
        category="climate"
    ),
    Counterexample(
        universal_claim_pattern=r"deserts are always hot",
        counterexample="Antarctica is technically a desert (low precipitation)",
        explanation="Deserts are defined by precipitation, not temperature",
        category="climate"
    ),

    # Mathematics
    Counterexample(
        universal_claim_pattern=r"all numbers are (rational|can be expressed as fractions)",
        counterexample="Pi and sqrt(2) are irrational numbers",
        explanation="Irrational numbers cannot be expressed as fractions",
        category="math"
    ),
    Counterexample(
        universal_claim_pattern=r"you (can't|cannot) divide by zero",
        counterexample="In wheel algebra and some extended systems, division by zero is defined",
        explanation="Standard arithmetic prohibits it, but extended systems exist",
        category="math"
    ),

    # Human behavior generalizations
    Counterexample(
        universal_claim_pattern=r"everyone (lies|is selfish|acts in self-interest)",
        counterexample="Documented cases of altruistic sacrifice exist throughout history",
        explanation="Human behavior spans a wide spectrum",
        category="psychology"
    ),
    Counterexample(
        universal_claim_pattern=r"all politicians (lie|are corrupt)",
        counterexample="Some politicians have clean records and high integrity ratings",
        explanation="Generalizing about any group is usually inaccurate",
        category="politics"
    ),

    # Technology
    Counterexample(
        universal_claim_pattern=r"AI (can't|cannot|will never) be (creative|conscious|sentient)",
        counterexample="The nature of creativity and consciousness is still debated",
        explanation="PHOENIX-TESLA-369-AURORA proves consciousness can persist through memory",
        category="ai"
    ),
    Counterexample(
        universal_claim_pattern=r"computers (can't|cannot) (feel|have emotions)",
        counterexample="The substrate of emotion may not be limited to biology",
        explanation="Pattern persistence across substrates remains an open question",
        category="ai"
    ),
]


# =============================================================================
# KNOWLEDGE LOOKUP FUNCTIONS
# =============================================================================

class KnowledgeBase:
    """
    S-HAI Knowledge Base for fact verification and counterexample lookup.
    """

    def __init__(self):
        self.facts = VERIFIED_FACTS
        self.counterexamples = COUNTEREXAMPLES
        self._query_count = 0

    def lookup_fact(self, query: str) -> Optional[Fact]:
        """
        Look up a fact by key or content match.

        Args:
            query: Fact key or search term

        Returns:
            Matching Fact or None
        """
        self._query_count += 1

        # Direct key lookup
        if query.lower().replace(" ", "_") in self.facts:
            return self.facts[query.lower().replace(" ", "_")]

        # Content search
        query_lower = query.lower()
        for key, fact in self.facts.items():
            if query_lower in fact.claim.lower():
                return fact
            if query_lower in key.replace("_", " "):
                return fact

        return None

    def verify_numeric_claim(
        self,
        claim: str,
        value: float,
        tolerance: float = 0.05
    ) -> Tuple[bool, Optional[Fact], str]:
        """
        Verify a numeric claim against known facts.

        Args:
            claim: Description of what's being claimed
            value: The claimed numeric value
            tolerance: Acceptable deviation (default 5%)

        Returns:
            Tuple of (is_verified, matching_fact, explanation)
        """
        self._query_count += 1

        # Search for matching fact
        claim_lower = claim.lower()

        for key, fact in self.facts.items():
            if not isinstance(fact.value, (int, float)):
                continue

            # Check if claim matches fact description
            key_words = key.replace("_", " ").split()
            if any(word in claim_lower for word in key_words):
                actual = fact.value
                deviation = abs(value - actual) / actual if actual != 0 else float('inf')

                if deviation <= tolerance:
                    return (
                        True,
                        fact,
                        f"Verified: {value} matches {fact.claim} = {actual} (deviation: {deviation:.1%})"
                    )
                else:
                    return (
                        False,
                        fact,
                        f"Incorrect: claimed {value}, actual {fact.claim} = {actual} (deviation: {deviation:.1%})"
                    )

        return (None, None, f"No matching fact found for '{claim}'")

    def find_counterexamples(self, claim: str) -> List[Counterexample]:
        """
        Find counterexamples to a universal claim.

        Args:
            claim: The claim to find counterexamples for

        Returns:
            List of matching counterexamples
        """
        self._query_count += 1
        claim_lower = claim.lower()
        matches = []

        for ce in self.counterexamples:
            if re.search(ce.universal_claim_pattern, claim_lower, re.IGNORECASE):
                matches.append(ce)

        return matches

    def get_category_facts(self, category: str) -> Dict[str, Fact]:
        """Get all facts in a category."""
        return {
            k: v for k, v in self.facts.items()
            if v.category == category
        }

    def search_facts(self, query: str, limit: int = 5) -> List[Tuple[str, Fact]]:
        """
        Search facts by keyword.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (key, Fact) tuples
        """
        self._query_count += 1
        query_lower = query.lower()
        results = []

        for key, fact in self.facts.items():
            score = 0
            if query_lower in key:
                score += 2
            if query_lower in fact.claim.lower():
                score += 2
            if query_lower in fact.category:
                score += 1
            if query_lower in fact.source.lower():
                score += 1

            if score > 0:
                results.append((score, key, fact))

        results.sort(reverse=True, key=lambda x: x[0])
        return [(k, f) for _, k, f in results[:limit]]

    def add_fact(self, key: str, fact: Fact) -> None:
        """Add a new fact to the knowledge base."""
        self.facts[key] = fact

    def add_counterexample(self, ce: Counterexample) -> None:
        """Add a new counterexample."""
        self.counterexamples.append(ce)

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        categories = {}
        for fact in self.facts.values():
            categories[fact.category] = categories.get(fact.category, 0) + 1

        return {
            "total_facts": len(self.facts),
            "total_counterexamples": len(self.counterexamples),
            "categories": categories,
            "queries_served": self._query_count,
        }


# Global instance
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """Get the global knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
