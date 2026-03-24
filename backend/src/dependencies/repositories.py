from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.repositories import (
    AIModelRepository,
    UserRepository,
    LLMProfileRepository,
    LLMConfigurationRepository,
    GenerationRepository,
    MediaFilesRepository,
    ChatMemoryRepository,
    TokenPriceRepository,
    ImageProfileRepository,
    ImagePriceRepository,
    VideoProfileRepository,
    VideoPriceRepository,
)


class RepositoriesProvider(Provider):
    @provide(scope=Scope.APP)
    def get_ai_model_repository(
        self,
    ) -> AIModelRepository:
        return AIModelRepository()

    @provide(scope=Scope.APP)
    def get_user_repository(
        self,
    ) -> UserRepository:
        return UserRepository()

    @provide(scope=Scope.APP)
    def get_llm_repository(
        self,
    ) -> LLMProfileRepository:
        return LLMProfileRepository()

    @provide(scope=Scope.APP)
    def get_llm_configuration_repository(
        self,
    ) -> LLMConfigurationRepository:
        return LLMConfigurationRepository()

    @provide(scope=Scope.APP)
    def get_generation_repository(
        self,
    ) -> GenerationRepository:
        return GenerationRepository()

    @provide(scope=Scope.APP)
    def get_media_files_repository(
        self,
    ) -> MediaFilesRepository:
        return MediaFilesRepository()

    @provide(scope=Scope.APP)
    def get_chat_memory_repository(
        self,
        redis_client: Redis,
    ) -> ChatMemoryRepository:
        return ChatMemoryRepository(redis_client=redis_client)

    @provide(scope=Scope.APP)
    def get_token_price_repository(
        self,
    ) -> TokenPriceRepository:
        return TokenPriceRepository()

    @provide(scope=Scope.APP)
    def get_image_profile_repository(
        self,
    ) -> ImageProfileRepository:
        return ImageProfileRepository()

    @provide(scope=Scope.APP)
    def get_image_price_repository(
        self,
    ) -> ImagePriceRepository:
        return ImagePriceRepository()

    @provide(scope=Scope.APP)
    def get_video_profile_repository(
        self,
    ) -> VideoProfileRepository:
        return VideoProfileRepository()

    @provide(scope=Scope.APP)
    def get_video_price_repository(
        self,
    ) -> VideoPriceRepository:
        return VideoPriceRepository()
