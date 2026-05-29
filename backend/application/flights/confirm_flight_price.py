from collections.abc import Mapping
from typing import Any, Protocol


FlightPricingResult = Any


class FlightPricingError(Exception):
    pass


class InvalidFlightPricingRequest(FlightPricingError):
    pass


class FlightPricingProviderError(FlightPricingError):
    pass


class FlightPricingProvider(Protocol):
    def confirm_price(self, flight_offer: dict[str, Any]) -> FlightPricingResult:
        ...


class ConfirmFlightPrice:
    def __init__(self, provider: FlightPricingProvider):
        self.provider = provider

    def execute(self, flight_offer: Mapping[str, Any]) -> FlightPricingResult:
        return self.provider.confirm_price(dict(flight_offer))
