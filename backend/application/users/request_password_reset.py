from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.application.users.user_accounts import (
    PasswordService,
    UserAccountRepository,
    UserEventPublisher,
)


@dataclass(frozen=True)
class PasswordResetRequestResult:
    email: str
    reset_token: str | None


class RequestPasswordReset:
    def __init__(
        self,
        *,
        user_repository: UserAccountRepository,
        password_service: PasswordService,
        event_publisher: UserEventPublisher,
    ):
        self.user_repository = user_repository
        self.password_service = password_service
        self.event_publisher = event_publisher

    def execute(self, *, email: str) -> PasswordResetRequestResult:
        reset_token = self.password_service.generate_reset_token()
        token_stored = self.user_repository.store_password_reset_token(
            email=email,
            token_hash=self.password_service.hash_reset_token(reset_token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        if not token_stored:
            return PasswordResetRequestResult(email=email, reset_token=None)

        self.event_publisher.publish_password_reset_requested(
            email=email,
            reset_token=reset_token,
        )
        return PasswordResetRequestResult(email=email, reset_token=reset_token)
