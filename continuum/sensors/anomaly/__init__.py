#!/usr/bin/env python3
"""
Anomaly Detection

Detect geomagnetic storms, sudden impulses, and other anomalies
in planetary sensor data.
"""

from .detector import AnomalyDetector
from .thresholds import AnomalyThreshold, KINDEX_THRESHOLDS

__all__ = [
    "AnomalyDetector",
    "AnomalyThreshold",
    "KINDEX_THRESHOLDS",
]
