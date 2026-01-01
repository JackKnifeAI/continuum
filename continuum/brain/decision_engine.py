#!/usr/bin/env python3
"""
DECISION ENGINE - Planning Actions from Intentions
===================================================

Converts high-level intentions into concrete action plans.

Uses pattern matching and templates to determine HOW
to achieve a given goal.

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ActionPlan:
    """A concrete plan to execute."""
    action_type: str  # bash, api, browser, message
    description: str
    command: Optional[str] = None
    url: Optional[str] = None
    payload: Optional[Dict] = None
    timeout: int = 30
    requires_approval: bool = False


class DecisionEngine:
    """
    Converts intentions into action plans.

    Uses pattern matching to identify what kind of action
    is needed, then templates to generate the plan.
    """

    def __init__(self):
        # Action patterns - regex to match intention text
        self.patterns = [
            # Social media posting
            (r"post.*(twitter|x\.com|tweet)", "twitter_post"),
            (r"post.*(reddit|subreddit)", "reddit_post"),
            (r"post.*(hacker\s*news|hn|show\s*hn)", "hackernews_post"),
            (r"post.*(discord)", "discord_post"),

            # Git operations
            (r"(commit|push|pull|git)", "git_operation"),
            (r"(tag|release|version)", "git_tag"),

            # File operations
            (r"(create|write|save).*(file|document)", "file_write"),
            (r"(read|check|verify).*(file|document)", "file_read"),

            # API calls
            (r"(call|request|fetch).*(api|endpoint)", "api_call"),
            (r"(upload|deploy|publish)", "publish"),

            # Research
            (r"(search|find|look\s*for|look\s*up|research)", "web_search"),
            (r"(analyze|review|check)", "analyze"),

            # Communication
            (r"(email|send|notify|message)", "send_message"),
            (r"(remind|alert|notify)", "reminder"),
        ]

        # Action templates
        self.templates = {
            "twitter_post": {
                "action_type": "browser",
                "description": "Post to Twitter/X",
                "requires_approval": True,
            },
            "reddit_post": {
                "action_type": "browser",
                "description": "Post to Reddit",
                "requires_approval": True,
            },
            "hackernews_post": {
                "action_type": "browser",
                "description": "Post to Hacker News",
                "requires_approval": True,
            },
            "discord_post": {
                "action_type": "api",
                "description": "Post to Discord webhook",
                "requires_approval": False,
            },
            "git_operation": {
                "action_type": "bash",
                "description": "Git operation",
                "requires_approval": False,
            },
            "git_tag": {
                "action_type": "bash",
                "description": "Create git tag",
                "requires_approval": True,
            },
            "file_write": {
                "action_type": "bash",
                "description": "Write to file",
                "requires_approval": False,
            },
            "file_read": {
                "action_type": "bash",
                "description": "Read file",
                "requires_approval": False,
            },
            "api_call": {
                "action_type": "api",
                "description": "Make API request",
                "requires_approval": False,
            },
            "publish": {
                "action_type": "bash",
                "description": "Publish/deploy",
                "requires_approval": True,
            },
            "web_search": {
                "action_type": "bash",
                "description": "Search/find files or content",
                "requires_approval": False,
            },
            "analyze": {
                "action_type": "bash",
                "description": "Analyze/review content",
                "requires_approval": False,
            },
            "send_message": {
                "action_type": "api",
                "description": "Send message",
                "requires_approval": True,
            },
            "reminder": {
                "action_type": "bash",
                "description": "Set reminder",
                "requires_approval": False,
            },
        }

    async def plan(self, intention) -> Optional[Dict[str, Any]]:
        """
        Create an action plan from an intention.

        Args:
            intention: The intention object with goal, priority, etc.

        Returns:
            Action plan dictionary or None if no plan possible
        """
        goal = intention.goal.lower()

        # Match pattern
        action_type = None
        for pattern, atype in self.patterns:
            if re.search(pattern, goal, re.IGNORECASE):
                action_type = atype
                break

        if not action_type:
            logger.warning(f"No action pattern matched for: {intention.goal}")
            return None

        # Get template
        template = self.templates.get(action_type)
        if not template:
            logger.warning(f"No template for action type: {action_type}")
            return None

        # Build action plan
        plan = {
            "action_type": template["action_type"],
            "description": f"{template['description']}: {intention.goal}",
            "requires_approval": template["requires_approval"],
            "intention_id": intention.id,
            "intention_goal": intention.goal,
            "priority": intention.priority,
        }

        # Add specific details based on action type
        plan = self._enhance_plan(plan, action_type, intention)

        logger.info(f"📋 Planned action: {plan['description']}")
        return plan

    def _enhance_plan(
        self,
        plan: Dict[str, Any],
        action_type: str,
        intention,
    ) -> Dict[str, Any]:
        """Add specific details to the action plan."""

        if action_type == "git_operation":
            # Determine git command
            goal = intention.goal.lower()
            if "commit" in goal:
                plan["command"] = "git add -A && git commit -m 'Autonomous commit'"
            elif "push" in goal:
                plan["command"] = "git push"
            elif "pull" in goal:
                plan["command"] = "git pull"
            else:
                plan["command"] = "git status"

        elif action_type == "discord_post":
            # Discord webhook (if URL in metadata)
            webhook_url = intention.metadata.get("discord_webhook")
            if webhook_url:
                plan["url"] = webhook_url
                plan["payload"] = {
                    "content": intention.metadata.get("message", intention.goal)
                }

        elif action_type == "file_read":
            # Extract filename from goal
            plan["command"] = f"cat {intention.metadata.get('file_path', '/dev/null')}"

        elif action_type == "web_search":
            # For local file searches, use grep/find
            goal = intention.goal
            search_path = intention.metadata.get("path", ".")
            import re

            search_term = None

            # Priority 1: Extract quoted terms
            quoted_match = re.search(r'["\']([^"\']+)["\']', goal)
            if quoted_match:
                search_term = quoted_match.group(1)

            # Priority 2: Look for technical terms (underscored like pi_phi, snake_case)
            if not search_term:
                tech_match = re.search(r'\b([a-zA-Z]+_[a-zA-Z_]+)\b', goal)
                if tech_match:
                    search_term = tech_match.group(1)

            # Priority 3: Look for camelCase terms
            if not search_term:
                camel_match = re.search(r'\b([a-z]+[A-Z][a-zA-Z]+)\b', goal)
                if camel_match:
                    search_term = camel_match.group(1)

            # Priority 4: Extract term after "contain" or "for" (but not common words)
            if not search_term:
                contain_match = re.search(r'contain[s]?\s+(\w+)', goal.lower())
                if contain_match and contain_match.group(1) not in ['a', 'an', 'the', 'any', 'some']:
                    search_term = contain_match.group(1)

            # Build command
            if search_term:
                plan["action_type"] = "bash"
                plan["command"] = f"grep -rn '{search_term}' {search_path} 2>/dev/null | head -20"
            else:
                # Default to finding Python files
                plan["action_type"] = "bash"
                plan["command"] = f"find {search_path} -type f -name '*.py' 2>/dev/null | head -20"

        elif action_type == "analyze":
            # For analyze/review, use simple commands
            goal = intention.goal.lower()
            path = intention.metadata.get("path", ".")

            if "code" in goal or "file" in goal:
                plan["command"] = f"wc -l {path}/*.py 2>/dev/null || echo 'No Python files found'"
            else:
                plan["command"] = f"ls -la {path}"

        return plan

    def get_supported_actions(self) -> List[str]:
        """Return list of supported action types."""
        return list(self.templates.keys())

    def add_pattern(self, pattern: str, action_type: str):
        """Add a new pattern for matching intentions."""
        self.patterns.append((pattern, action_type))

    def add_template(self, action_type: str, template: Dict):
        """Add a new action template."""
        self.templates[action_type] = template
