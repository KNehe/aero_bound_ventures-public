from sqlmodel import Session, select
from backend.schemas.notifications import NotificationCreate, NotificationResponse
from backend.models.notifications import Notification
import uuid


def create_notification(db: Session, notification: NotificationCreate) -> NotificationResponse:
    db_notification = Notification(**notification.model_dump())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notifications_by_user(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 10) -> list[NotificationResponse]:
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

def mark_notification_as_read(db: Session, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationResponse:
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

def delete_notification(db: Session, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
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