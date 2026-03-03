from collections.abc import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from dishka import AsyncContainer

from src.core.config import settings
from src.services.ai import AIService


class ServicesProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_ai_service(self) -> AsyncIterator[AIService]:
        service = AIService(
            base_url=settings.ai.ai_api_url,
            api_key=settings.ai.api_key,
            timeout_seconds=settings.ai.request_timeout_seconds,
        )
        try:
            yield service
        finally:
            await service.aclose()


container: AsyncContainer = make_async_container(ServicesProvider())
