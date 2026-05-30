from collections.abc import Mapping
from typing import Any, Protocol


SeatMapResult = list[dict[str, Any]]


class SeatMapFromOfferError(Exception):
    pass


class InvalidSeatMapOfferRequest(SeatMapFromOfferError):
    pass


class SeatMapFromOfferProviderError(SeatMapFromOfferError):
    pass


class SeatMapFromOfferProvider(Protocol):
    def view_seat_map_for_offer(
        self, flight_offer: dict[str, Any]
    ) -> SeatMapResult: ...


class GetSeatMapFromFlightOffer:
    def __init__(self, *, seat_map_provider: SeatMapFromOfferProvider):
        self.seat_map_provider = seat_map_provider

    def execute(self, flight_offer: Mapping[str, Any]) -> SeatMapResult:
        return self.seat_map_provider.view_seat_map_for_offer(dict(flight_offer))
