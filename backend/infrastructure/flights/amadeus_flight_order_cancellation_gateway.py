from amadeus import ResponseError

from backend.external_services.interface import FlightServiceProtocol


class AmadeusFlightOrderCancellationGateway:
    def __init__(self, flight_service: FlightServiceProtocol):
        self.flight_service = flight_service

    def cancel_order(self, flight_order_id: str) -> None:
        try:
            self.flight_service.cancel_flight_order(flight_order_id)
        except ResponseError as error:
            raise error
