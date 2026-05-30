import uuid
from datetime import datetime, timezone

import pytest

from backend.application.bookings.get_booking_details import (
    BookingDetailsNotFound,
    BookingDetailsRecord,
    GetBookingDetails,
)
from backend.infrastructure.bookings.booking_success_presenter import (
    BookingSuccessPresenter,
)


BOOKING_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
CREATED_AT = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class StubBookingDetailsRepository:
    def __init__(self, booking=None):
        self.booking = booking
        self.calls = []

    def get_user_booking_details(self, *, booking_id, user_id):
        self.calls.append({"booking_id": booking_id, "user_id": user_id})
        return self.booking


class StubBookingDetailsPresenter:
    def __init__(self):
        self.calls = []

    def present(self, *, booking, user_email):
        self.calls.append({"booking": booking, "user_email": user_email})
        return {"orderId": str(booking.id), "status": booking.status}


def make_booking_record():
    return BookingDetailsRecord(
        id=BOOKING_ID,
        created_at=CREATED_AT,
        status="confirmed",
        amadeus_order_response={
            "associatedRecords": [{"reference": "PNR123"}],
            "flightOffers": [
                {
                    "itineraries": [],
                    "price": {
                        "currency": "USD",
                        "grandTotal": "120.50",
                        "base": "100.00",
                        "fees": [],
                    },
                }
            ],
            "travelers": [],
            "contacts": [],
        },
        ticket_url="https://tickets.example.com/ticket.pdf",
    )


def test_get_booking_details_presents_user_booking():
    booking = make_booking_record()
    repository = StubBookingDetailsRepository(booking=booking)
    presenter = StubBookingDetailsPresenter()
    use_case = GetBookingDetails(
        booking_repository=repository,
        presenter=presenter,
    )

    response = use_case.execute(
        booking_id=BOOKING_ID,
        user_id=USER_ID,
        user_email="traveler@example.com",
    )

    assert response == {"orderId": str(BOOKING_ID), "status": "confirmed"}
    assert repository.calls == [{"booking_id": BOOKING_ID, "user_id": USER_ID}]
    assert presenter.calls == [
        {"booking": booking, "user_email": "traveler@example.com"}
    ]


def test_get_booking_details_raises_when_booking_is_not_found():
    repository = StubBookingDetailsRepository()
    presenter = StubBookingDetailsPresenter()
    use_case = GetBookingDetails(
        booking_repository=repository,
        presenter=presenter,
    )

    with pytest.raises(BookingDetailsNotFound):
        use_case.execute(
            booking_id=BOOKING_ID,
            user_id=USER_ID,
            user_email="traveler@example.com",
        )

    assert presenter.calls == []


def test_booking_success_presenter_returns_frontend_booking_details_shape():
    presenter = BookingSuccessPresenter()
    booking = make_booking_record()

    response = presenter.present(
        booking=booking,
        user_email="traveler@example.com",
    )

    assert response["orderId"] == str(BOOKING_ID)
    assert response["pnr"] == "PNR123"
    assert response["bookingDate"] == "2026-01-01T12:00:00Z"
    assert response["status"] == "confirmed"
    assert response["contact"]["email"] == "traveler@example.com"
    assert response["ticket_url"] == "https://tickets.example.com/ticket.pdf"
