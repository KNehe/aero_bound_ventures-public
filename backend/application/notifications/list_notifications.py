from uuid import UUID

from backend.application.notifications.notification_records import (
    NotificationPage,
    NotificationRepository,
)


class ListNotifications:
    def __init__(self, *, notification_repository: NotificationRepository):
        self.notification_repository = notification_repository

    def execute(
        self,
        *,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> NotificationPage:
        return self.notification_repository.get_user_notifications(
            user_id=user_id,
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )
