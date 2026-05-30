from dataclasses import dataclass

from backend.application.flights.get_travelled_destinations import (
    GetTravelledDestinations,
)
from backend.infrastructure.flights.amadeus_travel_analytics_gateway import (
    AmadeusTravelAnalyticsGateway,
)


@dataclass
class StubTravelledDestinationsProvider:
    response: list[dict]
    calls: list[tuple[str, str]]

    def get_travelled_destinations(self, *, origin_city_code, period):
        self.calls.append((origin_city_code, period))
        return self.response


@dataclass
class StubTravelledDestinationsCache:
    values: dict
    keys: list[str]
    saved: list[tuple[str, list[dict]]]

    def get(self, key):
        self.keys.append(key)
        return self.values.get(key)

    def set(self, key, value):
        self.saved.append((key, value))
        self.values[key] = value


@dataclass
class StubAmadeusFlightService:
    calls: list[tuple[str, str]]

    def get_most_travelled_destinations(self, origin_city_code, period):
        self.calls.append((origin_city_code, period))
        return [{"destination": "MBA"}]


def test_get_travelled_destinations_returns_cached_response_without_provider_call():
    cache_key = 'travelled_destinations:{"origin_city_code":"NBO","period":"2026-01"}'
    cache = StubTravelledDestinationsCache(
        values={cache_key: [{"destination": "MBA"}]},
        keys=[],
        saved=[],
    )
    provider = StubTravelledDestinationsProvider(response=[], calls=[])
    use_case = GetTravelledDestinations(provider=provider, cache=cache)

    result = use_case.execute(origin_city_code="NBO", period="2026-01")

    assert result == [{"destination": "MBA"}]
    assert provider.calls == []
    assert cache.keys == [cache_key]


def test_get_travelled_destinations_fetches_and_caches_provider_response():
    cache = StubTravelledDestinationsCache(values={}, keys=[], saved=[])
    provider = StubTravelledDestinationsProvider(
        response=[{"destination": "MBA"}],
        calls=[],
    )
    use_case = GetTravelledDestinations(provider=provider, cache=cache)

    result = use_case.execute(origin_city_code="NBO", period="2026-01")

    assert result == [{"destination": "MBA"}]
    assert provider.calls == [("NBO", "2026-01")]
    assert cache.saved == [
        (
            'travelled_destinations:{"origin_city_code":"NBO","period":"2026-01"}',
            result,
        )
    ]


def test_get_travelled_destinations_does_not_cache_empty_response():
    cache = StubTravelledDestinationsCache(values={}, keys=[], saved=[])
    provider = StubTravelledDestinationsProvider(response=[], calls=[])
    use_case = GetTravelledDestinations(provider=provider, cache=cache)

    result = use_case.execute(origin_city_code="NBO", period="2026-01")

    assert result == []
    assert cache.saved == []


def test_amadeus_travel_analytics_gateway_uses_travelled_destinations_lookup():
    flight_service = StubAmadeusFlightService(calls=[])
    gateway = AmadeusTravelAnalyticsGateway(flight_service)

    result = gateway.get_travelled_destinations(
        origin_city_code="NBO",
        period="2026-01",
    )

    assert result == [{"destination": "MBA"}]
    assert flight_service.calls == [("NBO", "2026-01")]
