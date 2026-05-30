import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from backend.application.notifications.delete_notification import DeleteNotification
from backend.application.notifications.get_unread_count import (
    GetUnreadNotificationCount,
)
from backend.application.notifications.list_notifications import ListNotifications
from backend.application.notifications.mark_all_notifications_read import (
    MarkAllNotificationsRead,
)
from backend.application.notifications.mark_notification_read import (
    MarkNotificationRead,
)
from backend.application.notifications.notification_records import (
    NotificationNotFound,
    NotificationPage,
    NotificationRecord,
)
from backend.application.notifications.open_notification_stream import (
    OpenNotificationStream,
)
from backend.application.notifications.open_unread_count_stream import (
    OpenUnreadCountStream,
)
from backend.crud.database import get_session
from backend.infrastructure.notifications.redis_notification_stream_provider import (
    RedisNotificationStreamProvider,
)
from backend.infrastructure.notifications.redis_unread_count_publisher import (
    RedisUnreadCountPublisher,
)
from backend.infrastructure.notifications.sqlmodel_notification_repository import (
    SqlModelNotificationRepository,
)
from backend.models.users import UserInDB
from backend.schemas.notifications import (
    CursorPaginatedNotificationResponse,
    NotificationResponse,
)
from backend.utils.pagination import MAX_PAGINATION_LIMIT
from backend.utils.security import get_current_user, get_user_from_token


router = APIRouter(prefix="/notifications", tags=["notifications"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def get_open_notification_stream_use_case(
    session: Session = Depends(get_session),
) -> OpenNotificationStream:
    return OpenNotificationStream(
        notification_repository=SqlModelNotificationRepository(session),
        notification_stream_provider=RedisNotificationStreamProvider(),
    )


def get_open_unread_count_stream_use_case(
    session: Session = Depends(get_session),
) -> OpenUnreadCountStream:
    return OpenUnreadCountStream(
        notification_repository=SqlModelNotificationRepository(session),
        notification_stream_provider=RedisNotificationStreamProvider(),
    )


def get_unread_notification_count_use_case(
    session: Session = Depends(get_session),
) -> GetUnreadNotificationCount:
    return GetUnreadNotificationCount(
        notification_repository=SqlModelNotificationRepository(session),
    )


def get_list_notifications_use_case(
    session: Session = Depends(get_session),
) -> ListNotifications:
    return ListNotifications(
        notification_repository=SqlModelNotificationRepository(session),
    )


def get_mark_all_notifications_read_use_case(
    session: Session = Depends(get_session),
) -> MarkAllNotificationsRead:
    return MarkAllNotificationsRead(
        notification_repository=SqlModelNotificationRepository(session),
        unread_count_publisher=RedisUnreadCountPublisher(session),
    )


def get_mark_notification_read_use_case(
    session: Session = Depends(get_session),
) -> MarkNotificationRead:
    return MarkNotificationRead(
        notification_repository=SqlModelNotificationRepository(session),
        unread_count_publisher=RedisUnreadCountPublisher(session),
    )


def get_delete_notification_use_case(
    session: Session = Depends(get_session),
) -> DeleteNotification:
    return DeleteNotification(
        notification_repository=SqlModelNotificationRepository(session),
        unread_count_publisher=RedisUnreadCountPublisher(session),
    )


def _to_notification_response(
    notification: NotificationRecord,
) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        message=notification.message,
        type=notification.type,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


def _to_paginated_response(
    notification_page: NotificationPage,
) -> CursorPaginatedNotificationResponse:
    return CursorPaginatedNotificationResponse(
        items=[
            _to_notification_response(notification)
            for notification in notification_page.items
        ],
        next_cursor=notification_page.next_cursor,
        has_more=notification_page.has_more,
        has_previous=notification_page.has_previous,
        total_count=notification_page.total_count,
        limit=notification_page.limit,
    )


@router.get("/stream")
async def notification_stream(
    request: Request,
    token: str | None = Query(None, description="JWT access token for authentication"),
    session: Session = Depends(get_session),
    open_notification_stream_use_case: OpenNotificationStream = Depends(
        get_open_notification_stream_use_case
    ),
):
    """
    SSE endpoint for real-time notifications.

    Authentication: Token can be passed as query param or via HTTP-only cookie.
    Query param takes precedence for backward compatibility.
    """
    current_user = get_user_from_token(token, session, request)
    stream = open_notification_stream_use_case.execute(user_id=current_user.id)

    return StreamingResponse(
        stream.events,
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/unread-count/stream")
async def unread_count_stream(
    request: Request,
    token: str | None = Query(None, description="JWT access token for authentication"),
    session: Session = Depends(get_session),
    open_unread_count_stream_use_case: OpenUnreadCountStream = Depends(
        get_open_unread_count_stream_use_case
    ),
):
    """
    SSE endpoint for real-time unread count updates.

    Authentication: Token can be passed as query param or via HTTP-only cookie.
    Query param takes precedence for backward compatibility.
    """
    current_user = get_user_from_token(token, session, request)
    stream = open_unread_count_stream_use_case.execute(user_id=current_user.id)

    return StreamingResponse(
        stream.events,
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/unread-count")
def get_unread_count(
    current_user: UserInDB = Depends(get_current_user),
    unread_count_use_case: GetUnreadNotificationCount = Depends(
        get_unread_notification_count_use_case
    ),
):
    """
    Get the current unread notification count (REST endpoint).
    """
    return {
        "unread_count": unread_count_use_case.execute(user_id=current_user.id),
    }


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
    current_user: UserInDB = Depends(get_current_user),
    list_notifications_use_case: ListNotifications = Depends(
        get_list_notifications_use_case
    ),
):
    """
    Get cursor-paginated list of notifications for the current user.
    """
    notification_page = list_notifications_use_case.execute(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        include_count=include_count,
    )
    return _to_paginated_response(notification_page)


@router.put("/mark-all-read")
async def mark_all_read(
    current_user: UserInDB = Depends(get_current_user),
    mark_all_notifications_read_use_case: MarkAllNotificationsRead = Depends(
        get_mark_all_notifications_read_use_case
    ),
):
    """
    Mark all notifications as read for the current user.
    """
    result = await mark_all_notifications_read_use_case.execute(
        user_id=current_user.id,
    )
    return {"marked_as_read": result.marked_as_read}


@router.put("/{notification_id}/mark-read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    mark_notification_read_use_case: MarkNotificationRead = Depends(
        get_mark_notification_read_use_case
    ),
):
    """
    Mark a specific notification as read.
    """
    try:
        notification = await mark_notification_read_use_case.execute(
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except NotificationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return _to_notification_response(notification)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_notification(
    notification_id: uuid.UUID,
    current_user: UserInDB = Depends(get_current_user),
    delete_notification_use_case: DeleteNotification = Depends(
        get_delete_notification_use_case
    ),
):
    """
    Delete a specific notification.
    """
    try:
        await delete_notification_use_case.execute(
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except NotificationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return None
