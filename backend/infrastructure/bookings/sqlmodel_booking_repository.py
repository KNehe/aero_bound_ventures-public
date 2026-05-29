from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from backend.application.bookings.create_flight_order import (
    CreatedFlightBooking,
)
from backend.application.bookings.get_flight_order_details import (
    FlightOrderDetailsRecord,
)
from backend.models.bookings import Booking


class SqlModelBookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_booking(
        self,
        *,
        user_id: UUID,
        flight_order_id: str,
        order_response: dict[str, Any],
        total_price: float,
    ) -> CreatedFlightBooking:
        booking = Booking(
            user_id=user_id,
            flight_order_id=flight_order_id,
            amadeus_order_response=order_response,
            total_price=total_price,
        )

        try:
            self.session.add(booking)
            self.session.commit()
            self.session.refresh(booking)
        except Exception:
            self.session.rollback()
            raise

        return CreatedFlightBooking(
            id=booking.id,
            flight_order_id=booking.flight_order_id,
            status=booking.status,
        )

    def get_user_flight_order_details(
        self, *, booking_id: UUID, user_id: UUID
    ) -> FlightOrderDetailsRecord | None:
        booking = self.session.exec(
            select(Booking)
            .where(Booking.id == booking_id)
            .where(Booking.user_id == user_id)
        ).first()
        if not booking:
            return None

        return FlightOrderDetailsRecord(
            id=booking.id,
            created_at=booking.created_at,
            status=booking.status,
            amadeus_order_response=booking.amadeus_order_response,
            ticket_url=booking.ticket_url,
        )
