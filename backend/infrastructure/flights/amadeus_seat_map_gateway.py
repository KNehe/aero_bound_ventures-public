from typing import Any

from amadeus import ResponseError
from amadeus.client.errors import ClientError

from backend.application.bookings.get_seat_map import (
    InvalidSeatMapRequest,
    SeatMapProviderError,
)
from backend.application.flights.get_seat_map_from_flight_offer import (
    InvalidSeatMapOfferRequest,
    SeatMapFromOfferProviderError,
)
from backend.external_services.interface import FlightServiceProtocol
from backend.infrastructure.flights.amadeus_error_parser import (
    parse_amadeus_client_error,
)


class AmadeusSeatMapGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def view_seat_map(self, *, flight_order_id: str) -> list[dict[str, Any]]:
        try:
            return self.flight_service.view_seat_map_get(flight_order_id)
        except ClientError as exc:
            raise InvalidSeatMapRequest(parse_amadeus_client_error(exc)) from exc
        except ResponseError as exc:
            raise SeatMapProviderError from exc

    def view_seat_map_for_offer(
        self, flight_offer: dict[str, Any]
    ) -> list[dict[str, Any]]:
        try:
            return self.flight_service.view_seat_map_post(flight_offer)
        except ClientError as exc:
            raise InvalidSeatMapOfferRequest(parse_amadeus_client_error(exc)) from exc
        except ResponseError as exc:
            raise SeatMapFromOfferProviderError from exc
