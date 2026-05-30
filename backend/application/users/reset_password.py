from dataclasses import dataclass

from backend.application.users.user_accounts import (
    InvalidPasswordResetToken,
    PasswordService,
    UserAccountRepository,
    find_valid_password_reset_candidate,
)


@dataclass(frozen=True)
class ResetPasswordCommand:
    token: str
    new_password: str


class ResetPassword:
    def __init__(
        self,
        *,
        user_repository: UserAccountRepository,
        password_service: PasswordService,
    ):
        self.user_repository = user_repository
        self.password_service = password_service

    def execute(self, *, command: ResetPasswordCommand) -> None:
        candidate = find_valid_password_reset_candidate(
            user_repository=self.user_repository,
            password_service=self.password_service,
            token=command.token,
        )
        if not candidate:
            raise InvalidPasswordResetToken

        password_updated = self.user_repository.update_password_and_clear_reset_token(
            user_id=candidate.id,
            password_hash=self.password_service.hash_password(command.new_password),
        )
        if not password_updated:
            raise InvalidPasswordResetToken
