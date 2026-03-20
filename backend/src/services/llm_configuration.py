from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import LLMConfiguration
from src.models.enums import LLMConfigurationType
from src.schemas.ai import LLMConfigCreateRequestSchema, LLMConfigResponseSchema
from src.repositories import UserRepository, LLMConfigurationRepository


class LLMConfigurationService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        llm_configuration_repo: LLMConfigurationRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo
        self.llm_configuration_repo = llm_configuration_repo

    def _build_llm_config_response(
        self, config: LLMConfiguration
    ) -> LLMConfigResponseSchema:
        return LLMConfigResponseSchema(
            id=config.id,
            user_id=config.user_id,
            name=config.name,
            configuration_type=config.configuration_type,
            temperature=config.temperature,
            instructions=config.instructions,
            created_at=config.created_at,
        )

    async def create_or_update_user_llm_config(
        self,
        user_id: UUID,
        payload: LLMConfigCreateRequestSchema,
    ) -> LLMConfigResponseSchema:
        user = await self.user_repo.get_one(
            session=self.session,
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        llm_config = await self.llm_configuration_repo.get_one(
            session=self.session,
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
        )

        payload_data = payload.model_dump(exclude_unset=True)
        if not llm_config:
            llm_config = self.llm_configuration_repo.add_user_config(
                session=self.session,
                user_id=user_id,
                data=payload_data,
            )
        else:
            for key, value in payload_data.items():
                setattr(llm_config, key, value)

        await self.session.commit()
        await self.session.refresh(llm_config)

        return self._build_llm_config_response(llm_config)

    async def get_user_llm_config(
        self,
        user_id: UUID,
    ) -> LLMConfigResponseSchema:
        user = await self.user_repo.get_one(
            session=self.session,
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        config = await self.llm_configuration_repo.get_one(
            session=self.session,
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
        )
        if not config:
            raise ValueError(f"LLMConfiguration not found for user_id={user_id}")

        return self._build_llm_config_response(config=config)
