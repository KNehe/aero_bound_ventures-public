"""
Google OAuth2 Authentication Router

This module handles Google OAuth2 login flow:
1. GET /auth/google - Redirects user to Google consent screen
2. GET /auth/google/callback - Handles callback, creates/finds user, returns JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session
import httpx
import os
from urllib.parse import urlencode, quote
import base64

from backend.crud.database import get_session
from backend.crud.users import (
    get_user_by_email,
    get_user_by_google_id,
    create_google_user,
    link_google_account,
)
from backend.utils.security import create_access_token
from backend.utils.cookies import get_cookie_settings, get_cookie_domain
from backend.schemas.auth import UserResponse, GroupResponse
from backend.utils.log_manager import get_app_logger

router = APIRouter(prefix="/auth", tags=["oauth"])
logger = get_app_logger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login(redirect: str | None = None):
    """
    Redirect to Google OAuth2 consent screen.
    """
    if not GOOGLE_CLIENT_ID:
        logger.error("Google OAuth is not configured: Missing GOOGLE_CLIENT_ID")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )

    # Encode redirect URL in state parameter
    state = base64.urlsafe_b64encode((redirect or "/").encode()).decode()
    logger.info(f"Initiating Google login with redirect state: {redirect or '/'}")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_session),
):
    """
    Handle Google OAuth2 callback.

    1. Exchange code for access token
    2. Fetch user info from Google
    3. Create or find user in database
    4. Return JWT token via redirect to frontend
    """
    if error:
        logger.error(f"Google OAuth callback error: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/login?error={error}")

    if not code:
        logger.error("Google OAuth callback missing code")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/login?error=no_code")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            logger.error(f"Failed to exchange code for token: {token_response.text}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/auth/login?error=token_exchange_failed"
            )

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        # Fetch user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )

        if userinfo_response.status_code != 200:
            logger.error(
                f"Failed to fetch user info from Google: {userinfo_response.text}"
            )
            return RedirectResponse(
                url=f"{FRONTEND_URL}/auth/login?error=userinfo_failed"
            )

        userinfo = userinfo_response.json()

    google_id = userinfo.get("id")
    email = userinfo.get("email")

    if not email or not google_id:
        logger.error("Google user info missing email or id")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/login?error=missing_email")

    user = get_user_by_google_id(db, google_id)

    if not user:
        user = get_user_by_email(db, email)
        if user:
            logger.info(f"Linking existing user {email} to Google account")
            user = link_google_account(db, user, google_id)
        else:
            logger.info(f"Creating new user from Google: {email}")
            user = create_google_user(db, email, google_id)
    else:
        logger.info(f"User logged in via Google: {email}")

    jwt_token = create_access_token(data={"sub": user.email})

    groups = [GroupResponse(id=str(g.id), name=g.name) for g in user.groups]
    user_data = UserResponse(
        id=str(user.id),
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        auth_provider=user.auth_provider,
        groups=groups,
    )

    # Decode redirect URL from state
    redirect_to = "/"
    if state:
        try:
            redirect_to = base64.urlsafe_b64decode(state.encode()).decode()
            logger.debug(f"Decoded redirect target from state: {redirect_to}")
        except Exception as e:
            logger.warning(f"Failed to decode state '{state}': {e}")
            redirect_to = "/"

    redirect_url = f"{FRONTEND_URL}/auth/google/callback?user={user_data.model_dump_json()}&redirect={quote(redirect_to)}"
    response = RedirectResponse(url=redirect_url)

    cookie_settings = get_cookie_settings()
    cookie_domain = get_cookie_domain()
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=cookie_settings["httponly"],
        secure=cookie_settings["secure"],
        samesite=cookie_settings["samesite"],
        max_age=cookie_settings["max_age"],
        domain=cookie_domain,
    )

    return response
