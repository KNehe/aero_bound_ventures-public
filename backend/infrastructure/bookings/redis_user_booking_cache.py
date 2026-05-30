from uuid import UUID

from backend.external_services.cache import RedisCache


class RedisUserBookingCache:
    def __init__(self, cache: RedisCache):
        self.cache = cache

    def get(self, cache_key: str) -> dict | None:
        return self.cache.get(cache_key)

    def set(self, cache_key: str, value: dict) -> None:
        self.cache.set(cache_key, value)

    def invalidate_user_bookings(self, user_id: UUID) -> None:
        self.cache.delete_pattern(f"user_bookings:{str(user_id)}*")
