from dishka import (
    Provider, 
    Scope, 
    provide
)
from redis.asyncio import Redis

from src.repositories import (
    UserRepository,
    LLMRepository,
    GenerationRepository,
    ChatMemoryRepository,
)


class RepositoriesProvider(Provider):
    @provide(scope=Scope.APP)
    def get_user_repository(
        self,
    ) -> UserRepository:
        return UserRepository()

    @provide(scope=Scope.APP)
    def get_llm_repository(
        self,
    ) -> LLMRepository:
        return LLMRepository()

    @provide(scope=Scope.APP)
    def get_generation_repository(
        self,
    ) -> GenerationRepository:
        return GenerationRepository()

    @provide(scope=Scope.APP)
    def get_chat_memory_repository(
        self,
        redis_client: Redis,
    ) -> ChatMemoryRepository:
        return ChatMemoryRepository(redis_client=redis_client)
