from dataclasses import dataclass

from backend.application.users.user_accounts import (
    AccessTokenProvider,
    InvalidLoginCredentials,
    PasswordService,
    UserAccountRepository,
    UserProfileRecord,
    build_user_profile,
)


@dataclass(frozen=True)
class LoginUserCommand:
    email: str
    password: str


@dataclass(frozen=True)
class LoggedInUser:
    access_token: str
    user: UserProfileRecord


class LoginUser:
    def __init__(
        self,
        *,
        user_repository: UserAccountRepository,
        password_service: PasswordService,
        access_token_provider: AccessTokenProvider,
    ):
        self.user_repository = user_repository
        self.password_service = password_service
        self.access_token_provider = access_token_provider

    def execute(self, *, command: LoginUserCommand) -> LoggedInUser:
        user = self.user_repository.get_user_for_authentication(command.email)
        if not user or not user.password_hash:
            raise InvalidLoginCredentials

        if not self.password_service.verify_password(
            command.password, user.password_hash
        ):
            raise InvalidLoginCredentials

        return LoggedInUser(
            access_token=self.access_token_provider.create_access_token(
                subject=user.email
            ),
            user=build_user_profile(
                user_id=user.id,
                email=user.email,
                auth_provider=user.auth_provider,
                groups=user.groups,
            ),
        )
