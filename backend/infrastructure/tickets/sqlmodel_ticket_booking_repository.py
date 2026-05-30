from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from backend.application.tickets.upload_ticket import TicketBookingRecord
from backend.models.bookings import Booking


class SqlModelTicketBookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_ticket_booking(self, booking_id: UUID) -> TicketBookingRecord | None:
        booking = self.session.exec(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(selectinload(Booking.user))
        ).first()
        if not booking:
            return None

        return TicketBookingRecord(
            id=booking.id,
            pnr=self._booking_pnr(booking),
            user_id=booking.user_id,
            user_email=str(booking.user.email),
        )

    def update_ticket_url(self, *, booking_id: UUID, ticket_url: str) -> bool:
        booking = self.session.exec(
            select(Booking).where(Booking.id == booking_id)
        ).first()
        if not booking:
            return False

        booking.ticket_url = ticket_url
        self.session.add(booking)
        self.session.commit()
        self.session.refresh(booking)
        return True

    @staticmethod
    def _booking_pnr(booking: Booking) -> str:
        if not booking.amadeus_order_response:
            return "N/A"

        associated_records = booking.amadeus_order_response.get("associatedRecords", [])
        if not associated_records:
            return "N/A"

        return associated_records[0].get("reference", "N/A")
