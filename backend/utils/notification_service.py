"""
Centralized notification service for creating and publishing notifications.

This service ensures notifications are both persisted to the database
and published to Redis for real-time delivery via SSE.
"""

from sqlmodel import Session
import uuid
import logging
from typing import Optional

from backend.models.notifications import Notification, NotificationType
from backend.schemas.notifications import NotificationResponse
from backend.utils.redis import publish_notification, publish_unread_count
from backend.crud.notifications import get_unread_notifications_count


logger = logging.getLogger(__name__)


async def create_and_publish_notification(
    db: Session,
    user_id: uuid.UUID,
    message: str,
    notification_type: str = NotificationType.GENERAL,
) -> Optional[NotificationResponse]:
    """
    Create a notification in the database and publish it to Redis for real-time delivery.
    
    This function ensures that notifications are both persisted (for history/retrieval)
    and published (for real-time SSE streaming).
    
    Args:
        db: Database session
        user_id: UUID of the user to notify
        message: The notification message
        notification_type: Type of notification (from NotificationType)
        
    Returns:
        NotificationResponse if successful, None if failed
    """
    try:
        db_notification = Notification(
            user_id=user_id,
            type=notification_type,
            message=message,
        )
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        
        notification_data = {
            "event_type": "notification",
            "id": str(db_notification.id),
            "type": db_notification.type,
            "message": db_notification.message,
            "is_read": db_notification.is_read,
            "created_at": db_notification.created_at.isoformat().replace("+00:00", "Z"),
            "user_id": str(db_notification.user_id),
        }
        
        try:
            await publish_notification(user_id, notification_data)
        except Exception as e: 
            logger.warning(f"Failed to publish notification to Redis: {e}")       
        return db_notification
        
    except Exception as e:
        logger.error(f"Failed to create notification for user {user_id}: {e}")
        db.rollback()
        return None


async def get_and_publish_unread_count(db: Session, user_id: uuid.UUID) -> int:
    """
    Get the unread notification count and publish it to Redis.
    
    This is useful after marking notifications as read to update
    connected clients in real-time.
    
    Args:
        db: Database session
        user_id: UUID of the user
        
    Returns:
        The unread notification count
    """    
    count = get_unread_notifications_count(db, user_id)
    
    try:
        await publish_unread_count(user_id, count)
    except Exception as e:
        logger.warning(f"Failed to publish unread count to Redis: {e}")
    
    return count
