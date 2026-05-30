from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.application.users.change_password import (
    ChangePassword,
    ChangePasswordCommand,
)
from backend.application.users.get_current_user_profile import (
    GetCurrentUserProfile,
    GetCurrentUserProfileCommand,
)
from backend.application.users.login_user import LoginUser, LoginUserCommand
from backend.application.users.register_user import RegisterUser, RegisterUserCommand
from backend.application.users.request_password_reset import RequestPasswordReset
from backend.application.users.reset_password import ResetPassword, ResetPasswordCommand
from backend.application.users.user_accounts import (
    AuthenticatedUserRecord,
    GroupRecord,
    IncorrectCurrentPassword,
    InvalidLoginCredentials,
    InvalidPasswordResetToken,
    PasswordResetCandidateRecord,
    PermissionRecord,
    UserAccountRecord,
    UserAlreadyExists,
    UserProfileRecord,
)
from backend.application.users.verify_password_reset import VerifyPasswordReset


USER_ID = uuid4()


class StubUserRepository:
    def __init__(self):
        self.accounts_by_email: dict[str, UserAccountRecord] = {}
        self.auth_users_by_email: dict[str, AuthenticatedUserRecord] = {}
        self.password_reset_candidates: list[PasswordResetCandidateRecord] = []
        self.created_users = []
        self.stored_reset_tokens = []
        self.password_reset_updates = []
        self.password_updates = []

    def get_by_email(self, email: str):
        return self.accounts_by_email.get(email)

    def create_email_user(self, *, email: str, password_hash: str):
        account = UserAccountRecord(id=USER_ID, email=email, auth_provider="email")
        self.accounts_by_email[email] = account
        self.created_users.append({"email": email, "password_hash": password_hash})
        return account

    def get_user_for_authentication(self, email: str):
        return self.auth_users_by_email.get(email)

    def store_password_reset_token(self, *, email: str, token_hash: str, expires_at):
        if email not in self.accounts_by_email:
            return False

        self.stored_reset_tokens.append(
            {"email": email, "token_hash": token_hash, "expires_at": expires_at}
        )
        return True

    def get_password_reset_candidates(self):
        return self.password_reset_candidates

    def update_password_and_clear_reset_token(self, *, user_id, password_hash: str):
        if not any(
            candidate.id == user_id for candidate in self.password_reset_candidates
        ):
            return False

        self.password_reset_updates.append(
            {"user_id": user_id, "password_hash": password_hash}
        )
        return True

    def update_user_password(self, *, user_id, password_hash: str):
        self.password_updates.append(
            {"user_id": user_id, "password_hash": password_hash}
        )
        return True


class StubPasswordService:
    def __init__(self):
        self.generated_reset_token = "plain-reset-token"
        self.hashed_passwords = []
        self.verified_passwords = []
        self.hashed_reset_tokens = []
        self.verified_reset_tokens = []

    def hash_password(self, password: str) -> str:
        self.hashed_passwords.append(password)
        return f"password-hash:{password}"

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        self.verified_passwords.append(
            {"plain_password": plain_password, "password_hash": password_hash}
        )
        return password_hash == f"password-hash:{plain_password}"

    def generate_reset_token(self) -> str:
        return self.generated_reset_token

    def hash_reset_token(self, token: str) -> str:
        self.hashed_reset_tokens.append(token)
        return f"reset-token-hash:{token}"

    def verify_reset_token(self, plain_token: str, token_hash: str) -> bool:
        self.verified_reset_tokens.append(
            {"plain_token": plain_token, "token_hash": token_hash}
        )
        return token_hash == f"reset-token-hash:{plain_token}"


class StubAccessTokenProvider:
    def __init__(self):
        self.subjects = []

    def create_access_token(self, *, subject: str) -> str:
        self.subjects.append(subject)
        return f"access-token:{subject}"


class StubUserEventPublisher:
    def __init__(self):
        self.registered_events = []
        self.password_reset_events = []
        self.password_changed_events = []

    def publish_user_registered(self, **kwargs) -> None:
        self.registered_events.append(kwargs)

    def publish_password_reset_requested(self, **kwargs) -> None:
        self.password_reset_events.append(kwargs)

    def publish_password_changed(self, **kwargs) -> None:
        self.password_changed_events.append(kwargs)


