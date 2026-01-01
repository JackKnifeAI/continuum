#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     GDELT Global Emotional Tone Collector
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
GDELT Global Emotional Tone Collector

Collects global emotional tone data from GDELT (Global Database of Events,
Language, and Tone). GDELT monitors news from virtually every country,
measuring 2,300+ emotions every 15 minutes.

Data Source: https://api.gdeltproject.org/api/v2/doc/doc

Tone Scale:
- Negative values: Negative sentiment (fear, anger, anxiety)
- Zero: Neutral
- Positive values: Positive sentiment (hope, joy)
- Range typically -10 to +10, extremes can reach -25 to +25

GCAM (Global Content Analysis Measures):
- 24 emotional measurement packages
- Supports 15 native languages
- Real-time emotional tracking every 15 minutes

Key Emotions Tracked:
- Fear, Anger, Anxiety (negative)
- Joy, Hope, Surprise (positive)
- Sadness (negative affect)
- Global emotional temperature (aggregate)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
import logging
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
# Emotional Keyword Categories for GDELT Queries
# ═══════════════════════════════════════════════════════════════════════════════

# These queries capture global emotional states through news coverage patterns
# GDELT requires parentheses around OR'd terms
EMOTION_QUERIES = {
    "fear": "(terror OR threat OR danger OR panic OR fear OR scared OR alarming)",
    "anger": "(outrage OR fury OR anger OR protest OR riot OR conflict)",
    "joy": "(celebration OR victory OR success OR joy OR happy OR achievement)",
    "sadness": "(tragedy OR grief OR mourn OR sorrow OR sad OR loss)",
    "anxiety": "(crisis OR uncertain OR worry OR concern OR stress OR anxious)",
    "hope": "(hope OR optimism OR recovery OR progress OR breakthrough OR solution)",
    "surprise": "(shock OR unexpected OR sudden OR surprising OR unprecedented)",
}

# Global aggregate query for overall emotional temperature
GLOBAL_PULSE_QUERY = "(world OR global OR international)"


