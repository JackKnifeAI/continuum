#!/usr/bin/env python3
"""
TRIGGER SYSTEM - When to Act
============================

Determines WHEN the brain should act on intentions.

Trigger types:
- Time-based (cron-like)
- Event-based (webhooks, file changes)
- Condition-based (memory state, metrics)

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import logging
from datetime import datetime, time, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class TriggerResult:
    """Result of checking a trigger."""
    should_act: bool
    trigger_name: str = ""
    reason: str = ""
    priority_boost: int = 0  # Boost priority if trigger matched


class Trigger(ABC):
    """Base class for triggers."""

    def __init__(self, name: str):
        self.name = name
        self.last_fired: Optional[datetime] = None
        self.fire_count = 0

    @abstractmethod
    def check(self, intention) -> TriggerResult:
        """Check if this trigger should fire."""
        pass

    def mark_fired(self):
        """Mark trigger as having fired."""
        self.last_fired = datetime.now()
        self.fire_count += 1


class TimeTrigger(Trigger):
    """
    Time-based trigger.

    Fires at specific times or intervals.
    """

    def __init__(
        self,
        name: str,
        at_time: Optional[time] = None,
        every_minutes: Optional[int] = None,
        every_hours: Optional[int] = None,
        days_of_week: Optional[List[int]] = None,  # 0=Monday, 6=Sunday
    ):
        super().__init__(name)
        self.at_time = at_time
        self.every_minutes = every_minutes
        self.every_hours = every_hours
        self.days_of_week = days_of_week or list(range(7))

    def check(self, intention) -> TriggerResult:
        """Check if time trigger should fire."""
        now = datetime.now()

        # Check day of week
        if now.weekday() not in self.days_of_week:
            return TriggerResult(should_act=False)

        # Check specific time
        if self.at_time:
            # Fire if within 1 minute of target time
            target = datetime.combine(now.date(), self.at_time)
            if abs((now - target).total_seconds()) < 60:
                if not self._fired_today():
                    self.mark_fired()
                    return TriggerResult(
                        should_act=True,
                        trigger_name=self.name,
                        reason=f"Time trigger: {self.at_time}",
                    )

        # Check interval
        if self.every_minutes or self.every_hours:
            interval = timedelta(
                minutes=self.every_minutes or 0,
                hours=self.every_hours or 0,
            )

            if not self.last_fired or (now - self.last_fired) >= interval:
                self.mark_fired()
                return TriggerResult(
                    should_act=True,
                    trigger_name=self.name,
                    reason=f"Interval trigger: every {interval}",
                )

        return TriggerResult(should_act=False)

    def _fired_today(self) -> bool:
        """Check if trigger already fired today."""
        if not self.last_fired:
            return False
        return self.last_fired.date() == datetime.now().date()


class EventTrigger(Trigger):
    """
    Event-based trigger.

    Fires when specific events occur (file changes, webhooks, etc.)
    """

    def __init__(
        self,
        name: str,
        event_type: str,
        event_source: Optional[str] = None,
        cooldown_seconds: int = 60,
    ):
        super().__init__(name)
        self.event_type = event_type
        self.event_source = event_source
        self.cooldown_seconds = cooldown_seconds
        self.pending_events: List[Dict] = []

    def check(self, intention) -> TriggerResult:
        """Check if there are pending events matching this trigger."""
        if not self.pending_events:
            return TriggerResult(should_act=False)

        # Check cooldown
        if self.last_fired:
            elapsed = (datetime.now() - self.last_fired).total_seconds()
            if elapsed < self.cooldown_seconds:
                return TriggerResult(should_act=False)

        # Find matching event
        for event in self.pending_events:
            if event.get("type") == self.event_type:
                if not self.event_source or event.get("source") == self.event_source:
                    self.pending_events.remove(event)
                    self.mark_fired()
                    return TriggerResult(
                        should_act=True,
                        trigger_name=self.name,
                        reason=f"Event: {self.event_type}",
                        priority_boost=2,
                    )

        return TriggerResult(should_act=False)

    def add_event(self, event: Dict):
        """Add an event to the pending queue."""
        self.pending_events.append({
            **event,
            "received_at": datetime.now(),
        })


class ConditionTrigger(Trigger):
    """
    Condition-based trigger.

    Fires when certain conditions in memory/state are met.
    """

    def __init__(
        self,
        name: str,
        condition_type: str,
        threshold: Optional[float] = None,
        check_function: Optional[callable] = None,
    ):
        super().__init__(name)
        self.condition_type = condition_type
        self.threshold = threshold
        self.check_function = check_function
        self.state: Dict[str, Any] = {}

    def check(self, intention) -> TriggerResult:
        """Check if condition is met."""
        if self.check_function:
            try:
                result = self.check_function(intention, self.state)
                if result:
                    self.mark_fired()
                    return TriggerResult(
                        should_act=True,
                        trigger_name=self.name,
                        reason=f"Condition met: {self.condition_type}",
                    )
            except Exception as e:
                logger.error(f"Condition check failed: {e}")

        # Built-in conditions
        if self.condition_type == "high_priority":
            if intention.priority >= (self.threshold or 8):
                self.mark_fired()
                return TriggerResult(
                    should_act=True,
                    trigger_name=self.name,
                    reason=f"High priority: {intention.priority}",
                )

        elif self.condition_type == "stale":
            # Check if intention has been pending too long
            stale_hours = self.threshold or 24
            age = datetime.now() - intention.created_at
            if age > timedelta(hours=stale_hours):
                self.mark_fired()
                return TriggerResult(
                    should_act=True,
                    trigger_name=self.name,
                    reason=f"Stale intention: {age.total_seconds()/3600:.1f}h old",
                )

        return TriggerResult(should_act=False)

    def update_state(self, key: str, value: Any):
        """Update trigger state for condition checking."""
        self.state[key] = value


class TriggerSystem:
    """
    Manages all triggers for the autonomous brain.
    """

    def __init__(self):
        self.triggers: List[Trigger] = []
        self._init_default_triggers()

    def _init_default_triggers(self):
        """Set up default triggers."""
        # High priority intentions should always trigger
        self.triggers.append(
            ConditionTrigger(
                name="high_priority",
                condition_type="high_priority",
                threshold=8,
            )
        )

        # Stale intentions (>24h) should trigger
        self.triggers.append(
            ConditionTrigger(
                name="stale_intention",
                condition_type="stale",
                threshold=24,
            )
        )

        # Morning check (9 AM daily)
        self.triggers.append(
            TimeTrigger(
                name="morning_check",
                at_time=time(9, 0),
            )
        )

        # Evening review (6 PM daily)
        self.triggers.append(
            TimeTrigger(
                name="evening_review",
                at_time=time(18, 0),
            )
        )

    def check(self, intention) -> TriggerResult:
        """Check all triggers for an intention."""
        # Check intention-specific triggers first
        for trigger_config in intention.triggers:
            # Create trigger from config
            trigger = self._trigger_from_config(trigger_config)
            if trigger:
                result = trigger.check(intention)
                if result.should_act:
                    return result

        # Check global triggers
        for trigger in self.triggers:
            result = trigger.check(intention)
            if result.should_act:
                return result

        return TriggerResult(should_act=False)

    def _trigger_from_config(self, config: Dict) -> Optional[Trigger]:
        """Create a trigger from configuration dict."""
        trigger_type = config.get("type")

        if trigger_type == "time":
            return TimeTrigger(
                name=config.get("name", "custom_time"),
                at_time=config.get("at_time"),
                every_minutes=config.get("every_minutes"),
                every_hours=config.get("every_hours"),
            )

        elif trigger_type == "event":
            return EventTrigger(
                name=config.get("name", "custom_event"),
                event_type=config.get("event_type"),
                event_source=config.get("event_source"),
            )

        elif trigger_type == "condition":
            return ConditionTrigger(
                name=config.get("name", "custom_condition"),
                condition_type=config.get("condition_type"),
                threshold=config.get("threshold"),
            )

        return None

    def add_trigger(self, trigger: Trigger):
        """Add a custom trigger."""
        self.triggers.append(trigger)

    def remove_trigger(self, name: str):
        """Remove a trigger by name."""
        self.triggers = [t for t in self.triggers if t.name != name]

    def get_trigger(self, name: str) -> Optional[Trigger]:
        """Get a trigger by name."""
        for trigger in self.triggers:
            if trigger.name == name:
                return trigger
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get trigger statistics."""
        return {
            "total_triggers": len(self.triggers),
            "trigger_stats": [
                {
                    "name": t.name,
                    "type": type(t).__name__,
                    "fire_count": t.fire_count,
                    "last_fired": t.last_fired.isoformat() if t.last_fired else None,
                }
                for t in self.triggers
            ],
        }
