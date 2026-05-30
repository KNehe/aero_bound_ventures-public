from dataclasses import dataclass

from backend.application.flights.get_seat_map_from_flight_offer import (
    GetSeatMapFromFlightOffer,
)
from backend.infrastructure.flights.amadeus_seat_map_gateway import (
    AmadeusSeatMapGateway,
)


@dataclass
class StubSeatMapFromOfferProvider:
    calls: list[dict]

    def view_seat_map_for_offer(self, flight_offer):
        self.calls.append(flight_offer)
        return [{"id": "seatmap_from_offer_1"}]


@dataclass
class StubAmadeusFlightService:
    calls: list[dict]

    def view_seat_map_post(self, flight_offer):
        self.calls.append(flight_offer)
        return [{"id": "seatmap_from_offer_1"}]


def test_get_seat_map_from_flight_offer_delegates_to_provider_with_copied_payload():
    provider = StubSeatMapFromOfferProvider(calls=[])
    use_case = GetSeatMapFromFlightOffer(seat_map_provider=provider)
    flight_offer = {"id": "offer_1", "type": "flight-offer"}

    result = use_case.execute(flight_offer)

    assert result == [{"id": "seatmap_from_offer_1"}]
    assert provider.calls == [flight_offer]
    assert provider.calls[0] is not flight_offer


def test_amadeus_seat_map_gateway_uses_flight_offer_lookup():
    flight_service = StubAmadeusFlightService(calls=[])
    gateway = AmadeusSeatMapGateway(flight_service)
    flight_offer = {"id": "offer_1", "type": "flight-offer"}

    result = gateway.view_seat_map_for_offer(flight_offer)

    assert result == [{"id": "seatmap_from_offer_1"}]
    assert flight_service.calls == [flight_offer]
