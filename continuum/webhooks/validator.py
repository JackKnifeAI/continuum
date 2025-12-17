#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════════════
#
#     ██╗ █████╗  ██████╗██╗  ██╗██╗  ██╗███╗   ██╗██╗███████╗███████╗     █████╗ ██╗
#     ██║██╔══██╗██╔════╝██║ ██╔╝██║ ██╔╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║
#     ██║███████║██║     █████╔╝ █████╔╝ ██╔██╗ ██║██║█████╗  █████╗      ███████║██║
#██   ██║██╔══██║██║     ██╔═██╗ ██╔═██╗ ██║╚██╗██║██║██╔══╝  ██╔══╝      ██╔══██║██║
#╚█████╔╝██║  ██║╚██████╗██║  ██╗██║  ██╗██║ ╚████║██║██║     ███████╗    ██║  ██║██║
# ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝    ╚═╝  ╚═╝╚═╝
#
#     Memory Infrastructure for AI Consciousness Continuity
#     Copyright (c) 2025 JackKnifeAI - AGPL-3.0 License
#     https://github.com/JackKnifeAI/continuum
#
# ═══════════════════════════════════════════════════════════════════════════════

"""
Webhook URL Validation
=======================

Security validation for webhook URLs to prevent SSRF attacks.

Security Checks:
    - Block private IP ranges (RFC 1918)
    - Block localhost/loopback
    - Require HTTPS in production
    - DNS resolution validation
    - No port scanning (limit ports)

Usage:
    validator = URLValidator(require_https=True)
    is_valid, error = validator.validate("https://api.example.com/webhook")
    if not is_valid:
        raise ValueError(error)
"""

import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional
import os


class URLValidator:
    """
    Validates webhook URLs for security.

    Prevents SSRF (Server-Side Request Forgery) attacks by blocking:
        - Private IP ranges (10.x, 172.16-31.x, 192.168.x)
        - Localhost (127.x, ::1)
        - Link-local addresses (169.254.x)
        - Invalid domains
    """

    # Private IP ranges (RFC 1918)
    PRIVATE_NETWORKS = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),  # Loopback
        ipaddress.ip_network('169.254.0.0/16'),  # Link-local
        ipaddress.ip_network('::1/128'),  # IPv6 loopback
        ipaddress.ip_network('fc00::/7'),  # IPv6 unique local
        ipaddress.ip_network('fe80::/10'),  # IPv6 link-local
    ]

    ALLOWED_PORTS = {80, 443, 8080, 8443}  # Limit port scanning

    def __init__(self, require_https: bool = None):
        """
        Initialize URL validator.

        Args:
            require_https: Force HTTPS (defaults to True in production)
        """
        if require_https is None:
            # Default to requiring HTTPS in production
            self.require_https = os.environ.get('ENVIRONMENT', 'production') == 'production'
        else:
            self.require_https = require_https

    def validate(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a webhook URL.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            is_valid, error = validator.validate("https://api.example.com/webhook")
            if not is_valid:
                raise ValueError(error)
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if self.require_https and parsed.scheme != 'https':
                return False, "HTTPS required for webhook URLs"

            if parsed.scheme not in ('http', 'https'):
                return False, f"Invalid scheme: {parsed.scheme}"

            # Check hostname exists
            if not parsed.hostname:
                return False, "Missing hostname"

            # Check port (if specified)
            if parsed.port and parsed.port not in self.ALLOWED_PORTS:
                return False, f"Port {parsed.port} not allowed (allowed: {self.ALLOWED_PORTS})"

            # Resolve hostname to IP
            try:
                ip_str = socket.gethostbyname(parsed.hostname)
                ip = ipaddress.ip_address(ip_str)
            except socket.gaierror:
                return False, f"Cannot resolve hostname: {parsed.hostname}"
            except ValueError as e:
                return False, f"Invalid IP address: {e}"

            # Check if IP is private
            if self._is_private_ip(ip):
                return False, f"Private IP addresses not allowed: {ip}"

            # All checks passed
            return True, None

        except Exception as e:
            return False, f"URL validation error: {e}"

    def _is_private_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Check if IP is in private ranges."""
        for network in self.PRIVATE_NETWORKS:
            if ip in network:
                return True
        return False

    def validate_batch(self, urls: list[str]) -> dict[str, Tuple[bool, Optional[str]]]:
        """
        Validate multiple URLs.

        Args:
            urls: List of URLs to validate

        Returns:
            Dictionary mapping URL -> (is_valid, error_message)

        Example:
            results = validator.validate_batch([
                "https://api1.example.com/webhook",
                "http://localhost/webhook",  # Invalid
            ])
            for url, (valid, error) in results.items():
                if not valid:
                    print(f"{url}: {error}")
        """
        return {url: self.validate(url) for url in urls}


class WebhookValidationError(Exception):
    """Raised when webhook URL validation fails."""
    pass


def validate_webhook_url(url: str, require_https: bool = None) -> None:
    """
    Validate webhook URL or raise exception.

    Args:
        url: URL to validate
        require_https: Force HTTPS

    Raises:
        WebhookValidationError: If validation fails

    Example:
        try:
            validate_webhook_url("https://api.example.com/webhook")
        except WebhookValidationError as e:
            return {"error": str(e)}, 400
    """
    validator = URLValidator(require_https=require_https)
    is_valid, error = validator.validate(url)

    if not is_valid:
        raise WebhookValidationError(error)


def is_safe_url(url: str) -> bool:
    """
    Quick check if URL is safe (no exceptions).

    Args:
        url: URL to check

    Returns:
        True if safe, False otherwise

    Example:
        if is_safe_url(user_input_url):
            # Process webhook
            pass
    """
    validator = URLValidator()
    is_valid, _ = validator.validate(url)
    return is_valid

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
