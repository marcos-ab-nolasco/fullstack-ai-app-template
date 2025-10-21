from functools import lru_cache
from typing import Any
from redis import Redis
# from redis.asyncio import Redis as AsyncioRedis

from src.core.config import get_settings

settings = get_settings()

# @lru_cache(1)
# def get_redis_async_client() -> "AsyncioRedis[Any]":
#     return AsyncioRedis.from_url(url=settings.REDIS_URL.get_secret_value())


@lru_cache(1)
def get_redis_sync_client() -> "Redis[Any]":
    return Redis.from_url(url=settings.REDIS_URL.get_secret_value())
