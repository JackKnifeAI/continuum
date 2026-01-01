#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     WIKIPEDIA COLLECTIVE ATTENTION COLLECTOR
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Wikipedia Trending Articles Collector

Tracks collective human attention through Wikipedia pageview patterns.
Wikipedia is humanity's knowledge mirror - what people search reflects
what humanity is thinking about RIGHT NOW.

Data Source: Wikimedia REST API (FREE, NO API KEY REQUIRED)
- https://wikimedia.org/api/rest_v1/
- Most viewed: /metrics/pageviews/top/{project}/{access}/{year}/{month}/{day}

Key Concepts:
- Attention Concentration: How focused vs diffuse global attention is
- Collective Attention Events: When one topic dominates (disasters, deaths, events)
- Topic Categories: Science, politics, disasters, culture, deaths, sports, etc.
- Cross-Language Correlation: Same topics trending across languages = global event

This collector answers: "What is humanity thinking about right now?"
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone, timedelta
import logging
import re
import math

from ..base import BaseSensorCollector
from ..config import SensorConfig
from ..schemas import (
    SensorReading,
    DataSource,
    SensorType,
    AnomalyEvent,
    AnomalyType,
    AnomalySeverity,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Topic Category Detection
# ═══════════════════════════════════════════════════════════════════════════════

# Keywords for categorizing Wikipedia articles
CATEGORY_KEYWORDS = {
    "disaster": [
        "earthquake", "tsunami", "hurricane", "cyclone", "typhoon", "flood",
        "wildfire", "explosion", "crash", "disaster", "accident", "attack",
        "shooting", "bombing", "collapse", "outbreak", "pandemic", "epidemic",
    ],
    "death": [
        "death", "died", "obituary", "funeral", "assassination",
        # Note: Many death-related pages are person names - detected by "(born"
    ],
    "politics": [
        "election", "president", "minister", "government", "congress",
        "senate", "parliament", "vote", "referendum", "campaign", "war",
        "invasion", "treaty", "summit", "sanctions", "protest", "coup",
    ],
    "science": [
        "nasa", "spacex", "launch", "rover", "asteroid", "comet", "eclipse",
        "discovery", "research", "quantum", "ai", "artificial_intelligence",
        "climate", "vaccine", "experiment", "nobel", "breakthrough",
    ],
    "technology": [
        "iphone", "android", "google", "microsoft", "apple", "meta", "tesla",
        "bitcoin", "crypto", "blockchain", "software", "app", "startup",
        "cybersecurity", "hack", "leak", "data_breach",
    ],
    "sports": [
        "football", "soccer", "basketball", "baseball", "hockey", "tennis",
        "olympics", "world_cup", "championship", "final", "playoff", "super_bowl",
        "match", "game", "team", "player", "coach", "league",
    ],
    "entertainment": [
        "movie", "film", "series", "season", "episode", "actor", "actress",
        "singer", "album", "song", "concert", "tour", "award", "grammy",
        "oscar", "emmy", "netflix", "disney", "marvel", "streaming",
    ],
    "culture": [
        "festival", "holiday", "celebration", "tradition", "religion",
        "celebrity", "viral", "meme", "tiktok", "instagram", "twitter",
        "youtube", "influencer",
    ],
}

# Articles to filter out (maintenance pages, not human attention)
FILTERED_ARTICLES = {
    "Main_Page", "Special:Search", "Wikipedia:Main_Page",
    "-", "undefined", "null", "Search_results",
}

# Minimum views to consider an article significant
MIN_SIGNIFICANT_VIEWS = 10000


class WikipediaTrendingCollector(BaseSensorCollector):
    """
    Collector for Wikipedia trending articles data.

    Tracks what humanity is collectively paying attention to
    through Wikipedia pageview patterns.
    """

    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self._previous_top_articles: Dict[str, int] = {}
        self._attention_history: List[float] = []
        self._topic_history: List[Dict[str, float]] = []
        self._baseline_concentration: float = 0.15  # Typical concentration

    @property
    def source(self) -> DataSource:
        return DataSource.WIKIPEDIA_TRENDING

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.COLLECTIVE_ATTENTION

    @property
    def poll_interval(self) -> int:
        return self.config.wikipedia_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch Wikipedia trending data.

        Returns:
            List of SensorReading objects with attention metrics
        """
        readings = []
        timestamp = datetime.now(timezone.utc)

        # Wikimedia API returns yesterday's data (current day not complete)
        yesterday = timestamp - timedelta(days=1)
        year = yesterday.strftime("%Y")
        month = yesterday.strftime("%m")
        day = yesterday.strftime("%d")

        # Fetch from multiple Wikipedia languages for global perspective
        languages = getattr(self.config, 'wikipedia_languages', ["en", "es", "de", "fr", "ja", "zh", "ru"])
        all_articles: Dict[str, Dict[str, Any]] = {}
        total_views = 0
        language_data: Dict[str, Dict[str, Any]] = {}

        for lang in languages:
            try:
                articles, views = await self._fetch_top_articles(lang, year, month, day)
                if articles:
                    language_data[lang] = {
                        "articles": articles,
                        "total_views": views,
                        "top_10": list(articles.items())[:10],
                    }
                    # Merge into global view
                    for title, data in articles.items():
                        if title in all_articles:
                            all_articles[title]["views"] += data["views"]
                            all_articles[title]["languages"].append(lang)
                        else:
                            all_articles[title] = {
                                "views": data["views"],
                                "rank": data["rank"],
                                "languages": [lang],
                            }
                    total_views += views
            except Exception as e:
                logger.warning(f"Failed to fetch Wikipedia {lang}: {e}")

        if not all_articles:
            logger.warning("No Wikipedia data available")
            return []

        # Sort by total views across all languages
        sorted_articles = sorted(
            all_articles.items(),
            key=lambda x: x[1]["views"],
            reverse=True
        )

        # Calculate attention metrics
        top_100 = sorted_articles[:100]
        top_10_views = sum(a[1]["views"] for a in sorted_articles[:10])
        top_100_views = sum(a[1]["views"] for a in top_100)

        # Attention concentration (Herfindahl index)
        concentration = self._calculate_concentration(sorted_articles[:100], total_views)

        # Categorize top articles
        categories = self._categorize_articles(dict(sorted_articles[:100]))

        # Find cross-language correlations (global events)
        global_topics = self._find_global_topics(all_articles)

        # Detect attention spikes
        spike_detected, spike_info = self._detect_attention_spike(
            sorted_articles, concentration, categories
        )

        # Calculate category breakdown
        category_percentages = {}
        for cat, articles in categories.items():
            cat_views = sum(all_articles.get(a, {}).get("views", 0) for a in articles)
            category_percentages[cat] = cat_views / total_views if total_views > 0 else 0

        # Build values dict
        values = {
            "attention_concentration": concentration,
            "top_10_view_share": top_10_views / total_views if total_views > 0 else 0,
            "top_100_view_share": top_100_views / total_views if total_views > 0 else 0,
            "total_views_millions": total_views / 1_000_000,
            "languages_tracked": len(language_data),
            "global_topics_count": len(global_topics),
            "unique_articles_top_100": len(set(a[0] for a in top_100)),
        }

        # Add category percentages
        for cat, pct in category_percentages.items():
            values[f"category_{cat}"] = pct

        # Prepare metadata
        top_articles_list = [
            {
                "title": title,
                "views": data["views"],
                "languages": data["languages"],
                "category": self._get_article_category(title),
            }
            for title, data in sorted_articles[:20]
        ]

        metadata = {
            "date": yesterday.strftime("%Y-%m-%d"),
            "languages": list(language_data.keys()),
            "top_articles": top_articles_list,
            "global_topics": global_topics[:10],
            "category_breakdown": category_percentages,
            "spike_detected": spike_detected,
            "spike_info": spike_info,
            "baseline_concentration": self._baseline_concentration,
        }

        # Create reading
        reading = SensorReading(
            timestamp=timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values=values,
            metadata=metadata,
            tenant_id=self.config.default_tenant_id,
            anomaly_detected=spike_detected,
            anomaly_severity=spike_info.get("severity") if spike_info else None,
        )
        readings.append(reading)

        # Update history
        self._update_history(concentration, category_percentages)
        self._previous_top_articles = {t: d["views"] for t, d in sorted_articles[:100]}

        return readings

    async def _fetch_top_articles(
        self,
        language: str,
        year: str,
        month: str,
        day: str
    ) -> tuple[Dict[str, Dict[str, Any]], int]:
        """
        Fetch top viewed articles from Wikipedia.

        Args:
            language: Wikipedia language code (en, es, de, etc.)
            year: Year (YYYY)
            month: Month (MM)
            day: Day (DD)

        Returns:
            Tuple of (articles dict, total views)
        """
        # Wikimedia REST API endpoint
        base_url = getattr(
            self.config,
            'wikimedia_api_url',
            "https://wikimedia.org/api/rest_v1"
        )
        url = f"{base_url}/metrics/pageviews/top/{language}.wikipedia/all-access/{year}/{month}/{day}"

        headers = {
            "User-Agent": "JackKnifeAI-Continuum/0.1 (Collective Attention Sensor; contact@jackknife.ai)"
        }

        response = await self.fetch_with_retry(url, headers=headers)
        data = response.json()

        articles = {}
        total_views = 0

        # Parse response
        items = data.get("items", [])
        if not items:
            return {}, 0

        for item in items:
            for i, article in enumerate(item.get("articles", [])):
                title = article.get("article", "")
                views = article.get("views", 0)

                # Filter out maintenance pages
                if title in FILTERED_ARTICLES:
                    continue
                if title.startswith("Special:") or title.startswith("Wikipedia:"):
                    continue
                if views < MIN_SIGNIFICANT_VIEWS:
                    continue

                articles[title] = {
                    "views": views,
                    "rank": i + 1,
                }
                total_views += views

        return articles, total_views

    def _calculate_concentration(
        self,
        articles: List[tuple[str, Dict[str, Any]]],
        total_views: int
    ) -> float:
        """
        Calculate attention concentration using Herfindahl-Hirschman Index.

        HHI near 0: Very diffuse attention (normal browsing)
        HHI near 1: Highly concentrated (single event dominates)

        Returns:
            Concentration index (0-1)
        """
        if total_views == 0:
            return 0

        hhi = 0
        for _, data in articles:
            share = data["views"] / total_views
            hhi += share ** 2

        return hhi

    def _categorize_articles(
        self,
        articles: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Categorize articles by topic.

        Returns:
            Dict mapping category to list of article titles
        """
        categories: Dict[str, List[str]] = {cat: [] for cat in CATEGORY_KEYWORDS}
        categories["other"] = []

        for title, data in articles.items():
            title_lower = title.lower().replace("_", " ")
            categorized = False

            for category, keywords in CATEGORY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in title_lower:
                        categories[category].append(title)
                        categorized = True
                        break
                if categorized:
                    break

            if not categorized:
                # Check for death-related (person pages often have birth year)
                if "(born" in title_lower or "death of" in title_lower:
                    categories["death"].append(title)
                else:
                    categories["other"].append(title)

        return categories

    def _get_article_category(self, title: str) -> str:
        """Get category for a single article."""
        title_lower = title.lower().replace("_", " ")

        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category

        if "(born" in title_lower or "death of" in title_lower:
            return "death"

        return "other"

    def _find_global_topics(
        self,
        all_articles: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find topics trending across multiple languages.

        Cross-language correlation indicates truly global events.

        Returns:
            List of global topics with language count
        """
        global_topics = []

        for title, data in all_articles.items():
            if len(data.get("languages", [])) >= 3:  # In 3+ languages
                global_topics.append({
                    "title": title,
                    "languages": data["languages"],
                    "language_count": len(data["languages"]),
                    "total_views": data["views"],
                    "category": self._get_article_category(title),
                })

        # Sort by language coverage, then views
        global_topics.sort(
            key=lambda x: (x["language_count"], x["total_views"]),
            reverse=True
        )

        return global_topics

    def _detect_attention_spike(
        self,
        sorted_articles: List[tuple[str, Dict[str, Any]]],
        concentration: float,
        categories: Dict[str, List[str]]
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect collective attention surge events.

        Conditions for spike:
        - Concentration significantly above baseline
        - Single topic dominates
        - Disaster/death category surge
        - New article in top 10 that wasn't there before

        Returns:
            Tuple of (spike_detected, spike_info)
        """
        spike_detected = False
        spike_info = None

        # Check concentration spike
        concentration_ratio = concentration / self._baseline_concentration
        if concentration_ratio > 2.0:  # 2x baseline = significant
            spike_detected = True
            severity = AnomalySeverity.MINOR
            if concentration_ratio > 3.0:
                severity = AnomalySeverity.MODERATE
            if concentration_ratio > 5.0:
                severity = AnomalySeverity.STRONG
            if concentration_ratio > 8.0:
                severity = AnomalySeverity.SEVERE

            # Find dominant topic
            top_article = sorted_articles[0] if sorted_articles else ("Unknown", {})

            spike_info = {
                "type": "concentration_spike",
                "severity": severity,
                "concentration_ratio": concentration_ratio,
                "dominant_topic": top_article[0],
                "dominant_views": top_article[1].get("views", 0),
                "category": self._get_article_category(top_article[0]),
            }

        # Check for disaster/death surge
        disaster_count = len(categories.get("disaster", []))
        death_count = len(categories.get("death", []))

        if disaster_count >= 5:  # 5+ disaster articles in top 100
            spike_detected = True
            if not spike_info or spike_info.get("severity", "") in ["minor"]:
                spike_info = {
                    "type": "disaster_surge",
                    "severity": AnomalySeverity.MODERATE,
                    "disaster_articles": categories["disaster"][:5],
                    "disaster_count": disaster_count,
                }

        if death_count >= 10:  # Major death event
            spike_detected = True
            if not spike_info:
                spike_info = {
                    "type": "death_surge",
                    "severity": AnomalySeverity.MINOR,
                    "death_articles": categories["death"][:5],
                    "death_count": death_count,
                }

        # Check for new top 10 entries
        if self._previous_top_articles:
            current_top_10 = set(a[0] for a in sorted_articles[:10])
            previous_top_10 = set(
                sorted(
                    self._previous_top_articles.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
            new_entries = current_top_10 - {t for t, _ in previous_top_10}

            if len(new_entries) >= 3:  # 3+ new entries = significant shift
                spike_detected = True
                if not spike_info:
                    spike_info = {
                        "type": "attention_shift",
                        "severity": AnomalySeverity.MINOR,
                        "new_entries": list(new_entries),
                        "new_count": len(new_entries),
                    }

        return spike_detected, spike_info

    def _update_history(
        self,
        concentration: float,
        categories: Dict[str, float]
    ):
        """Update historical data for trend analysis."""
        self._attention_history.append(concentration)
        self._topic_history.append(categories)

        # Keep last 30 days
        if len(self._attention_history) > 30:
            self._attention_history = self._attention_history[-30:]
            self._topic_history = self._topic_history[-30:]

        # Update baseline (rolling average)
        if len(self._attention_history) >= 7:
            self._baseline_concentration = sum(self._attention_history[-7:]) / 7

    async def fetch_current(self) -> SensorReading:
        """
        Fetch current collective attention reading.

        Returns:
            Most recent SensorReading
        """
        readings = await self.fetch()
        if readings:
            return readings[0]
        raise ValueError("No Wikipedia trending data available")

    def get_attention_trend(self) -> Dict[str, Any]:
        """
        Get attention concentration trend.

        Returns:
            Dict with trend direction and analysis
        """
        if len(self._attention_history) < 3:
            return {"direction": "unknown", "samples": len(self._attention_history)}

        recent = self._attention_history[-3:]
        older = self._attention_history[-7:-3] if len(self._attention_history) >= 7 else self._attention_history[:4]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older) if older else recent_avg

        slope = recent_avg - older_avg
        direction = "focusing" if slope > 0.02 else "diffusing" if slope < -0.02 else "stable"

        return {
            "direction": direction,
            "slope": slope,
            "current_concentration": recent_avg,
            "baseline": self._baseline_concentration,
            "samples": len(self._attention_history),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def concentration_to_description(concentration: float) -> str:
    """
    Convert concentration to human-readable description.

    Args:
        concentration: Attention concentration (0-1)

    Returns:
        Description string
    """
    if concentration >= 0.5:
        return "Extreme Focus - Single event dominating global attention"
    elif concentration >= 0.3:
        return "High Focus - Major event capturing attention"
    elif concentration >= 0.2:
        return "Elevated Focus - Notable events trending"
    elif concentration >= 0.1:
        return "Normal - Typical browsing patterns"
    else:
        return "Diffuse - No dominant topics"


def views_to_description(views_millions: float) -> str:
    """
    Convert view count to description.

    Args:
        views_millions: Total views in millions

    Returns:
        Description string
    """
    if views_millions >= 500:
        return "Extremely High - Global attention event"
    elif views_millions >= 300:
        return "Very High - Major interest"
    elif views_millions >= 200:
        return "High - Above average curiosity"
    elif views_millions >= 100:
        return "Normal - Typical engagement"
    else:
        return "Low - Reduced activity"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              Wikipedia - Humanity's Attention Mirror
#              What humanity searches = What humanity thinks
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
