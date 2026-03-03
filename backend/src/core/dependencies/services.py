from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dishka import Provider, Scope, provide

from src.core.config import settings
from src.services.ai_models import AIModelsService
from src.services.generation_billing import GenerationBillingService
from src.services.llm_configuration import LLMConfigurationService
from src.services.llm_generation import LLMGenerationService
from src.services.openrouter import OpenRouterService
from src.repositories import (
    AIModelRepository,
    UserRepository,
    LLMRepository,
    LLMConfigurationRepository,
    GenerationRepository,
    ChatMemoryRepository,
    TokenPriceRepository,
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
    def get_generation_billing_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        token_price_repo: TokenPriceRepository,
        generation_repo: GenerationRepository,
    ) -> GenerationBillingService:
        return GenerationBillingService(
            session=session,
            user_repo=user_repo,
            generation_repo=generation_repo,
            token_price_repo=token_price_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_generation_service(
        self,
        session: AsyncSession,
        llm_client: OpenRouterService,
        user_repo: UserRepository,
        llm_repo: LLMRepository,
        chat_memory_repo: ChatMemoryRepository,
        generation_billing_service: GenerationBillingService,
    ) -> LLMGenerationService:
        return LLMGenerationService(
            session=session,
            llm_client=llm_client,
            user_repo=user_repo,
            llm_repo=llm_repo,
            chat_memory_repo=chat_memory_repo,
            generation_billing_service=generation_billing_service,
        )

    @provide(scope=Scope.REQUEST)
    def get_ai_models_service(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        user_repo: UserRepository,
    ) -> AIModelsService:
        return AIModelsService(
            session=session,
            ai_model_repo=ai_model_repo,
            user_repo=user_repo,
        )

    @provide(scope=Scope.REQUEST)
    def get_llm_configuration_service(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        llm_configuration_repo: LLMConfigurationRepository,
    ) -> LLMConfigurationService:
        return LLMConfigurationService(
            session=session,
            user_repo=user_repo,
            llm_configuration_repo=llm_configuration_repo,
        )
