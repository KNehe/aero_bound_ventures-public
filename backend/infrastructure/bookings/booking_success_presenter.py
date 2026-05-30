from typing import Any

from backend.application.bookings.get_booking_details import (
    BookingDetailsRecord,
)
from backend.utils.booking_transformer import transform_amadeus_to_booking_success


class BookingSuccessPresenter:
    def present(
        self, *, booking: BookingDetailsRecord, user_email: str
    ) -> dict[str, Any]:
        return transform_amadeus_to_booking_success(
            booking_id=str(booking.id),
            booking_date=booking.created_at,
            booking_status=booking.status,
            amadeus_order=booking.amadeus_order_response,
            user_email=user_email,
            ticket_url=booking.ticket_url,
        )
