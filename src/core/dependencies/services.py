from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dishka import Provider, Scope, provide

from src.core.config import settings
from src.services.llm import LLMService
from src.services.openrouter import OpenRouterService
from src.repositories import UserRepository, AIModelRepository


class ServicesProvider(Provider):
    @provide(scope=Scope.APP)
    def get_openrouter_service(
        self,
        client: AsyncClient,
    ) -> OpenRouterService:
        return OpenRouterService(
            client=client,
            api_key=settings.openrouter.api_key,
            base_url=settings.openrouter.base_url,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_service(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        user_repo: UserRepository,
        ai_model_repo: AIModelRepository,
    ) -> LLMService:
        return LLMService(
            session=session,
            llm_client=llm_client,
            user_repo=user_repo,
            ai_model_repo=ai_model_repo,
        )
