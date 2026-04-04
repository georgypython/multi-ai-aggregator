from typing import AsyncGenerator
import httpx
import boto3
from botocore.client import BaseClient, Config
from redis.asyncio import Redis

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.db_helper import db_helper


class InfrastructureProvider(Provider):

    @provide(scope=Scope.APP)
    def get_s3_client(self) -> BaseClient:
        return boto3.client(
            "s3",
            endpoint_url=settings.storage.endpoint_url,
            region_name=settings.storage.region,
            aws_access_key_id=settings.storage.access_key,
            aws_secret_access_key=settings.storage.secret_key,
            config=Config(
                signature_version="s3v4",
                connect_timeout=settings.storage.connect_timeout_seconds,
                read_timeout=settings.storage.read_timeout_seconds,
                retries={
                    "max_attempts": settings.storage.max_retry_attempts,
                    "mode": "standard",
                },
                s3={"addressing_style": "path"},
                tcp_keepalive=True,
            ),
        )

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
