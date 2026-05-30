from typing import Any

from amadeus import ResponseError
from amadeus.client.errors import ClientError

from backend.application.flights.search_locations import (
    InvalidLocationSearchRequest,
    LocationSearchProviderError,
    LocationSearchResult,
)
from backend.external_services.interface import FlightServiceProtocol


class AmadeusLocationSearchGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def search_locations(self, criteria: dict[str, Any]) -> LocationSearchResult:
        try:
            return self.flight_service.airport_city_search(criteria)
        except ClientError as exc:
            raise InvalidLocationSearchRequest from exc
        except ResponseError as exc:
            raise LocationSearchProviderError from exc
