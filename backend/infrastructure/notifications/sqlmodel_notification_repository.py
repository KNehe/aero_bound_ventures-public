from uuid import UUID

from sqlmodel import Session

from backend.application.notifications.notification_records import (
    NotificationPage,
    NotificationRecord,
)
from backend.crud.notifications import (
    delete_notification,
    get_notifications_cursor,
    get_unread_notifications_count,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)
from backend.models.notifications import Notification


class SqlModelNotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_unread_count(self, user_id: UUID) -> int:
        return get_unread_notifications_count(self.session, user_id)

    def get_user_notifications(
        self,
        *,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> NotificationPage:
        notifications, next_cursor, has_more, total_count = get_notifications_cursor(
            self.session,
            user_id,
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )

        return NotificationPage(
            items=[self._to_record(notification) for notification in notifications],
            next_cursor=next_cursor,
            has_more=has_more,
            has_previous=cursor is not None,
            total_count=total_count,
            limit=limit,
        )

    def mark_all_as_read(self, user_id: UUID) -> int:
        return mark_all_notifications_as_read(self.session, user_id)

    def mark_as_read(
        self, *, notification_id: UUID, user_id: UUID
    ) -> NotificationRecord | None:
        notification = mark_notification_as_read(
            self.session,
            notification_id,
            user_id,
        )
        if not notification:
            return None

        return self._to_record(notification)

    def delete_notification(self, *, notification_id: UUID, user_id: UUID) -> bool:
        return delete_notification(self.session, notification_id, user_id)

    @staticmethod
    def _to_record(notification: Notification) -> NotificationRecord:
        return NotificationRecord(
            id=notification.id,
            user_id=notification.user_id,
            message=notification.message,
            type=notification.type,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )
