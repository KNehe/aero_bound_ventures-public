from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from backend.application.admin.admin_bookings import (
    AdminBookingRecord,
    AdminBookingStatsSourceRecord,
    AdminBookingUserRecord,
    AdminBookingsPage,
)
from backend.crud.bookings import get_all_bookings_cursor
from backend.models.bookings import Booking


class SqlModelAdminBookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_booking_stats_sources(self) -> list[AdminBookingStatsSourceRecord]:
        bookings = self.session.exec(select(Booking)).all()
        return [
            AdminBookingStatsSourceRecord(
                user_id=booking.user_id,
                status=booking.status,
                total_price=booking.total_price,
                created_at=booking.created_at,
            )
            for booking in bookings
        ]

    def get_admin_bookings(
        self,
        *,
        cursor: str | None,
        limit: int,
        include_count: bool,
    ) -> AdminBookingsPage:
        bookings, next_cursor, has_more, total_count = get_all_bookings_cursor(
            self.session,
            cursor=cursor,
            limit=limit,
            include_count=include_count,
        )

        return AdminBookingsPage(
            items=[self._to_record(booking) for booking in bookings],
            next_cursor=next_cursor,
            has_more=has_more,
            has_previous=cursor is not None,
            total_count=total_count,
            limit=limit,
        )

    def get_admin_booking(self, booking_id: str) -> AdminBookingRecord | None:
        booking = self.session.exec(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.user))
        ).first()
        if not booking:
            return None

        return self._to_record(booking)

    @staticmethod
    def _to_record(booking: Booking) -> AdminBookingRecord:
        return AdminBookingRecord(
            id=booking.id,
            flight_order_id=booking.flight_order_id,
            status=booking.status,
            created_at=booking.created_at,
            ticket_url=booking.ticket_url,
            total_price=booking.total_price,
            user=AdminBookingUserRecord(
                id=booking.user.id,
                email=str(booking.user.email),
            ),
            amadeus_order_response=booking.amadeus_order_response,
        )
