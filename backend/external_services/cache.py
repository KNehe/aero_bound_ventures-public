import redis
import json
import os


class RedisCache:
    def __init__(self, host: str, port: int):
        self.r = redis.Redis(host=host, port=port, db=0, decode_responses=True)

    def set(self, key: str, value, expiration_seconds: int = 300):
        try:
            json_value = json.dumps(value)
            self.r.setex(key, expiration_seconds, json_value)
        except redis.exceptions.ConnectionError as e:
            print(f"Redis connection error: {e}")

    def get(self, key: str):
        try:
            json_value = self.r.get(key)
            if json_value:
                return json.loads(json_value)
            return None
        except redis.exceptions.ConnectionError as e:
            print(f"Redis connection error: {e}")
            return None


host = os.getenv("REDIS_HOST", "redis")
port = os.getenv("REDIS_PORT", 6379)
redis_cache = RedisCache(host, port)
