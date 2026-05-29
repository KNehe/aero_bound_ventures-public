from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class FlightOrderDetailsRecord:
    id: UUID
    created_at: datetime
    status: str
    amadeus_order_response: dict[str, Any] | None
    ticket_url: str | None


class FlightOrderDetailsError(Exception):
    pass


class FlightOrderDetailsNotFound(FlightOrderDetailsError):
    pass


class FlightOrderDetailsRepository(Protocol):
    def get_user_flight_order_details(
        self, *, booking_id: UUID, user_id: UUID
    ) -> FlightOrderDetailsRecord | None:
        ...


class FlightOrderDetailsPresenter(Protocol):
    def present(
        self, *, booking: FlightOrderDetailsRecord, user_email: str
    ) -> dict[str, Any]:
        ...


class GetFlightOrderDetails:
    def __init__(
        self,
        *,
        booking_repository: FlightOrderDetailsRepository,
        presenter: FlightOrderDetailsPresenter,
    ):
        self.booking_repository = booking_repository
        self.presenter = presenter

    def execute(
        self, *, booking_id: UUID, user_id: UUID, user_email: str
    ) -> dict[str, Any]:
        booking = self.booking_repository.get_user_flight_order_details(
            booking_id=booking_id,
            user_id=user_id,
        )
        if not booking:
            raise FlightOrderDetailsNotFound

        return self.presenter.present(booking=booking, user_email=user_email)
