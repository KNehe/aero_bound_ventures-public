from dataclasses import dataclass
from uuid import UUID

from backend.application.notifications.notification_records import (
    NotificationRepository,
    UnreadCountPublisher,
)


@dataclass(frozen=True)
class MarkedNotifications:
    marked_as_read: int
    unread_count: int


class MarkAllNotificationsRead:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        unread_count_publisher: UnreadCountPublisher,
    ):
        self.notification_repository = notification_repository
        self.unread_count_publisher = unread_count_publisher

    async def execute(self, *, user_id: UUID) -> MarkedNotifications:
        marked_as_read = self.notification_repository.mark_all_as_read(user_id)
        unread_count = await self.unread_count_publisher.publish_for_user(user_id)
        return MarkedNotifications(
            marked_as_read=marked_as_read,
            unread_count=unread_count,
        )
