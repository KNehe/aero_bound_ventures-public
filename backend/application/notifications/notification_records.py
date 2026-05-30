from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class NotificationRecord:
    id: UUID
    user_id: UUID
    message: str
    type: str
    is_read: bool
    created_at: datetime


@dataclass(frozen=True)
class NotificationPage:
    items: list[NotificationRecord]
    next_cursor: str | None
    has_more: bool
    has_previous: bool
    total_count: int | None
    limit: int


@dataclass(frozen=True)
class NotificationStream:
    events: Any
    initial_count: int


class NotificationError(Exception):
    pass


class NotificationNotFound(NotificationError):
    pass


class NotificationRepository(Protocol):
    def get_unread_count(self, user_id: UUID) -> int: ...

    def get_user_notifications(
        self,
        *,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> NotificationPage: ...

    def mark_all_as_read(self, user_id: UUID) -> int: ...

    def mark_as_read(
        self, *, notification_id: UUID, user_id: UUID
    ) -> NotificationRecord | None: ...

    def delete_notification(self, *, notification_id: UUID, user_id: UUID) -> bool: ...


class NotificationStreamProvider(Protocol):
    def stream_notifications(self, *, user_id: UUID, initial_count: int) -> Any: ...

    def stream_unread_count(self, *, user_id: UUID, initial_count: int) -> Any: ...


class UnreadCountPublisher(Protocol):
    async def publish_for_user(self, user_id: UUID) -> int: ...
