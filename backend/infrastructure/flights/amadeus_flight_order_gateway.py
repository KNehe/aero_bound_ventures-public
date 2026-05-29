from typing import Any

from amadeus import ResponseError
from amadeus.client.errors import ClientError

from backend.application.bookings.create_flight_order import (
    FlightOrderProviderError,
    InvalidFlightOrderRequest,
)
from backend.external_services.interface import FlightServiceProtocol


class AmadeusFlightOrderGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def create_order(self, order_request: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.flight_service.create_flight_order(order_request)
        except ValueError as exc:
            raise InvalidFlightOrderRequest(str(exc)) from exc
        except ClientError as exc:
            raise InvalidFlightOrderRequest(
                "Unable to process your booking request. Please verify your "
                "information and try again."
            ) from exc
        except ResponseError as exc:
            raise FlightOrderProviderError from exc
