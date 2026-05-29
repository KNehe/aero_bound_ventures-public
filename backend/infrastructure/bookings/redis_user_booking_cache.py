from uuid import UUID

from backend.external_services.cache import RedisCache


class RedisUserBookingCache:
    def __init__(self, cache: RedisCache):
        self.cache = cache

    def invalidate_user_bookings(self, user_id: UUID) -> None:
        self.cache.delete_pattern(f"user_bookings:{str(user_id)}*")
