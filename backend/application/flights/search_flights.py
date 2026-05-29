import json
from collections.abc import Mapping
from typing import Any, Protocol


FlightSearchResult = list[dict[str, Any]]


class FlightSearchError(Exception):
    pass


class InvalidFlightSearchRequest(FlightSearchError):
    pass


class FlightSearchProviderError(FlightSearchError):
    pass


class FlightSearchCache(Protocol):
    def get(self, key: str) -> FlightSearchResult | None:
        ...

    def set(self, key: str, value: FlightSearchResult) -> None:
        ...


class FlightSearchProvider(Protocol):
    def search(self, criteria: dict[str, Any]) -> FlightSearchResult:
        ...


class SearchFlights:
    def __init__(self, provider: FlightSearchProvider, cache: FlightSearchCache):
        self.provider = provider
        self.cache = cache

    def execute(self, criteria: Mapping[str, Any]) -> FlightSearchResult:
        request_body = dict(criteria)
        cache_key = self._build_cache_key(request_body)

        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        response = self.provider.search(request_body)
        self.cache.set(cache_key, response)
        return response

    @staticmethod
    def _build_cache_key(data: Mapping[str, Any]) -> str:
        normalized = json.dumps(dict(data), sort_keys=True, separators=(",", ":"))
        return f"flight_search:{normalized}"
