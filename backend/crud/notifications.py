from sqlmodel import Session, select
from backend.schemas.notifications import NotificationCreate, NotificationResponse
from backend.models.notifications import Notification
from backend.utils.pagination import (
    CursorPaginator,
    get_total_count,
)
import uuid


def create_notification(
    db: Session, notification: NotificationCreate
) -> NotificationResponse:
    db_notification = Notification(**notification.model_dump())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def _notification_cursor_fields(notification: Notification) -> dict:
    """Extract cursor fields from a notification."""
    return {"created_at": notification.created_at, "id": notification.id}


def get_notifications_cursor(
    db: Session,
    user_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
    include_count: bool = False,
) -> tuple[list[Notification], str | None, bool, int | None]:
    """
    Get cursor-paginated notifications for a user.

    Args:
        db: Database session
        user_id: User ID to filter notifications
        cursor: Cursor for pagination (None for first page)
        limit: Maximum number of records to return (capped at MAX_PAGINATION_LIMIT)
        include_count: Whether to include total count (can be expensive)

    Returns:
        Tuple of (list of Notification objects, next_cursor or None, has_more, total_count or None)
    """
    paginator = CursorPaginator(
        cursor=cursor,
        limit=limit,
        order_fields=["created_at", "id"],
        order_direction="desc",
    )

    # Build base query
    query = select(Notification).where(Notification.user_id == user_id)

    # Get total count if requested
    total_count = None
    if include_count:
        count_query = select(Notification).where(Notification.user_id == user_id)
        total_count = get_total_count(db, count_query)

    # Apply pagination
    query = paginator.apply_cursor_filter(query, Notification)
    query = paginator.apply_ordering(query, Notification)
    query = paginator.apply_limit(query)

    notifications = list(db.exec(query).all())
    items, next_cursor, has_more = paginator.build_result(
        notifications, _notification_cursor_fields
    )

    return items, next_cursor, has_more, total_count


# NOTE: Keeping offset-based version for backward compatibility, but marked as deprecated
def get_notifications_by_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 10
) -> list[NotificationResponse]:
    """DEPRECATED: Use get_notifications_cursor for better performance on large datasets."""
    return db.exec(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()


def get_unread_notifications_count(db: Session, user_id: uuid.UUID) -> int:
    notifications = db.exec(
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read.is_(False))
    ).all()
    return len(notifications)


def mark_notification_as_read(
    db: Session, notification_id: uuid.UUID, user_id: uuid.UUID
) -> NotificationResponse:
    notification = db.exec(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == user_id)
    ).first()
    if notification:
        notification.is_read = True
        db.add(notification)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_notifications_as_read(db: Session, user_id: uuid.UUID) -> int:
    notifications = db.exec(
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read.is_(False))
    ).all()
    for notification in notifications:
        notification.is_read = True
        db.add(notification)
    db.commit()
    return len(notifications)


def delete_notification(
    db: Session, notification_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    notification = db.exec(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == user_id)
    ).first()
    if notification:
        db.delete(notification)
        db.commit()
        return True
    return False
