from backend.application.flights.confirm_flight_price import ConfirmFlightPrice
from backend.infrastructure.flights.amadeus_pricing_gateway import AmadeusPricingGateway


class StubPricingProvider:
    def __init__(self):
        self.calls = []

    def confirm_price(self, flight_offer):
        self.calls.append(flight_offer)
        return {"data": {"flightOffers": [{"id": "priced_flight"}]}}


class StubAmadeusFlightService:
    def __init__(self):
        self.confirm_price_calls = []

    def confirm_price(self, flight_offer):
        self.confirm_price_calls.append(flight_offer)
        return {"data": {"flightOffers": [{"id": "priced_flight"}]}}


def test_confirm_flight_price_delegates_to_provider_with_copied_payload():
    provider = StubPricingProvider()
    use_case = ConfirmFlightPrice(provider=provider)
    flight_offer = {
        "type": "flight-offer",
        "id": "1",
        "source": "GDS",
    }

    response = use_case.execute(flight_offer)

    assert response == {"data": {"flightOffers": [{"id": "priced_flight"}]}}
    assert provider.calls == [flight_offer]
    assert provider.calls[0] is not flight_offer


def test_amadeus_pricing_gateway_uses_confirm_price_method():
    flight_service = StubAmadeusFlightService()
    gateway = AmadeusPricingGateway(flight_service)
    flight_offer = {
        "type": "flight-offer",
        "id": "1",
        "source": "GDS",
    }

    response = gateway.confirm_price(flight_offer)

    assert response == {"data": {"flightOffers": [{"id": "priced_flight"}]}}
    assert flight_service.confirm_price_calls == [flight_offer]
