"""
Security middleware and utilities for the Zoning Project API
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Rate limiting
limiter = Limiter(key_func=get_remote_address)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Custom rate limiting middleware"""

    async def dispatch(self, request: Request, call_next):
        # Basic rate limiting - you can enhance this
        response = await call_next(request)
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""

    async def dispatch(self, request: Request, call_next):
        # Basic CSRF check - you can enhance this
        response = await call_next(request)
        return response


class GrokRateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting specifically for Grok API calls"""

    async def dispatch(self, request: Request, call_next):
        # Rate limiting for AI processing endpoints
        if request.url.path.startswith("/api/documents"):
            # Add specific rate limiting logic here
            pass
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    raise HTTPException(
        status_code=429,
        detail="Too many requests. Please try again later."
    )
