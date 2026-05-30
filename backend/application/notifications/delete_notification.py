from uuid import UUID

from backend.application.notifications.notification_records import (
    NotificationNotFound,
    NotificationRepository,
    UnreadCountPublisher,
)


class DeleteNotification:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        unread_count_publisher: UnreadCountPublisher,
    ):
        self.notification_repository = notification_repository
        self.unread_count_publisher = unread_count_publisher

    async def execute(self, *, notification_id: UUID, user_id: UUID) -> None:
        deleted = self.notification_repository.delete_notification(
            notification_id=notification_id,
            user_id=user_id,
        )
        if not deleted:
            raise NotificationNotFound

        await self.unread_count_publisher.publish_for_user(user_id)