def test_register_user_hashes_password_and_publishes_registration_event():
    repository = StubUserRepository()
    password_service = StubPasswordService()
    publisher = StubUserEventPublisher()
    use_case = RegisterUser(
        user_repository=repository,
        password_service=password_service,
        event_publisher=publisher,
    )

    user = use_case.execute(
        command=RegisterUserCommand(
            email="traveler@example.com",
            password="secret-password",
        )
    )

    assert user == UserAccountRecord(
        id=USER_ID,
        email="traveler@example.com",
        auth_provider="email",
    )
    assert repository.created_users == [
        {
            "email": "traveler@example.com",
            "password_hash": "password-hash:secret-password",
        }
    ]
    assert publisher.registered_events == [
        {"user_id": USER_ID, "email": "traveler@example.com"}
    ]


def test_register_user_rejects_existing_email():
    repository = StubUserRepository()
    repository.accounts_by_email["traveler@example.com"] = UserAccountRecord(
        id=USER_ID,
        email="traveler@example.com",
    )
    use_case = RegisterUser(
        user_repository=repository,
        password_service=StubPasswordService(),
        event_publisher=StubUserEventPublisher(),
    )

    with pytest.raises(UserAlreadyExists):
        use_case.execute(
            command=RegisterUserCommand(
                email="traveler@example.com",
                password="secret-password",
            )
        )

    assert repository.created_users == []


def test_login_user_returns_access_token_and_profile():
    repository = StubUserRepository()
    repository.auth_users_by_email["traveler@example.com"] = AuthenticatedUserRecord(
        id=USER_ID,
        email="traveler@example.com",
        auth_provider="email",
        password_hash="password-hash:secret-password",
        groups=(
            GroupRecord(
                name="customer",
                description="Customer account",
                permissions=(
                    PermissionRecord(
                        name="View bookings",
                        codename="bookings.view",
                    ),
                ),
            ),
        ),
    )
    access_token_provider = StubAccessTokenProvider()
    use_case = LoginUser(
        user_repository=repository,
        password_service=StubPasswordService(),
        access_token_provider=access_token_provider,
    )

    result = use_case.execute(
        command=LoginUserCommand(
            email="traveler@example.com",
            password="secret-password",
        )
    )

    assert result.access_token == "access-token:traveler@example.com"
    assert result.user.email == "traveler@example.com"
    assert result.user.groups[0].permissions[0].codename == "bookings.view"
    assert access_token_provider.subjects == ["traveler@example.com"]


def test_login_user_rejects_missing_user_or_bad_password():
    repository = StubUserRepository()
    repository.auth_users_by_email["traveler@example.com"] = AuthenticatedUserRecord(
        id=USER_ID,
        email="traveler@example.com",
        password_hash="password-hash:expected-password",
    )
    use_case = LoginUser(
        user_repository=repository,
        password_service=StubPasswordService(),
        access_token_provider=StubAccessTokenProvider(),
    )

    with pytest.raises(InvalidLoginCredentials):
        use_case.execute(
            command=LoginUserCommand(
                email="missing@example.com",
                password="expected-password",
            )
        )

    with pytest.raises(InvalidLoginCredentials):
        use_case.execute(
            command=LoginUserCommand(
                email="traveler@example.com",
                password="wrong-password",
            )
        )


def test_request_password_reset_stores_hashed_token_and_publishes_plain_token():
    repository = StubUserRepository()
    repository.accounts_by_email["traveler@example.com"] = UserAccountRecord(
        id=USER_ID,
        email="traveler@example.com",
    )
    publisher = StubUserEventPublisher()
    use_case = RequestPasswordReset(
        user_repository=repository,
        password_service=StubPasswordService(),
        event_publisher=publisher,
    )

    result = use_case.execute(email="traveler@example.com")

    assert result.reset_token == "plain-reset-token"
    assert repository.stored_reset_tokens[0]["email"] == "traveler@example.com"
    assert repository.stored_reset_tokens[0]["token_hash"] == (
        "reset-token-hash:plain-reset-token"
    )
    assert repository.stored_reset_tokens[0]["expires_at"] > datetime.now(timezone.utc)
    assert publisher.password_reset_events == [
        {"email": "traveler@example.com", "reset_token": "plain-reset-token"}
    ]


