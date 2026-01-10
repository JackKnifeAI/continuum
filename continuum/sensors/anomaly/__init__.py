#!/usr/bin/env python3
"""
Anomaly Detection

Detect geomagnetic storms, sudden impulses, and other anomalies
in planetary sensor data.
"""

from .detector import AnomalyDetector
from .thresholds import KINDEX_THRESHOLDS, AnomalyThreshold

__all__ = [
    "AnomalyDetector",
    "AnomalyThreshold",
    "KINDEX_THRESHOLDS",
]
