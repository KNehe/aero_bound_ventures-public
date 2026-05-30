from dataclasses import dataclass

from backend.application.users.user_accounts import (
    PasswordService,
    UserAccountRepository,
    find_valid_password_reset_candidate,
)


@dataclass(frozen=True)
class PasswordResetTokenVerification:
    valid: bool


class VerifyPasswordReset:
    def __init__(
        self,
        *,
        user_repository: UserAccountRepository,
        password_service: PasswordService,
    ):
        self.user_repository = user_repository
        self.password_service = password_service

    def execute(self, *, token: str) -> PasswordResetTokenVerification:
        candidate = find_valid_password_reset_candidate(
            user_repository=self.user_repository,
            password_service=self.password_service,
            token=token,
        )
        return PasswordResetTokenVerification(valid=candidate is not None)