def test_request_password_reset_does_not_publish_for_unknown_email():
    publisher = StubUserEventPublisher()
    use_case = RequestPasswordReset(
        user_repository=StubUserRepository(),
        password_service=StubPasswordService(),
        event_publisher=publisher,
    )

    result = use_case.execute(email="missing@example.com")

    assert result.reset_token is None
    assert publisher.password_reset_events == []


def test_verify_password_reset_accepts_only_matching_unexpired_tokens():
    repository = StubUserRepository()
    repository.password_reset_candidates = [
        PasswordResetCandidateRecord(
            id=USER_ID,
            email="traveler@example.com",
            reset_token_hash="reset-token-hash:valid-token",
            reset_token_expires=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
    ]
    use_case = VerifyPasswordReset(
        user_repository=repository,
        password_service=StubPasswordService(),
    )

    assert use_case.execute(token="valid-token").valid is True
    assert use_case.execute(token="wrong-token").valid is False

    repository.password_reset_candidates[0] = PasswordResetCandidateRecord(
        id=USER_ID,
        email="traveler@example.com",
        reset_token_hash="reset-token-hash:valid-token",
        reset_token_expires=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    assert use_case.execute(token="valid-token").valid is False


def test_reset_password_updates_password_and_clears_reset_token():
    repository = StubUserRepository()
    repository.password_reset_candidates = [
        PasswordResetCandidateRecord(
            id=USER_ID,
            email="traveler@example.com",
            reset_token_hash="reset-token-hash:valid-token",
            reset_token_expires=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
    ]
    use_case = ResetPassword(
        user_repository=repository,
        password_service=StubPasswordService(),
    )

    use_case.execute(
        command=ResetPasswordCommand(
            token="valid-token",
            new_password="NewPassword123!",
        )
    )

    assert repository.password_reset_updates == [
        {"user_id": USER_ID, "password_hash": "password-hash:NewPassword123!"}
    ]


def test_reset_password_rejects_invalid_token():
    use_case = ResetPassword(
        user_repository=StubUserRepository(),
        password_service=StubPasswordService(),
    )

    with pytest.raises(InvalidPasswordResetToken):
        use_case.execute(
            command=ResetPasswordCommand(
                token="invalid-token",
                new_password="NewPassword123!",
            )
        )


def test_get_current_user_profile_returns_supplied_profile():
    profile = UserProfileRecord(
        id=USER_ID,
        email="traveler@example.com",
        auth_provider="email",
    )

    result = GetCurrentUserProfile().execute(
        command=GetCurrentUserProfileCommand(user_profile=profile)
    )

    assert result == profile


def test_change_password_updates_password_and_publishes_event():
    repository = StubUserRepository()
    publisher = StubUserEventPublisher()
    use_case = ChangePassword(
        user_repository=repository,
        password_service=StubPasswordService(),
        event_publisher=publisher,
    )

    use_case.execute(
        command=ChangePasswordCommand(
            user_id=USER_ID,
            email="traveler@example.com",
            current_password_hash="password-hash:old-password",
            current_password="old-password",
            new_password="NewPassword123!",
        )
    )

    assert repository.password_updates == [
        {"user_id": USER_ID, "password_hash": "password-hash:NewPassword123!"}
    ]
    assert publisher.password_changed_events == [
        {"user_id": USER_ID, "email": "traveler@example.com"}
    ]


def test_change_password_rejects_incorrect_current_password():
    repository = StubUserRepository()
    publisher = StubUserEventPublisher()
    use_case = ChangePassword(
        user_repository=repository,
        password_service=StubPasswordService(),
        event_publisher=publisher,
    )

    with pytest.raises(IncorrectCurrentPassword):
        use_case.execute(
            command=ChangePasswordCommand(
                user_id=USER_ID,
                email="traveler@example.com",
                current_password_hash="password-hash:old-password",
                current_password="wrong-password",
                new_password="NewPassword123!",
            )
        )

    assert repository.password_updates == []
    assert publisher.password_changed_events == []
