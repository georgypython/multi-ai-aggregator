from typing import AsyncGenerator
import httpx

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

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
