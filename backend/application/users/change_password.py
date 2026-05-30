from dataclasses import dataclass
from uuid import UUID

from backend.application.users.user_accounts import (
    IncorrectCurrentPassword,
    PasswordService,
    UserAccountRepository,
    UserEventPublisher,
)


@dataclass(frozen=True)
class ChangePasswordCommand:
    user_id: UUID
    email: str
    current_password_hash: str | None
    current_password: str
    new_password: str


class ChangePassword:
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

    def execute(self, *, command: ChangePasswordCommand) -> None:
        if not command.current_password_hash:
            raise IncorrectCurrentPassword

        password_matches = self.password_service.verify_password(
            command.current_password,
            command.current_password_hash,
        )
        if not password_matches:
            raise IncorrectCurrentPassword

        password_updated = self.user_repository.update_user_password(
            user_id=command.user_id,
            password_hash=self.password_service.hash_password(command.new_password),
        )
        if not password_updated:
            raise IncorrectCurrentPassword

        self.event_publisher.publish_password_changed(
            user_id=command.user_id,
            email=command.email,
        )
