from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dishka import Provider, Scope, provide

from src.core.config import settings
from src.services.llm import LLMService
from src.services.openrouter import OpenRouterService
from src.repositories import (
    AIModelRepository,
    UserRepository, 
    LLMRepository, 
    LLMConfigurationRepository,
    GenerationRepository, 
    ChatMemoryRepository, 
    TokenPriceRepository
)

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
        ai_model_repo: AIModelRepository,
        user_repo: UserRepository,
        llm_repo: LLMRepository,
        llm_configuration_repo: LLMConfigurationRepository,
        generation_repo: GenerationRepository,
        chat_memory_repo: ChatMemoryRepository,
        token_price_repo: TokenPriceRepository,
    ) -> LLMService:
        return LLMService(
            session=session,
            llm_client=llm_client,
            ai_model_repo=ai_model_repo,
            user_repo=user_repo,
            llm_repo=llm_repo,
            llm_configuration_repo=llm_configuration_repo,
            generation_repo=generation_repo,
            chat_memory_repo=chat_memory_repo,
            token_price_repo=token_price_repo,
        )
