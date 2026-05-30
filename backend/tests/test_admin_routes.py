from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Session

from backend.application.admin.admin_bookings import (
    AdminBookingRecord,
    AdminBookingStatsRecord,
    AdminBookingUserRecord,
    AdminBookingsPage,
)
from backend.crud.users import create_user
from backend.models.bookings import BookingStatus
from backend.routers.admin import (
    get_admin_booking_stats_use_case,
    get_admin_booking_use_case,
    get_list_admin_bookings_use_case,
)
from backend.utils.security import get_current_user
from tests.conftest import API_V1_PREFIX


BOOKING_ID = uuid4()
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class StubAdminBookingStatsUseCase:
    def __init__(self):
        self.calls = 0

    def execute(self):
        self.calls += 1
        return AdminBookingStatsRecord(
            total_bookings=3,
            total_revenue=150.0,
            active_users=2,
            bookings_today=1,
            bookings_this_week=2,
        )


class StubListAdminBookingsUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, cursor, limit, include_count):
        self.calls.append(
            {
                "cursor": cursor,
                "limit": limit,
                "include_count": include_count,
            }
        )
        return AdminBookingsPage(
            items=[make_booking()],
            next_cursor="cursor_2",
            has_more=False,
            has_previous=True,
            total_count=1,
            limit=limit,
        )


class StubAdminBookingUseCase:
    def __init__(self):
        self.calls = []

    def execute(self, *, booking_id):
        self.calls.append(booking_id)
        return make_booking(booking_id=booking_id)


def make_booking(*, booking_id=BOOKING_ID) -> AdminBookingRecord:
    return AdminBookingRecord(
        id=booking_id,
        flight_order_id="AMADEUS_ORDER_1",
        status=BookingStatus.PAID,
        created_at=CREATED_AT,
        ticket_url="https://tickets.example.com/ticket.pdf",
        total_price=100.0,
        user=AdminBookingUserRecord(
            id=uuid4(),
            email="traveler@example.com",
        ),
        amadeus_order_response={"id": "AMADEUS_ORDER_1"},
    )


def override_admin_user(client, session: Session):
    admin_user = create_user(session, "admin-route@example.com", "password")
    admin_user.is_superuser = True
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    client.app.dependency_overrides[get_current_user] = lambda: admin_user
    return admin_user


def test_admin_booking_stats_route_uses_use_case(client, session: Session):
    override_admin_user(client, session)
    use_case = StubAdminBookingStatsUseCase()
    client.app.dependency_overrides[get_admin_booking_stats_use_case] = lambda: use_case

    try:
        response = client.get(f"{API_V1_PREFIX}/admin/stats/bookings")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "total_bookings": 3,
        "total_revenue": 150.0,
        "active_users": 2,
        "bookings_today": 1,
        "bookings_this_week": 2,
    }
    assert use_case.calls == 1


def test_admin_bookings_route_uses_use_case(client, session: Session):
    override_admin_user(client, session)
    use_case = StubListAdminBookingsUseCase()
    client.app.dependency_overrides[get_list_admin_bookings_use_case] = lambda: use_case

    try:
        response = client.get(
            f"{API_V1_PREFIX}/admin/bookings",
            params={"cursor": "cursor_1", "limit": 20, "include_count": True},
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["id"] == str(BOOKING_ID)
    assert data["items"][0]["user"]["email"] == "traveler@example.com"
    assert data["next_cursor"] == "cursor_2"
    assert data["has_previous"] is True
    assert use_case.calls == [
        {"cursor": "cursor_1", "limit": 20, "include_count": True}
    ]


def test_admin_booking_detail_route_uses_use_case(client, session: Session):
    override_admin_user(client, session)
    use_case = StubAdminBookingUseCase()
    client.app.dependency_overrides[get_admin_booking_use_case] = lambda: use_case

    try:
        response = client.get(f"{API_V1_PREFIX}/admin/bookings/{BOOKING_ID}")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(BOOKING_ID)
    assert response.json()["flight_order_id"] == "AMADEUS_ORDER_1"
    assert use_case.calls == [str(BOOKING_ID)]
