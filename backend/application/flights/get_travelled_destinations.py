import json
from typing import Any, Protocol


TravelledDestinationsResult = list[dict[str, Any]]


class TravelledDestinationsError(Exception):
    pass


class InvalidTravelledDestinationsRequest(TravelledDestinationsError):
    pass


class TravelledDestinationsProviderError(TravelledDestinationsError):
    pass


class TravelledDestinationsProvider(Protocol):
    def get_travelled_destinations(
        self, *, origin_city_code: str, period: str
    ) -> TravelledDestinationsResult: ...


class TravelledDestinationsCache(Protocol):
    def get(self, key: str) -> TravelledDestinationsResult | None: ...

    def set(self, key: str, value: TravelledDestinationsResult) -> None: ...


class GetTravelledDestinations:
    def __init__(
        self,
        *,
        provider: TravelledDestinationsProvider,
        cache: TravelledDestinationsCache,
    ):
        self.provider = provider
        self.cache = cache

    def execute(
        self, *, origin_city_code: str, period: str
    ) -> TravelledDestinationsResult:
        cache_key = self._build_cache_key(
            origin_city_code=origin_city_code,
            period=period,
        )

        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        response = self.provider.get_travelled_destinations(
            origin_city_code=origin_city_code,
            period=period,
        )
        if response:
            self.cache.set(cache_key, response)
        return response

    @staticmethod
    def _build_cache_key(*, origin_city_code: str, period: str) -> str:
        normalized = json.dumps(
            {"origin_city_code": origin_city_code, "period": period},
            sort_keys=True,
            separators=(",", ":"),
        )
        return f"travelled_destinations:{normalized}"
