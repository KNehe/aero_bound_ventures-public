from dataclasses import dataclass

from backend.application.users.user_accounts import (
    UserAccountRecord,
    UserAccountRepository,
    UserAlreadyExists,
    UserEventPublisher,
    PasswordService,
)


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    password: str


class RegisterUser:
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

    def execute(self, *, command: RegisterUserCommand) -> UserAccountRecord:
        existing_user = self.user_repository.get_by_email(command.email)
        if existing_user:
            raise UserAlreadyExists

        user = self.user_repository.create_email_user(
            email=command.email,
            password_hash=self.password_service.hash_password(command.password),
        )
        self.event_publisher.publish_user_registered(
            user_id=user.id,
            email=user.email,
        )
        return user
