from collections.abc import AsyncIterator

from dishka import Provider, Scope, make_async_container, provide
from dishka import AsyncContainer

from src.core.config import settings
from src.services.ai import AIService
from src.services.image_generation import ImageGenerationService
from src.services.llm_generation import LLMGenerationService


class ServicesProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_ai_service(self) -> AsyncIterator[AIService]:
        ai_service = AIService(
            base_url=settings.ai.ai_api_url,
            api_key=settings.ai.api_key,
            timeout_seconds=settings.ai.request_timeout_seconds,
        )
        try:
            yield ai_service
        finally:
            await ai_service.aclose()

    @provide(scope=Scope.APP)
    async def get_llm_generation_service(self) -> AsyncIterator[LLMGenerationService]:
        llm_generation_service = LLMGenerationService(
            base_url=settings.ai.ai_api_url,
            api_key=settings.ai.api_key,
            timeout_seconds=settings.ai.request_timeout_seconds,
        )
        try:
            yield llm_generation_service
        finally:
            await llm_generation_service.aclose()

    @provide(scope=Scope.APP)
    async def get_image_generation_service(self) -> AsyncIterator[ImageGenerationService]:
        image_generation_service = ImageGenerationService(
            base_url=settings.ai.ai_api_url,
            api_key=settings.ai.api_key,
            timeout_seconds=settings.ai.request_timeout_seconds,
        )
        try:
            yield image_generation_service
        finally:
            await image_generation_service.aclose()


container: AsyncContainer = make_async_container(ServicesProvider())
