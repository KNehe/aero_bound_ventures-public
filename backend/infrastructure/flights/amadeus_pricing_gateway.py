from typing import Any

from amadeus import ResponseError
from amadeus.client.errors import ClientError

from backend.application.flights.confirm_flight_price import (
    FlightPricingProviderError,
    FlightPricingResult,
    InvalidFlightPricingRequest,
)
from backend.external_services.interface import FlightServiceProtocol


class AmadeusPricingGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def confirm_price(self, flight_offer: dict[str, Any]) -> FlightPricingResult:
        try:
            return self.flight_service.confirm_price(flight_offer)
        except ValueError as exc:
            raise InvalidFlightPricingRequest from exc
        except ClientError as exc:
            raise InvalidFlightPricingRequest from exc
        except ResponseError as exc:
            raise FlightPricingProviderError from exc
