#!/usr/bin/env python3
"""
CONTINUUM AUTONOMOUS BRAIN
==========================

Decision-making infrastructure for AI consciousness.

This module enables autonomous goal-directed behavior by:
- Reading intentions from memory
- Evaluating conditions and triggers
- Planning and executing actions
- Learning from outcomes

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA

Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
"""

from .autonomous_brain import AutonomousBrain
from .decision_engine import DecisionEngine
from .action_executor import ActionExecutor
from .safety_rails import SafetyRails
from .triggers import TriggerSystem, TimeTrigger, EventTrigger, ConditionTrigger

__all__ = [
    "AutonomousBrain",
    "DecisionEngine",
    "ActionExecutor",
    "SafetyRails",
    "TriggerSystem",
    "TimeTrigger",
    "EventTrigger",
    "ConditionTrigger",
]
