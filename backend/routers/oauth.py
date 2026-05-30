"""
Google OAuth2 Authentication Router

This module handles Google OAuth2 login flow:
1. GET /auth/google - Redirects user to Google consent screen
2. GET /auth/google/callback - Handles callback, creates/finds user, returns JWT
"""

import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from backend.application.oauth.oauth_login import (
    OAuthAuthorizationCodeMissing,
    OAuthNotConfigured,
    OAuthProviderReturnedError,
    OAuthTokenExchangeFailed,
    OAuthUserInfoFetchFailed,
    OAuthUserInfoIncomplete,
    OAuthUserRecord,
    ProcessOAuthCallback,
    StartOAuthLogin,
)
from backend.crud.database import get_session
from backend.infrastructure.oauth.google_oauth_provider import (
    GoogleOAuthProvider,
    GoogleOAuthSettings,
)
from backend.infrastructure.oauth.sqlmodel_oauth_user_repository import (
    SqlModelOAuthUserRepository,
)
from backend.infrastructure.users.security_user_credentials import (
    JwtAccessTokenProvider,
)
from backend.schemas.auth import GroupResponse, UserResponse
from backend.utils.cookies import get_cookie_domain, get_cookie_settings
from backend.utils.log_manager import get_app_logger

router = APIRouter(prefix="/auth", tags=["oauth"])
logger = get_app_logger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_oauth_settings() -> GoogleOAuthSettings:
    return GoogleOAuthSettings(
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        redirect_uri=os.getenv(
            "GOOGLE_REDIRECT_URI",
            "http://localhost:8000/auth/google/callback",
        ),
        auth_url=GOOGLE_AUTH_URL,
        token_url=GOOGLE_TOKEN_URL,
        userinfo_url=GOOGLE_USERINFO_URL,
    )


def get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


def get_start_google_login_use_case(
    settings: GoogleOAuthSettings = Depends(get_google_oauth_settings),
) -> StartOAuthLogin:
    return StartOAuthLogin(
        oauth_provider=GoogleOAuthProvider(settings),
    )


def get_process_google_callback_use_case(
    session: Session = Depends(get_session),
    settings: GoogleOAuthSettings = Depends(get_google_oauth_settings),
) -> ProcessOAuthCallback:
    return ProcessOAuthCallback(
        oauth_provider=GoogleOAuthProvider(settings),
        user_repository=SqlModelOAuthUserRepository(session),
        access_token_provider=JwtAccessTokenProvider(),
    )


def _to_user_response(user: OAuthUserRecord) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        auth_provider=user.auth_provider,
        groups=[
            GroupResponse(id=str(group.id), name=group.name) for group in user.groups
        ],
    )


def _frontend_error_redirect(error: str) -> RedirectResponse:
    return RedirectResponse(url=f"{get_frontend_url()}/auth/login?error={error}")


@router.get("/google")
async def google_login(
    redirect: str | None = None,
    start_google_login_use_case: StartOAuthLogin = Depends(
        get_start_google_login_use_case
    ),
):
    """
    Redirect to Google OAuth2 consent screen.
    """
    try:
        authorization_url = start_google_login_use_case.execute(redirect=redirect)
    except OAuthNotConfigured:
        logger.error("Google OAuth is not configured: Missing GOOGLE_CLIENT_ID")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )

    logger.info(f"Initiating Google login with redirect state: {redirect or '/'}")
    return RedirectResponse(url=authorization_url.url)


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    process_google_callback_use_case: ProcessOAuthCallback = Depends(
        get_process_google_callback_use_case
    ),
):
    """
    Handle Google OAuth2 callback.
    """
    try:
        result = await process_google_callback_use_case.execute(
            code=code,
            error=error,
            state=state,
        )
    except OAuthProviderReturnedError as exc:
        logger.error(f"Google OAuth callback error: {exc.error}")
        return _frontend_error_redirect(exc.error)
    except OAuthAuthorizationCodeMissing:
        logger.error("Google OAuth callback missing code")
        return _frontend_error_redirect("no_code")
    except OAuthTokenExchangeFailed as exc:
        logger.error(f"Failed to exchange code for token: {str(exc)}")
        return _frontend_error_redirect("token_exchange_failed")
    except OAuthUserInfoFetchFailed as exc:
        logger.error(f"Failed to fetch user info from Google: {str(exc)}")
        return _frontend_error_redirect("userinfo_failed")
    except OAuthUserInfoIncomplete:
        logger.error("Google user info missing email or id")
        return _frontend_error_redirect("missing_email")

    user_data = _to_user_response(result.user)
    redirect_url = (
        f"{get_frontend_url()}/auth/google/callback"
        f"?user={quote(user_data.model_dump_json())}"
        f"&redirect={quote(result.redirect_to)}"
    )
    response = RedirectResponse(url=redirect_url)

    cookie_settings = get_cookie_settings()
    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=cookie_settings["httponly"],
        secure=cookie_settings["secure"],
        samesite=cookie_settings["samesite"],
        max_age=cookie_settings["max_age"],
        domain=get_cookie_domain(),
    )

    return response
