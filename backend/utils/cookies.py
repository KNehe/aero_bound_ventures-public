"""
Cookie utility functions for HTTP-only cookie authentication.

This module provides environment-aware cookie settings that work for both
development (HTTP) and production (HTTPS) environments.
"""

import os
from typing import TypedDict


class CookieSettings(TypedDict):
    httponly: bool
    secure: bool
    samesite: str
    max_age: int


def is_production() -> bool:
    """Check if we're running in production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def get_cookie_settings() -> CookieSettings:
    """
    Get cookie settings based on environment.
    
    Returns:
        CookieSettings with appropriate values for the current environment:
        - Development: secure=False (works with HTTP on localhost)
        - Production: secure=True (requires HTTPS)
    """
    is_prod = is_production()
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    
    return CookieSettings(
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=access_token_expire_minutes * 60,
    )


def get_cookie_domain() -> str | None:
    """
    Get cookie domain based on environment.
    
    Returns:
        Domain string for production, None for development (localhost).
    """
    if is_production():
        return os.getenv("COOKIE_DOMAIN", None)
    return None
