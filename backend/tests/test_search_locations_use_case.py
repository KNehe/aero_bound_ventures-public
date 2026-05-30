from dataclasses import dataclass

from backend.application.flights.search_locations import SearchLocations
from backend.infrastructure.flights.amadeus_location_search_gateway import (
    AmadeusLocationSearchGateway,
)


@dataclass
class StubLocationSearchProvider:
    calls: list[dict]

    def search_locations(self, criteria):
        self.calls.append(criteria)
        return [{"iataCode": "NBO"}]


@dataclass
class StubLocationSearchCache:
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
    calls: list[dict]

    def airport_city_search(self, criteria):
        self.calls.append(criteria)
        return [{"iataCode": "NBO"}]


def test_search_locations_returns_cached_response_without_provider_call():
    cache_key = 'location_search:{"keyword":"NBO","sub_type":"AIRPORT"}'
    cache = StubLocationSearchCache(
        values={cache_key: [{"iataCode": "NBO"}]},
        keys=[],
        saved=[],
    )
    provider = StubLocationSearchProvider(calls=[])
    use_case = SearchLocations(provider=provider, cache=cache)

    result = use_case.execute({"keyword": "NBO", "sub_type": "AIRPORT"})

    assert result == [{"iataCode": "NBO"}]
    assert provider.calls == []
    assert cache.keys == [cache_key]


def test_search_locations_fetches_and_caches_provider_response():
    cache = StubLocationSearchCache(values={}, keys=[], saved=[])
    provider = StubLocationSearchProvider(calls=[])
    use_case = SearchLocations(provider=provider, cache=cache)
    criteria = {"keyword": "Nairobi", "sub_type": "ANY"}

    result = use_case.execute(criteria)

    assert result == [{"iataCode": "NBO"}]
    assert provider.calls == [criteria]
    assert cache.saved == [
        ('location_search:{"keyword":"Nairobi","sub_type":"ANY"}', result)
    ]


def test_amadeus_location_search_gateway_uses_airport_city_search():
    flight_service = StubAmadeusFlightService(calls=[])
    gateway = AmadeusLocationSearchGateway(flight_service)
    criteria = {"keyword": "Nairobi", "sub_type": "ANY"}

    result = gateway.search_locations(criteria)

    assert result == [{"iataCode": "NBO"}]
    assert flight_service.calls == [criteria]
