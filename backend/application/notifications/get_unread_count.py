from uuid import UUID

from backend.application.notifications.notification_records import (
    NotificationRepository,
)


class GetUnreadNotificationCount:
    def __init__(self, *, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    def execute(self, *, user_id: UUID) -> int:
        return self.notification_repository.get_unread_count(user_id)
