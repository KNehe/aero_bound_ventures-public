from datetime import datetime, timezone
from uuid import uuid4

import pytest

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


USER_ID = uuid4()
NOTIFICATION_ID = uuid4()
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class StubNotificationRepository:
    def __init__(self):
        self.unread_count = 3
        self.page = NotificationPage(
            items=[make_notification()],
            next_cursor="cursor_2",
            has_more=True,
            has_previous=False,
            total_count=1,
            limit=20,
        )
        self.marked_all_count = 2
        self.marked_notification = make_notification(is_read=True)
        self.delete_succeeds = True
        self.calls = []

    def get_unread_count(self, user_id):
        self.calls.append({"method": "get_unread_count", "user_id": user_id})
        return self.unread_count

    def get_user_notifications(self, *, user_id, cursor, limit, include_count):
        self.calls.append(
            {
                "method": "get_user_notifications",
                "user_id": user_id,
                "cursor": cursor,
                "limit": limit,
                "include_count": include_count,
            }
        )
        return self.page

    def mark_all_as_read(self, user_id):
        self.calls.append({"method": "mark_all_as_read", "user_id": user_id})
        return self.marked_all_count

    def mark_as_read(self, *, notification_id, user_id):
        self.calls.append(
            {
                "method": "mark_as_read",
                "notification_id": notification_id,
                "user_id": user_id,
            }
        )
        return self.marked_notification

    def delete_notification(self, *, notification_id, user_id):
        self.calls.append(
            {
                "method": "delete_notification",
                "notification_id": notification_id,
                "user_id": user_id,
            }
        )
        return self.delete_succeeds


class StubUnreadCountPublisher:
    def __init__(self):
        self.calls = []
        self.published_count = 0

    async def publish_for_user(self, user_id):
        self.calls.append(user_id)
        return self.published_count


class StubNotificationStreamProvider:
    def __init__(self):
        self.notification_calls = []
        self.unread_count_calls = []

    def stream_notifications(self, *, user_id, initial_count):
        self.notification_calls.append(
            {"user_id": user_id, "initial_count": initial_count}
        )
        return "notification-events"

    def stream_unread_count(self, *, user_id, initial_count):
        self.unread_count_calls.append(
            {"user_id": user_id, "initial_count": initial_count}
        )
        return "count-events"


def make_notification(*, is_read: bool = False):
    return NotificationRecord(
        id=NOTIFICATION_ID,
        user_id=USER_ID,
        message="Ticket uploaded",
        type="ticket_uploaded",
        is_read=is_read,
        created_at=CREATED_AT,
    )


def test_get_unread_notification_count_reads_from_repository():
    repository = StubNotificationRepository()
    use_case = GetUnreadNotificationCount(notification_repository=repository)

    assert use_case.execute(user_id=USER_ID) == 3
    assert repository.calls == [{"method": "get_unread_count", "user_id": USER_ID}]


def test_list_notifications_reads_page_from_repository():
    repository = StubNotificationRepository()
    use_case = ListNotifications(notification_repository=repository)

    result = use_case.execute(
        user_id=USER_ID,
        cursor="cursor_1",
        limit=20,
        include_count=True,
    )

    assert result == repository.page
    assert repository.calls == [
        {
            "method": "get_user_notifications",
            "user_id": USER_ID,
            "cursor": "cursor_1",
            "limit": 20,
            "include_count": True,
        }
    ]


def test_open_notification_stream_uses_initial_unread_count():
    repository = StubNotificationRepository()
    stream_provider = StubNotificationStreamProvider()
    use_case = OpenNotificationStream(
        notification_repository=repository,
        notification_stream_provider=stream_provider,
    )

    stream = use_case.execute(user_id=USER_ID)

    assert stream.events == "notification-events"
    assert stream.initial_count == 3
    assert stream_provider.notification_calls == [
        {"user_id": USER_ID, "initial_count": 3}
    ]


def test_open_unread_count_stream_uses_initial_unread_count():
    repository = StubNotificationRepository()
    stream_provider = StubNotificationStreamProvider()
    use_case = OpenUnreadCountStream(
        notification_repository=repository,
        notification_stream_provider=stream_provider,
    )

    stream = use_case.execute(user_id=USER_ID)

    assert stream.events == "count-events"
    assert stream.initial_count == 3
    assert stream_provider.unread_count_calls == [
        {"user_id": USER_ID, "initial_count": 3}
    ]


@pytest.mark.asyncio
async def test_mark_all_notifications_read_updates_repository_and_publishes_count():
    repository = StubNotificationRepository()
    publisher = StubUnreadCountPublisher()
    use_case = MarkAllNotificationsRead(
        notification_repository=repository,
        unread_count_publisher=publisher,
    )

    result = await use_case.execute(user_id=USER_ID)

    assert result.marked_as_read == 2
    assert result.unread_count == 0
    assert repository.calls == [{"method": "mark_all_as_read", "user_id": USER_ID}]
    assert publisher.calls == [USER_ID]


@pytest.mark.asyncio
async def test_mark_notification_read_updates_single_notification_and_publishes_count():
    repository = StubNotificationRepository()
    publisher = StubUnreadCountPublisher()
    use_case = MarkNotificationRead(
        notification_repository=repository,
        unread_count_publisher=publisher,
    )

    notification = await use_case.execute(
        notification_id=NOTIFICATION_ID,
        user_id=USER_ID,
    )

    assert notification == make_notification(is_read=True)
    assert repository.calls == [
        {
            "method": "mark_as_read",
            "notification_id": NOTIFICATION_ID,
            "user_id": USER_ID,
        }
    ]
    assert publisher.calls == [USER_ID]


@pytest.mark.asyncio
async def test_mark_notification_read_rejects_missing_notification():
    repository = StubNotificationRepository()
    repository.marked_notification = None
    publisher = StubUnreadCountPublisher()
    use_case = MarkNotificationRead(
        notification_repository=repository,
        unread_count_publisher=publisher,
    )

    with pytest.raises(NotificationNotFound):
        await use_case.execute(
            notification_id=NOTIFICATION_ID,
            user_id=USER_ID,
        )

    assert publisher.calls == []


@pytest.mark.asyncio
async def test_delete_notification_deletes_and_publishes_count():
    repository = StubNotificationRepository()
    publisher = StubUnreadCountPublisher()
    use_case = DeleteNotification(
        notification_repository=repository,
        unread_count_publisher=publisher,
    )

    await use_case.execute(notification_id=NOTIFICATION_ID, user_id=USER_ID)

    assert repository.calls == [
        {
            "method": "delete_notification",
            "notification_id": NOTIFICATION_ID,
            "user_id": USER_ID,
        }
    ]
    assert publisher.calls == [USER_ID]


@pytest.mark.asyncio
async def test_delete_notification_rejects_missing_notification():
    repository = StubNotificationRepository()
    repository.delete_succeeds = False
    publisher = StubUnreadCountPublisher()
    use_case = DeleteNotification(
        notification_repository=repository,
        unread_count_publisher=publisher,
    )

    with pytest.raises(NotificationNotFound):
        await use_case.execute(notification_id=NOTIFICATION_ID, user_id=USER_ID)

    assert publisher.calls == []
