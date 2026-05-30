from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class BookingDetailsRecord:
    id: UUID
    created_at: datetime
    status: str
    amadeus_order_response: dict[str, Any] | None
    ticket_url: str | None


class BookingDetailsError(Exception):
    pass


class BookingDetailsNotFound(BookingDetailsError):
    pass


class BookingDetailsRepository(Protocol):
    def get_user_booking_details(
        self, *, booking_id: UUID, user_id: UUID
    ) -> BookingDetailsRecord | None: ...


class BookingDetailsPresenter(Protocol):
    def present(
        self, *, booking: BookingDetailsRecord, user_email: str
    ) -> dict[str, Any]: ...


class GetBookingDetails:
    def __init__(
        self,
        *,
        booking_repository: BookingDetailsRepository,
        presenter: BookingDetailsPresenter,
    ):
        self.booking_repository = booking_repository
        self.presenter = presenter

    def execute(
        self, *, booking_id: UUID, user_id: UUID, user_email: str
    ) -> dict[str, Any]:
        booking = self.booking_repository.get_user_booking_details(
            booking_id=booking_id,
            user_id=user_id,
        )
        if not booking:
            raise BookingDetailsNotFound

        return self.presenter.present(booking=booking, user_email=user_email)
