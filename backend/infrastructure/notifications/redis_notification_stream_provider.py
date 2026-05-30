from typing import Any
from uuid import UUID

from backend.utils.redis import notification_streamer, unread_count_streamer


class RedisNotificationStreamProvider:
    def stream_notifications(self, *, user_id: UUID, initial_count: int) -> Any:
        return notification_streamer(user_id, initial_count)

    def stream_unread_count(self, *, user_id: UUID, initial_count: int) -> Any:
        return unread_count_streamer(user_id, initial_count)
