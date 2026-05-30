import base64
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class OAuthAuthorizationUrl:
    url: str


@dataclass(frozen=True)
class ExternalOAuthUser:
    provider_user_id: str
    email: str


@dataclass(frozen=True)
class OAuthGroupRecord:
    id: UUID
    name: str


@dataclass(frozen=True)
class OAuthUserRecord:
    id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    auth_provider: str
    groups: tuple[OAuthGroupRecord, ...] = ()


@dataclass(frozen=True)
class OAuthCallbackResult:
    access_token: str
    user: OAuthUserRecord
    redirect_to: str


class OAuthError(Exception):
    pass


class OAuthNotConfigured(OAuthError):
    pass


class OAuthProviderReturnedError(OAuthError):
    def __init__(self, error: str):
        self.error = error
        super().__init__(error)


class OAuthAuthorizationCodeMissing(OAuthError):
    pass


class OAuthTokenExchangeFailed(OAuthError):
    pass


class OAuthUserInfoFetchFailed(OAuthError):
    pass


class OAuthUserInfoIncomplete(OAuthError):
    pass


class OAuthIdentityProvider(Protocol):
    def is_configured(self) -> bool: ...

    def build_authorization_url(self, *, state: str) -> str: ...

    async def fetch_user_info(self, *, code: str) -> ExternalOAuthUser: ...


class OAuthUserRepository(Protocol):
    def get_by_provider_user_id(
        self, provider_user_id: str
    ) -> OAuthUserRecord | None: ...

    def get_by_email(self, email: str) -> OAuthUserRecord | None: ...

    def create_provider_user(
        self, *, email: str, provider_user_id: str
    ) -> OAuthUserRecord: ...

    def link_provider_account(
        self, *, user_id: UUID, provider_user_id: str
    ) -> OAuthUserRecord: ...


class OAuthAccessTokenProvider(Protocol):
    def create_access_token(self, *, subject: str) -> str: ...


class StartOAuthLogin:
    def __init__(self, *, oauth_provider: OAuthIdentityProvider):
        self.oauth_provider = oauth_provider

    def execute(self, *, redirect: str | None) -> OAuthAuthorizationUrl:
        if not self.oauth_provider.is_configured():
            raise OAuthNotConfigured

        state = _encode_redirect_state(redirect or "/")
        return OAuthAuthorizationUrl(
            url=self.oauth_provider.build_authorization_url(state=state)
        )


class ProcessOAuthCallback:
    def __init__(
        self,
        *,
        oauth_provider: OAuthIdentityProvider,
        user_repository: OAuthUserRepository,
        access_token_provider: OAuthAccessTokenProvider,
    ):
        self.oauth_provider = oauth_provider
        self.user_repository = user_repository
        self.access_token_provider = access_token_provider

    async def execute(
        self,
        *,
        code: str | None,
        error: str | None,
        state: str | None,
    ) -> OAuthCallbackResult:
        if error:
            raise OAuthProviderReturnedError(error)

        if not code:
            raise OAuthAuthorizationCodeMissing

        external_user = await self.oauth_provider.fetch_user_info(code=code)
        user = self.user_repository.get_by_provider_user_id(
            external_user.provider_user_id
        )

        if not user:
            user = self.user_repository.get_by_email(external_user.email)
            if user:
                user = self.user_repository.link_provider_account(
                    user_id=user.id,
                    provider_user_id=external_user.provider_user_id,
                )
            else:
                user = self.user_repository.create_provider_user(
                    email=external_user.email,
                    provider_user_id=external_user.provider_user_id,
                )

        return OAuthCallbackResult(
            access_token=self.access_token_provider.create_access_token(
                subject=user.email
            ),
            user=user,
            redirect_to=_decode_redirect_state(state),
        )


def _encode_redirect_state(redirect_to: str) -> str:
    return base64.urlsafe_b64encode(redirect_to.encode()).decode()


def _decode_redirect_state(state: str | None) -> str:
    if not state:
        return "/"

    try:
        return base64.urlsafe_b64decode(state.encode()).decode()
    except Exception:
        return "/"
