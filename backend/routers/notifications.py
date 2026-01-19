from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from backend.utils.redis import notification_streamer, unread_count_streamer
from backend.utils.notification_service import get_and_publish_unread_count
import uuid
from sqlmodel import Session
from backend.utils.security import get_current_user, get_user_from_token
from backend.models.users import UserInDB
from backend.crud.notifications import (
    mark_all_notifications_as_read,
    delete_notification as crud_delete_notification,
    get_unread_notifications_count,
    mark_notification_as_read,
    get_notifications_cursor,
)
from backend.utils.pagination import MAX_PAGINATION_LIMIT
from backend.crud.database import get_session
from backend.schemas.notifications import (
    NotificationResponse,
    CursorPaginatedNotificationResponse,
)


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/stream")
async def notification_stream(
    request: Request,
    token: str | None = Query(None, description="JWT access token for authentication"),
    db: Session = Depends(get_session),
):
    """
    SSE endpoint for real-time notifications.

    This endpoint establishes a Server-Sent Events connection that streams
    notifications to the authenticated user in real-time.

    Authentication: Token can be passed as query param or via HTTP-only cookie.
    Query param takes precedence for backward compatibility.

    The stream includes:
    - Connected event on initial connection (with current unread count)
    - Notification events when new notifications arrive
    - Unread count events when count changes
    - Heartbeat comments every 30 seconds to keep connection alive

    Returns:
        StreamingResponse with SSE content type
    """
    current_user = get_user_from_token(token, db, request)

    initial_count = get_unread_notifications_count(db, current_user.id)

    return StreamingResponse(
        notification_streamer(current_user.id, initial_count),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/unread-count/stream")
async def unread_count_stream(
    request: Request,
    token: str | None = Query(None, description="JWT access token for authentication"),
    db: Session = Depends(get_session),
):
    """
    SSE endpoint for real-time unread count updates.

    This is a lightweight stream specifically for notification badge updates.
    Use this when you only need to display the unread count (e.g., in a header badge)
    without receiving the full notification content.

    Authentication: Token can be passed as query param or via HTTP-only cookie.
    Query param takes precedence for backward compatibility.

    The stream includes:
    - Initial count event on connection
    - Count events whenever unread count changes
    - Heartbeat comments every 30 seconds to keep connection alive

    Returns:
        StreamingResponse with SSE content type
    """
    current_user = get_user_from_token(token, db, request)

    initial_count = get_unread_notifications_count(db, current_user.id)

    return StreamingResponse(
        unread_count_streamer(current_user.id, initial_count),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get the current unread notification count (REST endpoint).

    For real-time updates, use GET /notifications/unread-count/stream instead.

    Returns:
        Object with unread_count field
    """
    count = get_unread_notifications_count(db, current_user.id)
    return {"unread_count": count}


@router.get("/", response_model=CursorPaginatedNotificationResponse)
def get_notifications(
    cursor: str | None = None,
    limit: int = Query(
        20,
        ge=1,
        le=MAX_PAGINATION_LIMIT,
        description="Maximum number of notifications to return",
    ),
    include_count: bool = Query(
        False,
        description="Include total_count in response (may be slower)",
    ),
    db: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Get cursor-paginated list of notifications for the current user.

    Args:
        cursor: Cursor for pagination (None for first page)
        limit: Maximum number of notifications to return (default: 20, max: 100)
        include_count: Whether to include total count in response

    Returns:
        Cursor-paginated notifications ordered by creation date (newest first)
    """
    notifications, next_cursor, has_more, total_count = get_notifications_cursor(
        db, current_user.id, cursor=cursor, limit=limit, include_count=include_count
    )

    items = [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            message=n.message,
            type=n.type,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]

    return CursorPaginatedNotificationResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        has_previous=cursor is not None,
        total_count=total_count,
        limit=limit,
    )


@router.put("/mark-all-read")
async def mark_all_read(
    db: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Mark all notifications as read for the current user.

    Also publishes the updated unread count (0) to SSE streams.

    Returns:
        Object with count of notifications marked as read
    """
    count = mark_all_notifications_as_read(db, current_user.id)

    await get_and_publish_unread_count(db, current_user.id)

    return {"marked_as_read": count}


@router.put("/{notification_id}/mark-read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Mark a specific notification as read.

    Also publishes the updated unread count to SSE streams.

    Args:
        notification_id: UUID of the notification to mark as read

    Returns:
        The updated notification

    Raises:
        HTTPException 404: If notification not found or doesn't belong to user
    """
    notification = mark_notification_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    await get_and_publish_unread_count(db, current_user.id)

    return notification


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_notification(
    notification_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Delete a specific notification.

    Also publishes the updated unread count to SSE streams.

    Args:
        notification_id: UUID of the notification to delete

    Raises:
        HTTPException 404: If notification not found or doesn't belong to user
    """
    deleted = crud_delete_notification(db, notification_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    await get_and_publish_unread_count(db, current_user.id)

    return None
