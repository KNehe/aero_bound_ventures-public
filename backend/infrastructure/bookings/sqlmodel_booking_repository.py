from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from backend.application.bookings.create_flight_order import (
    CreatedFlightBooking,
)
from backend.application.bookings.cancel_booking import (
    BookingCancellationRecord,
)
from backend.application.bookings.get_booking_details import (
    BookingDetailsRecord,
)
from backend.application.payments.initiate_payment import PaymentBookingRecord
from backend.application.payments.process_payment_callback import (
    PaymentCallbackBookingRecord,
)
from backend.application.payments.process_payment_notification import (
    PaymentNotificationBookingRecord,
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

    def get_user_booking_details(
        self, *, booking_id: UUID, user_id: UUID
    ) -> BookingDetailsRecord | None:
        booking = self.session.exec(
            select(Booking)
            .where(Booking.id == booking_id)
            .where(Booking.user_id == user_id)
        ).first()
        if not booking:
            return None

        return BookingDetailsRecord(
            id=booking.id,
            created_at=booking.created_at,
            status=booking.status,
            amadeus_order_response=booking.amadeus_order_response,
            ticket_url=booking.ticket_url,
        )

    def get_user_booking_to_cancel(
        self, *, booking_id: UUID, user_id: UUID
    ) -> BookingCancellationRecord | None:
        booking = self.session.exec(
            select(Booking)
            .where(Booking.id == booking_id)
            .where(Booking.user_id == user_id)
        ).first()
        if not booking:
            return None

        pnr = None
        if booking.amadeus_order_response:
            associated_records = booking.amadeus_order_response.get(
                "associatedRecords", []
            )
            if associated_records:
                pnr = associated_records[0].get("reference")

        return BookingCancellationRecord(
            id=booking.id,
            user_id=booking.user_id,
            flight_order_id=booking.flight_order_id,
            status=booking.status,
            pnr=pnr,
        )

    def get_payment_booking(self, booking_id: str) -> PaymentBookingRecord | None:
        booking = self.session.exec(
            select(Booking).where(Booking.id == booking_id)
        ).first()
        if not booking:
            return None

        return PaymentBookingRecord(
            id=booking.id,
            user_id=booking.user_id,
            status=booking.status,
        )

    def get_payment_callback_booking(
        self, booking_id: str
    ) -> PaymentCallbackBookingRecord | None:
        booking = self.session.exec(
            select(Booking).where(Booking.id == booking_id)
        ).first()
        if not booking:
            return None

        pnr = "N/A"
        if booking.amadeus_order_response:
            associated_records = booking.amadeus_order_response.get(
                "associatedRecords", []
            )
            if associated_records:
                pnr = associated_records[0].get("reference", "N/A")

        return PaymentCallbackBookingRecord(
            id=booking.id,
            user_id=booking.user_id,
            user_email=booking.user.email,
            pnr=pnr,
        )

    def get_payment_notification_booking(
        self, booking_id: str
    ) -> PaymentNotificationBookingRecord | None:
        booking = self.session.exec(
            select(Booking).where(Booking.id == booking_id)
        ).first()
        if not booking:
            return None

        pnr = "N/A"
        if booking.amadeus_order_response:
            associated_records = booking.amadeus_order_response.get(
                "associatedRecords", []
            )
            if associated_records:
                pnr = associated_records[0].get("reference", "N/A")

        return PaymentNotificationBookingRecord(
            id=booking.id,
            user_id=booking.user_id,
            user_email=booking.user.email,
            pnr=pnr,
        )

    def update_payment_booking_status(self, booking_id: UUID, status: str) -> None:
        booking = self.session.exec(
            select(Booking).where(Booking.id == booking_id)
        ).first()
        if not booking:
            return

        booking.status = status
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
