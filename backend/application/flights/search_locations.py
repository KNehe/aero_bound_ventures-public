import json
from collections.abc import Mapping
from typing import Any, Protocol


LocationSearchResult = list[dict[str, Any]]


class LocationSearchError(Exception):
    pass


class InvalidLocationSearchRequest(LocationSearchError):
    pass


class LocationSearchProviderError(LocationSearchError):
    pass


class LocationSearchProvider(Protocol):
    def search_locations(self, criteria: dict[str, Any]) -> LocationSearchResult: ...


class LocationSearchCache(Protocol):
    def get(self, key: str) -> LocationSearchResult | None: ...

    def set(self, key: str, value: LocationSearchResult) -> None: ...


class SearchLocations:
    def __init__(self, *, provider: LocationSearchProvider, cache: LocationSearchCache):
        self.provider = provider
        self.cache = cache

    def execute(self, criteria: Mapping[str, Any]) -> LocationSearchResult:
        request_body = dict(criteria)
        cache_key = self._build_cache_key(request_body)

        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        response = self.provider.search_locations(request_body)
        self.cache.set(cache_key, response)
        return response

    @staticmethod
    def _build_cache_key(data: Mapping[str, Any]) -> str:
        normalized = json.dumps(dict(data), sort_keys=True, separators=(",", ":"))
        return f"location_search:{normalized}"
