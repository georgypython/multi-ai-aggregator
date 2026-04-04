from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models import LLMConfiguration, User
from src.models.enums import LLMConfigurationType
from src.schemas import LLMConfigCreateRequestSchema, LLMConfigResponseSchema
from src.services.db_access import DBAccessService


class LLMConfigurationService(DBAccessService):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

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
        user = await self.get_one(
            model=User,
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        llm_config = await self.get_one(
            model=LLMConfiguration,
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
        )

        payload_data = payload.model_dump(exclude_unset=True)
        if not llm_config:
            llm_config = LLMConfiguration(
                user_id=user_id,
                configuration_type=LLMConfigurationType.USER,
                **payload_data,
            )
            self.session.add(llm_config)
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
        user = await self.get_one(
            model=User,
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")

        config = await self.get_one(
            model=LLMConfiguration,
            user_id=user_id,
            configuration_type=LLMConfigurationType.USER,
        )
        if not config:
            raise ValueError(f"LLMConfiguration not found for user_id={user_id}")

        return self._build_llm_config_response(config=config)
