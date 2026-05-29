from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True)
class CreatedFlightBooking:
    id: UUID
    flight_order_id: str
    status: str


class FlightOrderError(Exception):
    pass


class InvalidFlightOrderRequest(FlightOrderError):
    pass


class FlightOrderProviderError(FlightOrderError):
    pass


class FlightOrderProvider(Protocol):
    def create_order(self, order_request: dict[str, Any]) -> dict[str, Any]:
        ...


class FlightBookingRepository(Protocol):
    def create_booking(
        self,
        *,
        user_id: UUID,
        flight_order_id: str,
        order_response: dict[str, Any],
        total_price: float,
    ) -> CreatedFlightBooking:
        ...


class UserBookingCache(Protocol):
    def invalidate_user_bookings(self, user_id: UUID) -> None:
        ...


class BookingEventPublisher(Protocol):
    def publish_booking_created(
        self,
        *,
        booking_id: UUID,
        user_id: UUID,
        pnr: str,
        user_email: str,
    ) -> None:
        ...


class CreateFlightOrder:
    def __init__(
        self,
        *,
        order_provider: FlightOrderProvider,
        booking_repository: FlightBookingRepository,
        booking_cache: UserBookingCache,
        event_publisher: BookingEventPublisher,
    ):
        self.order_provider = order_provider
        self.booking_repository = booking_repository
        self.booking_cache = booking_cache
        self.event_publisher = event_publisher

    def execute(
        self,
        *,
        user_id: UUID,
        user_email: str,
        order_request: Mapping[str, Any],
    ) -> CreatedFlightBooking:
        request_body = dict(order_request)
        order_response = self.order_provider.create_order(request_body)
        flight_order_id = order_response.get("id")
        if not flight_order_id:
            raise FlightOrderProviderError(
                "Flight provider did not return an order id"
            )

        booking = self.booking_repository.create_booking(
            user_id=user_id,
            flight_order_id=flight_order_id,
            order_response=order_response,
            total_price=self._extract_total_price(order_response),
        )

        self.booking_cache.invalidate_user_bookings(user_id)
        self.event_publisher.publish_booking_created(
            booking_id=booking.id,
            user_id=user_id,
            pnr=self._extract_pnr(order_response),
            user_email=user_email,
        )

        return booking

    @staticmethod
    def _extract_total_price(order_response: Mapping[str, Any]) -> float:
        flight_offers = order_response.get("flightOffers", [])
        if not flight_offers:
            return 0.0

        price_info = flight_offers[0].get("price", {})
        grand_total = price_info.get("grandTotal", "0")
        try:
            return float(grand_total)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _extract_pnr(order_response: Mapping[str, Any]) -> str:
        associated_records = order_response.get("associatedRecords") or [{}]
        return associated_records[0].get("reference", "N/A")
