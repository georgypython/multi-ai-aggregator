from fastapi import Depends, HTTPException, Query, Response, status
from redis.asyncio import Redis

from .redis_client import get_redis


class TgRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: int,
        path_name_key: str = "global",
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.path_name_key = path_name_key

    async def __call__(
        self,
        response: Response,
        tg_user_id: int = Query(..., ge=1),
        redis: Redis = Depends(get_redis),
    ) -> None:
        key = f"rl:{self.path_name_key}:tg:{tg_user_id}"

        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, self.window_seconds)

        ttl = await redis.ttl(key)
        if ttl < 0:
            ttl = self.window_seconds

        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - current))
        response.headers["X-RateLimit-Reset"] = str(ttl)

        if current > self.limit:
            response.headers["Retry-After"] = str(ttl)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests: {self.limit}/{self.window_seconds}s",
            )
