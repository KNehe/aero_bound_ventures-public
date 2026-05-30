from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Session

from backend.application.notifications.mark_all_notifications_read import (
    MarkedNotifications,
)
from backend.application.notifications.notification_records import (
    NotificationPage,
    NotificationRecord,
)
from backend.crud.users import create_user
from backend.routers.notifications import (
    get_delete_notification_use_case,
    get_list_notifications_use_case,
    get_mark_all_notifications_read_use_case,
    get_mark_notification_read_use_case,
    get_unread_notification_count_use_case,
)
from backend.utils.security import get_current_user
from tests.conftest import API_V1_PREFIX


NOTIFICATION_ID = uuid4()
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class StubUnreadCountUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, user_id):
        self.calls.append(user_id)
        return 4


class StubListNotificationsUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, user_id, cursor, limit, include_count):
        self.calls.append(
            {
                "user_id": user_id,
                "cursor": cursor,
                "limit": limit,
                "include_count": include_count,
            }
        )
        return NotificationPage(
            items=[
                NotificationRecord(
                    id=NOTIFICATION_ID,
                    user_id=user_id,
                    message="Ticket uploaded",
                    type="ticket_uploaded",
                    is_read=False,
                    created_at=CREATED_AT,
                )
            ],
            next_cursor="cursor_2",
            has_more=False,
            has_previous=True,
            total_count=1,
            limit=limit,
        )


class StubMarkAllNotificationsReadUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, *, user_id):
        self.calls.append(user_id)
        return MarkedNotifications(marked_as_read=2, unread_count=0)


class StubMarkNotificationReadUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, *, notification_id, user_id):
        self.calls.append({"notification_id": notification_id, "user_id": user_id})
        return NotificationRecord(
            id=notification_id,
            user_id=user_id,
            message="Ticket uploaded",
            type="ticket_uploaded",
            is_read=True,
            created_at=CREATED_AT,
        )


class StubDeleteNotificationUseCase:
    def __init__(self):
        self.calls = []

    async def execute(self, *, notification_id, user_id):
        self.calls.append({"notification_id": notification_id, "user_id": user_id})


def override_current_user(client, session: Session):
    user = create_user(session, "notifications@example.com", "password")
    client.app.dependency_overrides[get_current_user] = lambda: user
    return user


def test_unread_count_route_uses_use_case(client, session: Session):
    user = override_current_user(client, session)
    use_case = StubUnreadCountUseCase()
    client.app.dependency_overrides[get_unread_notification_count_use_case] = (
        lambda: use_case
    )

    try:
        response = client.get(f"{API_V1_PREFIX}/notifications/unread-count")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"unread_count": 4}
    assert use_case.calls == [user.id]


def test_list_notifications_route_uses_use_case(client, session: Session):
    user = override_current_user(client, session)
    use_case = StubListNotificationsUseCase()
    client.app.dependency_overrides[get_list_notifications_use_case] = lambda: use_case

    try:
        response = client.get(
            f"{API_V1_PREFIX}/notifications/",
            params={"cursor": "cursor_1", "limit": 20, "include_count": True},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": str(NOTIFICATION_ID),
                "user_id": str(user.id),
                "message": "Ticket uploaded",
                "type": "ticket_uploaded",
                "is_read": False,
                "created_at": "2026-01-01T12:00:00Z",
            }
        ],
        "next_cursor": "cursor_2",
        "has_more": False,
        "has_previous": True,
        "total_count": 1,
        "limit": 20,
    }
    assert use_case.calls == [
        {
            "user_id": user.id,
            "cursor": "cursor_1",
            "limit": 20,
            "include_count": True,
        }
    ]


def test_mark_all_read_route_uses_use_case(client, session: Session):
    user = override_current_user(client, session)
    use_case = StubMarkAllNotificationsReadUseCase()
    client.app.dependency_overrides[get_mark_all_notifications_read_use_case] = (
        lambda: use_case
    )

    try:
        response = client.put(f"{API_V1_PREFIX}/notifications/mark-all-read")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"marked_as_read": 2}
    assert use_case.calls == [user.id]


def test_mark_as_read_route_uses_use_case(client, session: Session):
    user = override_current_user(client, session)
    use_case = StubMarkNotificationReadUseCase()
    client.app.dependency_overrides[get_mark_notification_read_use_case] = (
        lambda: use_case
    )

    try:
        response = client.put(
            f"{API_V1_PREFIX}/notifications/{NOTIFICATION_ID}/mark-read"
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["is_read"] is True
    assert use_case.calls == [{"notification_id": NOTIFICATION_ID, "user_id": user.id}]


def test_delete_notification_route_uses_use_case(client, session: Session):
    user = override_current_user(client, session)
    use_case = StubDeleteNotificationUseCase()
    client.app.dependency_overrides[get_delete_notification_use_case] = lambda: use_case

    try:
        response = client.delete(f"{API_V1_PREFIX}/notifications/{NOTIFICATION_ID}")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 204
    assert use_case.calls == [{"notification_id": NOTIFICATION_ID, "user_id": user.id}]
