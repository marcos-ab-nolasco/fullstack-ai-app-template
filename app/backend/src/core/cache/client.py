from functools import lru_cache

from redis.asyncio import Redis

from src.core.config import get_settings

settings = get_settings()


@lru_cache(1)
def get_redis_client() -> Redis:
    return Redis.from_url(url=settings.REDIS_URL.get_secret_value())
