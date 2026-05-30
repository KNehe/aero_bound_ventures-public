from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.application.admin.admin_bookings import (
    AdminBookingNotFound,
    AdminBookingRecord,
    AdminBookingStatsRecord,
    AdminBookingStatsSourceRecord,
    AdminBookingUserRecord,
    AdminBookingsPage,
    GetAdminBooking,
    GetAdminBookingStats,
    ListAdminBookings,
)
from backend.models.bookings import BookingStatus


USER_ID = uuid4()
OTHER_USER_ID = uuid4()
BOOKING_ID = uuid4()
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
NOW = datetime(2026, 1, 8, 12, 0, tzinfo=timezone.utc)


class StubAdminBookingRepository:
    def __init__(self):
        self.stats_sources = []
        self.page = AdminBookingsPage(
            items=[make_booking()],
            next_cursor="cursor_2",
            has_more=False,
            has_previous=False,
            total_count=1,
            limit=20,
        )
        self.booking = make_booking()
        self.calls = []

    def get_booking_stats_sources(self):
        self.calls.append({"method": "get_booking_stats_sources"})
        return self.stats_sources

    def get_admin_bookings(self, *, cursor, limit, include_count):
        self.calls.append(
            {
                "method": "get_admin_bookings",
                "cursor": cursor,
                "limit": limit,
                "include_count": include_count,
            }
        )
        return self.page

    def get_admin_booking(self, booking_id: str):
        self.calls.append({"method": "get_admin_booking", "booking_id": booking_id})
        return self.booking


def make_booking() -> AdminBookingRecord:
    return AdminBookingRecord(
        id=BOOKING_ID,
        flight_order_id="AMADEUS_ORDER_1",
        status=BookingStatus.PAID,
        created_at=CREATED_AT,
        ticket_url="https://tickets.example.com/ticket.pdf",
        total_price=100.0,
        user=AdminBookingUserRecord(
            id=USER_ID,
            email="traveler@example.com",
        ),
        amadeus_order_response={"id": "AMADEUS_ORDER_1"},
    )


def test_get_admin_booking_stats_calculates_dashboard_metrics():
    repository = StubAdminBookingRepository()
    repository.stats_sources = [
        AdminBookingStatsSourceRecord(
            user_id=USER_ID,
            status=BookingStatus.PAID,
            total_price=100.0,
            created_at=NOW,
        ),
        AdminBookingStatsSourceRecord(
            user_id=USER_ID,
            status=BookingStatus.CANCELLED,
            total_price=500.0,
            created_at=NOW - timedelta(days=1),
        ),
        AdminBookingStatsSourceRecord(
            user_id=OTHER_USER_ID,
            status=BookingStatus.PAID,
            total_price=50.0,
            created_at=NOW - timedelta(days=8),
        ),
    ]
    use_case = GetAdminBookingStats(admin_booking_repository=repository)

    result = use_case.execute(now=NOW)

    assert result == AdminBookingStatsRecord(
        total_bookings=3,
        total_revenue=150.0,
        active_users=2,
        bookings_today=1,
        bookings_this_week=2,
    )


def test_list_admin_bookings_reads_page_from_repository():
    repository = StubAdminBookingRepository()
    use_case = ListAdminBookings(admin_booking_repository=repository)

    result = use_case.execute(
        cursor="cursor_1",
        limit=20,
        include_count=True,
    )

    assert result == repository.page
    assert repository.calls == [
        {
            "method": "get_admin_bookings",
            "cursor": "cursor_1",
            "limit": 20,
            "include_count": True,
        }
    ]


def test_get_admin_booking_reads_booking_from_repository():
    repository = StubAdminBookingRepository()
    use_case = GetAdminBooking(admin_booking_repository=repository)

    result = use_case.execute(booking_id=str(BOOKING_ID))

    assert result == repository.booking
    assert repository.calls == [
        {"method": "get_admin_booking", "booking_id": str(BOOKING_ID)}
    ]


def test_get_admin_booking_rejects_missing_booking():
    repository = StubAdminBookingRepository()
    repository.booking = None
    use_case = GetAdminBooking(admin_booking_repository=repository)

    with pytest.raises(AdminBookingNotFound):
        use_case.execute(booking_id=str(BOOKING_ID))
