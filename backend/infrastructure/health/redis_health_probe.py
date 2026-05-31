import redis


class RedisHealthProbe:
    service_name = "redis"

    def __init__(self, redis_url: str):
        self.redis_url = redis_url

    def check(self) -> None:
        client = redis.from_url(self.redis_url)
        client.ping()
