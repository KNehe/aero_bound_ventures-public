from backend.application.flights.search_flights import SearchFlights
from backend.infrastructure.flights.amadeus_search_gateway import AmadeusSearchGateway


EXPECTED_CACHE_KEY = (
    'flight_search:{"adults":1,"departureDate":"2024-12-01",'
    '"destinationLocationCode":"LON","originLocationCode":"NYC"}'
)


class StubFlightProvider:
    def __init__(self):
        self.calls = []

    def search(self, criteria):
        self.calls.append(criteria)
        return [{"id": "flight_1"}]


class StubFlightCache:
    def __init__(self, cached_value=None):
        self.cached_value = cached_value
        self.keys = []
        self.saved = []

    def get(self, key):
        self.keys.append(key)
        return self.cached_value

    def set(self, key, value):
        self.saved.append((key, value))


class StubAmadeusFlightService:
    def __init__(self):
        self.get_calls = []

    def search_flights_get(self, criteria):
        self.get_calls.append(criteria)
        return [{"id": "flight_1"}]

    def search_flights(self, criteria):
        raise AssertionError("GET flight search flow must not call POST search")


def test_search_flights_returns_cached_response_without_provider_call():
    provider = StubFlightProvider()
    cache = StubFlightCache(cached_value=[{"id": "cached_flight"}])
    use_case = SearchFlights(provider=provider, cache=cache)

    response = use_case.execute(
        {
            "originLocationCode": "NYC",
            "destinationLocationCode": "LON",
            "departureDate": "2024-12-01",
            "adults": 1,
        }
    )

    assert response == [{"id": "cached_flight"}]
    assert provider.calls == []
    assert cache.keys == [EXPECTED_CACHE_KEY]


def test_search_flights_returns_cached_empty_response_without_provider_call():
    provider = StubFlightProvider()
    cache = StubFlightCache(cached_value=[])
    use_case = SearchFlights(provider=provider, cache=cache)

    response = use_case.execute(
        {
            "originLocationCode": "NYC",
            "destinationLocationCode": "LON",
            "departureDate": "2024-12-01",
            "adults": 1,
        }
    )

    assert response == []
    assert provider.calls == []
    assert cache.keys == [EXPECTED_CACHE_KEY]


def test_search_flights_fetches_and_caches_provider_response_on_cache_miss():
    provider = StubFlightProvider()
    cache = StubFlightCache()
    use_case = SearchFlights(provider=provider, cache=cache)
    criteria = {
        "originLocationCode": "NYC",
        "destinationLocationCode": "LON",
        "departureDate": "2024-12-01",
        "adults": 1,
    }

    response = use_case.execute(criteria)

    assert response == [{"id": "flight_1"}]
    assert provider.calls == [criteria]
    assert cache.saved == [(EXPECTED_CACHE_KEY, [{"id": "flight_1"}])]


def test_amadeus_search_gateway_uses_get_search_method():
    flight_service = StubAmadeusFlightService()
    gateway = AmadeusSearchGateway(flight_service)
    criteria = {
        "originLocationCode": "NYC",
        "destinationLocationCode": "LON",
        "departureDate": "2024-12-01",
        "adults": 1,
    }

    response = gateway.search(criteria)

    assert response == [{"id": "flight_1"}]
    assert flight_service.get_calls == [criteria]
