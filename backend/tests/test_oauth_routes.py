from uuid import uuid4

from backend.application.oauth.oauth_login import (
    OAuthAuthorizationCodeMissing,
    OAuthAuthorizationUrl,
    OAuthCallbackResult,
    OAuthGroupRecord,
    OAuthUserRecord,
)
from backend.routers.oauth import (
    get_process_google_callback_use_case,
    get_start_google_login_use_case,
)
from tests.conftest import API_V1_PREFIX


USER_ID = uuid4()
GROUP_ID = uuid4()


class StubStartGoogleLoginUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, redirect):
        self.calls.append(redirect)
        return OAuthAuthorizationUrl(url="https://accounts.google.com/auth")


class StubProcessGoogleCallbackUseCase:
    def __init__(self, *, should_raise_missing_code: bool = False):
        self.calls = []
        self.should_raise_missing_code = should_raise_missing_code

    async def execute(self, *, code, error, state):
        self.calls.append({"code": code, "error": error, "state": state})
        if self.should_raise_missing_code:
            raise OAuthAuthorizationCodeMissing

        return OAuthCallbackResult(
            access_token="jwt-token",
            user=OAuthUserRecord(
                id=USER_ID,
                email="traveler@example.com",
                is_active=True,
                is_superuser=False,
                auth_provider="google",
                groups=(OAuthGroupRecord(id=GROUP_ID, name="Customers"),),
            ),
            redirect_to="/dashboard",
        )


def test_google_login_route_uses_start_login_use_case(client):
    use_case = StubStartGoogleLoginUseCase()
    client.app.dependency_overrides[get_start_google_login_use_case] = lambda: use_case

    try:
        response = client.get(
            f"{API_V1_PREFIX}/auth/google",
            params={"redirect": "/dashboard"},
            follow_redirects=False,
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "https://accounts.google.com/auth"
    assert use_case.calls == ["/dashboard"]


def test_google_callback_route_sets_cookie_and_redirects_to_frontend(
    client,
    monkeypatch,
):
    monkeypatch.setenv("FRONTEND_URL", "https://frontend.example.com")
    use_case = StubProcessGoogleCallbackUseCase()
    client.app.dependency_overrides[get_process_google_callback_use_case] = (
        lambda: use_case
    )

    try:
        response = client.get(
            f"{API_V1_PREFIX}/auth/google/callback",
            params={"code": "auth-code", "state": "state-value"},
            follow_redirects=False,
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code in (302, 307)
    assert response.headers["location"].startswith(
        "https://frontend.example.com/auth/google/callback?user="
    )
    assert "redirect=/dashboard" in response.headers["location"]
    assert "access_token=jwt-token" in response.headers["set-cookie"]
    assert use_case.calls == [
        {"code": "auth-code", "error": None, "state": "state-value"}
    ]


def test_google_callback_route_redirects_known_errors_to_login(
    client,
    monkeypatch,
):
    monkeypatch.setenv("FRONTEND_URL", "https://frontend.example.com")
    use_case = StubProcessGoogleCallbackUseCase(should_raise_missing_code=True)
    client.app.dependency_overrides[get_process_google_callback_use_case] = (
        lambda: use_case
    )

    try:
        response = client.get(
            f"{API_V1_PREFIX}/auth/google/callback",
            follow_redirects=False,
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code in (302, 307)
    assert response.headers["location"] == (
        "https://frontend.example.com/auth/login?error=no_code"
    )
