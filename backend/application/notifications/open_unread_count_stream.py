from uuid import UUID

from backend.application.notifications.notification_records import (
    NotificationRepository,
    NotificationStream,
    NotificationStreamProvider,
)


class OpenUnreadCountStream:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        notification_stream_provider: NotificationStreamProvider,
    ):
        self.notification_repository = notification_repository
        self.notification_stream_provider = notification_stream_provider

    def execute(self, *, user_id: UUID) -> NotificationStream:
        initial_count = self.notification_repository.get_unread_count(user_id)
        return NotificationStream(
            events=self.notification_stream_provider.stream_unread_count(
                user_id=user_id,
                initial_count=initial_count,
            ),
            initial_count=initial_count,
        )
