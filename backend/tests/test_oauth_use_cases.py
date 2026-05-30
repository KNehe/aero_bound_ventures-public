import base64
from uuid import uuid4

import pytest

from backend.application.oauth.oauth_login import (
    ExternalOAuthUser,
    OAuthAuthorizationCodeMissing,
    OAuthGroupRecord,
    OAuthNotConfigured,
    OAuthProviderReturnedError,
    OAuthUserRecord,
    ProcessOAuthCallback,
    StartOAuthLogin,
)


USER_ID = uuid4()
GROUP_ID = uuid4()


class StubOAuthProvider:
    def __init__(self, *, configured: bool = True):
        self.configured = configured
        self.authorization_states = []
        self.fetched_codes = []
        self.external_user = ExternalOAuthUser(
            provider_user_id="google-user-1",
            email="traveler@example.com",
        )

    def is_configured(self):
        return self.configured

    def build_authorization_url(self, *, state: str):
        self.authorization_states.append(state)
        return f"https://accounts.google.com/auth?state={state}"

    async def fetch_user_info(self, *, code: str):
        self.fetched_codes.append(code)
        return self.external_user


class StubOAuthUserRepository:
    def __init__(self):
        self.users_by_provider_id = {}
        self.users_by_email = {}
        self.created_provider_users = []
        self.linked_provider_accounts = []

    def get_by_provider_user_id(self, provider_user_id: str):
        return self.users_by_provider_id.get(provider_user_id)

    def get_by_email(self, email: str):
        return self.users_by_email.get(email)

    def create_provider_user(self, *, email: str, provider_user_id: str):
        self.created_provider_users.append(
            {"email": email, "provider_user_id": provider_user_id}
        )
        return make_user(email=email, auth_provider="google")

    def link_provider_account(self, *, user_id, provider_user_id: str):
        self.linked_provider_accounts.append(
            {"user_id": user_id, "provider_user_id": provider_user_id}
        )
        return make_user(auth_provider="google")


class StubAccessTokenProvider:
    def __init__(self):
        self.subjects = []

    def create_access_token(self, *, subject: str):
        self.subjects.append(subject)
        return f"jwt:{subject}"


def make_user(*, email: str = "traveler@example.com", auth_provider: str = "email"):
    return OAuthUserRecord(
        id=USER_ID,
        email=email,
        is_active=True,
        is_superuser=False,
        auth_provider=auth_provider,
        groups=(OAuthGroupRecord(id=GROUP_ID, name="Customers"),),
    )


def test_start_oauth_login_builds_authorization_url_with_encoded_redirect():
    provider = StubOAuthProvider()
    use_case = StartOAuthLogin(oauth_provider=provider)

    result = use_case.execute(redirect="/booking/checkout")

    encoded_state = provider.authorization_states[0]
    assert base64.urlsafe_b64decode(encoded_state.encode()).decode() == (
        "/booking/checkout"
    )
    assert result.url == f"https://accounts.google.com/auth?state={encoded_state}"


def test_start_oauth_login_rejects_missing_provider_config():
    use_case = StartOAuthLogin(oauth_provider=StubOAuthProvider(configured=False))

    with pytest.raises(OAuthNotConfigured):
        use_case.execute(redirect="/")


@pytest.mark.asyncio
async def test_process_oauth_callback_links_existing_email_account():
    provider = StubOAuthProvider()
    repository = StubOAuthUserRepository()
    existing_user = make_user(auth_provider="email")
    repository.users_by_email["traveler@example.com"] = existing_user
    token_provider = StubAccessTokenProvider()
    use_case = ProcessOAuthCallback(
        oauth_provider=provider,
        user_repository=repository,
        access_token_provider=token_provider,
    )
    state = base64.urlsafe_b64encode("/dashboard".encode()).decode()

    result = await use_case.execute(code="auth-code", error=None, state=state)

    assert result.access_token == "jwt:traveler@example.com"
    assert result.redirect_to == "/dashboard"
    assert result.user.auth_provider == "google"
    assert repository.linked_provider_accounts == [
        {"user_id": USER_ID, "provider_user_id": "google-user-1"}
    ]
    assert repository.created_provider_users == []
    assert token_provider.subjects == ["traveler@example.com"]


@pytest.mark.asyncio
async def test_process_oauth_callback_uses_existing_provider_account():
    provider = StubOAuthProvider()
    repository = StubOAuthUserRepository()
    repository.users_by_provider_id["google-user-1"] = make_user(auth_provider="google")
    use_case = ProcessOAuthCallback(
        oauth_provider=provider,
        user_repository=repository,
        access_token_provider=StubAccessTokenProvider(),
    )

    result = await use_case.execute(code="auth-code", error=None, state=None)

    assert result.user.auth_provider == "google"
    assert result.redirect_to == "/"
    assert repository.linked_provider_accounts == []
    assert repository.created_provider_users == []


@pytest.mark.asyncio
async def test_process_oauth_callback_creates_provider_user_when_missing():
    provider = StubOAuthProvider()
    repository = StubOAuthUserRepository()
    use_case = ProcessOAuthCallback(
        oauth_provider=provider,
        user_repository=repository,
        access_token_provider=StubAccessTokenProvider(),
    )

    result = await use_case.execute(code="auth-code", error=None, state=None)

    assert result.user.email == "traveler@example.com"
    assert repository.created_provider_users == [
        {"email": "traveler@example.com", "provider_user_id": "google-user-1"}
    ]


@pytest.mark.asyncio
async def test_process_oauth_callback_rejects_provider_error_and_missing_code():
    use_case = ProcessOAuthCallback(
        oauth_provider=StubOAuthProvider(),
        user_repository=StubOAuthUserRepository(),
        access_token_provider=StubAccessTokenProvider(),
    )

    with pytest.raises(OAuthProviderReturnedError):
        await use_case.execute(code=None, error="access_denied", state=None)

    with pytest.raises(OAuthAuthorizationCodeMissing):
        await use_case.execute(code=None, error=None, state=None)
