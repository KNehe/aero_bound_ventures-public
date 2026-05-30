from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from backend.models.bookings import BookingStatus


@dataclass(frozen=True)
class AdminBookingUserRecord:
    id: UUID
    email: str


@dataclass(frozen=True)
class AdminBookingRecord:
    id: UUID
    flight_order_id: str
    status: str
    created_at: datetime
    ticket_url: str | None
    total_price: float
    user: AdminBookingUserRecord
    amadeus_order_response: dict | None


@dataclass(frozen=True)
class AdminBookingStatsSourceRecord:
    user_id: UUID
    status: str
    total_price: float
    created_at: datetime


@dataclass(frozen=True)
class AdminBookingStatsRecord:
    total_bookings: int
    total_revenue: float
    active_users: int
    bookings_today: int
    bookings_this_week: int


@dataclass(frozen=True)
class AdminBookingsPage:
    items: list[AdminBookingRecord]
    next_cursor: str | None
    has_more: bool
    has_previous: bool
    total_count: int | None
    limit: int


class AdminBookingError(Exception):
    pass


class AdminBookingNotFound(AdminBookingError):
    pass


class AdminBookingRepository(Protocol):
    def get_booking_stats_sources(self) -> list[AdminBookingStatsSourceRecord]: ...

    def get_admin_bookings(
        self,
        *,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> AdminBookingsPage: ...

    def get_admin_booking(self, booking_id: str) -> AdminBookingRecord | None: ...


class GetAdminBookingStats:
    def __init__(self, *, admin_booking_repository: AdminBookingRepository):
        self.admin_booking_repository = admin_booking_repository

    def execute(self, *, now: datetime | None = None) -> AdminBookingStatsRecord:
        bookings = self.admin_booking_repository.get_booking_stats_sources()

        checked_at = now or datetime.now(timezone.utc)
        today_start = datetime(
            checked_at.year,
            checked_at.month,
            checked_at.day,
            tzinfo=timezone.utc,
        )
        one_week_ago = checked_at - timedelta(days=7)

        return AdminBookingStatsRecord(
            total_bookings=len(bookings),
            total_revenue=sum(
                booking.total_price
                for booking in bookings
                if booking.status == BookingStatus.PAID
            ),
            active_users=len({booking.user_id for booking in bookings}),
            bookings_today=sum(
                1
                for booking in bookings
                if self._as_aware_datetime(booking.created_at) >= today_start
            ),
            bookings_this_week=sum(
                1
                for booking in bookings
                if self._as_aware_datetime(booking.created_at) >= one_week_ago
            ),
        )

    @staticmethod
    def _as_aware_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class ListAdminBookings:
    def __init__(self, *, admin_booking_repository: AdminBookingRepository):
        self.admin_booking_repository = admin_booking_repository

    def execute(
        self,
        *,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> AdminBookingsPage:
        return self.admin_booking_repository.get_admin_bookings(
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )


class GetAdminBooking:
    def __init__(self, *, admin_booking_repository: AdminBookingRepository):
        self.admin_booking_repository = admin_booking_repository

    def execute(self, *, booking_id: str) -> AdminBookingRecord:
        booking = self.admin_booking_repository.get_admin_booking(booking_id)
        if not booking:
            raise AdminBookingNotFound
        return booking
