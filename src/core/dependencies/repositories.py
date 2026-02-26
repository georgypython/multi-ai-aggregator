from dishka import Provider, Scope, provide

from src.repositories import UserRepository, AIModelRepository


class RepositoriesProvider(Provider):
    @provide(scope=Scope.APP)
    def get_user_repository(
        self,
    ) -> UserRepository:
        return UserRepository()

    @provide(scope=Scope.APP)
    def get_ai_model_repository(
        self,
    ) -> AIModelRepository:
        return AIModelRepository()
