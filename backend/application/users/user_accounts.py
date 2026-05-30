from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class PermissionRecord:
    name: str
    codename: str
    description: str | None = None


@dataclass(frozen=True)
class GroupRecord:
    name: str
    description: str | None = None
    permissions: tuple[PermissionRecord, ...] = ()


@dataclass(frozen=True)
class UserAccountRecord:
    id: UUID
    email: str
    auth_provider: str = "email"


@dataclass(frozen=True)
class AuthenticatedUserRecord(UserAccountRecord):
    password_hash: str | None = None
    groups: tuple[GroupRecord, ...] = ()


@dataclass(frozen=True)
class UserProfileRecord(UserAccountRecord):
    groups: tuple[GroupRecord, ...] = ()


@dataclass(frozen=True)
class PasswordResetCandidateRecord:
    id: UUID
    email: str
    reset_token_hash: str | None
    reset_token_expires: datetime | None


class UserAccountError(Exception):
    pass


class UserAlreadyExists(UserAccountError):
    pass


class InvalidLoginCredentials(UserAccountError):
    pass


class InvalidPasswordResetToken(UserAccountError):
    pass


class IncorrectCurrentPassword(UserAccountError):
    pass


class UserAccountRepository(Protocol):
    def get_by_email(self, email: str) -> UserAccountRecord | None: ...

    def create_email_user(
        self, *, email: str, password_hash: str
    ) -> UserAccountRecord: ...

    def get_user_for_authentication(
        self, email: str
    ) -> AuthenticatedUserRecord | None: ...

    def store_password_reset_token(
        self, *, email: str, token_hash: str, expires_at: datetime
    ) -> bool: ...

    def get_password_reset_candidates(
        self,
    ) -> list[PasswordResetCandidateRecord]: ...

    def update_password_and_clear_reset_token(
        self, *, user_id: UUID, password_hash: str
    ) -> bool: ...

    def update_user_password(self, *, user_id: UUID, password_hash: str) -> bool: ...


class PasswordService(Protocol):
    def hash_password(self, password: str) -> str: ...

    def verify_password(self, plain_password: str, password_hash: str) -> bool: ...

    def generate_reset_token(self) -> str: ...

    def hash_reset_token(self, token: str) -> str: ...

    def verify_reset_token(self, plain_token: str, token_hash: str) -> bool: ...


class AccessTokenProvider(Protocol):
    def create_access_token(self, *, subject: str) -> str: ...


class UserEventPublisher(Protocol):
    def publish_user_registered(self, *, user_id: UUID, email: str) -> None: ...

    def publish_password_reset_requested(
        self, *, email: str, reset_token: str
    ) -> None: ...

    def publish_password_changed(self, *, user_id: UUID, email: str) -> None: ...


def build_user_profile(
    *,
    user_id: UUID,
    email: str,
    auth_provider: str | None,
    groups: tuple[GroupRecord, ...],
) -> UserProfileRecord:
    return UserProfileRecord(
        id=user_id,
        email=email,
        auth_provider=auth_provider or "email",
        groups=groups,
    )


def find_valid_password_reset_candidate(
    *,
    user_repository: UserAccountRepository,
    password_service: PasswordService,
    token: str,
    now: datetime | None = None,
) -> PasswordResetCandidateRecord | None:
    checked_at = now or datetime.now(timezone.utc)

    for candidate in user_repository.get_password_reset_candidates():
        if not candidate.reset_token_hash or not candidate.reset_token_expires:
            continue

        expires_at = candidate.reset_token_expires
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= checked_at:
            continue

        if password_service.verify_reset_token(token, candidate.reset_token_hash):
            return candidate

    return None
