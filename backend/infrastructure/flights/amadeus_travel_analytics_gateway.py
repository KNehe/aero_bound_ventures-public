from amadeus import ResponseError
from amadeus.client.errors import ClientError

from backend.application.flights.get_travelled_destinations import (
    InvalidTravelledDestinationsRequest,
    TravelledDestinationsProviderError,
    TravelledDestinationsResult,
)
from backend.external_services.interface import FlightServiceProtocol


class AmadeusTravelAnalyticsGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def get_travelled_destinations(
        self, *, origin_city_code: str, period: str
    ) -> TravelledDestinationsResult:
        try:
            return self.flight_service.get_most_travelled_destinations(
                origin_city_code,
                period,
            )
        except ClientError as exc:
            raise InvalidTravelledDestinationsRequest from exc
        except ResponseError as exc:
            raise TravelledDestinationsProviderError from exc
