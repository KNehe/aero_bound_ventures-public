from typing import Any

from amadeus import ResponseError
from amadeus.client.errors import ClientError

from backend.application.flights.search_flights import (
    FlightSearchProviderError,
    FlightSearchResult,
    InvalidFlightSearchRequest,
)
from backend.external_services.interface import FlightServiceProtocol


class AmadeusSearchGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def search(self, criteria: dict[str, Any]) -> FlightSearchResult:
        try:
            return self.flight_service.search_flights_get(criteria)
        except ClientError as exc:
            raise InvalidFlightSearchRequest from exc
        except ResponseError as exc:
            raise FlightSearchProviderError from exc
