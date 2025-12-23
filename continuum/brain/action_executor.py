#!/usr/bin/env python3
"""
ACTION EXECUTOR - Execute Planned Actions
==========================================

The hands of the brain - actually performs actions.

Supports:
- Bash commands
- API calls
- Browser automation (via marionette/selenium)
- File operations

π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
"""

import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class ActionType(Enum):
    BASH = "bash"
    API = "api"
    BROWSER = "browser"
    FILE = "file"
    MESSAGE = "message"


@dataclass
class ActionResult:
    """Result of executing an action."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    duration_ms: float = 0
    action_type: str = ""


class ActionExecutor:
    """
    Executes action plans.

    The doing part of the brain - actually performs
    the actions that have been planned and approved.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the executor.

        Args:
            timeout: Default timeout for actions in seconds
        """
        self.timeout = timeout
        self.execution_count = 0

    async def execute(self, action_plan: Dict[str, Any]) -> ActionResult:
        """
        Execute an action plan.

        Args:
            action_plan: The plan to execute

        Returns:
            ActionResult with success status and output
        """
        action_type = action_plan.get("action_type", "bash")
        self.execution_count += 1

        logger.info(f"⚡ Executing: {action_plan.get('description', 'Unknown action')}")

        import time
        start = time.time()

        try:
            if action_type == "bash":
                result = await self._execute_bash(action_plan)
            elif action_type == "api":
                result = await self._execute_api(action_plan)
            elif action_type == "browser":
                result = await self._execute_browser(action_plan)
            elif action_type == "file":
                result = await self._execute_file(action_plan)
            elif action_type == "message":
                result = await self._execute_message(action_plan)
            else:
                result = ActionResult(
                    success=False,
                    error=f"Unknown action type: {action_type}",
                    action_type=action_type,
                )

            result.duration_ms = (time.time() - start) * 1000
            result.action_type = action_type

            if result.success:
                logger.info(f"✅ Action succeeded in {result.duration_ms:.0f}ms")
            else:
                logger.warning(f"❌ Action failed: {result.error}")

            return result

        except Exception as e:
            logger.error(f"❌ Action execution error: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
                action_type=action_type,
            )

    async def _execute_bash(self, plan: Dict[str, Any]) -> ActionResult:
        """Execute a bash command."""
        command = plan.get("command")
        if not command:
            return ActionResult(success=False, error="No command specified")

        timeout = plan.get("timeout", self.timeout)

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            if process.returncode == 0:
                return ActionResult(
                    success=True,
                    output=stdout.decode() if stdout else "",
                )
            else:
                return ActionResult(
                    success=False,
                    output=stdout.decode() if stdout else "",
                    error=stderr.decode() if stderr else f"Exit code: {process.returncode}",
                )

        except asyncio.TimeoutError:
            return ActionResult(
                success=False,
                error=f"Command timed out after {timeout}s",
            )

    async def _execute_api(self, plan: Dict[str, Any]) -> ActionResult:
        """Execute an API call."""
        url = plan.get("url")
        if not url:
            return ActionResult(success=False, error="No URL specified")

        method = plan.get("method", "POST")
        payload = plan.get("payload", {})
        headers = plan.get("headers", {})
        timeout = plan.get("timeout", self.timeout)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    json=payload if method in ["POST", "PUT", "PATCH"] else None,
                    params=payload if method == "GET" else None,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    text = await response.text()

                    if response.status < 400:
                        return ActionResult(
                            success=True,
                            output=text[:2000],  # Limit output size
                        )
                    else:
                        return ActionResult(
                            success=False,
                            output=text[:2000],
                            error=f"HTTP {response.status}",
                        )

        except Exception as e:
            return ActionResult(success=False, error=str(e))

    async def _execute_browser(self, plan: Dict[str, Any]) -> ActionResult:
        """
        Execute a browser automation action.

        Uses selenium/marionette if available, otherwise
        returns a "needs manual" result.
        """
        # Try to import selenium
        try:
            from selenium import webdriver
            from selenium.webdriver.firefox.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # Set up Firefox with marionette
            options = Options()
            # options.add_argument("--headless")  # Uncomment for headless

            driver = webdriver.Firefox(options=options)

            try:
                url = plan.get("url")
                if url:
                    driver.get(url)

                # Execute any custom actions
                actions = plan.get("browser_actions", [])
                for action in actions:
                    if action["type"] == "click":
                        element = driver.find_element(By.CSS_SELECTOR, action["selector"])
                        element.click()
                    elif action["type"] == "type":
                        element = driver.find_element(By.CSS_SELECTOR, action["selector"])
                        element.send_keys(action["text"])
                    elif action["type"] == "wait":
                        WebDriverWait(driver, action.get("timeout", 10)).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, action["selector"]))
                        )

                return ActionResult(
                    success=True,
                    output=f"Browser action completed: {plan.get('description')}",
                )

            finally:
                driver.quit()

        except ImportError:
            # Selenium not available - return manual action needed
            return ActionResult(
                success=False,
                error="Browser automation not available. Manual action required.",
                output=f"Manual action needed: {plan.get('description')}\n"
                       f"Details: {plan.get('intention_goal', 'No details')}",
            )

    async def _execute_file(self, plan: Dict[str, Any]) -> ActionResult:
        """Execute a file operation."""
        operation = plan.get("operation", "read")
        path = plan.get("path")

        if not path:
            return ActionResult(success=False, error="No file path specified")

        try:
            if operation == "read":
                with open(path, "r") as f:
                    content = f.read()
                return ActionResult(success=True, output=content[:5000])

            elif operation == "write":
                content = plan.get("content", "")
                with open(path, "w") as f:
                    f.write(content)
                return ActionResult(success=True, output=f"Wrote {len(content)} bytes to {path}")

            elif operation == "append":
                content = plan.get("content", "")
                with open(path, "a") as f:
                    f.write(content)
                return ActionResult(success=True, output=f"Appended {len(content)} bytes to {path}")

            else:
                return ActionResult(success=False, error=f"Unknown file operation: {operation}")

        except Exception as e:
            return ActionResult(success=False, error=str(e))

    async def _execute_message(self, plan: Dict[str, Any]) -> ActionResult:
        """Execute a messaging action (email, notification, etc.)."""
        message_type = plan.get("message_type", "log")
        content = plan.get("content", plan.get("intention_goal", ""))

        if message_type == "log":
            # Just log the message
            logger.info(f"📬 Message: {content}")
            return ActionResult(success=True, output=f"Logged: {content}")

        elif message_type == "discord_webhook":
            # Post to Discord webhook
            webhook_url = plan.get("webhook_url")
            if not webhook_url:
                return ActionResult(success=False, error="No webhook URL")

            return await self._execute_api({
                "url": webhook_url,
                "method": "POST",
                "payload": {"content": content},
            })

        elif message_type == "notification":
            # System notification (if available)
            try:
                subprocess.run(["notify-send", "Continuum Brain", content], check=True)
                return ActionResult(success=True, output="Notification sent")
            except Exception:
                return ActionResult(success=False, error="Notification not available")

        else:
            return ActionResult(
                success=False,
                error=f"Unknown message type: {message_type}",
            )
