from typing import AsyncGenerator
import httpx
from redis.asyncio import Redis

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.models.db_helper import db_helper


class InfrastructureProvider(Provider):

    @provide(scope=Scope.REQUEST)
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with db_helper.session_factory() as session:
            yield session

    @provide(scope=Scope.APP)
    async def get_http_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            yield client

    @provide(scope=Scope.APP)
    async def get_redis_client(self) -> AsyncGenerator[Redis, None]:
        redis_client = Redis.from_url(
            settings.redis.url,
            decode_responses=True,
            encoding="utf-8",
        )
        try:
            yield redis_client
        finally:
            await redis_client.aclose()
