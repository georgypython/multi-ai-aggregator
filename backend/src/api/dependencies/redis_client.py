from typing import AsyncGenerator

from redis.asyncio import Redis

from src.core.config import settings


async def get_redis() -> AsyncGenerator[Redis, None]:
    redis = Redis.from_url(settings.redis.url)
    try:
        yield redis
    finally:
        await redis.aclose()