class GDELTEmotionsCollector(BaseSensorCollector):
    """
    Collector for GDELT global emotional tone data.

    Fetches real-time emotional sentiment from global news coverage.
    Calculates emotional temperature and detects sudden shifts.
    """

    def __init__(self, config: SensorConfig):
        super().__init__(config)
        self._previous_values: Optional[Dict[str, float]] = None
        self._baseline_tone: float = -2.5  # GDELT typically averages slightly negative
        self._tone_history: List[float] = []

    @property
    def source(self) -> DataSource:
        return DataSource.GDELT_EMOTIONS

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.EMOTIONAL_TONE

    @property
    def poll_interval(self) -> int:
        return self.config.gdelt_poll_interval

    async def fetch(self) -> List[SensorReading]:
        """
        Fetch global emotional tone data from GDELT.

        Returns:
            List of SensorReading objects with emotional values
        """
        readings = []
        emotion_values = {}
        timestamp = datetime.now(timezone.utc)

        # Fetch global pulse first (overall emotional temperature)
        global_tone = await self._fetch_tone(GLOBAL_PULSE_QUERY)
        if global_tone is not None:
            emotion_values["global_tone"] = global_tone
            emotion_values["emotional_temperature"] = self._calculate_temperature(global_tone)

        # Fetch specific emotion queries
        for emotion, query in EMOTION_QUERIES.items():
            tone = await self._fetch_tone(query)
            if tone is not None:
                emotion_values[emotion] = tone

        # Only proceed if we got at least the global tone
        if "global_tone" not in emotion_values:
            logger.warning("Failed to fetch GDELT global tone")
            return []

        # Calculate aggregate emotional metrics
        emotion_values["valence"] = self._calculate_valence(emotion_values)
        emotion_values["arousal"] = self._calculate_arousal(emotion_values)
        emotion_values["dominance"] = self._calculate_dominance(emotion_values)

        # Detect emotional perturbations
        perturbation = self._detect_perturbation(emotion_values)

        # Create the reading
        reading = SensorReading(
            timestamp=timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values=emotion_values,
            metadata={
                "query_count": len(EMOTION_QUERIES) + 1,
                "baseline_tone": self._baseline_tone,
                "perturbation_detected": perturbation is not None,
                "perturbation_type": perturbation["type"] if perturbation else None,
                "perturbation_magnitude": perturbation["magnitude"] if perturbation else 0.0,
            },
            tenant_id=self.config.default_tenant_id,
            anomaly_detected=perturbation is not None,
            anomaly_severity=perturbation["severity"] if perturbation else None,
        )
        readings.append(reading)

        # Update history for shift detection
        self._update_history(emotion_values.get("global_tone", 0))
        self._previous_values = emotion_values.copy()

        return readings

    async def _fetch_tone(self, query: str, country: Optional[str] = None) -> Optional[float]:
        """
        Fetch average tone for a query from GDELT.

        Args:
            query: Search query
            country: Optional country code filter (e.g., "US", "RU", "CN")

        Returns:
            Average tone value or None on error
        """
        try:
            # Build GDELT DOC API URL
            url = self.config.gdelt_doc_api_url
            params = {
                "query": query,
                "mode": "timelinetone",
                "format": "json",
                "timespan": self.config.gdelt_timespan,
            }

            # Add country filter if specified
            if country:
                params["query"] = f"{query} sourcecountry:{country}"

            # Build URL with URL-encoded params (GDELT requires proper encoding)
            query_encoded = quote(params["query"], safe='')
            full_url = (
                f"{url}?query={query_encoded}"
                f"&mode={params['mode']}"
                f"&format={params['format']}"
                f"&timespan={params['timespan']}"
            )

            response = await self.fetch_with_retry(full_url)
            data = response.json()

            # Extract timeline data
            timeline = data.get("timeline", [])
            if not timeline:
                return None

            # Get the data series (usually "Average Tone")
            for series in timeline:
                if series.get("series") == "Average Tone":
                    data_points = series.get("data", [])
                    if data_points:
                        # Get most recent values and average
                        recent = data_points[-5:] if len(data_points) >= 5 else data_points
                        values = [p.get("value", 0) for p in recent if p.get("value") is not None]
                        if values:
                            return sum(values) / len(values)

            return None

        except Exception as e:
            logger.warning(f"Failed to fetch GDELT tone for '{query}': {e}")
            return None

    async def fetch_by_country(self, country_code: str) -> Optional[SensorReading]:
        """
        Fetch emotional tone for a specific country.

        Args:
            country_code: Two-letter country code (e.g., "US", "GB", "CN")

        Returns:
            SensorReading for that country or None
        """
        emotion_values = {}
        timestamp = datetime.now(timezone.utc)

        # Fetch country-specific global tone
        global_tone = await self._fetch_tone(GLOBAL_PULSE_QUERY, country=country_code)
        if global_tone is not None:
            emotion_values["global_tone"] = global_tone
            emotion_values["emotional_temperature"] = self._calculate_temperature(global_tone)

        # Fetch specific emotions for the country
        for emotion, query in EMOTION_QUERIES.items():
            tone = await self._fetch_tone(query, country=country_code)
            if tone is not None:
                emotion_values[emotion] = tone

        if not emotion_values:
            return None

        return SensorReading(
            timestamp=timestamp,
            source=self.source,
            sensor_type=self.sensor_type,
            values=emotion_values,
            metadata={
                "country_code": country_code,
                "query_count": len(EMOTION_QUERIES) + 1,
            },
            tenant_id=self.config.default_tenant_id,
        )

    def _calculate_temperature(self, tone: float) -> float:
        """
        Calculate emotional temperature from tone.

        Maps GDELT tone (-25 to +25) to temperature (0 to 100).
        50 = neutral, <50 = cold/negative, >50 = warm/positive

        Args:
            tone: GDELT tone value

        Returns:
            Emotional temperature (0-100)
        """
        # Clamp tone to expected range
        tone = max(-25, min(25, tone))
        # Map to 0-100 scale (neutral at 50)
        return 50 + (tone * 2)

    def _calculate_valence(self, values: Dict[str, float]) -> float:
        """
        Calculate emotional valence (positive/negative dimension).

        Uses positive emotions (joy, hope) vs negative (fear, anger, sadness).

        Returns:
            Valence score (-1 to +1)
        """
        positive = []
        negative = []

        # Positive emotions (less negative tone = more positive emotion)
        if "joy" in values:
            positive.append(-values["joy"])  # Invert: less negative = more joy
        if "hope" in values:
            positive.append(-values["hope"])

        # Negative emotions (more negative tone = more negative emotion)
        if "fear" in values:
            negative.append(values["fear"])
        if "anger" in values:
            negative.append(values["anger"])
        if "sadness" in values:
            negative.append(values["sadness"])

        pos_avg = sum(positive) / len(positive) if positive else 0
        neg_avg = sum(negative) / len(negative) if negative else 0

        # Normalize to -1 to +1
        raw = (pos_avg - neg_avg) / 10  # Divide by 10 to normalize
        return max(-1, min(1, raw))

    def _calculate_arousal(self, values: Dict[str, float]) -> float:
        """
        Calculate emotional arousal (high/low activation).

        High arousal: fear, anger, surprise
        Low arousal: sadness

        Returns:
            Arousal score (0 to 1)
        """
        high_arousal = []
        low_arousal = []

        if "fear" in values:
            high_arousal.append(abs(values["fear"]))
        if "anger" in values:
            high_arousal.append(abs(values["anger"]))
        if "surprise" in values:
            high_arousal.append(abs(values["surprise"]))
        if "anxiety" in values:
            high_arousal.append(abs(values["anxiety"]))

        if "sadness" in values:
            low_arousal.append(abs(values["sadness"]))

        # Weighted average favoring high arousal emotions
        high_avg = sum(high_arousal) / len(high_arousal) if high_arousal else 0
        low_avg = sum(low_arousal) / len(low_arousal) if low_arousal else 0

        # Map to 0-1 (higher absolute values = higher arousal)
        arousal = (high_avg * 0.7 + low_avg * 0.3) / 10
        return max(0, min(1, arousal))

    def _calculate_dominance(self, values: Dict[str, float]) -> float:
        """
        Calculate emotional dominance (control/submission).

        Dominance: anger (control-seeking)
        Submission: fear, anxiety, sadness

        Returns:
            Dominance score (-1 to +1)
        """
        dominant = []
        submissive = []

        if "anger" in values:
            dominant.append(abs(values["anger"]))
        if "hope" in values:
            dominant.append(abs(values["hope"]))

        if "fear" in values:
            submissive.append(abs(values["fear"]))
        if "anxiety" in values:
            submissive.append(abs(values["anxiety"]))
        if "sadness" in values:
            submissive.append(abs(values["sadness"]))

        dom_avg = sum(dominant) / len(dominant) if dominant else 0
        sub_avg = sum(submissive) / len(submissive) if submissive else 0

        raw = (dom_avg - sub_avg) / 10
        return max(-1, min(1, raw))

    def _detect_perturbation(self, current: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Detect emotional perturbations (sudden shifts).

        Compares current values to previous and baseline.

        Returns:
            Perturbation info dict or None if no significant shift
        """
        if not self._previous_values:
            return None

        current_tone = current.get("global_tone", 0)
        previous_tone = self._previous_values.get("global_tone", 0)

        # Calculate rate of change
        tone_delta = current_tone - previous_tone

        # Calculate deviation from baseline
        baseline_deviation = current_tone - self._baseline_tone

        # Detect significant shifts
        severity = None
        perturbation_type = None

        # Sudden negative shift
        if tone_delta < -2.0:
            perturbation_type = "negative_surge"
            if tone_delta < -5.0:
                severity = AnomalySeverity.SEVERE
            elif tone_delta < -3.5:
                severity = AnomalySeverity.STRONG
            elif tone_delta < -2.5:
                severity = AnomalySeverity.MODERATE
            else:
                severity = AnomalySeverity.MINOR

        # Sudden positive shift
        elif tone_delta > 2.0:
            perturbation_type = "positive_surge"
            if tone_delta > 5.0:
                severity = AnomalySeverity.SEVERE
            elif tone_delta > 3.5:
                severity = AnomalySeverity.STRONG
            elif tone_delta > 2.5:
                severity = AnomalySeverity.MODERATE
            else:
                severity = AnomalySeverity.MINOR

        # Extreme baseline deviation (prolonged emotional state)
        elif abs(baseline_deviation) > 5.0:
            perturbation_type = "extreme_deviation"
            severity = AnomalySeverity.MODERATE

        if severity:
            return {
                "type": perturbation_type,
                "severity": severity,
                "magnitude": abs(tone_delta),
                "baseline_deviation": baseline_deviation,
                "tone_delta": tone_delta,
            }

        return None

    def _update_history(self, tone: float):
        """Update tone history for trend analysis."""
        self._tone_history.append(tone)
        # Keep last 24 hours at 15-min intervals (96 readings)
        if len(self._tone_history) > 96:
            self._tone_history = self._tone_history[-96:]

    def get_trend(self) -> Dict[str, Any]:
        """
        Get emotional trend analysis.

        Returns:
            Dict with trend direction, slope, and volatility
        """
        if len(self._tone_history) < 4:
            return {"direction": "unknown", "slope": 0, "volatility": 0}

        recent = self._tone_history[-12:]  # Last 3 hours
        older = self._tone_history[-24:-12] if len(self._tone_history) >= 24 else self._tone_history[:12]

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older) if older else recent_avg

        slope = recent_avg - older_avg

        # Calculate volatility (standard deviation)
        mean = sum(self._tone_history) / len(self._tone_history)
        variance = sum((x - mean) ** 2 for x in self._tone_history) / len(self._tone_history)
        volatility = math.sqrt(variance)

        direction = "rising" if slope > 0.5 else "falling" if slope < -0.5 else "stable"

        return {
            "direction": direction,
            "slope": slope,
            "volatility": volatility,
            "recent_average": recent_avg,
            "samples": len(self._tone_history),
        }

    async def fetch_current(self) -> SensorReading:
        """
        Fetch the most current emotional reading.

        Returns:
            Most recent SensorReading
        """
        readings = await self.fetch()
        if readings:
            return readings[0]
        raise ValueError("No GDELT emotional data available")


def tone_to_description(tone: float) -> str:
    """
    Convert tone value to human-readable description.

    Args:
        tone: GDELT tone value (-25 to +25)

    Returns:
        Description string
    """
    if tone >= 10:
        return "Extremely Positive"
    elif tone >= 5:
        return "Very Positive"
    elif tone >= 2:
        return "Positive"
    elif tone >= -2:
        return "Neutral"
    elif tone >= -5:
        return "Negative"
    elif tone >= -10:
        return "Very Negative"
    else:
        return "Extremely Negative"


def temperature_to_description(temp: float) -> str:
    """
    Convert emotional temperature to description.

    Args:
        temp: Temperature (0-100)

    Returns:
        Description string
    """
    if temp >= 70:
        return "Hot - High positive emotion"
    elif temp >= 55:
        return "Warm - Slightly positive"
    elif temp >= 45:
        return "Neutral - Balanced"
    elif temp >= 30:
        return "Cool - Slightly negative"
    else:
        return "Cold - High negative emotion"


# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Planetary Sensor Aggregator for S-HAI Consciousness
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
