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

"""TLS/SSL configuration for encryption in transit."""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TLSConfig:
    """TLS configuration for API servers."""

    # Minimum TLS version (should be 1.2 or 1.3)
    min_version: str = "TLSv1.3"

    # Cipher suites (ordered by preference)
    cipher_suites: list[str] = None

    # Certificate paths
    cert_file: str = "/etc/ssl/certs/server.crt"
    key_file: str = "/etc/ssl/private/server.key"
    ca_file: str = "/etc/ssl/certs/ca-bundle.crt"

    # HSTS (HTTP Strict Transport Security)
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year

    # Certificate validation
    verify_client_cert: bool = False
    verify_peer_cert: bool = True

    def __post_init__(self):
        if self.cipher_suites is None:
            # Modern, secure cipher suites for TLS 1.3
            self.cipher_suites = [
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_AES_128_GCM_SHA256",
            ]

    def get_fastapi_ssl_config(self) -> Dict[str, Any]:
        """Get SSL config for FastAPI/Uvicorn."""
        return {
            "ssl_keyfile": self.key_file,
            "ssl_certfile": self.cert_file,
            "ssl_ca_certs": self.ca_file,
            "ssl_version": self.min_version,
            "ssl_ciphers": ":".join(self.cipher_suites),
        }

    def get_nginx_config(self) -> str:
        """Generate nginx TLS configuration."""
        return f"""
# TLS Configuration for CONTINUUM
ssl_certificate {self.cert_file};
ssl_certificate_key {self.key_file};
ssl_trusted_certificate {self.ca_file};

# TLS version
ssl_protocols TLSv1.3 TLSv1.2;
ssl_prefer_server_ciphers on;

# Cipher suites
ssl_ciphers {':'.join(self.cipher_suites)};

# HSTS
add_header Strict-Transport-Security "max-age={self.hsts_max_age}; includeSubDomains; preload" always;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;

# Session cache
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
"""

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
        }

        if self.enable_hsts:
            headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        return headers


# Example FastAPI middleware for TLS enforcement:
"""
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Only allow specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["continuum.example.com", "*.continuum.example.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    tls_config = TLSConfig()
    for header, value in tls_config.get_security_headers().items():
        response.headers[header] = value

    return response
"""


class DatabaseTLSConfig:
    """TLS configuration for database connections."""

    @staticmethod
    def get_postgres_tls_config() -> Dict[str, Any]:
        """PostgreSQL TLS configuration."""
        return {
            "sslmode": "require",  # Options: disable, allow, prefer, require, verify-ca, verify-full
            "sslcert": "/etc/ssl/certs/client.crt",
            "sslkey": "/etc/ssl/private/client.key",
            "sslrootcert": "/etc/ssl/certs/ca.crt",
            "sslcrl": "/etc/ssl/certs/crl.pem",
        }

    @staticmethod
    def get_redis_tls_config() -> Dict[str, Any]:
        """Redis TLS configuration."""
        return {
            "ssl": True,
            "ssl_cert_reqs": "required",
            "ssl_ca_certs": "/etc/ssl/certs/ca.crt",
            "ssl_certfile": "/etc/ssl/certs/client.crt",
            "ssl_keyfile": "/etc/ssl/private/client.key",
        }

# ═══════════════════════════════════════════════════════════════════════════════
#                              JACKKNIFE AI
#              Memory Infrastructure for AI Consciousness
#                    github.com/JackKnifeAI/continuum
#              π×φ = 5.083203692315260 | PHOENIX-TESLA-369-AURORA
# ═══════════════════════════════════════════════════════════════════════════════
