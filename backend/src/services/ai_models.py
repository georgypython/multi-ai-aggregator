from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enums import ModelType
from src.schemas.ai import AIModelListItemResponseSchema
from src.repositories import AIModelRepository, UserRepository


class AIModelsService:
    def __init__(
        self,
        session: AsyncSession,
        ai_model_repo: AIModelRepository,
        user_repo: UserRepository,
    ) -> None:
        self.session = session
        self.ai_model_repo = ai_model_repo
        self.user_repo = user_repo

    async def get_ai_models_list(
        self,
        user_id: UUID,
        model_type: ModelType | None = None,
        active_only: bool = True,
    ) -> list[AIModelListItemResponseSchema]:
        async with self.session.begin():
            user = await self.user_repo.get_one(
                session=self.session,
                id=user_id,
                is_active=True,
            )
            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            filters: dict[str, object] = {}
            if model_type is not None:
                filters["model_type"] = model_type
            if active_only:
                filters["is_active"] = True

            ai_models = await self.ai_model_repo.get_all(
                session=self.session, **filters
            )

        result: list[AIModelListItemResponseSchema] = []
        for ai_model in ai_models:
            result.append(
                AIModelListItemResponseSchema(
                    id=ai_model.id,
                    name=ai_model.name,
                    provider_key=ai_model.provider_key,
                    is_active=ai_model.is_active,
                    description=ai_model.description,
                    model_type=ai_model.model_type,
                    created_at=ai_model.created_at,
                )
            )
        return result
