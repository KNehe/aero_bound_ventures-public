from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from backend.application.oauth.oauth_login import (
    ExternalOAuthUser,
    OAuthTokenExchangeFailed,
    OAuthUserInfoFetchFailed,
    OAuthUserInfoIncomplete,
)


@dataclass(frozen=True)
class GoogleOAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    token_url: str
    userinfo_url: str


class GoogleOAuthProvider:
    def __init__(self, settings: GoogleOAuthSettings):
        self.settings = settings

    def is_configured(self) -> bool:
        return bool(self.settings.client_id)

    def build_authorization_url(self, *, state: str) -> str:
        params = {
            "client_id": self.settings.client_id,
            "redirect_uri": self.settings.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{self.settings.auth_url}?{urlencode(params)}"

    async def fetch_user_info(self, *, code: str) -> ExternalOAuthUser:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                self.settings.token_url,
                data={
                    "code": code,
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                    "redirect_uri": self.settings.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise OAuthTokenExchangeFailed(token_response.text)

            access_token = token_response.json().get("access_token")
            userinfo_response = await client.get(
                self.settings.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if userinfo_response.status_code != 200:
                raise OAuthUserInfoFetchFailed(userinfo_response.text)

            userinfo = userinfo_response.json()

        provider_user_id = userinfo.get("id")
        email = userinfo.get("email")

        if not email or not provider_user_id:
            raise OAuthUserInfoIncomplete

        return ExternalOAuthUser(
            provider_user_id=str(provider_user_id),
            email=str(email),
        )
